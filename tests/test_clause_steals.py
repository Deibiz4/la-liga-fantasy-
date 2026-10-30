import unittest
from unittest.mock import MagicMock, patch

from fantasybot.strategy.clause_steals import evaluate_rival_player, find_rival_clause_flips


class TestClauseSteals(unittest.TestCase):

    def setUp(self):
        self.mock_index = {
            "pau-cubarsi": {
                "nombre": "Pau Cubarsí",
                "valor": 10_000_000,
                "valor1": 9_800_000,
                "valor3": 9_400_000,
                "valor7": 8_600_000,
                "tendencia": 200_000,
            },
            "nico-williams": {
                "nombre": "Nico Williams",
                "valor": 50_000_000,
                "valor1": 50_500_000,
                "valor3": 51_000_000,
                "valor7": 52_000_000,
                "tendencia": -500_000,
            },
            "pedri": {
                "nombre": "Pedri",
                "valor": 60_000_000,
                "valor1": 59_000_000,
                "valor3": 57_000_000,
                "valor7": 53_000_000,
                "tendencia": 1_000_000,
            }
        }

    def test_evaluate_positive_clause_flip(self):
        player = {
            "buyoutClause": 10_200_000,
            "playerMaster": {
                "id": "101",
                "nickname": "Cubarsí",
                "name": "Pau Cubarsí",
                "positionId": 2,
                "marketValue": 10_000_000,
                "lastSeasonPoints": 120,
            }
        }
        mgr = {"manager_id": 99, "manager_name": "Rival FC", "position": 2}
        res = evaluate_rival_player(player, mgr, self.mock_index, horizon=7)

        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "Cubarsí")
        self.assertEqual(res["pos"], "DEF")
        self.assertEqual(res["manager_name"], "Rival FC")
        self.assertEqual(res["buyout_clause"], 10_200_000)
        self.assertGreater(res["rate_dia"], 0)
        self.assertGreater(res["margin"], 0)
        self.assertEqual(res["badge"], "💎 GANGA FLIP")

    def test_evaluate_unprotected_star_falling_trend(self):
        player = {
            "buyoutClause": 50_000_000,
            "playerMaster": {
                "id": "102",
                "nickname": "Nico Williams",
                "name": "Nicholas Williams",
                "positionId": 4,
                "marketValue": 50_000_000,
                "lastSeasonPoints": 190,
                "points": 45,
            }
        }
        mgr = {"manager_id": 88, "manager_name": "Athletic Boss", "position": 1}
        res = evaluate_rival_player(player, mgr, self.mock_index, horizon=7)

        self.assertIsNotNone(res)
        self.assertEqual(res["clause_ratio"], 1.0)
        # Because trend is negative, rate is not extrapolated upward
        self.assertLessEqual(res["rate_dia"], 0)
        self.assertEqual(res["badge"], "⭐ CRACK ASEQUIBLE")

    def test_find_rival_clause_flips_excludes_own_players(self):
        client = MagicMock()
        client.league_teams.return_value = [
            {
                "id": "team_me",
                "teamMoney": 15_000_000,  # User's own team
                "manager": {"managerName": "Yo", "id": 1},
                "players": [
                    {
                        "buyoutClause": 20_000_000,
                        "playerMaster": {
                            "id": "101",
                            "nickname": "Cubarsí",
                            "marketValue": 10_000_000,
                        }
                    }
                ]
            },
            {
                "id": "team_rival",
                "teamMoney": None,  # Rival team
                "manager": {"managerName": "Rival Uno", "id": 2},
                "position": 3,
                "players": [
                    {
                        "buyoutClause": 62_000_000,
                        "playerMaster": {
                            "id": "103",
                            "nickname": "Pedri",
                            "name": "Pedro González",
                            "positionId": 3,
                            "marketValue": 60_000_000,
                            "lastSeasonPoints": 180,
                        }
                    }
                ]
            }
        ]

        with patch("fantasybot.strategy.clause_steals.trends_index", return_value=self.mock_index):
            flips = find_rival_clause_flips(client, "league_123")

        # Cubarsi (own player) must NOT be in flips
        player_ids = [f["player_id"] for f in flips]
        self.assertNotIn("101", player_ids)
        self.assertIn("103", player_ids)
        self.assertEqual(flips[0]["name"], "Pedri")

    def test_find_rival_clause_flips_manager_filter(self):
        client = MagicMock()
        client.league_teams.return_value = [
            {
                "id": "team_rival1",
                "teamMoney": None,
                "manager": {"managerName": "Javier Madrid", "id": 20},
                "position": 1,
                "players": [
                    {
                        "buyoutClause": 10_000_000,
                        "playerMaster": {"id": "201", "nickname": "Pau Cubarsí", "marketValue": 10_000_000}
                    }
                ]
            },
            {
                "id": "team_rival2",
                "teamMoney": None,
                "manager": {"managerName": "Dani Betis", "id": 30},
                "position": 2,
                "players": [
                    {
                        "buyoutClause": 60_000_000,
                        "playerMaster": {"id": "202", "nickname": "Pedri", "marketValue": 60_000_000}
                    }
                ]
            }
        ]

        with patch("fantasybot.strategy.clause_steals.trends_index", return_value=self.mock_index):
            # Filter by manager name 'Javier'
            flips_javier = find_rival_clause_flips(client, "league_123", manager_query="Javier")
            self.assertEqual(len(flips_javier), 1)
            self.assertEqual(flips_javier[0]["manager_name"], "Javier Madrid")

            # Filter by rank '#2'
            flips_rank2 = find_rival_clause_flips(client, "league_123", manager_query="#2")
            self.assertEqual(len(flips_rank2), 1)
            self.assertEqual(flips_rank2[0]["manager_name"], "Dani Betis")


class TestClauseLockAndStart(unittest.TestCase):
    MGR = {"manager_id": 1, "manager_name": "Rival", "position": 3}

    def _player(self, pid, nick, lock=None, status="ok"):
        return {"buyoutClause": 5_000_000, "buyoutClauseLockedEndTime": lock,
                "playerMaster": {"id": pid, "nickname": nick, "name": nick, "positionId": 3,
                                 "marketValue": 4_000_000, "teamId": "7", "playerStatus": status}}

    def test_locked_clause_flagged_and_past_lock_ignored(self):
        res = evaluate_rival_player(self._player("1", "Uno", lock="2999-01-01T10:00:00+02:00"),
                                    self.MGR, {})
        self.assertIsNotNone(res["locked_until"])
        res = evaluate_rival_player(self._player("1", "Uno", lock="2020-01-01T10:00:00+02:00"),
                                    self.MGR, {})
        self.assertIsNone(res["locked_until"])

    def test_benchwarmer_and_injured_do_not_play(self):
        probs = {"suplente": {"nombre": "suplente", "equipo": "x", "prob": 10},
                 "titular": {"nombre": "titular", "equipo": "x", "prob": 90}}
        bench = evaluate_rival_player(self._player("1", "Suplente"), self.MGR, {}, prob_index=probs)
        starter = evaluate_rival_player(self._player("2", "Titular"), self.MGR, {}, prob_index=probs)
        hurt = evaluate_rival_player(self._player("3", "Otro", status="injured"), self.MGR, {})
        self.assertFalse(bench["plays"])
        self.assertTrue(starter["plays"])
        self.assertEqual(starter["prob"], 90)
        self.assertTrue(hurt["injured"])
        self.assertFalse(hurt["plays"])

    def test_ranking_payable_starters_first(self):
        probs = {"suplente": {"nombre": "suplente", "equipo": "x", "prob": 10},
                 "titular": {"nombre": "titular", "equipo": "x", "prob": 90},
                 "cerrado": {"nombre": "cerrado", "equipo": "x", "prob": 95}}
        client = MagicMock()
        client.league_teams.return_value = [{"manager": {"managerName": "Rival"}, "players": [
            self._player("1", "Suplente"),
            self._player("2", "Cerrado", lock="2999-01-01T10:00:00+02:00"),
            self._player("3", "Titular"),
        ]}]
        with patch("fantasybot.strategy.clause_steals.trends_index", return_value={}):
            names = [s["name"] for s in find_rival_clause_flips(client, "l", prob_index=probs)]
        self.assertEqual(names, ["Titular", "Suplente", "Cerrado"])


if __name__ == "__main__":
    unittest.main()
