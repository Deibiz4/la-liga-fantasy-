"""Name normalization and matching across sources.

The LaLiga API uses nicknames ("Etta Eyong") and futbolfantasy uses full names
("karl etta eyong"). This module centralizes the matching, previously duplicated
in several places.
"""

import unicodedata

# API positions (positionId -> abbreviation). Shared by the strategies.
POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}


def normalize(name: str) -> str:
    """lowercase + accent-stripped, to match names across sources."""
    n = unicodedata.normalize("NFKD", name or "")
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.lower().strip()


def index_by_name(items, key="nombre"):
    """Dict normalized_name -> item."""
    return {normalize(it[key]): it for it in items}


def match_name(nickname: str, full_name: str, index: dict, team: str | None = None):
    """Finds the `index` entry for a player from the LaLiga API.

    Tries an exact match by nickname and by full name; if that fails, by tokens
    (all the significant tokens of the nickname appear in the key). `team` (the
    futbolfantasy team slug, see `ff_team`) breaks ties between several hits.
    Returns the entry or None.
    """
    nick = normalize(nickname)
    full = normalize(full_name)
    if nick in index:
        return index[nick]
    if full in index:
        return index[full]
    tokens = [t for t in nick.split() if len(t) > 2]
    if tokens:
        # Only trust a token match if it's UNIQUE. A short/common nickname
        # ("Pedro", "Álvarez") is a subset of several names; returning an arbitrary
        # one is a false positive (what SANITY_MAX_DIFF in flip.py papers over).
        # Ambiguous -> no confident match. The ID crosswalk is the real fix.
        hits = [value for key, value in index.items()
                if all(t in key for t in tokens)]
        if len(hits) > 1 and team:
            hits = [h for h in hits if h.get("equipo") == team]
        if len(hits) == 1:
            return hits[0]
    return None


def ff_team(laliga_slug: str | None, index: dict) -> str | None:
    """futbolfantasy team slug for a LaLiga team slug: the futbolfantasy slug is
    contained in LaLiga's ('athletic' in 'athletic-club', 'real-madrid' in 'real-madrid',
    'racing' in 'r-racing-club'). Longest wins, so 'real-sociedad' never reads as 'real'."""
    if not laliga_slug:
        return None
    teams = {e.get("equipo") for e in index.values() if e.get("equipo")}
    found = [t for t in teams if t in laliga_slug]
    return max(found, key=len) if found else None


def ff_team_map(players, index: dict) -> dict:
    """{LaLiga teamId: futbolfantasy slug} for lists that carry only `teamId` (the
    `/players` master list): each team takes the slug most of its exactly-matched
    players belong to."""
    from collections import Counter, defaultdict
    votes = defaultdict(Counter)
    for p in players:
        e = index.get(normalize(p.get("nickname", "")))
        if e and e.get("equipo") and p.get("teamId") is not None:
            votes[str(p["teamId"])][e["equipo"]] += 1
    return {t: v.most_common(1)[0][0] for t, v in votes.items()}
