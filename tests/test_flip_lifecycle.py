"""Flip lifecycle: a won bid is remembered, then resold at target or after the horizon.

Before, the bot bought flips but never closed them (it only sold on a heavy value
drop), and it accepted the FIRST offer >= 95% of value instead of the best one at value.
"""

import tempfile
import time
import unittest
from unittest import mock

from fantasybot import execute, state
from fantasybot.strategy import sell


def _player(pid, value, position_id=3):
    return {"playerTeamId": f"pt{pid}",
            "playerMaster": {"id": pid, "nickname": f"N{pid}", "name": f"N{pid}",
                             "positionId": position_id, "marketValue": value}}


class _Client:
    def __init__(self, market=()):
        self._market = list(market)
        self.listed, self.accepted = [], []

    def market(self, lid):
        return self._market

    def sell_player(self, lid, pid, price):
        self.listed.append((pid, price))

    def accept_offer(self, lid, mid, oid, money):
        self.accepted.append((mid, oid, money))


class FlipLifecycle(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.mkdtemp()
        self._p = mock.patch.object(state, "STATE_DIR", tmp)
        self._p.start()
        self._e = mock.patch.object(execute.events, "emit")
        self._e.start()

    def tearDown(self):
        self._p.stop()
        self._e.stop()

    def test_won_bid_becomes_flip(self):
        team = {"players": [_player("7", 600_000)]}
        bids = {"m1": {"amount": 580_000, "nombre": "N7", "player_id": "7", "margin_pct": 1.0},
                "m2": {"amount": 1, "nombre": "Other", "player_id": "99"}}
        won = execute._record_won_flips(team, bids, chat_id=1, dry_run=False)
        self.assertEqual(set(won), {"m1"})
        self.assertNotIn("m1", bids)   # no longer an open bid → won't be "cancelled"
        self.assertIn("m2", bids)
        f = state.load_flips(1)["7"]
        self.assertEqual(f["buy_price"], 580_000)
        self.assertEqual(f["target_pct"], execute.MIN_FLIP_MARGIN_PCT)  # floor, not 1%

    def test_legacy_bid_matches_by_name(self):
        team = {"players": [_player("7", 600_000)]}
        bids = {"m1": {"amount": 580_000, "nombre": "N7"}}
        self.assertIn("m1", execute._record_won_flips(team, bids, None, dry_run=False))

    def test_exits_at_target_or_expiry_only(self):
        now = time.time()
        team = {"players": [_player("a", 1_100_000), _player("b", 1_000_000),
                            _player("c", 1_000_000)]}
        flips = {"a": {"buy_price": 1_000_000, "bought_at": now, "target_pct": 5},
                 "b": {"buy_price": 1_000_000, "bought_at": now - 8 * 86400, "target_pct": 5},
                 "c": {"buy_price": 1_000_000, "bought_at": now, "target_pct": 5}}
        out = {c["player_id"]: c["reason"] for c in sell.flip_exits(team, None, flips, now)}
        self.assertIn("target", out["a"])
        self.assertIn("expired", out["b"])
        self.assertNotIn("c", out)   # still inside the horizon, below target → hold

    def test_flip_in_xi_is_kept(self):
        team = {"players": [_player("a", 2_000_000)]}
        flips = {"a": {"buy_price": 1_000_000, "bought_at": 0, "target_pct": 3}}
        best = {"payload": {"goalkeeper": "x", "defender": [], "midfield": ["pta"],
                            "striker": []}}
        self.assertEqual(sell.flip_exits(team, best, flips), [])

    def test_accepts_only_best_offer_at_value(self):
        item = {"id": "mk", "team": {"id": "T"},
                "playerMaster": {"id": "z", "nickname": "Z", "marketValue": 1_000_000},
                "offers": [{"id": "o1", "money": 990_000}, {"id": "o2", "money": 1_050_000},
                           {"id": "o3", "money": 1_010_000}]}
        client = _Client([item])
        with mock.patch("fantasybot.sources.market_trends.trends_index", return_value={}):
            res = execute.sync_sells(client, "L", "T", {"players": []}, None, dry_run=False)
        self.assertEqual(client.accepted, [("mk", "o2", 1_050_000)])
        self.assertEqual(len(res["accepted"]), 1)

    def test_rejects_offer_below_value(self):
        item = {"id": "mk", "team": {"id": "T"},
                "playerMaster": {"id": "z", "nickname": "Z", "marketValue": 1_000_000},
                "offers": [{"id": "o1", "money": 960_000}]}
        client = _Client([item])
        with mock.patch("fantasybot.sources.market_trends.trends_index", return_value={}):
            execute.sync_sells(client, "L", "T", {"players": []}, None, dry_run=False)
        self.assertEqual(client.accepted, [])

    def test_sold_flip_is_forgotten(self):
        state.save_flips({"gone": {"buy_price": 1, "bought_at": 0, "target_pct": 3}}, 5)
        with mock.patch("fantasybot.sources.market_trends.trends_index", return_value={}):
            execute.sync_sells(_Client(), "L", "T", {"players": []}, None,
                               dry_run=False, chat_id=5)
        self.assertEqual(state.load_flips(5), {})


if __name__ == "__main__":
    unittest.main()
