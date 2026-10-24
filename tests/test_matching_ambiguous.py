"""Regression: match_name must not silently pick one of several ambiguous matches.

The token fallback accepted the FIRST index entry whose key contained all the
nickname tokens. With a short/common nickname ("Pedro", "Álvarez") several players
match and it returned an arbitrary one — a false positive that SANITY_MAX_DIFF in
flip.py then has to paper over. An ambiguous token match must resolve to None; the
real fix (an ID crosswalk) builds on top of a matcher that no longer lies.
"""

import unittest

from fantasybot.matching import index_by_name, match_name


class TestAmbiguousMatch(unittest.TestCase):
    def test_ambiguous_token_match_is_rejected(self):
        index = index_by_name([{"nombre": "pedro porro", "v": 1},
                               {"nombre": "pedro leon", "v": 2}])
        # "Pedro" alone matches BOTH keys -> must not pick one at random
        self.assertIsNone(match_name("Pedro", "", index))

    def test_unique_token_match_still_works(self):
        index = index_by_name([{"nombre": "karl etta eyong", "v": 1},
                               {"nombre": "pedro porro", "v": 2}])
        # "Etta Eyong" matches exactly one key -> still resolved
        self.assertEqual(match_name("Etta Eyong", "", index)["v"], 1)


if __name__ == "__main__":
    unittest.main()


class TeamTieBreak(unittest.TestCase):
    """An ambiguous nickname ('Ramon': ramon enriquez / pablo ramon) resolves by team."""

    IDX = {"ramon enriquez": {"prob": 20, "equipo": "malaga"},
           "pablo ramon": {"prob": 70, "equipo": "racing"},
           "inaki williams": {"prob": 90, "equipo": "athletic"},
           "takefusa kubo": {"prob": 90, "equipo": "real-sociedad"},
           "kylian mbappe": {"prob": 95, "equipo": "real-madrid"}}

    def test_team_breaks_ambiguity(self):
        from fantasybot.matching import match_name
        self.assertIsNone(match_name("Ramon", "", self.IDX))
        self.assertEqual(match_name("Ramon", "", self.IDX, team="malaga")["prob"], 20)
        self.assertEqual(match_name("Ramon", "", self.IDX, team="racing")["prob"], 70)
        self.assertIsNone(match_name("Ramon", "", self.IDX, team="betis"))

    def test_ff_team_from_laliga_slug(self):
        from fantasybot.matching import ff_team
        self.assertEqual(ff_team("athletic-club", self.IDX), "athletic")
        self.assertEqual(ff_team("real-sociedad", self.IDX), "real-sociedad")
        self.assertEqual(ff_team("real-madrid", self.IDX), "real-madrid")
        self.assertIsNone(ff_team("fc-barcelona", self.IDX))
        self.assertIsNone(ff_team(None, self.IDX))

    def test_team_map_by_majority(self):
        from fantasybot.matching import ff_team_map
        players = [{"nickname": "Kylian Mbappé", "teamId": "15"},
                   {"nickname": "Takefusa Kubo", "teamId": "16"}]
        self.assertEqual(ff_team_map(players, self.IDX), {"15": "real-madrid", "16": "real-sociedad"})
