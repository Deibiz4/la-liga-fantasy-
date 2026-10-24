"""Bargains: the most cost-effective players per position (points per million).

A watchlist, not a buy signal: ranks every LaLiga player by points scored this season
per million of market value, so cheap regulars who score surface above expensive
names. Flags who is on your league's market right now and who is already yours.
"""

from ..matching import match_name

MIN_POINTS = 20   # below this a high ratio is one lucky match, not a bargain
TOP_N = 10
_PLAYABLE = ("ok", "doubtful")


def bargains(players, position_id, prob_index=None, on_market=(), owned=(),
             n=TOP_N, min_points=MIN_POINTS):
    """Top `n` players of a position by points per million.

    `players` is the `/players` master list (values come as strings). `on_market` and
    `owned` are sets of playerMaster ids, used only to flag rows.
    """
    prob_index = prob_index or {}
    on_market, owned = {str(i) for i in on_market}, {str(i) for i in owned}
    out = []
    for p in players:
        if str(p.get("positionId")) != str(position_id):
            continue
        if p.get("playerStatus") not in _PLAYABLE:
            continue
        value = int(p.get("marketValue") or 0)
        points = int(p.get("points") or 0)
        if value <= 0 or points < min_points:
            continue
        info = match_name(p.get("nickname", ""), p.get("nickname", ""), prob_index)
        pid = str(p.get("id"))
        out.append({
            "player_id": pid,
            "nombre": p.get("nickname"),
            "points": points,
            "avg": round(p.get("averagePoints") or 0, 1),
            "valor": value,
            "ppm": round(points / (value / 1_000_000), 1),
            "prob": info.get("prob") if info else None,
            "doubtful": p.get("playerStatus") == "doubtful",
            "on_market": pid in on_market,
            "owned": pid in owned,
        })
    out.sort(key=lambda b: -b["ppm"])
    return out[:n]
