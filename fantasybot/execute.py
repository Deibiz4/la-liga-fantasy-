"""EXECUTION layer: turns decisions into real actions.

Autonomy authorized by the user:
  - Lineup: applies the best lineup (reversible, no spending).
  - Bid/cancel in market: places bids on profitable flips and pulls those that no
    longer apply (reversible until market close). May use the whole balance.
  - Buyouts: NOT automatic (irreversible spending) → left as an alert/task.

Everything runs through `dry_run`: if True, it only returns the PLAN without
touching anything.
"""

import time

from . import events, state
from .strategy import flip
from .strategy.lineup import payload_ids


def apply_lineup(client, team_id, best, current_ids, dry_run=True):
    """Applies the optimal lineup if it differs from the current one."""
    new_ids = payload_ids(best)
    if new_ids == current_ids:
        return {"action": "lineup", "changed": False}
    if not dry_run:
        client.update_lineup(team_id, best["payload"])
        d, m, f = best["formation"]
        events.emit("lineup", f"Lineup {d}-{m}-{f} applied",
                    detail={"score": best.get("total")})
    return {"action": "lineup", "changed": True, "applied": not dry_run,
            "formation": best["formation"]}


# Same bar as the flip alerts: a +0.6% "margin" on a 0.5M benchwarmer is trend noise,
# not a flip, and it burns a squad slot on a player who never scores.
MIN_FLIP_MARGIN_PCT = 3.0
MIN_FLIP_MARGIN = 200_000


def _system_flips(client, league_id):
    """Profitable SYSTEM flips (a single pass over market + trends).

    Only real flips: margin over the alert thresholds and a player who has actually
    scored this season (0 points = hasn't played all year).
    """
    return [o for o in flip.opportunities(client, league_id)
            if o["via"] == "SISTEMA"
            and o["margin_pct"] >= MIN_FLIP_MARGIN_PCT
            and o["margin"] >= MIN_FLIP_MARGIN
            and o["points"] > 0]


def plan_bids(client, league_id, team, ops=None, chat_id=None):
    """What to bid on: profitable SYSTEM flips that fit the balance, by margin.

    SYSTEM only (auction). Buyouts are outside the scope of autonomy.
    """
    money = team["teamMoney"]
    if ops is None:
        ops = _system_flips(client, league_id)
    already = state.load_bids(chat_id)
    plan, committed = [], 0
    for o in ops:
        if o["market_id"] in already:
            continue  # we already have a bid in local state
        if o.get("has_my_bid"):
            continue  # we already have an active bid on the server
        if committed + o["buy_price"] > money:
            continue  # doesn't fit in the balance
        plan.append({"market_id": o["market_id"], "nombre": o["nombre"],
                     "player_id": o["player_id"],
                     "amount": o["buy_price"], "margin_pct": o["margin_pct"]})
        committed += o["buy_price"]
    return plan


def sync_bids(client, league_id, team, dry_run=True, chat_id=None):
    """Places new bids from the plan and cancels those that no longer apply."""
    ops = _system_flips(client, league_id)   # a single pass, reused below
    plan = plan_bids(client, league_id, team, ops, chat_id=chat_id)
    bids = state.load_bids(chat_id)
    valid_ids = {o["market_id"] for o in ops}

    placed, cancelled = [], []
    won = _record_won_flips(team, bids, chat_id, dry_run)
    # cancel bids whose target is no longer profitable
    for mid, info in list(bids.items()):
        if mid in won:
            continue
        if mid not in valid_ids:
            if not dry_run:
                try:
                    client.cancel_bid(league_id, mid, info["bid_id"])
                except Exception:
                    pass
                bids.pop(mid, None)
                events.emit("cancel", f"Bid cancelled: {info.get('nombre', mid)}",
                            detail="no longer profitable")
            cancelled.append(info.get("nombre", mid))
    # place new bids
    for b in plan:
        if not dry_run:
            try:
                resp = client.make_bid(league_id, b["market_id"], b["amount"])
                bid_id = resp.get("id") if isinstance(resp, dict) else None
                bids[b["market_id"]] = {"bid_id": bid_id, "amount": b["amount"],
                                        "nombre": b["nombre"], "player_id": b["player_id"],
                                        "margin_pct": b["margin_pct"]}
                events.emit("bid", f"Bid {b['amount']:,} for {b['nombre']}",
                            detail={"margin": f"{b['margin_pct']}%"})
                placed.append(b)
            except Exception as e:
                # If we already have a pending bid on this player, record it and continue gracefully
                if "030.01.09" in str(e) or "pending bid" in str(e).lower():
                    bids[b["market_id"]] = {"amount": b["amount"], "nombre": b["nombre"],
                                            "player_id": b["player_id"],
                                            "margin_pct": b["margin_pct"]}
                else:
                    raise
        else:
            placed.append(b)

    if not dry_run:
        state.save_bids(bids, chat_id)
    return {"action": "bids", "placed": placed, "cancelled": cancelled,
            "won": [w.get("nombre") for w in won.values()],
            "applied": not dry_run}


def _record_won_flips(team, bids, chat_id, dry_run):
    """Bids whose player is now in the squad were WON: remember them as flips to resell
    (buy price, date, target) and drop them from the open bids. Returns {market_id: bid}.
    Older bid records have no player_id, so they fall back to the player name."""
    by_id = {str(p["playerMaster"].get("id")): p["playerMaster"] for p in team["players"]}
    by_name = {(pm.get("nickname") or pm.get("name")): pid for pid, pm in by_id.items()}
    flips = state.load_flips(chat_id)
    won = {}
    for mid, info in list(bids.items()):
        pid = str(info["player_id"]) if info.get("player_id") else by_name.get(info.get("nombre"))
        if not pid or pid not in by_id:
            continue
        won[mid] = info
        flips[pid] = {"nombre": info.get("nombre"), "buy_price": info.get("amount"),
                      "bought_at": int(time.time()),
                      "target_pct": max(info.get("margin_pct") or 0, MIN_FLIP_MARGIN_PCT)}
        if not dry_run:
            bids.pop(mid, None)
            events.emit("flip", f"Flip bought: {info.get('nombre')}",
                        detail={"price": info.get("amount")})
    if won and not dry_run:
        state.save_flips(flips, chat_id)
    return won


def _best_offer(item):
    offers = [o for o in (item.get("bids") or item.get("offers") or [])
              if o.get("id") and (o.get("money") or o.get("amount") or o.get("offerMoney"))]
    return max(offers, key=lambda o: o.get("money") or o.get("amount") or o.get("offerMoney"),
               default=None)


def sync_sells(client, league_id, team_id, team, best, dry_run=True, chat_id=None):
    """Lists players to sell and accepts offers on our listings.

    Sells: flips that hit their target or expired (see `sell.flip_exits`), plus the
    standard non-XI candidates (transfer risk / falling value). Offers: only the BEST
    one per listing, and only at or above the player's current value — we never sell
    below what he's worth.
    """
    from .sources.market_trends import trends_index
    from .strategy import sell as sell_mod

    flips = state.load_flips(chat_id)
    squad = {str(p["playerMaster"].get("id")) for p in team["players"]}
    gone = [pid for pid in flips if pid not in squad]   # sold (or stolen) → no longer held
    for pid in gone:
        flips.pop(pid)
    if gone and not dry_run:
        state.save_flips(flips, chat_id)

    candidates = sell_mod.flip_exits(team, best, flips)
    seen = {str(c["player_id"]) for c in candidates}
    candidates += [c for c in sell_mod.sell_candidates(team, best, trends_index())
                   if str(c["player_id"]) not in seen]

    market = client.market(league_id) or []
    mine = [m for m in market if str((m.get("team") or {}).get("id")) == str(team_id)]
    on_market = {str((m.get("playerMaster") or {}).get("id")) for m in mine}

    listed, accepted = [], []
    for c in candidates:
        if str(c["player_id"]) in on_market:
            continue
        if not dry_run:
            try:
                client.sell_player(league_id, c["player_id"], c["sale_price"])
            except Exception:
                continue
            events.emit("sell", f"Listed {c['nombre']} for {c['sale_price']:,}",
                        detail=c["reason"])
        listed.append(c)

    for item in mine:
        pm = item.get("playerMaster") or {}
        offer = _best_offer(item)
        if not offer:
            continue
        money = offer.get("money") or offer.get("amount") or offer.get("offerMoney")
        if money < (pm.get("marketValue") or item.get("salePrice") or 0):
            continue
        nombre = pm.get("nickname") or pm.get("name") or "Jugador"
        if not dry_run:
            try:
                client.accept_offer(league_id, item.get("id"), offer["id"], money)
            except Exception:
                continue
            events.emit("sale", f"Sold {nombre} for {money:,}")
        accepted.append({"nombre": nombre, "money": money})

    return {"action": "sells", "listed": listed, "accepted": accepted,
            "applied": not dry_run}


def act(client, league_id, team_id, team, best, current_ids, dry_run=True, chat_id=None):
    """Executes (or plans) the autonomous actions: set lineup + bid."""
    return {
        "lineup": apply_lineup(client, team_id, best, current_ids, dry_run),
        "bids": sync_bids(client, league_id, team, dry_run, chat_id=chat_id),
    }
