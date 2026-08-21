import unittest
from fantasybot.strategy import scouting
from fantasybot.telegram import ui


class TestScoutingModule(unittest.TestCase):

    def test_scouting_star_player(self):
        pm = {
            "id": "100",
            "nickname": "Pedri",
            "name": "Pedro González",
            "positionId": 3,
            "team": {"name": "Barcelona"},
            "marketValue": 65_000_000,
            "points": 25,
            "averagePoints": 8.3,
            "lastSeasonPoints": 235,
            "playerStatus": "ok"
        }
        prob_index = {
            "pedri": {"nombre": "pedri", "prob": 90, "lesionado": False, "sancionado": False, "disponible": True}
        }
        report = scouting.analyze_player_profile(pm, prob_index=prob_index)

        self.assertEqual(report["name"], "Pedri")
        self.assertEqual(report["last_season_points"], 235)
        self.assertIn("Estrella Top", report["tier_badge"])
        self.assertIn("Titular Indiscutible", report["starter_status"])
        self.assertTrue(report["is_available"])
        self.assertIn("MUY RECOMENDABLE", report["verdict"])

    def test_scouting_lost_role_warning(self):
        pm = {
            "id": "101",
            "nickname": "Veterano",
            "name": "Jugador Veterano",
            "positionId": 2,
            "team": {"name": "Sevilla"},
            "marketValue": 10_000_000,
            "points": 2,
            "averagePoints": 1.0,
            "lastSeasonPoints": 175,
            "playerStatus": "ok"
        }
        prob_index = {
            "veterano": {"nombre": "veterano", "prob": 10, "lesionado": False, "sancionado": False, "disponible": True}
        }
        report = scouting.analyze_player_profile(pm, prob_index=prob_index)

        self.assertEqual(report["role_shift_level"], "WARNING")
        self.assertIn("Pérdida de Rol", report["role_shift"])

    def test_scouting_injured_player(self):
        pm = {
            "id": "102",
            "nickname": "Baja",
            "name": "Jugador Lesionado",
            "positionId": 4,
            "team": {"name": "Valencia"},
            "marketValue": 15_000_000,
            "points": 0,
            "averagePoints": 0.0,
            "lastSeasonPoints": 120,
            "playerStatus": "injured"
        }
        report = scouting.analyze_player_profile(pm, prob_index={})

        self.assertFalse(report["is_available"])
        self.assertIn("Lesionado", report["physical_status"])
        self.assertIn("NO RECOMENDABLE", report["verdict"])

    def test_search_player_in_list(self):
        catalog = [
            {"id": "1", "nickname": "Lamine Yamal", "name": "Lamine Yamal Nasraoui"},
            {"id": "2", "nickname": "Vinicius Jr", "name": "Vinicius Jose Paixao"},
            {"id": "3", "nickname": "A. Batalla", "name": "Augusto Batalla"},
        ]

        # Search by ID
        m1 = scouting.search_player_in_list("1", catalog)
        self.assertIsNotNone(m1)
        self.assertEqual(m1["nickname"], "Lamine Yamal")

        # Search by nickname substring
        m2 = scouting.search_player_in_list("yamal", catalog)
        self.assertIsNotNone(m2)
        self.assertEqual(m2["id"], "1")

        # Search by partial name
        m3 = scouting.search_player_in_list("batalla", catalog)
        self.assertIsNotNone(m3)
        self.assertEqual(m3["id"], "3")

        # Non-matching
        m4 = scouting.search_player_in_list("desconocido_xyz", catalog)
        self.assertIsNone(m4)

    def test_ui_scouting_card(self):
        pm = {
            "id": "200",
            "nickname": "Kubo",
            "name": "Takefusa Kubo",
            "positionId": 3,
            "team": {"name": "Real Sociedad"},
            "marketValue": 35_000_000,
            "points": 18,
            "averagePoints": 6.0,
            "lastSeasonPoints": 185,
            "playerStatus": "ok"
        }
        report = scouting.analyze_player_profile(pm)
        formatted = ui.format_scouting_card(report)

        self.assertIn("Informe de Scouting: Kubo", formatted)
        self.assertIn("185 pts", formatted)
        self.assertIn("DICTAMEN DE SCOUTING", formatted)


if __name__ == "__main__":
    unittest.main()
