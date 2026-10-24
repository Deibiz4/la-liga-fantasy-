"""SELL advisor: who to offload and at what price.

Safe rule: only proposes selling players NOT in your optimal XI (so it doesn't
break your lineup) and only for a clear reason:
  1) Transfer risk: valuable but outside the probable lineup (the ⚠ Etta types) →
     sell him before he leaves LaLiga and his value collapses.
  2) Falling value: his trend is clearly negative → cash in before losing more.

It does NOT touch a cheap backup whose value is rising or stable (an appreciating
asset or useful rotation).
"""

import time

from ..matching import match_name, POS
from .lineup import payload_ids

FALLING_THRESHOLD = -20  # trend (from futbolfantasy) below which it's "falling"


def sell_candidates(team, best, trends_index, falling_threshold=FALLING_THRESHOLD):
    """Players recommended to sell, with reason, priority and suggested price.

    `best` may be None when the squad can't field a valid XI yet (e.g. no goalkeeper).
    A missing lineup shouldn't silence the sell advice — there are simply no protected
    starters, so we fall back to flagging clearly-falling-value players.
    """
    xi_ids = payload_ids(best) if best else set()
    watch_ids = {w["playerTeamId"] for w in best.get("watch", [])} if best else set()

    out = []
    for p in team["players"]:
        pm = p["playerMaster"]
        ptid = p.get("playerTeamId") or pm["id"]
        if ptid in xi_ids:
            continue  # he's a starter → don't sell

        valor = pm.get("marketValue") or 0
        trend = match_name(pm.get("nickname", ""), pm.get("name", ""), trends_index)
        tendencia = trend.get("tendencia") if trend else None

        if ptid in watch_ids:
            reason, prio = "transfer risk (out of the lineup, valuable)", 1
        elif tendencia is not None and tendencia <= falling_threshold:
            reason, prio = f"falling value (trend {tendencia})", 2
        else:
            continue  # stable/rising backup → keep

        out.append({
            "nombre": pm.get("nickname") or pm.get("name"),
            "player_id": pm.get("id"),
            "pos": POS.get(pm.get("positionId"), "?"),
            "valor": valor,
            "sale_price": round(valor),  # fair price for a quick sale
            "tendencia": tendencia,
            "reason": reason,
            "priority": prio,
        })
    out.sort(key=lambda c: (c["priority"], -c["valor"]))
    return out


FLIP_MAX_HOLD_DAYS = 7  # = flip.DEFAULT_HORIZON: the projection the buy was based on


def flip_exits(team, best, flips, now=None):
    """Flips to close: bought to resell, so sell once the target margin is reached, or
    after FLIP_MAX_HOLD_DAYS if it never got there (the projection failed; dead money
    and a wasted squad slot). A flip that made it into the optimal XI is kept for now.
    """
    now = time.time() if now is None else now
    xi_ids = payload_ids(best) if best else set()
    out = []
    for p in team["players"]:
        pm = p["playerMaster"]
        f = flips.get(str(pm.get("id")))
        if not f or (p.get("playerTeamId") or pm["id"]) in xi_ids:
            continue
        valor = pm.get("marketValue") or 0
        buy = f.get("buy_price") or 0
        gain_pct = round((valor / buy - 1) * 100, 1) if buy else 0.0
        held_days = (now - (f.get("bought_at") or now)) / 86400
        if gain_pct >= f.get("target_pct", 0):
            reason = f"flip closed: target reached ({gain_pct:+.1f}%)"
        elif held_days >= FLIP_MAX_HOLD_DAYS:
            reason = f"flip expired: {int(held_days)} days, {gain_pct:+.1f}%"
        else:
            continue
        out.append({
            "nombre": pm.get("nickname") or pm.get("name"),
            "player_id": pm.get("id"),
            "pos": POS.get(pm.get("positionId"), "?"),
            "valor": valor,
            "sale_price": round(valor),
            "tendencia": None,
            "reason": reason,
            "priority": 0,
        })
    return out
