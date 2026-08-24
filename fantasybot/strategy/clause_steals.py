"""Rival Clause Robbery & Flip Engine (Clausulazos a Rivales).

Scans all rival squads in the league to identify lucrative clause buyout ("clausulazo")
opportunities by cross-referencing rival players' buyout clauses with FutbolFantasy
real-time market trend trajectories, player points, and protection ratios.
"""

from typing import Any, Dict, List, Optional, Set
from ..matching import match_name, POS
from ..sources.market_trends import trends_index
from .flip import daily_rate, project, DEFAULT_HORIZON, SELL_COMMISSION, SANITY_MAX_DIFF


def evaluate_rival_player(
    player: Dict[str, Any],
    manager_info: Dict[str, Any],
    index: Dict[str, Any],
    horizon: int = DEFAULT_HORIZON
) -> Optional[Dict[str, Any]]:
    """Evaluates a single player from a rival squad for a potential clause buyout / flip."""
    pm = player.get("playerMaster") or {}
    player_id = pm.get("id")
    if not player_id:
        return None

    nickname = pm.get("nickname") or pm.get("name") or "Unknown"
    full_name = pm.get("name") or ""
    pos = POS.get(pm.get("positionId"), "?")
    market_value = pm.get("marketValue") or 0
    buyout_clause = player.get("buyoutClause") or 0

    if buyout_clause <= 0 and market_value <= 0:
        return None

    # If buyoutClause is not explicitly set or is zero, fallback to default ~1.67x or market value
    if buyout_clause <= 0:
        buyout_clause = round(market_value * 1.67) if market_value else 0

    protection = max(0, buyout_clause - market_value)
    clause_ratio = round(buyout_clause / market_value, 2) if market_value > 0 else 1.0

    trend = match_name(nickname, full_name, index)
    if trend and trend.get("valor"):
        trend_val = trend["valor"]
        # Sanity check: if trend value is absurdly different, ignore trend extrapolation
        if market_value and abs(trend_val - market_value) / market_value > SANITY_MAX_DIFF:
            rate = 0.0
            proj = float(market_value)
            tendencia = 0
        else:
            rate = daily_rate(trend)
            proj = project(trend, horizon)
            tendencia = trend.get("tendencia", 0)
    else:
        rate = 0.0
        proj = float(market_value)
        tendencia = 0

    margin = proj * (1 - SELL_COMMISSION) - buyout_clause
    margin_pct = (margin / buyout_clause * 100.0) if buyout_clause > 0 else 0.0

    last_season_points = int(pm.get("lastSeasonPoints") or 0)
    points = int(pm.get("points") or 0)
    real_team = (pm.get("team") or {}).get("name") or ""

    # Categorization and Verdict Badges
    if margin_pct > 0:
        badge = "💎 GANGA FLIP"
        verdict = f"ROI positivo (+{margin_pct:.1f}%)! La subida estimada cubre la cláusula."
    elif rate >= 150_000:
        badge = "🚀 COHETE"
        verdict = f"Subiendo +{round(rate):,} €/día. Oportunidad top antes de que suba la cláusula."
    elif rate >= 70_000 and clause_ratio <= 1.35:
        badge = "🔓 DESPROTEGIDO"
        verdict = f"Cláusula muy baja ({clause_ratio}x) y subiendo con fuerza."
    elif rate >= 50_000:
        badge = "📈 EN ALZA"
        verdict = f"Revalorización activa (+{round(rate):,} €/día)."
    elif clause_ratio <= 1.15 and (last_season_points >= 140 or points >= 30):
        badge = "⭐ CRACK ASEQUIBLE"
        verdict = f"Gran rendimiento con cláusula mínima sin blindar ({clause_ratio}x)."
    elif clause_ratio >= 2.5:
        badge = "🛡️ BLINDADO"
        verdict = f"Sobreprotegido por su dueño ({clause_ratio}x su valor)."
    else:
        badge = "⚪ ESTABLE"
        verdict = "Sin diferencial de valor inmediato."

    # Composite Steal Score (higher is better)
    # Rewards positive ROI, high daily rise, low clause ratio and good points
    steal_score = (margin_pct * 3.0) + (rate / 4_000.0) - (clause_ratio * 15.0)
    if last_season_points >= 150 or points >= 40:
        steal_score += 20.0
    if clause_ratio <= 1.25:
        steal_score += 15.0

    return {
        "player_id": player_id,
        "name": nickname,
        "full_name": full_name,
        "pos": pos,
        "real_team": real_team,
        "manager_id": manager_info.get("manager_id"),
        "manager_name": manager_info.get("manager_name", "Rival"),
        "manager_rank": manager_info.get("position", 0),
        "market_value": market_value,
        "buyout_clause": buyout_clause,
        "protection": protection,
        "clause_ratio": clause_ratio,
        "rate_dia": round(rate),
        "tendencia": tendencia,
        "proyeccion": round(proj),
        "margin": round(margin),
        "margin_pct": round(margin_pct, 1),
        "last_season_points": last_season_points,
        "points": points,
        "badge": badge,
        "verdict": verdict,
        "steal_score": round(steal_score, 1),
    }


def find_rival_clause_flips(
    client,
    league_id: str,
    horizon: int = DEFAULT_HORIZON,
    min_daily_rise: int = 0,
    manager_query: Optional[str] = None,
    owned_ids: Optional[Set[Any]] = None
) -> List[Dict[str, Any]]:
    """Scans all rival teams in the league and returns ranked clause flip/robbery targets."""
    teams = client.league_teams(league_id) or []
    index = trends_index()

    # Identify user's own team or player IDs to exclude
    owned: Set[Any] = set(owned_ids) if owned_ids else set()
    for t in teams:
        if t.get("teamMoney") is not None:  # authenticated user's team
            for p in t.get("players", []) or []:
                pid = (p.get("playerMaster") or {}).get("id")
                if pid:
                    owned.add(pid)
                    owned.add(str(pid))

    candidates: List[Dict[str, Any]] = []

    for t in teams:
        # Skip own team
        if t.get("teamMoney") is not None:
            continue

        mgr = t.get("manager") or {}
        mgr_name = mgr.get("managerName") or "Unknown"
        mgr_id = t.get("managerId") or mgr.get("id")
        mgr_rank = t.get("position") or 0

        # Manager filter if specified
        if manager_query:
            q = manager_query.lower().strip().lstrip("#")
            if q.isdigit() and int(q) != mgr_rank:
                continue
            if not q.isdigit() and q not in mgr_name.lower() and str(mgr_id) != q:
                continue

        mgr_info = {
            "manager_id": mgr_id,
            "manager_name": mgr_name,
            "position": mgr_rank,
        }

        for p in t.get("players", []) or []:
            pid = (p.get("playerMaster") or {}).get("id")
            if not pid or pid in owned or str(pid) in owned:
                continue

            evaluated = evaluate_rival_player(p, mgr_info, index, horizon)
            if evaluated is not None:
                if min_daily_rise > 0 and evaluated["rate_dia"] < min_daily_rise:
                    continue
                candidates.append(evaluated)

    # Sort primarily by steal_score (or margin_pct if profitable)
    candidates.sort(key=lambda x: (x["margin_pct"] > 0, x["steal_score"], x["rate_dia"]), reverse=True)
    return candidates
