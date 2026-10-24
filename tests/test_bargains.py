"""Bargains watchlist: points per million by position, flags market/owned."""

import unittest

from fantasybot.strategy.bargains import bargains
from fantasybot.telegram import ui


def _p(pid, pos, points, value, status="ok", nick=None):
    # /players returns positionId and marketValue as strings
    return {"id": str(pid), "positionId": str(pos), "nickname": nick or f"P{pid}",
            "points": points, "averagePoints": points / 9, "marketValue": str(value),
            "playerStatus": status}


class Bargains(unittest.TestCase):
    def test_ranks_by_points_per_million_within_position(self):
        players = [_p(1, 3, 40, 1_000_000), _p(2, 3, 60, 30_000_000), _p(3, 3, 30, 500_000),
                   _p(4, 4, 99, 100_000)]   # other position
        got = [b["player_id"] for b in bargains(players, 3)]
        self.assertEqual(got, ["3", "1", "2"])

    def test_filters_unplayable_and_low_points(self):
        players = [_p(1, 2, 50, 1_000_000, status="injured"), _p(2, 2, 10, 100_000),
                   _p(3, 2, 25, 1_000_000, status="doubtful"), _p(4, 2, 30, 0)]
        self.assertEqual([b["player_id"] for b in bargains(players, 2)], ["3"])

    def test_flags_market_owned_and_prob(self):
        players = [_p(1, 4, 30, 1_000_000, nick="Niño")]
        b = bargains(players, 4, prob_index={"nino": {"prob": 70}},
                     on_market={1}, owned={"1"})[0]
        self.assertEqual((b["on_market"], b["owned"], b["prob"]), (True, True, 70))

    def test_format_renders(self):
        rows = bargains([_p(1, 4, 30, 1_000_000, nick="Niño")], 4, on_market={"1"})
        text = ui.format_chollos(rows, 4)
        self.assertIn("Niño", text)
        self.assertIn("🛒", text)
        self.assertIn("30,0 pts/M", text)


if __name__ == "__main__":
    unittest.main()
