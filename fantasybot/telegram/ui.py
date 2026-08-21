"""Telegram message formatting, emojis, and inline keyboard builders."""

from typing import List, Dict, Any, Optional
from ..matching import POS


def main_menu_keyboard(logged_in: bool = True) -> Dict[str, Any]:
    """Builds the main interactive keyboard for Telegram."""
    if not logged_in:
        return {
            "inline_keyboard": [
                [{"text": "🔐 Iniciar Sesión en LaLiga Fantasy", "callback_data": "cmd_login"}],
                [{"text": "📖 Tutorial Paso a Paso (Móvil / PC)", "callback_data": "cmd_tutorial"}],
                [{"text": "ℹ️ Ayuda & Comandos", "callback_data": "cmd_help"}]
            ]
        }

    return {
        "inline_keyboard": [
            [
                {"text": "📋 Mi Plantilla", "callback_data": "cmd_team"},
                {"text": "⚔️ Rivales & Finanzas", "callback_data": "cmd_rivals"},
            ],
            [
                {"text": "📊 Histórico & Flips", "callback_data": "cmd_history"},
                {"text": "🛒 Mercado en Vivo", "callback_data": "cmd_market"},
            ],
            [
                {"text": "⚽ Alineación Óptima", "callback_data": "cmd_lineup"},
                {"text": "🔄 Oportunidades (Flip)", "callback_data": "cmd_flip"},
            ],
            [
                {"text": "🚀 Autopilot Completo", "callback_data": "cmd_autopilot"},
                {"text": "⚙️ Ajustes & Alertas", "callback_data": "cmd_settings"},
            ],
            [
                {"text": "🏆 Mis Ligas / Cambiar", "callback_data": "cmd_leagues"},
                {"text": "👤 Mi Perfil", "callback_data": "cmd_me"},
            ],
            [
                {"text": "💡 Enviar Sugerencia", "callback_data": "cmd_sugerencia_btn"},
                {"text": "🐛 Reportar Bug", "callback_data": "cmd_bug_btn"},
            ],
            [
                {"text": "💖 Apoyar / Donar ⭐", "callback_data": "cmd_donate"},
                {"text": "ℹ️ Ayuda & Comandos", "callback_data": "cmd_help"},
            ],
            [
                {"text": "📖 Tutorial Paso a Paso", "callback_data": "cmd_tutorial"},
            ]
        ]
    }


def donate_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "☕ Invitar a un Café (50 ⭐)", "callback_data": "donate_50"}],
            [{"text": "🍕 Invitar a una Pizza (150 ⭐)", "callback_data": "donate_150"}],
            [{"text": "🚀 Super Sponsor (500 ⭐)", "callback_data": "donate_500"}],
            [{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}]
        ]
    }


def lineup_keyboard(can_apply: bool = False) -> Dict[str, Any]:
    rows = []
    if can_apply:
        rows.append([{"text": "🚀 Aplicar Alineación Óptima en LaLiga", "callback_data": "action_apply_lineup"}])
    rows.append([{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}])
    return {"inline_keyboard": rows}


def flips_keyboard(flips: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for f in flips[:6]:
        mid = f.get("market_id")
        amt = f.get("buy_price")
        name = f.get("nombre")
        via = f.get("via", "SISTEMA")
        pid = f.get("player_id")
        owner = f.get("owner", "Rival")
        last_pts = f.get("last_season_points", 0)
        p_badge = f" | 🏆 {last_pts}p" if last_pts > 0 else ""

        btn_row = []
        if via == "SISTEMA" and mid and amt:
            btn_row.append({"text": f"💰 Pujar {name} ({fmt_eur(amt, compact=True)})", "callback_data": f"bid_{mid}_{amt}"})
        elif via == "CLAUSULA" and pid and amt:
            btn_row.append({"text": f"⚡ Clausulazo {name} ({fmt_eur(amt, compact=True)})", "callback_data": f"clause_{pid}_{amt}"})
        if pid:
            btn_row.append({"text": f"🔍 Scout {name}{p_badge}", "callback_data": f"scout_{pid}"})
        if btn_row:
            rows.append(btn_row)

    if any(f.get("via") == "SISTEMA" for f in flips):
        rows.append([{"text": "🚀 Auto-Pujar por Flips de Mercado", "callback_data": "action_auto_bids"}])
    rows.append([{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}])
    return {"inline_keyboard": rows}


def market_keyboard(market_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    sorted_items = sorted(
        market_items,
        key=lambda x: -(x.get("salePrice") or x.get("price") or (x.get("playerMaster") or {}).get("marketValue") or 0)
    )
    for it in sorted_items[:8]:
        pm = it.get("playerMaster", {})
        pid = pm.get("id")
        name = pm.get("nickname") or pm.get("name") or "Jugador"
        pos = POS.get(pm.get("positionId"), "?")
        last_pts = int(pm.get("lastSeasonPoints") or 0)
        p_badge = f" | 🏆 {last_pts} pts" if last_pts > 0 else ""
        if pid:
            rows.append([{"text": f"🔍 Scout {name} ({pos}{p_badge})", "callback_data": f"scout_{pid}"}])
    rows.append([{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}])
    return {"inline_keyboard": rows}


def team_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "🔍 Scouting de mi Plantilla", "callback_data": "cmd_scout_team"}],
            [{"text": "🏷 Poner Jugador en Venta", "callback_data": "cmd_sell_menu"}],
            [{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}]
        ]
    }


def scout_team_keyboard(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for p in players:
        pm = p.get("playerMaster", {})
        pid = pm.get("id")
        name = pm.get("nickname") or pm.get("name") or "Jugador"
        pos = POS.get(pm.get("positionId"), "?")
        last_pts = int(pm.get("lastSeasonPoints") or 0)
        p_badge = f"{last_pts} pts" if last_pts > 0 else "Nuevo"
        if pid:
            rows.append([{"text": f"🔍 {name} ({pos} | 🏆 {p_badge})", "callback_data": f"scout_{pid}"}])
    rows.append([{"text": "🔙 Volver a Mi Plantilla", "callback_data": "cmd_team"}])
    rows.append([{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}])
    return {"inline_keyboard": rows}


def sell_player_keyboard(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for p in players:
        pm = p.get("playerMaster", {})
        pid = pm.get("id")
        name = pm.get("nickname") or pm.get("name") or "Jugador"
        val = pm.get("marketValue") or 0
        if pid:
            rows.append([{"text": f"🏷 Vender {name} ({val:,} €)", "callback_data": f"sell_{pid}"}])
    rows.append([{"text": "🔙 Volver a Mi Plantilla", "callback_data": "cmd_team"}])
    return {"inline_keyboard": rows}


def settings_keyboard(settings: Dict[str, bool]) -> Dict[str, Any]:
    m_txt = "ACTIVADO 🛒" if settings.get("notify_market_reset", True) else "DESACTIVADO 🔕"
    inj_txt = "ACTIVADO 🚑" if settings.get("notify_injuries", True) else "DESACTIVADO 🔕"
    exp_txt = "ACTIVADO 🟥" if settings.get("notify_expulsions", True) else "DESACTIVADO 🔕"
    pts_txt = "ACTIVADO ⚽" if (settings.get("notify_player_points", True) or settings.get("notify_matchday_points", True)) else "DESACTIVADO 🔕"
    f_txt = "ACTIVADAS 🔔" if settings.get("notify_flips", True) else "DESACTIVADAS 🔕"
    gw_txt = "ACTIVADO ⏳" if settings.get("notify_gameweek_6h", True) else "DESACTIVADO 🔕"
    l_txt = "ACTIVADO ⏰" if settings.get("notify_lineup", True) else "DESACTIVADO 🔕"
    a_txt = "ACTIVADO 🤖" if settings.get("auto_lineup", False) else "DESACTIVADO ⏸"
    return {
        "inline_keyboard": [
            [{"text": f"🛒 Mercado Diario Renovado: {m_txt}", "callback_data": "toggle_notify_market_reset"}],
            [{"text": f"🚑 Alerta de Lesiones: {inj_txt}", "callback_data": "toggle_notify_injuries"}],
            [{"text": f"🟥 Alerta de Sanciones / Expulsión: {exp_txt}", "callback_data": "toggle_notify_expulsions"}],
            [{"text": f"⚽ Puntos de Jugadores (Partido): {pts_txt}", "callback_data": "toggle_notify_player_points"}],
            [{"text": f"⏳ Alerta 6h Inicio Jornada: {gw_txt}", "callback_data": "toggle_notify_gameweek_6h"}],
            [{"text": f"🔔 Chollos de Reventa (Flips): {f_txt}", "callback_data": "toggle_notify_flips"}],
            [{"text": f"⏰ Recordatorio de Alineación: {l_txt}", "callback_data": "toggle_notify_lineup"}],
            [{"text": f"🤖 Auto-Alinear Automático: {a_txt}", "callback_data": "toggle_auto_lineup"}],
            [{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}]
        ]
    }


def leagues_keyboard(leagues: List[Dict[str, Any]], active_lid: Optional[str] = None) -> Dict[str, Any]:
    rows = []
    for lg in leagues:
        lid = str(lg.get("id"))
        name = lg.get("name", "Liga")
        is_active = (str(lid) == str(active_lid))
        prefix = "✅ " if is_active else "🏆 "
        rows.append([{"text": f"{prefix}{name}", "callback_data": f"set_league_{lid}"}])
    rows.append([{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}])
    return {"inline_keyboard": rows}


def back_to_menu_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}]
        ]
    }


def rivals_keyboard(rivals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Creates inline buttons for each rival to inspect their detailed squad."""
    rows = []
    current_row = []
    for idx, r in enumerate(rivals, 1):
        name = r.get("manager_name", f"Manager {idx}")[:12]
        current_row.append({
            "text": f"#{idx} {name}",
            "callback_data": f"rival_{r.get('manager_id')}"
        })
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    rows.append([{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}])
    return {"inline_keyboard": rows}


def history_keyboard(managers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Creates inline buttons for each manager to inspect their trading flips."""
    rows = []
    current_row = []
    for idx, m in enumerate(managers, 1):
        name = m.get("manager_name", f"Manager {idx}")[:12]
        current_row.append({
            "text": f"#{idx} {name}",
            "callback_data": f"history_{m.get('manager_id')}"
        })
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    rows.append([{"text": "🔙 Menú Principal", "callback_data": "cmd_menu"}])
    return {"inline_keyboard": rows}


# --- Text formatters ---

# --- Text Formatters (Mobile-First & Clean Cards) ---

def fmt_eur(amount: Optional[int], compact: bool = False) -> str:
    if amount is None:
        return "0 €"
    if compact:
        if abs(amount) >= 1_000_000:
            return f"{amount / 1_000_000:.1f}M €".replace(".", ",")
        elif abs(amount) >= 1_000:
            return f"{amount / 1_000:.0f}k €"
    # Spanish format: 1.234.567 €
    s = f"{amount:,}".replace(",", ".")
    return f"{s} €"


def format_team(team_data: Dict[str, Any]) -> str:
    players = team_data.get("players", [])
    t_val = team_data.get("teamValue", 0)
    t_money = team_data.get("teamMoney", 0)

    lines = [
        f"📋 <b>Mi Plantilla: {team_data.get('name', 'Equipo')}</b>",
        f"💰 <b>Valor:</b> {fmt_eur(t_val)}  |  🏦 <b>Saldo:</b> {fmt_eur(t_money)}",
        f"👥 <b>Total:</b> {len(players)} jugadores\n"
    ]

    by_pos = {1: ("🧤 PORTEROS", []), 2: ("🛡 DEFENSAS", []), 3: ("🎯 CENTROCAMPISTAS", []), 4: ("⚡ DELANTEROS", [])}
    for p in players:
        pm = p.get("playerMaster", {})
        pos_id = pm.get("positionId", 1)
        if pos_id in by_pos:
            by_pos[pos_id][1].append(p)

    for pos_id in (1, 2, 3, 4):
        header, plist = by_pos[pos_id]
        if plist:
            lines.append(f"<b>{header} ({len(plist)})</b>")
            plist.sort(key=lambda x: -(x.get("playerMaster", {}).get("marketValue") or 0))
            for p in plist:
                pm = p.get("playerMaster", {})
                name = pm.get("nickname") or pm.get("name") or "Jugador"
                mv = pm.get("marketValue") or 0
                clause = p.get("buyoutClause") or 0
                lines.append(f"• <b>{name}</b>: {fmt_eur(mv)} <i>(Cláusula: {fmt_eur(clause, compact=True)})</i>")
            lines.append("")

    return "\n".join(lines)


def format_rivals_summary(rivals: List[Dict[str, Any]]) -> str:
    events_count = rivals[0].get("tracked_events_count", 0) if rivals else 0
    d_from = rivals[0].get("tracked_from_date", "?") if rivals else "?"
    d_to = rivals[0].get("tracked_to_date", "?") if rivals else "?"

    lines = [
        "⚔️ <b>Finanzas y Presupuesto de Rivales</b>",
        f"📦 <i>Historial: {events_count} operaciones ({d_from} a {d_to})</i>\n"
    ]

    medals = ["🥇", "🥈", "🥉"]
    for idx, r in enumerate(rivals, 1):
        is_me = " <b>(TÚ)</b>" if r.get("is_me") else ""
        badge = medals[idx - 1] if idx <= 3 else f"<b>#{idx}</b>"
        name = r.get("manager_name", "Manager")
        tv = r.get("team_value", 0)
        cash = r.get("estimated_balance", 0)
        net = r.get("net_profit", 0)
        net_sign = "+" if net >= 0 else ""

        lines.append(
            f"{badge} <b>{name}</b>{is_me}\n"
            f"  • 💰 <b>Saldo Est.:</b> ~{fmt_eur(cash)}\n"
            f"  • 👥 <b>Plantilla:</b> {fmt_eur(tv)} ({len(r.get('players', []))} jug.)\n"
            f"  • 📈 <b>Neto Fichajes:</b> {net_sign}{fmt_eur(net)}\n"
        )

    lines.append("<i>💡 Pulsa en cualquier botón abajo para ver la plantilla de un rival.</i>")
    return "\n".join(lines)


def format_rival_detail(r: Dict[str, Any]) -> str:
    profit_sign = "+" if r.get("net_profit", 0) >= 0 else ""
    lines = [
        f"👤 <b>Rival: {r.get('manager_name')}</b> (#{r.get('position')} - {r.get('points', 0)} pts)",
        f"💰 <b>Valor Equipo:</b> {fmt_eur(r.get('team_value', 0))}  |  🏦 <b>Saldo Est.:</b> ~{fmt_eur(r.get('estimated_balance', 0))}",
        f"🛒 <b>Compras:</b> {fmt_eur(r.get('purchases', 0))}  |  🏷 <b>Ventas:</b> {fmt_eur(r.get('sales', 0))} ({profit_sign}{fmt_eur(r.get('net_profit', 0))})\n",
        "👥 <b>JUGADORES EN PLANTILLA:</b>\n"
    ]

    players = r.get("players", [])
    if not players:
        lines.append("<i>(Sin jugadores registrados)</i>")
    else:
        for p in players:
            name = p.get("name", "Jugador")
            pos = p.get("pos", "?")
            mv = p.get("market_value", 0)
            diff = p.get("diff", 0)
            diff_sign = "+" if diff >= 0 else ""
            if p.get("is_initial"):
                lines.append(f"• <b>{name}</b> ({pos})\n  💵 Fichaje: <i>(Inicial)</i> → Vale: {fmt_eur(mv)}")
            else:
                bp = p.get("bought_price", 0)
                roi = (diff / bp * 100) if bp else 0
                lines.append(
                    f"• <b>{name}</b> ({pos})\n"
                    f"  💵 Compra: {fmt_eur(bp)} → Vale: {fmt_eur(mv)}\n"
                    f"  📈 Ganancia: <b>{diff_sign}{fmt_eur(diff)}</b> ({roi:+.1f}%)"
                )
            lines.append("")

    return "\n".join(lines)


def format_history_summary(report: Dict[str, Any]) -> str:
    managers = report.get("managers", [])
    lines = [
        "📊 <b>Ranking de Especulación y Rentabilidad (Flips)</b>",
        f"📦 <i>{report.get('tracked_events', 0)} operaciones ({report.get('tracked_from')} a {report.get('tracked_to')})</i>\n"
    ]

    medals = ["🥇", "🥈", "🥉"]
    for idx, m in enumerate(managers, 1):
        is_me = " <b>(TÚ)</b>" if m.get("is_me") else ""
        badge = medals[idx - 1] if idx <= 3 else f"<b>#{idx}</b>"
        name = m.get("manager_name", "Manager")
        tot = m.get("total_pnl", 0)
        tot_sign = "+" if tot >= 0 else ""
        flips = m.get("total_trades", 0)
        win = f"{m.get('win_rate_pct', 0):.0f}%" if flips else "-"
        roi = f"{m.get('avg_roi_pct', 0):+.1f}%" if flips else "-"

        lines.append(
            f"{badge} <b>{name}</b>{is_me}\n"
            f"  • 📈 <b>P&L Total:</b> {tot_sign}{fmt_eur(tot)}\n"
            f"  • 🔄 <b>Flips:</b> {flips} ops  |  🎯 <b>Win Rate:</b> {win}\n"
            f"  • 🚀 <b>ROI Medio:</b> {roi}\n"
        )

    lines.append("<i>💡 Pulsa en cualquier botón abajo para ver el detalle de operaciones.</i>")
    return "\n".join(lines)


def format_manager_history(m: Dict[str, Any]) -> str:
    tot_sign = "+" if m.get("total_pnl", 0) >= 0 else ""
    real_sign = "+" if m.get("realized_profit", 0) >= 0 else ""
    unreal_sign = "+" if m.get("unrealized_profit", 0) >= 0 else ""

    lines = [
        f"📊 <b>Historial de Trading: {m.get('manager_name')}</b> (#{m.get('position')} - {m.get('points', 0)} pts)",
        f"📈 <b>P&L Total:</b> {tot_sign}{fmt_eur(m.get('total_pnl', 0))}",
        f"  • Realizado (Flips cerrados): {real_sign}{fmt_eur(m.get('realized_profit', 0))}",
        f"  • Latente (En plantilla): {unreal_sign}{fmt_eur(m.get('unrealized_profit', 0))}\n"
    ]

    open_h = m.get("open_holdings", [])
    if open_h:
        lines.append("🟢 <b>POSICIONES EN PLANTILLA (Latente):</b>\n")
        for o in open_h:
            diff_sign = "+" if o.get("unrealized_profit", 0) >= 0 else ""
            lines.append(
                f"• <b>{o['name']}</b> ({o['pos']})\n"
                f"  💵 Compra: {fmt_eur(o['buy_price'])} → Vale: {fmt_eur(o['market_value'])}\n"
                f"  📈 Beneficio: <b>{diff_sign}{fmt_eur(o['unrealized_profit'])}</b> ({o['roi_pct']:+.1f}%)\n"
            )

    flips = m.get("completed_flips", [])
    if flips:
        lines.append(f"🔄 <b>FLIPS CERRADOS ({len(flips)} ops | {m.get('win_rate_pct', 0):.1f}% Win):</b>\n")
        for f in flips[:8]:
            diff_sign = "+" if f.get("profit", 0) >= 0 else ""
            lines.append(
                f"• <b>{f['name']}</b> ({f['pos']})\n"
                f"  💵 {fmt_eur(f['buy_price'])} → {fmt_eur(f['sell_price'])}\n"
                f"  💰 Ganancia: <b>{diff_sign}{fmt_eur(f['profit'])}</b> ({f['roi_pct']:+.1f}%)\n"
            )
        if len(flips) > 8:
            lines.append(f"<i>...y {len(flips) - 8} operaciones más en el historial.</i>\n")

    init_s = m.get("initial_sales", [])
    if init_s:
        lines.append(f"📦 <b>VENTAS DE PLANTILLA INICIAL ({len(init_s)}):</b>")
        for s in init_s[:4]:
            lines.append(f"• <b>{s['name']}</b> ({s['pos']}): {fmt_eur(s['sell_price'])} <i>({s['sell_date']})</i>")
        if len(init_s) > 4:
            lines.append(f"<i>...y {len(init_s) - 4} ventas más.</i>")

    return "\n".join(lines)


def format_scouting_card(s: Dict[str, Any]) -> str:
    name = s.get("name", "Jugador")
    pos = s.get("pos", "Jugador")
    team = s.get("team", "LaLiga")
    mv = s.get("market_value", 0)
    cur_pts = s.get("current_points", 0)
    cur_avg = s.get("current_avg", 0.0)
    last_pts = s.get("last_season_points", 0)
    last_avg = s.get("last_season_avg", 0.0)
    tier = s.get("tier_badge", "")
    starter = s.get("starter_status", "")
    role_shift = s.get("role_shift", "")
    evolution = s.get("evolution", "")
    phys = s.get("physical_status", "")
    efficiency = s.get("efficiency", "")
    verdict = s.get("verdict", "")

    lines = [
        f"🔍 <b>Informe de Scouting: {name}</b> ({pos})",
        f"🏟 <b>Equipo:</b> {team}  |  💵 <b>Valor:</b> {fmt_eur(mv)}\n",
        f"📜 <b>HISTORIAL TEMPORADA PASADA:</b>",
        f"• <b>Puntos Totales:</b> <b>{last_pts} pts</b> (Media: ~{last_avg} pts/jornada)",
        f"• <b>Categoría:</b> {tier}\n",
        f"📊 <b>TEMPORADA ACTUAL:</b>",
        f"• <b>Puntos Acumulados:</b> <b>{cur_pts} pts</b> (Media: {cur_avg:.1f} pts/partido)",
        f"• <b>Evolución:</b> {evolution}\n",
        f"🏃‍♂️ <b>TITULARIDAD Y ROL TÁCTICO:</b>",
        f"• <b>Previsión Once:</b> {starter}",
        f"• <b>Análisis de Rol:</b> <i>{role_shift}</i>\n",
        f"🩺 <b>ESTADO FÍSICO Y DISPONIBILIDAD:</b>",
        f"• {phys}\n",
        f"💰 <b>RENTABILIDAD ECONÓMICA (€/pt):</b>",
        f"• {efficiency}\n",
        f"🎯 <b>DICTAMEN DE SCOUTING:</b>",
        f"<b>{verdict}</b>"
    ]
    return "\n".join(lines)


def format_team_scouting_report(ts: Dict[str, Any]) -> str:
    name = ts.get("team_name", "Mi Plantilla")
    n_players = ts.get("total_players", 0)
    t_val = ts.get("total_val", 0)
    t_money = ts.get("team_money", 0)
    tot_last_pts = ts.get("total_last_pts", 0)
    avg_last_pts = ts.get("avg_last_pts", 0.0)

    stars = ts.get("stars", [])
    invalids = ts.get("injured_or_suspended", [])
    risk = ts.get("role_risk", [])
    emerging = ts.get("emerging", [])

    lines = [
        f"🔍 <b>Auditoría de Scouting: {name}</b>",
        f"💰 <b>Valor:</b> {fmt_eur(t_val)}  |  🏦 <b>Saldo:</b> {fmt_eur(t_money)}",
        f"👥 <b>Plantilla:</b> {n_players} jugadores  |  🏆 <b>Pts Totales Año Pasado:</b> {tot_last_pts} pts (Media: {avg_last_pts} pts/jugador)\n"
    ]

    if stars:
        s_names = ", ".join([f"<b>{r['name']}</b> ({r['last_season_points']} pts)" for r in stars[:5]])
        lines.append(f"🌟 <b>ESTRELLAS CONSOLIDADAS:</b>\n{s_names}\n")

    if invalids:
        inv_lines = []
        for r in invalids:
            inv_lines.append(f"• <b>{r['name']}</b> ({r['pos']}): {r['physical_status']}")
        lines.append(f"🚑 <b>BAJAS Y SANCIONES ACTIVAS ({len(invalids)}):</b>\n" + "\n".join(inv_lines) + "\n")

    if risk:
        r_lines = []
        for r in risk:
            prob_str = f"{r['starting_prob']}%" if r['starting_prob'] is not None else "?"
            r_lines.append(f"• <b>{r['name']}</b> ({r['pos']}): {r['last_season_points']} pts el año pasado → Hoy suplente ({prob_str})")
        lines.append(f"⚠️ <b>JUGADORES EN RIESGO / PÉRDIDA DE ROL ({len(risk)}):</b>\n" + "\n".join(r_lines) + "\n")

    if emerging:
        em_lines = []
        for r in emerging:
            prob_str = f"{r['starting_prob']}%" if r['starting_prob'] is not None else "?"
            em_lines.append(f"• <b>{r['name']}</b> ({r['pos']}): {prob_str} titular (sin minutos año pasado)")
        lines.append(f"🚀 <b>JUGADORES EMERGENTES / REVELACIÓN ({len(emerging)}):</b>\n" + "\n".join(em_lines) + "\n")

    lines.append("📋 <b>RESUMEN POR LÍNEAS:</b>")
    headers = {1: "🧤 PORTEROS", 2: "🛡 DEFENSAS", 3: "🎯 CENTROCAMPISTAS", 4: "⚡ DELANTEROS"}
    by_pos = ts.get("by_pos", {})
    for pid in (1, 2, 3, 4):
        plist = by_pos.get(pid, [])
        if plist:
            lines.append(f"\n<b>{headers[pid]}:</b>")
            for r in plist:
                last_p = r['last_season_points']
                p_badge = f"{last_p} pts" if last_p > 0 else "Nuevo"
                prob_s = f"{r['starting_prob']}%" if r['starting_prob'] is not None else "?"
                emoji_v = "🟢" if "MUY" in r['verdict'] else ("🟡" if "ROTACIÓN" in r['verdict'] else "🔴")
                lines.append(f"{emoji_v} <b>{r['name']}</b>: 🏆 {p_badge} | ⚡ {prob_s} | {fmt_eur(r['market_value'], compact=True)}")

    lines.append("\n<i>💡 Pulsa en cualquier botón abajo para ver la ficha detallada de un jugador.</i>")
    return "\n".join(lines)


def format_market(market_items: List[Dict[str, Any]]) -> str:
    lines = [
        "🛒 <b>Mercado de Fichajes en Vivo</b>",
        "<i>Todos los jugadores actualmente a subasta en tu liga:</i>\n"
    ]
    sorted_items = sorted(
        market_items,
        key=lambda x: -(x.get("salePrice") or x.get("price") or (x.get("playerMaster") or {}).get("marketValue") or 0)
    )

    if not sorted_items:
        lines.append("📭 No hay jugadores en subasta en este momento.")
        return "\n".join(lines)

    for it in sorted_items[:12]:
        pm = it.get("playerMaster", {})
        pos = POS.get(pm.get("positionId"), "?")
        name = pm.get("nickname") or pm.get("name") or "Jugador"
        price = it.get("salePrice") or it.get("price") or pm.get("marketValue") or 0
        clause = it.get("playerTeam", {}).get("buyoutClause") or it.get("buyoutClause") or pm.get("marketValue") or 0
        last_pts = int(pm.get("lastSeasonPoints") or 0)
        pts_badge = f"  |  🏆 Año pasado: <b>{last_pts} pts</b>" if last_pts > 0 else ""

        discr = it.get("discr", "")
        if discr == "marketPlayerLeague":
            origin = "🏛 Mercado Libre"
        else:
            mgr = it.get("sellerTeam", {}).get("manager", {}).get("managerName") or "Rival"
            origin = f"👤 Rival: {mgr}"

        lines.append(
            f"• <b>{name}</b> ({pos}){pts_badge}\n"
            f"  💵 <b>Precio:</b> {fmt_eur(price)}  |  🔒 <b>Cláusula:</b> {fmt_eur(clause, compact=True)}\n"
            f"  🏷 <i>{origin}</i>\n"
        )

    lines.append("<i>💡 Pulsa en cualquier botón abajo para ver el informe de scouting completo.</i>")
    return "\n".join(lines)


def format_trends(trends_list: List[Dict[str, Any]]) -> str:
    up = sorted([p for p in trends_list if p.get("tendencia", 0) > 0], key=lambda x: -x["tendencia"])[:6]
    down = sorted([p for p in trends_list if p.get("tendencia", 0) < 0], key=lambda x: x["tendencia"])[:6]

    lines = [
        "📈 <b>Tendencias de Mercado LaLiga</b>\n",
        "🟢 <b>MAYORES SUBIDAS:</b>"
    ]
    for p in up:
        lines.append(f"• <b>{p.get('nombre', 'Jugador')}</b> ({p.get('equipo', '')}): <b>+{fmt_eur(p.get('tendencia', 0))}/día 📈</b>")

    lines.append("\n🔴 <b>MAYORES BAJADAS:</b>")
    for p in down:
        lines.append(f"• <b>{p.get('nombre', 'Jugador')}</b> ({p.get('equipo', '')}): <b>{fmt_eur(p.get('tendencia', 0))}/día 📉</b>")

    return "\n".join(lines)


def format_tutorial() -> str:
    return (
        "📖 <b>Tutorial: Cómo conectar tu cuenta paso a paso</b>\n\n"
        "La autenticación es 100% oficial mediante <b>OAuth2 y PKCE</b> de LaLiga. "
        "El bot nunca ve tu contraseña.\n\n"
        "─────────────────────────\n"
        "📱 <b>MÉTODO 1: DESDE EL MÓVIL (Recomendado)</b>\n"
        "1️⃣ Pulsa en /login y haz clic en <b>Iniciar Sesión Oficial en LaLiga</b>.\n"
        "2️⃣ Inicia sesión con tu cuenta (Google, Apple o Email).\n"
        "3️⃣ Al terminar, el navegador intentará abrir la app y se quedará en blanco o mostrará un mensaje de alerta.\n"
        "4️⃣ <b>Toca arriba en la barra de direcciones del navegador</b> y copia la URL completa (empieza por <code>authredirect://...</code>).\n"
        "5️⃣ <b>Pega ese enlace aquí en el chat</b> y el bot te conectará al instante.\n\n"
        "─────────────────────────\n"
        "💻 <b>MÉTODO 2: DESDE EL ORDENADOR (Chrome / Edge)</b>\n"
        "1️⃣ Abre el enlace de /login en tu PC.\n"
        "2️⃣ Pulsa la tecla <b>F12</b> (o clic derecho → Inspeccionar) y ve a la pestaña <b>Red (Network)</b>.\n"
        "3️⃣ Marca la casilla <b>Preserve log</b> (Conservar registro).\n"
        "4️⃣ Inicia sesión con tu cuenta.\n"
        "5️⃣ En la lista de peticiones verás una fila en rojo que dice <code>authredirect://... (canceled)</code>.\n"
        "6️⃣ Haz <b>clic derecho sobre esa fila → Copiar → Copiar dirección del enlace</b>.\n"
        "7️⃣ <b>Pega el enlace en el chat</b> de Telegram.\n\n"
        "<i>✅ ¡Una vez conectado, la sesión dura 90 días y se renueva automáticamente!</i>"
    )


def format_admin_stats(stats: Dict[str, Any]) -> str:
    total_u = stats.get("total_telegram_users", 0)
    logged_u = stats.get("total_logged_in_users", 0)
    users = stats.get("users", [])

    lines = [
        "📊 <b>Panel de Estadísticas y Usuarios del Bot</b>\n",
        f"👥 <b>Usuarios Registrados (Telegram):</b> <code>{total_u}</code>",
        f"🔐 <b>Cuentas Fantasy Conectadas:</b> <code>{logged_u}</code>",
        f"⏳ <b>Ratio de Conversión:</b> <code>{(logged_u / max(1, total_u)) * 100:.1f}%</code>\n",
        "📋 <b>LISTADO DE USUARIOS ACTIVOS:</b>"
    ]

    if not users:
        lines.append("<i>(No hay usuarios registrados todavía)</i>")
        return "\n".join(lines)

    for idx, u in enumerate(users[:20], 1):
        status_icon = "🟢" if u.get("is_logged_in") else "⚪"
        uname = f"@{u['username']}" if u.get("username") else "Sin alias"
        fname = u.get("first_name", "Usuario")
        cid = u.get("chat_id")
        last_s = u.get("last_seen", "Desconocido")
        cnt = u.get("interaction_count", 1)

        lines.append(
            f"{idx}. {status_icon} <b>{fname}</b> ({uname})\n"
            f"   🆔 <code>{cid}</code>  |  🔄 {cnt} interacciones\n"
            f"   📅 Última actividad: <i>{last_s}</i>\n"
        )

    if len(users) > 20:
        lines.append(f"<i>...y {len(users) - 20} usuarios más en el registro.</i>")

    return "\n".join(lines)
