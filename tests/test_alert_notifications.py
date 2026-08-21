import unittest
import os
import shutil
import tempfile
from unittest.mock import MagicMock

from fantasybot.telegram import sessions, ui, notifications


class TestAlertNotifications(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_sessions_dir = sessions.TELEGRAM_SESSIONS_DIR
        self.orig_registry_path = sessions.REGISTRY_PATH
        sessions.TELEGRAM_SESSIONS_DIR = self.test_dir
        sessions.REGISTRY_PATH = os.path.join(self.test_dir, "test_registry.json")

        # Reset in-memory trackers
        notifications._LAST_SEEN_PLAYER_STATUS.clear()
        notifications._LAST_SEEN_PLAYER_POINTS.clear()
        notifications._LAST_SEEN_MARKET_BATCH.clear()
        notifications._LAST_PROCESSED_WEEK.clear()

        self.mock_bot = MagicMock()
        self.chat_id = 123456789

    def tearDown(self):
        sessions.TELEGRAM_SESSIONS_DIR = self.orig_sessions_dir
        sessions.REGISTRY_PATH = self.orig_registry_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_settings_and_toggles(self):
        settings = sessions.get_user_settings(self.chat_id)
        self.assertTrue(settings["notify_market_reset"])
        self.assertTrue(settings["notify_injuries"])
        self.assertTrue(settings["notify_expulsions"])
        self.assertTrue(settings["notify_player_points"])

        # Toggle injuries
        new_settings = sessions.toggle_user_setting(self.chat_id, "notify_injuries")
        self.assertFalse(new_settings["notify_injuries"])

        # Toggle back
        new_settings = sessions.toggle_user_setting(self.chat_id, "notify_injuries")
        self.assertTrue(new_settings["notify_injuries"])

        # Check UI keyboard
        kb = ui.settings_keyboard(new_settings)
        btn_texts = [btn["text"] for row in kb["inline_keyboard"] for btn in row]
        self.assertTrue(any("Mercado Diario" in t for t in btn_texts))
        self.assertTrue(any("Alerta de Lesiones" in t for t in btn_texts))
        self.assertTrue(any("Alerta de Sanciones" in t for t in btn_texts))
        self.assertTrue(any("Puntos de Jugadores" in t for t in btn_texts))

    def test_injury_and_expulsion_alerts(self):
        # Initial squad state (all healthy)
        team_data_v1 = {
            "players": [
                {"playerMaster": {"id": "p1", "nickname": "Pedri", "positionId": 3, "playerStatus": "ok"}},
                {"playerMaster": {"id": "p2", "nickname": "Vinicius", "positionId": 4, "playerStatus": "ok"}},
                {"playerMaster": {"id": "p3", "nickname": "Cubarsi", "positionId": 2, "playerStatus": "ok"}},
            ]
        }
        settings = sessions.get_user_settings(self.chat_id)

        # First run: baseline recorded, no spam
        notifications._check_player_injuries_and_expulsions(self.mock_bot, self.chat_id, team_data_v1, settings)
        self.mock_bot.send_message.assert_not_called()

        # Second run: Pedri gets injured, Vinicius gets red card
        team_data_v2 = {
            "players": [
                {"playerMaster": {"id": "p1", "nickname": "Pedri", "positionId": 3, "playerStatus": "injured"}},
                {"playerMaster": {"id": "p2", "nickname": "Vinicius", "positionId": 4, "playerStatus": "suspended"}},
                {"playerMaster": {"id": "p3", "nickname": "Cubarsi", "positionId": 2, "playerStatus": "ok"}},
            ]
        }
        notifications._check_player_injuries_and_expulsions(self.mock_bot, self.chat_id, team_data_v2, settings)

        self.assertEqual(self.mock_bot.send_message.call_count, 2)
        sent_texts = [call[0][1] for call in self.mock_bot.send_message.call_args_list]

        self.assertTrue(any("Lesión" in t and "Pedri" in t for t in sent_texts))
        self.assertTrue(any("Sanción" in t and "Vinicius" in t for t in sent_texts))

    def test_player_points_increment_alert(self):
        team_data_v1 = {
            "teamPoints": 45,
            "position": 2,
            "players": [
                {"playerMaster": {"id": "p1", "nickname": "Yamal", "positionId": 4, "points": 10}},
                {"playerMaster": {"id": "p2", "nickname": "Baena", "positionId": 3, "points": 8}},
            ]
        }
        settings = sessions.get_user_settings(self.chat_id)
        mock_client = MagicMock()
        mock_client.league_activity.return_value = []

        # Baseline run
        notifications._check_player_points(self.mock_bot, self.chat_id, mock_client, "l1", "t1", team_data_v1, settings)
        self.mock_bot.send_message.assert_not_called()

        # Points update after match
        team_data_v2 = {
            "teamPoints": 62,
            "position": 1,
            "players": [
                {"playerMaster": {"id": "p1", "nickname": "Yamal", "positionId": 4, "points": 21}},  # +11 pts
                {"playerMaster": {"id": "p2", "nickname": "Baena", "positionId": 3, "points": 14}},  # +6 pts
            ]
        }
        notifications._check_player_points(self.mock_bot, self.chat_id, mock_client, "l1", "t1", team_data_v2, settings)

        self.assertEqual(self.mock_bot.send_message.call_count, 1)
        msg_text = self.mock_bot.send_message.call_args[0][1]
        self.assertIn("Puntuaciones de Partido Actualizadas", msg_text)
        self.assertIn("Yamal", msg_text)
        self.assertIn("+11 pts", msg_text)
        self.assertIn("Baena", msg_text)
        self.assertIn("+6 pts", msg_text)
        self.assertIn("62 pts", msg_text)

    def test_market_reset_alert(self):
        mock_client = MagicMock()
        mock_client.leagues.return_value = [{"id": "l1", "name": "Liga Santander Amigos"}]
        mock_client.market.return_value = [
            {"id": "m1", "discr": "marketPlayerLeague", "playerMaster": {"nickname": "Mbappe", "positionId": 4, "marketValue": 80_000_000}},
            {"id": "m2", "discr": "marketPlayerLeague", "playerMaster": {"nickname": "Bellingham", "positionId": 3, "marketValue": 70_000_000}},
        ]

        # Initial baseline
        notifications._check_market_reset(self.mock_bot, self.chat_id, mock_client, "l1")
        self.mock_bot.send_message.assert_not_called()

        # Next day market reset
        mock_client.market.return_value = [
            {"id": "m3", "discr": "marketPlayerLeague", "playerMaster": {"nickname": "Lewandowski", "positionId": 4, "marketValue": 50_000_000}},
            {"id": "m4", "discr": "marketPlayerLeague", "playerMaster": {"nickname": "Valverde", "positionId": 3, "marketValue": 45_000_000}},
        ]
        notifications._check_market_reset(self.mock_bot, self.chat_id, mock_client, "l1")

        self.mock_bot.send_message.assert_called_once()
        msg_text = self.mock_bot.send_message.call_args[0][1]
        self.assertIn("Mercado Diario Renovado", msg_text)
        self.assertIn("Lewandowski", msg_text)
        self.assertIn("Valverde", msg_text)

    def test_gameweek_6h_reminder(self):
        from unittest.mock import patch
        from datetime import datetime, timezone, timedelta

        # Set next gameweek kickoff 3 hours in the future (inside the 6h window)
        now = datetime.now(timezone.utc)
        future_3h = (now + timedelta(hours=3)).isoformat()

        team_data = {
            "teamMoney": -2_500_000,
            "players": [
                {"playerMaster": {"id": "1", "nickname": "Courtois", "positionId": 1, "marketValue": 10_000_000}},
                {"playerMaster": {"id": "2", "nickname": "Rudiger", "positionId": 2, "marketValue": 10_000_000}},
            ]
        }
        settings = sessions.get_user_settings(self.chat_id)
        mock_client = MagicMock()

        with patch("fantasybot.sources.matchday.next_gameweek_kickoff", return_value=future_3h):
            with patch("fantasybot.strategy.lineup.optimize", return_value={"formation": (4, 4, 2), "xi": []}):
                with patch("fantasybot.agent._current_xi_ids", return_value=["1"]):
                    notifications._check_gameweek_reminder(self.mock_bot, self.chat_id, mock_client, "l1", "t1", team_data, settings)

        self.mock_bot.send_message.assert_called_once()
        msg_text = self.mock_bot.send_message.call_args[0][1]
        self.assertIn("AVISO DE JORNADA", msg_text)
        self.assertIn("SALDO NEGATIVO DETECTADO", msg_text)

    def test_user_registry_and_stats(self):
        sessions.record_user_interaction(111, {"username": "user1", "first_name": "Alice"})
        sessions.record_user_interaction(222, {"username": "user2", "first_name": "Bob"})

        stats = sessions.get_bot_usage_stats()
        self.assertGreaterEqual(stats["total_telegram_users"], 2)
        formatted = ui.format_admin_stats(stats)
        self.assertIn("Panel de Estadísticas", formatted)
        self.assertIn("Alice", formatted)
        self.assertIn("Bob", formatted)


if __name__ == "__main__":
    unittest.main()
