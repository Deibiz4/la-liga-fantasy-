# Changelog

All notable changes to the **fantasybot** project for rival tracking, transfer accounting, and squad analysis.

---

## [Unreleased] - 2026-08-24

### Added

#### 1. Rival Clause Robbery & Flips Engine (`fantasybot/strategy/clause_steals.py`)
- **`find_rival_clause_flips()` & `evaluate_rival_player()`**: Scans all rival squads in the league to identify lucrative clause buyout ("clausulazo") opportunities by cross-referencing rival buyout clauses (`buyoutClause`) against FutbolFantasy real-time trend trajectories, player points, and protection ratios.
- **Smart Protection & ROI Metrics**:
  - `clause_ratio`: Ratio of buyout clause vs market value (1.00x = unprotected, 2.50x+ = heavily shielded).
  - `rate_dia`: Daily rate of market value change (€/day).
  - `proyeccion`: Projected market valuation at $N$ days (horizon).
  - `margin` & `margin_pct`: Estimated net profit and ROI % against the buyout clause.
  - `steal_score`: Composite opportunity rating.
- **Verdict Badges**: Categorizes players as `💎 GANGA FLIP` (positive projected ROI), `🚀 COHETE` (rising ≥150k/day), `🔓 DESPROTEGIDO` (low clause ratio and fast rise), `⭐ CRACK ASEQUIBLE` (high-performing star with affordable clause), and `🛡️ BLINDADO` (heavily protected).

#### 2. CLI Command (`fantasybot/cli.py`)
- **`python -m fantasybot clausulas`** (aliases: `steals`, `clause-flips`):
  - Formatted terminal table showing Player, Position, Rival Owner, Market Value, Buyout Clause, Clause Ratio, Daily Rise, 7D Projection, ROI %, Badges, and Affordability flag (`<=`).
  - Supports `--min-rise <euros>`, `--horizon <days>`, manager query (`"Agrobetis"`, `"#1"`), and `--json`.
- **`python -m fantasybot clause <playerId> [amount]`**:
  - Automatically queries the exact live `buyoutClause` from the server if `amount` is omitted.

#### 3. Telegram Bot Clausulazos & Robos Menu (`fantasybot/telegram/`)
- **Interactive Button & Command**: Added `⚡ Clausulazos & Robos` in main menu and `/clausulas` / `/robos` command.
- **Direct Action Buttons**: Single-tap `⚡ Robar <Jugador> (<Precio>)` and `🔍 Scout <Jugador>` buttons.
- **Affordability Indicators**: Real-time solvency badges (`🟢` within liquid balance / `🔴` exceeds liquid balance).

#### 4. Universal Contextual "Back" Navigation (`fantasybot/telegram/ui.py`, `fantasybot/telegram/bot.py`)
- **Context-Aware Scouting Return**: Scouting cards now include explicit return buttons back to the calling view (`⚡ Volver a Clausulazos & Robos`, `🛒 Volver a Mercado`, `🔄 Volver a Flips`, `📋 Volver a Mi Plantilla`).
- **Sub-Menu Back Buttons**: Added return buttons across Rival Detail (`⚔️ Volver a Lista de Rivales`), History Detail (`📊 Volver a Histórico & P/L`), Trends (`🛒 Volver a Mercado`), and Action Results.

#### 5. Windows Control Panel & Launcher (`iniciar_bot.bat`, `start.bat`)
- Interactive batch launcher with UTF-8 encoding support, automatic Python detection, and 1-click execution for Telegram daemon, Mission Control web UI, User Stats, Agent Review, OAuth Login, and Clause Steals Scanner.

#### 6. VPS Deployment (`deploy/fantasybot.service`, `SERVER_CONFIG.md`)
- **Systemd unit** for running the Telegram daemon as a managed service on a VPS (`Restart=always`, unbuffered output to `journalctl`).
- **Server inventory document** (`SERVER_CONFIG.md`, gitignored) with VPS ports, paths, and per-project isolation guidelines.

#### 7. Unit Tests (`tests/test_clause_steals.py`)
- Added unit tests covering positive ROI clause flips, falling trend safeguards, own-player exclusions, and manager/rank filtering.
- **74/74 unit tests passing**.

### Fixed & Hardened

- **35-Second Menu Freezes on VPS — Flaky IPv6 Fallback (`fantasybot/net.py`, `fantasybot/cli.py`, `fantasybot/telegram/bot.py`)**: Telegram menus stalled for exactly 35s at random once deployed on the VPS. Root cause: `api.telegram.org` resolves to both IPv4 and IPv6, the host's IPv6 path intermittently blackholes, and `urllib` (unlike `curl`, which implements Happy Eyeballs) tries the AAAA address first and blocks for the **entire socket timeout** before falling back to IPv4.
  - **`net.prefer_ipv4()`**: Sorts `getaddrinfo` results IPv4-first while keeping IPv6 as fallback (still works on IPv6-only hosts). Applied at CLI startup and in the Telegram polling daemon, so it also covers the LaLiga Fantasy API and FutbolFantasy scrapes. Escape hatch: `FANTASYBOT_PREFER_IPV4=0`.
  - **Bounded Telegram timeouts (`_api_call`)**: Reduced from a fixed 35s to 12s with one automatic retry, so a stalled connection costs seconds instead of freezing the user's menu; `getUpdates` keeps a 25s timeout to outlast its 10s server-side long poll.
  - **Measured on the VPS**: cold requests went from 60.17s / 30.15s stalls to a steady 0.09–0.16s (8/8 requests).

- **Live Buyout Clause Resolution & 409 Error Prevention (`fantasybot/telegram/bot.py`, `fantasybot/cli.py`)**: Resolves live `buyoutClause` and `buyoutClauseLockedEndTime` before submitting `pay_buyout_clause`, avoiding `409 Buyout wanted to pay is not updated` and displaying friendly error / balance requirement messages.
- **Position Lookup Name Definition**: Imported `POS` in `fantasybot/telegram/bot.py` to prevent `NameError: name 'POS' is not defined`.

---

## [0.1.0] - 2026-08-21

### Added

#### 1. API Client Enhancements (`fantasybot/api.py`)
- **`league_teams(league_id)`**: Fetches live roster, market valuations, manager points, positions, and squad clause data for all league participants.
- **`league_activity(league_id, fetch_all=True)`**: Automatically iterates through paginated endpoints (`/leagues/{id}/activity/{idx}`) to retrieve the complete chronological transfer history from day 1 of the league.

#### 2. Persistent Transaction & Squad State (`fantasybot/state.py`)
- **Cumulative Activity Storage (`.state/activity_history.json`)**: Merges and de-duplicates transfer events across sessions so that historical transactions are never lost even after API circular buffer rollovers.
- **Rival Squad Snapshots (`.state/rivals_snapshot.json`)**: Tracks squad rosters and detects clause increases / blindajes between runs.
- **Players Metadata Cache (`.state/players_cache.json`)**: Caches player name, position, and valuations locally to minimize API traffic.
- Added state management functions: `record_activity()`, `load_activity_history()`, `snapshot_rivals()`, `save_rivals_snapshot()`, `load_rivals_snapshot()`, `load_players_cache()`, `save_players_cache()`, and `diff_rival_clauses()`.

#### 3. Rival Strategy & Accounting Module (`fantasybot/strategy/rivals.py`)
- **`parse_activity()`**: Aggregates market purchases (`Type 31`), market sales (`Type 33`), manager-to-manager buyouts (`Type 1`), and matchday point rewards (`Type 6`).
- **`analyze_player_acquisitions()`**: Cross-references squad players with historical purchases to identify:
  - Exact purchase price (`BOUGHT AT`) and buy date.
  - Capital gain/loss (`PROFIT / LOSS`) in currency and percentage revaluation ($\Delta \text{Value}$ and $\%\text{Gain}$).
  - Identification of players from the initial assigned squad (`(Initial)`).
- **`analyze_squad_clauses()`**: Calculates total squad clause valuation, highest clause, and top protected player ($\text{Clause} - \text{Market Value}$).
- **`analyze_rivals()`**: Combines squad valuations, persistent transaction history, and pure baseline accounting to estimate available liquid cash for all league rivals.

#### 4. Trading History & P&L Module (`fantasybot/strategy/history.py`)
- **`compute_manager_trading_history()`**:
  - Matches buy and sell transactions (FIFO) by player to compute completed flips, holding duration in days, and return on equity (ROI %).
  - Tracks open purchased holdings with live unrealized capital gains/losses.
  - Tracks initial squad liquidations and total sales revenue.
- **`resolve_player_names()`**: Resolves player metadata from local cache and API.
- **`analyze_league_trading_history()`**: Produces league-wide speculation leaderboards sorted by total portfolio P&L.

#### 5. CLI Commands (`fantasybot/cli.py`)
- **`python -m fantasybot rivals [manager|rank]`**:
  - General league overview with position, team value, squad size, total purchases, total sales, net profit, estimated cash, and top protected players.
  - Detailed individual squad performance table (`PLAYER`, `POS`, `BOUGHT AT`, `CURRENT VALUE`, `PROFIT / LOSS`, `CLAUSE`, `PROTECTION`).
  - Reality check comparison on user's own account (`Real Cash vs Pure Estimated`).
- **`python -m fantasybot history [manager|rank]`**:
  - League-wide speculation and trading ROI leaderboard (`TOTAL P&L`, `REALIZED`, `UNREALIZED`, `FLIPS`, `WIN%`, `AVG ROI`).
  - Detailed trade log showing open holdings, completed flips with ROI %, and initial squad sales.
- **Flexible search support**: Query by multi-word name without quotes (`rivals EPT Alfaro`), rank position (`rivals 1` or `#1`), manager/team ID (`rivals 867521`), or shortcut for own account (`rivals me`).
- **`--json` flags**: Structured JSON export for programmatic consumption (`rivals --json`, `history --json`).
- **`--initial-budget` flag**: Allows custom league starting budget overrides.

#### 6. Multi-User Telegram Bot & Interactive Autopilot (`fantasybot/telegram/`)
- **Multi-Tenant Sessions (`fantasybot/telegram/sessions.py`)**:
  - Multi-user session storage with isolated tokens per `chat_id` and automatic OAuth2 PKCE login.
  - Multi-league switcher (`/leagues`) with dynamic league selection and persistent active league tracking.
  - User preference toggles (`get_user_settings`, `toggle_user_setting`) for personalized alert configuration.
- **Interactive Action Engine (`fantasybot/telegram/bot.py`)**:
  - **1-Click Lineup Applicator**: Directly sets optimal tactical XI on official LaLiga Fantasy accounts.
  - **Single-Tap Bids & Buyouts**: Distinguishes between auction market bids (`make_bid`) and manager buyout clauses (`pay_buyout_clause`) with dedicated buttons and owner tags.
  - **Squad Player Sales**: List players on the transfer market with one click (`/sell`).
  - **1-Click Autopilot**: Runs lineup optimization, submits high-margin flip bids within balance limits, and cancels declining bids (`/autopilot` / `/run`).
- **Mobile-First UX & Visual Card Redesign (`fantasybot/telegram/ui.py`)**:
  - Overhauled all command outputs for mobile legibility, replacing monospaced tables with structured card layouts.
  - Spanish currency formatting (`1.000.000 €` / `14,2M €`).
  - Categorized squad breakdown by position (`🧤 PORTEROS`, `🛡 DEFENSAS`, `🎯 CENTROCAMPISTAS`, `⚡ DELANTEROS`).
  - Flip opportunity cards with manager ownership indicator, 7-day projections, and expected profit margin.
  - Ranked rival cards with podium medals (🥇, 🥈, 🥉), estimated liquid cash, and squad valuations.
- **Background Notification & Alert Worker (`fantasybot/telegram/notifications.py`)**:
  - Background daemon thread checking for new profitable market flips and automatic matchday lineup optimization.
  - Interactive settings panel (`/settings`) with instant toggle buttons for flip alerts, matchday reminders, and auto-lineups.
- **User Feedback & Bug Inbox (`fantasybot/telegram/feedback.py`)**:
  - `/bug <msg>` and `/sugerencia <msg>` commands for users to send feedback directly.
  - Persistent JSON Lines feedback storage (`.state/feedback.jsonl`).
  - Real-time forwarding of reports to admin chat ID.
  - Admin inbox viewer command (`/reportes` / `/admin_feedback`).
- **Zero External Dependencies**: Pure Python standard library implementation (`urllib.request`, `json`, `threading`).

#### 7. Player Scouting & Multi-Season Historical Intelligence (`fantasybot/strategy/scouting.py`)
- **Multi-Season Historical Scoring**: Extracts and evaluates `lastSeasonPoints` and per-gameweek scoring rhythm from master player catalogs.
- **Historical Tier Classification**: 🌟 *Estrella Top LaLiga* (>220 pts), 🛡️ *Titular Fijo Consolidado* (150-219 pts), 🔄 *Jugador de Rotación* (80-149 pts), 🪑 *Suplente / Secundario* (<80 pts), 🆕 *Sin Registro / Debutante*.
- **Scoring Evolution & Trajectory**: Analyzes real-time season scoring pace vs past season baseline (*En Clara Ascensión +X%*, *En Declive*, *Rendimiento Estable*).
- **Role Shift & Starter Detection**: Cross-references FutbolFantasy lineups (0-95%) to detect established players losing starter status or emergent breakout starters.
- **Physical Fitness & Availability**: Flags medical injuries (`playerStatus: injured`), doubts, and discipline expulsions/suspensions.
- **Economic Efficiency (€/pt)** and **Tactical Recommendation Verdicts** (🟢 *Muy Recomendable*, 🟡 *Rotación / Especulación*, 🔴 *Evitar / No Recomendable*).
- **Whole-Squad Scouting Audit (`analyze_team_squad`)**: Full-squad audit evaluating total past season output, squad stars, fitness risk, and line-by-line overview.
- **Telegram & CLI Integration**:
  - `/scout <jugador>` / `/player <jugador>`: Instant deep-dive scouting dossier for any LaLiga footballer.
  - `/scout_team`: Full squad audit with quick-tap individual player scouting buttons.
  - Live Market (`/market`) and Flips (`/flip`) enriched with past season point badges and direct interactive scout buttons.
  - CLI commands `python -m fantasybot scout <jugador>` and `python -m fantasybot scout --team`.

#### 8. Proactive Notification & Alert System (`fantasybot/telegram/notifications.py`)
- **Daily Market Reset Alert**: Proactive morning notification whenever the league launches a new batch of player auctions.
- **Squad Injury & Fitness Doubt Alerts**: Real-time alerts when a squad member transitions to injured, doubtful, or medical recovery.
- **Squad Red Card / Suspension Alerts**: Immediate alerts on player expulsions and disciplinary sanctions.
- **Live Match Points Increments (`+X pts`) & Matchday Rewards**: Notifies incremental points gained by squad players during live matches and official matchday payout distribution.
- **Gameweek Kickoff Countdown Alert (~6 Hours Before)**: Proactive matchday eve reminder with:
  - 🚨 **Critical Negative Balance Warning**: Urges managers with negative balances to sell a player before the kickoff deadline to avoid a 0-point penalty.
  - ⚽ **Lineup Audit**: Compares current XI with AI optimal lineup and provides a 1-tap apply button.
- **Interactive Preference Toggles (`/settings`)**: Full user control over every individual notification category.

#### 9. Admin Usage Analytics & User Registry (`fantasybot/telegram/sessions.py`)
- **Permanent User Registry (`.state/telegram_registry.json`)**: Tracks unique Telegram users, `@username`, first name, interaction counts, and last active timestamps.
- **Admin Access Control**: `/stats` (or `/usuarios` / `/admin_stats`) and `/reportes` restricted exclusively to authorized bot administrator (`TELEGRAM_ADMIN_CHAT_ID` / developer ID `351138675`).
- **CLI Analytics**: `python -m fantasybot stats` for terminal-based user adoption statistics.

#### 10. LLM Agent Integration (`fantasybot/agent.py`)
- Included league rival financial data and clause increases into `review()` dictionary and CLI summary output.

#### 11. Unit Tests (`tests/test_rivals.py`, `tests/test_history.py`, `tests/test_telegram.py`, `tests/test_scouting.py`, `tests/test_alert_notifications.py`)
- Added comprehensive unit test suites covering rival accounting, historical scouting, alert notifications, and multi-user administration.
- All **70/70 unit tests** passing (100% OK).

#### 12. Documentation (`README.md`, `CHANGELOG.md`)
- Complete documentation of multi-season scouting, proactive notifications, and administration commands.

### Fixed & Security Hardening

- **CLI Watch Command Architecture (`fantasybot/cli.py`)**: Restored clean lifecycle for `cmd_watch` (Ctrl+C event loop, browser launcher, background daemon threads) and separated `cmd_scout`, `cmd_stats`, and `cmd_telegram` into dedicated top-level functions.
- **Activity Pagination & Network Safety (`fantasybot/api.py`)**: Capped activity scraping at 100 pages, verified list types, and re-raised exceptions on initial page load to prevent state corruption while gracefully handling network hiccups on subsequent pages.
- **Null Safety in Flips (`fantasybot/strategy/flip.py`)**: Added defensive `.get()` chaining on `playerTeam` and `sellerTeam` to prevent `NoneType` crashes during market scans.
- **Chronological FIFO Lot Matching (`fantasybot/strategy/history.py`)**: Rebuilt trade matching with an ordered open buy lot queue, ensuring accurate P&L calculation and properly distinguishing day 1 squad sales from realized flips.
- **Player Cache Hygiene (`fantasybot/strategy/history.py`)**: Fixed `None` check to avoid caching `"None"` keys, and prevented persistent disk storage of placeholder names on network failures.
- **Incremental Traffic Optimization (`fantasybot/strategy/rivals.py`)**: Switched to page 0 incremental polling for leagues with existing local history, substantially reducing HTTP request volume.
- **Thread Safety & Atomic Persistence (`fantasybot/state.py`, `fantasybot/telegram/sessions.py`)**: Added mutex locking on user registries and atomic file replacement (`.tmp` + `os.replace`) to guarantee data integrity across concurrent Telegram requests.
- **Telegram HTML Sanitization (`fantasybot/telegram/ui.py`, `fantasybot/telegram/bot.py`)**: Wrapped all dynamic manager, player, team, and feedback strings with `html.escape` to eliminate Telegram 400 Bad Request parsing errors.
