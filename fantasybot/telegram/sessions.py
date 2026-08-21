"""Multi-user session & authentication management for Telegram.

Allows any Telegram user (identified by chat_id) to connect their own LaLiga Fantasy account
using official OAuth2 PKCE without sharing passwords.
"""

import json
import os
import time
import urllib.parse
from typing import Optional, Tuple, Dict, Any

from .. import auth
from .. import config
from ..api import FantasyClient, FantasyError

_PENDING_PKCE: Dict[int, Dict[str, Any]] = {}
TELEGRAM_SESSIONS_DIR = os.path.join(config.ROOT, ".state", "telegram_users")


def _ensure_dir():
    os.makedirs(TELEGRAM_SESSIONS_DIR, exist_ok=True)


def _user_token_path(chat_id: int) -> str:
    _ensure_dir()
    return os.path.join(TELEGRAM_SESSIONS_DIR, f"{chat_id}.json")


def load_user_tokens(chat_id: int) -> Optional[Dict[str, Any]]:
    path = _user_token_path(chat_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_user_tokens(chat_id: int, tokens: Dict[str, Any]):
    path = _user_token_path(chat_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)


def delete_user_session(chat_id: int):
    path = _user_token_path(chat_id)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def is_user_logged_in(chat_id: int) -> bool:
    return load_user_tokens(chat_id) is not None


def get_user_settings(chat_id: int) -> Dict[str, bool]:
    tokens = load_user_tokens(chat_id) or {}
    settings = tokens.get("settings", {})
    return {
        "notify_flips": settings.get("notify_flips", True),
        "notify_market_reset": settings.get("notify_market_reset", True),
        "notify_injuries": settings.get("notify_injuries", True),
        "notify_expulsions": settings.get("notify_expulsions", True),
        "notify_player_points": settings.get("notify_player_points", True),
        "notify_lineup": settings.get("notify_lineup", True),
        "auto_lineup": settings.get("auto_lineup", False),
    }


def toggle_user_setting(chat_id: int, key: str) -> Dict[str, bool]:
    tokens = load_user_tokens(chat_id) or {}
    settings = tokens.get("settings", {})
    default_on = (key in (
        "notify_flips",
        "notify_market_reset",
        "notify_injuries",
        "notify_expulsions",
        "notify_player_points",
        "notify_matchday_points",
        "notify_lineup",
    ))
    cur_val = settings.get(key, default_on)
    settings[key] = not cur_val
    tokens["settings"] = settings
    save_user_tokens(chat_id, tokens)
    return get_user_settings(chat_id)


def get_all_logged_in_chat_ids() -> list:
    _ensure_dir()
    chat_ids = []
    for fname in os.listdir(TELEGRAM_SESSIONS_DIR):
        if fname.endswith(".json"):
            try:
                cid = int(fname[:-5])
                chat_ids.append(cid)
            except ValueError:
                pass
    return chat_ids


import secrets


def start_pkce_login(chat_id: int) -> Tuple[str, str]:
    """Generates (auth_url, verifier) and stores verifier in pending state."""
    verifier, challenge = auth.make_pkce()
    state = secrets.token_urlsafe(16)
    _PENDING_PKCE[chat_id] = {
        "verifier": verifier,
        "state": state,
        "created_at": time.time(),
    }
    auth_url = auth.build_authorize_url(challenge, state)
    return auth_url, verifier


def complete_pkce_login(chat_id: int, text_or_url: str) -> Dict[str, Any]:
    """Exchanges an authredirect:// URL or code for tokens and saves user session strictly isolated."""
    pending = _PENDING_PKCE.get(chat_id)
    if not pending:
        raise auth.AuthError("No hay un inicio de sesión pendiente. Escribe /login para empezar.")

    code = auth.extract_code(text_or_url)
    verifier = pending["verifier"]
    # Exchange code directly without touching global tokens.json
    tokens = auth._post_token({
        "grant_type": "authorization_code",
        "client_id": config.CLIENT_ID,
        "code": code,
        "redirect_uri": config.REDIRECT_URI,
        "code_verifier": verifier,
        "scope": config.SCOPE,
    })
    save_user_tokens(chat_id, tokens)
    _PENDING_PKCE.pop(chat_id, None)

    # Initialize client to fetch user profile
    client = get_client_for_user(chat_id)
    me = client.me()
    leagues = client.leagues()
    return {
        "user": me,
        "leagues": leagues,
    }


def set_user_active_league(chat_id: int, league_id: str):
    tokens = load_user_tokens(chat_id)
    if tokens:
        tokens["active_league_id"] = str(league_id)
        save_user_tokens(chat_id, tokens)


class UserFantasyClient(FantasyClient):
    """A FantasyClient subclass that reads tokens and active league strictly isolated to a Telegram chat_id."""

    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        # Do NOT call super().__init__() because it loads global tokens.json
        self.tokens = {}

    def _bearer(self) -> str:
        tokens = load_user_tokens(self.chat_id)
        if not tokens:
            raise auth.AuthError("No has iniciado sesión. Escribe /login para conectar tu cuenta.")

        # Check expiration
        acc_token = tokens.get("access_token")
        id_token = tokens.get("id_token")
        target_token = acc_token or id_token
        exp = auth.jwt_exp(target_token) if target_token else None

        if exp is not None and time.time() >= (exp - config.TOKEN_EXPIRY_MARGIN):
            self.refresh()
            tokens = load_user_tokens(self.chat_id)

        return auth.bearer_token(tokens)

    def refresh(self):
        tokens = load_user_tokens(self.chat_id)
        if not tokens:
            raise auth.AuthError("No has iniciado sesión. Escribe /login para conectar tu cuenta.")
        rt = tokens.get("refresh_token")
        if not rt:
            raise auth.AuthError("No hay token de renovación. Escribe /login para volver a conectar.")
        new_tokens = auth._post_token({
            "grant_type": "refresh_token",
            "refresh_token": rt,
            "client_id": config.CLIENT_ID,
            "scope": config.SCOPE,
        })
        new_tokens.setdefault("refresh_token", rt)
        if "settings" in tokens:
            new_tokens["settings"] = tokens["settings"]
        if "active_league_id" in tokens:
            new_tokens["active_league_id"] = tokens["active_league_id"]
        save_user_tokens(self.chat_id, new_tokens)

    def default_ids(self):
        leagues = self.leagues()
        if not leagues:
            raise FantasyError("El usuario no pertenece a ninguna liga.")

        tokens = load_user_tokens(self.chat_id) or {}
        active_lid = tokens.get("active_league_id")

        if active_lid:
            for lg in leagues:
                if str(lg.get("id")) == str(active_lid):
                    return lg["id"], str(lg["team"]["id"])

        # Fallback to first league
        lg = leagues[0]
        return lg["id"], str(lg["team"]["id"])


def get_client_for_user(chat_id: int) -> UserFantasyClient:
    return UserFantasyClient(chat_id)
