"""
skills/statistics — Capa 1 (histórico 2024-2025)

Números duros: goles, finales, premios, head-to-head. Mismo contrato que
skills.py (Firestore): cada función devuelve un string ya formateado y
listo para presentar — el LLM no calcula nada, solo lo redacta.
"""
import pandas as pd
from graph_skills._client import q


def jugador_perfil_historico(nombre: str) -> str:
    """
    Perfil completo de un jugador: goles por equipo/edición, tarjetas y premios.
    Igual que goles_jugador_todas_temporadas en skills.py: nunca suma goles
    entre equipos distintos.
    """
    goles = q(
        """
        MATCH (p:Player)-[r:SCORED_IN]->(e:Edition)
        WHERE toLower(p.name) CONTAINS toLower($nombre)
        MATCH (t:Team {id: r.teamId})
        RETURN p.name AS jugador, e.name AS edicion, t.name AS equipo, r.goals AS goles
        ORDER BY e.year, e.name
        """,
        {"nombre": nombre},
    )
    tarjetas = q(
        """
        MATCH (p:Player)-[r:CARDED_IN]->(m:Match)
        WHERE toLower(p.name) CONTAINS toLower($nombre)
        MATCH (t:Team {id: r.teamId})
        OPTIONAL MATCH (rival:Team)-[:PLAYED_MATCH]->(m)
        WHERE rival <> t
        RETURN t.name AS equipo, m.fecha AS fecha, m.partido AS partido,
               rival.name AS rival, r.yellowCards AS amarillas, r.redCards AS rojas
        """,
        {"nombre": nombre},
    )
    premios = q(
        """
        MATCH (p:Player)-[:WON]->(a:Award)-[:IN_EDITION]->(e:Edition)
        WHERE toLower(p.name) CONTAINS toLower($nombre)
        RETURN a.name AS premio, e.name AS edicion
        ORDER BY e.year
        """,
        {"nombre": nombre},
    )

    if not goles and not tarjetas and not premios:
        return f"No se encontró a '{nombre}' en el grafo histórico."

    nombre_real = goles[0]["jugador"] if goles else nombre.title()
    lineas = ["RESULTADO CALCULADO — presenta esto exactamente, sin sumar entre equipos:", ""]
    lineas.append(f"Historial de {nombre_real} en la CLC (fuente: grafo histórico):")

    if goles:
        por_equipo: dict[str, list] = {}
        for g in goles:
            por_equipo.setdefault(g["equipo"], []).append((g["edicion"], g["goles"]))
        lineas.append("")
        lineas.append("GOLES:")
        for equipo, registros in por_equipo.items():
            lineas.append(f"  {equipo}:")
            for edicion, goles_ed in registros:
                lineas.append(f"    - {edicion}: {goles_ed} goles")
            total = sum(g for _, g in registros)
            lineas.append(f"    Total en {equipo}: {total} goles")
    else:
        lineas.append("")
        lineas.append("GOLES: sin registros.")

    if tarjetas:
        lineas.append("")
        lineas.append("TARJETAS:")
        for t in tarjetas:
            partes = []
            if t["amarillas"]:
                partes.append(f"{t['amarillas']} amarilla(s)")
            if t["rojas"]:
                partes.append(f"{t['rojas']} roja(s)")
            rival = f" vs {t['rival']}" if t.get("rival") else ""
            lineas.append(
                f"  - Fecha {t['fecha']}, Partido {t['partido']}{rival} ({t['equipo']}): "
                f"{', '.join(partes) or 'sin sanción registrada'}"
            )

    if premios:
        lineas.append("")
        lineas.append("PREMIOS:")
        for p in premios:
            lineas.append(f"  - {p['premio']} ({p['edicion']})")

    lineas.append("")
    lineas.append("REGLA: Muestra cada equipo por separado en goles. NO sumes totales entre equipos distintos.")
    return "\n".join(lineas)


def top_goleadores_historico(n: int = 10) -> str:
    """
    Ranking real sumado entre ediciones DEL MISMO EQUIPO — a diferencia de
    top_goleadores_todas_temporadas (Firestore), que solo puede rankear por
    mejor temporada individual.
    """
    filas = q(
        """
        MATCH (p:Player)-[r:SCORED_IN]->(e:Edition)
        MATCH (t:Team {id: r.teamId})
        RETURN p.name AS jugador, t.name AS equipo, sum(r.goals) AS goles
        ORDER BY goles DESC
        LIMIT $n
        """,
        {"n": n},
    )
    if not filas:
        return "No hay datos de goles en el grafo."
    df = pd.DataFrame(filas)
    return (
        f"Top {n} goleadores CLC — histórico, por jugador+equipo (grafo):\n"
        f"{df.to_string(index=False)}\n"
        f"DATOS EXACTOS — no hagas cálculos adicionales, no sumes entre equipos distintos."
    )


def finales_por_equipo() -> str:
    """Cuántas finales jugó cada equipo, histórico, con detalle de en qué
    edición fue cada una y si ganó o perdió (y contra quién)."""
    filas = q(
        """
        MATCH (t:Team)-[r:REACHED_STAGE]->(s:Stage {id: 'stage_final'})
        MATCH (e:Edition {id: r.editionId})
        OPTIONAL MATCH (t)-[:PLAYED_MATCH]->(m:Match)-[:AT_STAGE]->(s)
        WHERE EXISTS { (m)-[:IN_EDITION]->(e) }
        OPTIONAL MATCH (rival:Team)-[:PLAYED_MATCH]->(m) WHERE rival <> t
        RETURN t.name AS equipo, t.id AS team_id, e.name AS edicion,
               m.winnerTeamId AS winner_id, rival.name AS rival
        ORDER BY t.name, e.year
        """
    )
    if not filas:
        return "No hay datos de finales en el grafo."

    por_equipo: dict[str, list] = {}
    for f in filas:
        por_equipo.setdefault(f["equipo"], []).append(f)

    ranking = sorted(por_equipo.items(), key=lambda x: len(x[1]), reverse=True)
    lineas = ["Finales jugadas por equipo (histórico), con detalle de cada una:", ""]
    for equipo, partidos in ranking:
        lineas.append(f"{equipo} ({len(partidos)} finales):")
        for f in partidos:
            if f.get("winner_id") and f["winner_id"] == f["team_id"]:
                resultado = "ganó"
            elif f.get("rival"):
                resultado = f"perdió ante {f['rival']}"
            else:
                resultado = "resultado no disponible"
            lineas.append(f"  - {f['edicion']}: {resultado}")
        lineas.append("")
    return "\n".join(lineas)


def premios_historicos(award_type: str) -> str:
    """award_type: 'GOLDEN_BOOT' | 'BEST_PLAYER' | 'BEST_GOALKEEPER'"""
    filas = q(
        """
        MATCH (p:Player)-[:WON]->(a:Award {type: $award_type})-[:IN_EDITION]->(e:Edition)
        RETURN e.name AS edicion, p.name AS jugador, a.name AS premio
        ORDER BY e.year
        """,
        {"award_type": award_type},
    )
    if not filas:
        return f"No hay ganadores registrados para '{award_type}'."
    df = pd.DataFrame(filas)
    nombre_premio = filas[0]["premio"]
    return f"Ganadores históricos — {nombre_premio}:\n{df[['edicion', 'jugador']].to_string(index=False)}"


def _vez_o_veces(n: int) -> str:
    return "1 vez" if n == 1 else f"{n} veces"


def enfrentamientos_entre_equipos(equipo1: str = None, equipo2: str = None) -> str:
    """
    Estadísticas AGREGADAS de enfrentamientos (victorias-empates-derrotas),
    no partido por partido (para eso está historial_entre_equipos). Tres modos:

    - equipo1 Y equipo2: resumen agregado entre esos dos equipos específicos.
    - solo equipo1: resumen agregado de ese equipo contra CADA rival que ha
      enfrentado en la historia.
    - ninguno de los dos: busca en TODO el grafo pares de equipos donde uno
      de los dos nunca le ha ganado al otro (con al menos 2 partidos jugados
      entre ellos) — para preguntas abiertas tipo '¿qué equipo nunca le ha
      ganado a otro?'.

    IMPORTANTE: usa r.result ('G'/'E'/'P'), NUNCA compara goles directamente.
    Un partido definido por penales (ej. 0-0) tiene goles empatados pero SÍ
    hay un ganador real — comparar goles a favor lo contaría como empate,
    ocultando la victoria/derrota real. r.result ya viene calculado
    correctamente desde el dato original, penales incluidos.
    """
    if equipo1:
        filtro_equipo2 = "AND toLower(t2.name) CONTAINS toLower($equipo2)" if equipo2 else ""
        filas = q(
            f"""
            MATCH (t1:Team)-[r1:PLAYED_MATCH]->(m:Match)<-[r2:PLAYED_MATCH]-(t2:Team)
            WHERE toLower(t1.name) CONTAINS toLower($equipo1) AND t1 <> t2
            {filtro_equipo2}
            WITH t1, t2,
                 sum(CASE WHEN r1.result = 'G' THEN 1 ELSE 0 END) AS victorias,
                 sum(CASE WHEN r1.result = 'E' THEN 1 ELSE 0 END) AS empates,
                 sum(CASE WHEN r1.result = 'P' THEN 1 ELSE 0 END) AS derrotas,
                 count(*) AS partidos
            RETURN t1.name AS equipo1, t2.name AS rival, victorias, empates, derrotas, partidos
            ORDER BY partidos DESC
            """,
            {"equipo1": equipo1, "equipo2": equipo2},
        )
        if not filas:
            objetivo = f"'{equipo1}' contra '{equipo2}'" if equipo2 else f"'{equipo1}'"
            return f"No se encontraron enfrentamientos de {objetivo} en el grafo."

        partidos_detalle = q(
            f"""
            MATCH (t1:Team)-[r1:PLAYED_MATCH]->(m:Match)<-[r2:PLAYED_MATCH]-(t2:Team)
            WHERE toLower(t1.name) CONTAINS toLower($equipo1) AND t1 <> t2
            {filtro_equipo2}
            MATCH (m)-[:IN_EDITION]->(e:Edition)
            MATCH (m)-[:AT_STAGE]->(s:Stage)
            RETURN t2.name AS rival, e.name AS edicion, s.name AS fase, r1.goals AS goles1, r2.goals AS goles2
            ORDER BY t2.name, e.year
            """,
            {"equipo1": equipo1, "equipo2": equipo2},
        )
        partidos_por_rival: dict[str, list] = {}
        for p in partidos_detalle:
            partidos_por_rival.setdefault(p["rival"], []).append(p)

        nombre1 = filas[0]["equipo1"]
        lineas = [f"Enfrentamientos históricos de {nombre1} (agregado, con detalle de partidos):", ""]
        for f in filas:
            nunca_gano = " — NUNCA le ha ganado" if f["victorias"] == 0 else ""
            nunca_perdio = " — NUNCA ha perdido contra este rival" if f["derrotas"] == 0 else ""
            lineas.append(
                f"  vs {f['rival']}: {f['victorias']}V {f['empates']}E {f['derrotas']}D "
                f"({f['partidos']} partidos){nunca_gano}{nunca_perdio}"
            )
            for p in partidos_por_rival.get(f["rival"], []):
                lineas.append(f"      · {p['edicion']}, {p['fase']}: {nombre1} {p['goles1']} - {p['goles2']} {p['rival']}")
        return "\n".join(lineas)

    # Ninguno de los dos equipos dado: escaneo global
    filas = q(
        """
        MATCH (t1:Team)-[r1:PLAYED_MATCH]->(m:Match)<-[r2:PLAYED_MATCH]-(t2:Team)
        WHERE elementId(t1) < elementId(t2)
        WITH t1, t2,
             sum(CASE WHEN r1.result = 'G' THEN 1 ELSE 0 END) AS t1_gano,
             sum(CASE WHEN r2.result = 'G' THEN 1 ELSE 0 END) AS t2_gano,
             sum(CASE WHEN r1.result = 'E' THEN 1 ELSE 0 END) AS empates,
             count(*) AS partidos
        WHERE partidos >= 2 AND (t1_gano = 0 OR t2_gano = 0)
        RETURN t1.name AS equipo1, t2.name AS equipo2, t1_gano, t2_gano, empates, partidos
        ORDER BY partidos DESC
        """
    )
    if not filas:
        return "No se encontró ningún par de equipos donde uno nunca le haya ganado al otro (con al menos 2 partidos jugados entre ellos)."

    todos_partidos = q(
        """
        MATCH (t1:Team)-[r1:PLAYED_MATCH]->(m:Match)<-[r2:PLAYED_MATCH]-(t2:Team)
        WHERE elementId(t1) < elementId(t2)
        MATCH (m)-[:IN_EDITION]->(e:Edition)
        MATCH (m)-[:AT_STAGE]->(s:Stage)
        RETURN t1.name AS equipo1, t2.name AS equipo2, e.name AS edicion, s.name AS fase,
               r1.goals AS goles1, r2.goals AS goles2
        ORDER BY t1.name, t2.name, e.year
        """
    )
    partidos_por_par: dict[tuple, list] = {}
    for p in todos_partidos:
        partidos_por_par.setdefault((p["equipo1"], p["equipo2"]), []).append(p)

    def _lineas_partidos(equipo1_nombre, equipo2_nombre):
        out = []
        for p in partidos_por_par.get((equipo1_nombre, equipo2_nombre), []):
            out.append(f"      · {p['edicion']}, {p['fase']}: {equipo1_nombre} {p['goles1']} - {p['goles2']} {equipo2_nombre}")
        return out

    # OJO: "nunca ha ganado" (0 victorias) NO es lo mismo que "el otro SIEMPRE
    # ha ganado" — puede haber empates de por medio. Solo es "siempre ganó"
    # si el otro equipo ganó TODOS los partidos (0 empates, 0 derrotas propias).
    siempre_gano = [f for f in filas if f["t1_gano"] == f["partidos"] or f["t2_gano"] == f["partidos"]]
    nunca_gano_con_empates = [f for f in filas if f not in siempre_gano and not (f["t1_gano"] == 0 and f["t2_gano"] == 0)]
    todo_empate = [f for f in filas if f["t1_gano"] == 0 and f["t2_gano"] == 0]

    lineas = [
        f"TOTAL: {len(filas)} pares donde un equipo nunca ha ganado al otro (mínimo 2 partidos). "
        f"De esos, {len(siempre_gano)} son de dominio absoluto (el otro equipo ganó todos los partidos, "
        f"sin empates ni derrotas), {len(nunca_gano_con_empates)} tienen victorias del otro equipo mezcladas "
        f"con empates, y {len(todo_empate)} son solo empates. Usa estos números exactos — no cuentes tú mismo.",
        "",
    ]
    if siempre_gano:
        lineas.append(f"Dominio absoluto — el otro equipo ganó todos los partidos ({len(siempre_gano)} casos):")
        for f in siempre_gano:
            ganador, perdedor = (f["equipo1"], f["equipo2"]) if f["t1_gano"] == f["partidos"] else (f["equipo2"], f["equipo1"])
            lineas.append(f"  - {ganador} siempre le ha ganado a {perdedor}: le ganó los {f['partidos']} partidos que jugaron, sin ningún empate.")
            lineas += _lineas_partidos(f["equipo1"], f["equipo2"])
        lineas.append("")
    if nunca_gano_con_empates:
        lineas.append(f"Nunca ganó, con empates y/o victorias del rival mezcladas ({len(nunca_gano_con_empates)} casos):")
        for f in nunca_gano_con_empates:
            perdedor, ganador, veces_gano = (f["equipo1"], f["equipo2"], f["t2_gano"]) if f["t1_gano"] == 0 else (f["equipo2"], f["equipo1"], f["t1_gano"])
            derrotas = f["partidos"] - veces_gano - f["empates"]
            partes = []
            if veces_gano:
                partes.append(f"{ganador} le ganó {_vez_o_veces(veces_gano)}")
            if f["empates"]:
                partes.append(f"empataron {_vez_o_veces(f['empates'])}")
            detalle = " y ".join(partes) if partes else ""
            lineas.append(
                f"  - {perdedor} nunca le ha ganado a {ganador} en {f['partidos']} partidos jugados: {detalle}."
            )
            lineas += _lineas_partidos(f["equipo1"], f["equipo2"])
        lineas.append("")
    if todo_empate:
        lineas.append(f"Solo empates — nunca hubo un ganador entre ellos ({len(todo_empate)} casos):")
        for f in todo_empate:
            lineas.append(
                f"  - {f['equipo1']} nunca le ha ganado a {f['equipo2']}, han empatado {_vez_o_veces(f['partidos'])}."
            )
            lineas += _lineas_partidos(f["equipo1"], f["equipo2"])
    return "\n".join(lineas)



def ficha_equipo(equipo: str) -> str:
    """
    Ficha consolidada de un equipo: nombres anteriores, fase máxima por
    edición (con resultado y contra quién), cuántas finales jugó, y su
    goleador histórico. Junta en una sola llamada lo que antes requería
    historia_equipo + cambios_nombre + finales_por_equipo + top_goleadores
    por separado — útil para preguntas abiertas tipo 'cuéntame todo sobre X'.
    """
    info = q(
        "MATCH (t:Team) WHERE toLower(t.name) CONTAINS toLower($equipo) RETURN t.name AS equipo, t.id AS id LIMIT 1",
        {"equipo": equipo},
    )
    if not info:
        return f"No se encontró al equipo '{equipo}' en el grafo histórico."
    equipo_id, nombre_real = info[0]["id"], info[0]["equipo"]

    alias = q(
        "MATCH (t:Team {id: $id})-[:USED_NAME]->(n:TeamName) WHERE n.nameType <> 'CANONICAL' RETURN n.name AS nombre",
        {"id": equipo_id},
    )
    fases = q(
        """
        MATCH (t:Team {id: $id})-[r:REACHED_STAGE]->(s:Stage)
        MATCH (e:Edition {id: r.editionId})
        OPTIONAL MATCH (t)-[:PLAYED_MATCH]->(m:Match)-[:AT_STAGE]->(s)
        WHERE EXISTS { (m)-[:IN_EDITION]->(e) }
        OPTIONAL MATCH (rival:Team)-[:PLAYED_MATCH]->(m) WHERE rival <> t
        RETURN e.name AS edicion, s.name AS fase, m.winnerTeamId AS winner_id, rival.name AS rival
        ORDER BY e.year
        """,
        {"id": equipo_id},
    )
    goleador = q(
        """
        MATCH (p:Player)-[r:SCORED_IN]->(:Edition) WHERE r.teamId = $id
        RETURN p.name AS jugador, sum(r.goals) AS goles ORDER BY goles DESC LIMIT 1
        """,
        {"id": equipo_id},
    )

    finales = sum(1 for f in fases if f["fase"] == "Final")
    lineas = [f"Ficha de {nombre_real}:", ""]
    if alias:
        lineas.append(f"Nombres anteriores: {', '.join(a['nombre'] for a in alias)}")
        lineas.append("")
    lineas.append(f"Finales jugadas: {finales}")
    lineas.append("")
    lineas.append("Fase máxima por edición:")
    for f in fases:
        resultado = ""
        if f.get("winner_id"):
            resultado = " (ganó ese partido)" if f["winner_id"] == equipo_id else (f" (perdió ante {f['rival']})" if f.get("rival") else "")
        lineas.append(f"  - {f['edicion']}: {f['fase']}{resultado}")
    if goleador:
        lineas.append("")
        lineas.append(f"Máximo goleador histórico del equipo: {goleador[0]['jugador']} ({goleador[0]['goles']} goles)")
    return "\n".join(lineas)


def comparar_equipos(equipo1: str, equipo2: str) -> str:
    """
    Compara dos equipos lado a lado: finales jugadas/ganadas, récord general
    (victorias-empates-derrotas en TODA su historia, no solo entre sí) y su
    goleador histórico. NO es head-to-head entre ellos — para eso usa
    enfrentamientos_entre_equipos o historial_entre_equipos.
    """

    def _datos(equipo):
        info = q(
            "MATCH (t:Team) WHERE toLower(t.name) CONTAINS toLower($equipo) RETURN t.name AS equipo, t.id AS id LIMIT 1",
            {"equipo": equipo},
        )
        if not info:
            return None
        equipo_id, nombre_real = info[0]["id"], info[0]["equipo"]

        finales = q(
            """
            MATCH (t:Team {id: $id})-[r:REACHED_STAGE]->(s:Stage {id: 'stage_final'})
            MATCH (e:Edition {id: r.editionId})
            OPTIONAL MATCH (t)-[:PLAYED_MATCH]->(m:Match)-[:AT_STAGE]->(s)
            WHERE EXISTS { (m)-[:IN_EDITION]->(e) }
            RETURN count(*) AS jugadas, sum(CASE WHEN m.winnerTeamId = $id THEN 1 ELSE 0 END) AS ganadas
            """,
            {"id": equipo_id},
        )
        record = q(
            """
            MATCH (t:Team {id: $id})-[r:PLAYED_MATCH]->(:Match)
            RETURN sum(CASE WHEN r.result = 'G' THEN 1 ELSE 0 END) AS victorias,
                   sum(CASE WHEN r.result = 'E' THEN 1 ELSE 0 END) AS empates,
                   sum(CASE WHEN r.result = 'P' THEN 1 ELSE 0 END) AS derrotas
            """,
            {"id": equipo_id},
        )
        goleador = q(
            """
            MATCH (p:Player)-[r:SCORED_IN]->(:Edition) WHERE r.teamId = $id
            RETURN p.name AS jugador, sum(r.goals) AS goles ORDER BY goles DESC LIMIT 1
            """,
            {"id": equipo_id},
        )
        return {
            "nombre": nombre_real,
            "finales_jugadas": finales[0]["jugadas"] if finales else 0,
            "finales_ganadas": finales[0]["ganadas"] if finales else 0,
            "record": record[0] if record else {"victorias": 0, "empates": 0, "derrotas": 0},
            "goleador": goleador[0] if goleador else None,
        }

    d1 = _datos(equipo1)
    d2 = _datos(equipo2)
    if not d1:
        return f"No se encontró al equipo '{equipo1}' en el grafo histórico."
    if not d2:
        return f"No se encontró al equipo '{equipo2}' en el grafo histórico."

    def _bloque(d):
        r = d["record"]
        goleador_txt = f"{d['goleador']['jugador']} ({d['goleador']['goles']} goles)" if d["goleador"] else "sin registros"
        return [
            f"{d['nombre']}:",
            f"  Finales jugadas: {d['finales_jugadas']} (ganadas: {d['finales_ganadas']})",
            f"  Récord general (todos sus partidos, no solo entre sí): {r['victorias']} victorias, "
            f"{r['empates']} empates, {r['derrotas']} derrotas",
            f"  Goleador histórico del equipo: {goleador_txt}",
        ]

    lineas = ["COMPARACIÓN DE EQUIPOS — presenta ambos bloques exactamente, no combines sus números entre sí:", ""]
    lineas += _bloque(d1)
    lineas.append("")
    lineas += _bloque(d2)
    lineas.append("")
    lineas.append(
        "Nota: esto NO es head-to-head entre ambos equipos — para saber cómo les ha ido "
        "JUGANDO ENTRE SÍ, usa enfrentamientos_entre_equipos o historial_entre_equipos."
    )
    return "\n".join(lineas)


def comparar_jugadores(nombre1: str, nombre2: str) -> str:
    """Compara dos jugadores lado a lado: goles por equipo, tarjetas y premios."""

    def _datos(nombre):
        goles = q(
            """
            MATCH (p:Player)-[r:SCORED_IN]->(:Edition)
            WHERE toLower(p.name) CONTAINS toLower($nombre)
            MATCH (t:Team {id: r.teamId})
            RETURN p.name AS jugador, t.name AS equipo, sum(r.goals) AS goles
            """,
            {"nombre": nombre},
        )
        tarjetas = q(
            """
            MATCH (p:Player)-[r:CARDED_IN]->(:Match)
            WHERE toLower(p.name) CONTAINS toLower($nombre)
            RETURN sum(r.yellowCards) AS amarillas, sum(r.redCards) AS rojas
            """,
            {"nombre": nombre},
        )
        premios = q(
            "MATCH (p:Player)-[:WON]->(a:Award) WHERE toLower(p.name) CONTAINS toLower($nombre) RETURN count(a) AS total",
            {"nombre": nombre},
        )
        return goles, tarjetas, premios

    g1, t1, pr1 = _datos(nombre1)
    g2, t2, pr2 = _datos(nombre2)
    if not g1 and not t1 and not (pr1 and pr1[0]["total"]):
        return f"No se encontró a '{nombre1}' en el grafo histórico."
    if not g2 and not t2 and not (pr2 and pr2[0]["total"]):
        return f"No se encontró a '{nombre2}' en el grafo histórico."

    def _bloque(nombre, goles, tarjetas, premios):
        real = goles[0]["jugador"] if goles else nombre.title()
        equipos = ", ".join(f"{g['equipo']} ({g['goles']})" for g in goles) if goles else "sin registros"
        am = tarjetas[0]["amarillas"] or 0 if tarjetas and tarjetas[0]["amarillas"] else 0
        ro = tarjetas[0]["rojas"] or 0 if tarjetas and tarjetas[0]["rojas"] else 0
        pr = premios[0]["total"] if premios else 0
        return [
            f"{real}:",
            f"  Goles por equipo: {equipos}",
            f"  Tarjetas: {am} amarillas, {ro} rojas",
            f"  Premios ganados: {pr}",
        ]

    lineas = ["COMPARACIÓN — presenta ambos bloques exactamente, no combines sus números entre sí:", ""]
    lineas += _bloque(nombre1, g1, t1, pr1)
    lineas.append("")
    lineas += _bloque(nombre2, g2, t2, pr2)
    return "\n".join(lineas)


def partidos_por_fecha(numero_fecha, edicion: str = None) -> str:
    """Lista los partidos jugados en una fecha/jornada específica, opcionalmente filtrado por edición."""
    try:
        numero_fecha = int(numero_fecha)
    except (TypeError, ValueError):
        return f"'{numero_fecha}' no es un número de fecha válido."

    filtro_edicion = "AND toLower(e.name) CONTAINS toLower($edicion)" if edicion else ""
    filas = q(
        f"""
        MATCH (m:Match {{fecha: $numero_fecha}})-[:IN_EDITION]->(e:Edition)
        WHERE true {filtro_edicion}
        MATCH (t1:Team)-[r1:PLAYED_MATCH]->(m)<-[r2:PLAYED_MATCH]-(t2:Team)
        WHERE elementId(t1) < elementId(t2)
        RETURN e.name AS edicion, m.partido AS partido,
               t1.name AS equipo1, r1.goals AS goles1,
               t2.name AS equipo2, r2.goals AS goles2
        ORDER BY e.year, m.partido
        """,
        {"numero_fecha": numero_fecha, "edicion": edicion},
    )
    if not filas:
        objetivo = f"la fecha {numero_fecha}" + (f" de {edicion}" if edicion else "")
        return f"No se encontraron partidos en {objetivo}."
    lineas = [f"Partidos de la fecha {numero_fecha}:", ""]
    for f in filas:
        lineas.append(f"  - {f['edicion']}, Partido {f['partido']}: {f['equipo1']} {f['goles1']} - {f['goles2']} {f['equipo2']}")
    return "\n".join(lineas)


def racha_historica(equipo: str = None) -> str:
    """
    Racha ganadora, perdedora Y DE EMPATES más larga, calculado partido a
    partido en orden cronológico. La racha se reinicia al cambiar de edición
    (no se combina el cierre de un torneo con el arranque del siguiente).
    Incluye el DETALLE de qué partidos componen cada racha máxima (edición,
    fecha, rival) — no solo el número.

    - equipo dado: rachas de ESE equipo específico, con sus partidos.
    - sin equipo (None): recorre TODOS los equipos y devuelve quién tiene la
      racha ganadora más larga, la perdedora más larga y la de empates más
      larga de TODA la historia, con los partidos de esa racha — para
      preguntas abiertas tipo '¿qué equipo tiene la mayor racha de partidos
      ganados?' sin nombre de equipo.
    """
    filtro = "WHERE toLower(t.name) CONTAINS toLower($equipo)" if equipo else ""
    filas = q(
        f"""
        MATCH (t:Team)-[r:PLAYED_MATCH]->(m:Match)-[:IN_EDITION]->(e:Edition)
        {filtro}
        MATCH (rival:Team)-[:PLAYED_MATCH]->(m) WHERE rival <> t
        RETURN t.name AS equipo, e.name AS edicion, e.year AS anio, m.fecha AS fecha,
               m.partido AS partido, r.result AS resultado, rival.name AS rival
        ORDER BY t.name, e.year, m.fecha
        """,
        {"equipo": equipo},
    )
    if not filas:
        if equipo:
            return f"No se encontró al equipo '{equipo}' en el grafo histórico."
        return "No hay datos suficientes en el grafo para calcular rachas."

    def _fmt_partidos(lista):
        return [f"{p['edicion']}, fecha {p['fecha']}, partido {p['partido']} vs {p['rival']}" for p in lista]

    rachas: dict[str, dict] = {}
    equipo_actual = edicion_anterior = None
    racha_v = racha_p = racha_e = 0
    partidos_v = partidos_p = partidos_e = []
    for f in filas:
        if f["equipo"] != equipo_actual:
            equipo_actual = f["equipo"]
            edicion_anterior = None
            racha_v = racha_p = racha_e = 0
            partidos_v, partidos_p, partidos_e = [], [], []
            rachas[equipo_actual] = {
                "mejor_v": 0, "mejor_p": 0, "mejor_e": 0,
                "partidos_v": [], "partidos_p": [], "partidos_e": [],
            }
        if f["edicion"] != edicion_anterior:
            racha_v = racha_p = racha_e = 0
            partidos_v, partidos_p, partidos_e = [], [], []
            edicion_anterior = f["edicion"]

        detalle = {"edicion": f["edicion"], "fecha": f["fecha"], "partido": f["partido"], "rival": f["rival"]}
        if f["resultado"] == "G":
            racha_v += 1
            racha_p = racha_e = 0
            partidos_v = partidos_v + [detalle]
            partidos_p, partidos_e = [], []
        elif f["resultado"] == "P":
            racha_p += 1
            racha_v = racha_e = 0
            partidos_p = partidos_p + [detalle]
            partidos_v, partidos_e = [], []
        else:
            racha_e += 1
            racha_v = racha_p = 0
            partidos_e = partidos_e + [detalle]
            partidos_v, partidos_p = [], []

        d = rachas[equipo_actual]
        if racha_v > d["mejor_v"]:
            d["mejor_v"], d["partidos_v"] = racha_v, list(partidos_v)
        if racha_p > d["mejor_p"]:
            d["mejor_p"], d["partidos_p"] = racha_p, list(partidos_p)
        if racha_e > d["mejor_e"]:
            d["mejor_e"], d["partidos_e"] = racha_e, list(partidos_e)

    def _bloque_racha(titulo, cantidad, lista_partidos):
        out = [f"{titulo}: {cantidad} partidos consecutivos"]
        if lista_partidos:
            out.append("  Partidos de esa racha:")
            for linea in _fmt_partidos(lista_partidos):
                out.append(f"    - {linea}")
        return out

    if equipo:
        nombre_real = filas[0]["equipo"]
        d = rachas[nombre_real]
        lineas = [f"Rachas históricas de {nombre_real} (2024-2025, calculado partido a partido):", ""]
        lineas += _bloque_racha("Racha ganadora más larga", d["mejor_v"], d["partidos_v"])
        lineas.append("")
        lineas += _bloque_racha("Racha perdedora más larga", d["mejor_p"], d["partidos_p"])
        lineas.append("")
        lineas += _bloque_racha("Racha de empates más larga", d["mejor_e"], d["partidos_e"])
        lineas.append("")
        lineas.append("Nota: la racha se reinicia entre ediciones distintas.")
        return "\n".join(lineas)

    mejor_ganadora = max(rachas.items(), key=lambda x: x[1]["mejor_v"])
    mejor_perdedora = max(rachas.items(), key=lambda x: x[1]["mejor_p"])
    mejor_empatadora = max(rachas.items(), key=lambda x: x[1]["mejor_e"])

    lineas = ["Rachas históricas más largas de toda la CLC (2024-2025, calculado partido a partido):", ""]
    lineas += _bloque_racha(f"Racha ganadora más larga: {mejor_ganadora[0]}", mejor_ganadora[1]["mejor_v"], mejor_ganadora[1]["partidos_v"])
    lineas.append("")
    lineas += _bloque_racha(f"Racha perdedora más larga: {mejor_perdedora[0]}", mejor_perdedora[1]["mejor_p"], mejor_perdedora[1]["partidos_p"])
    lineas.append("")
    lineas += _bloque_racha(f"Racha de empates más larga: {mejor_empatadora[0]}", mejor_empatadora[1]["mejor_e"], mejor_empatadora[1]["partidos_e"])
    lineas.append("")
    lineas.append("Nota: la racha se reinicia entre ediciones distintas.")
    return "\n".join(lineas)


def equipo_mas_dominante() -> str:
    """
    Ranking histórico agregado de 'dominancia': suma del orden de la fase
    máxima alcanzada en cada edición, con bonus si ganó esa fase. Es una
    métrica compuesta explícita para responder '¿quién ha sido el mejor
    equipo de la historia?' — NO es un título oficial del torneo.
    """
    filas = q(
        """
        MATCH (t:Team)-[r:REACHED_STAGE]->(s:Stage)
        MATCH (e:Edition {id: r.editionId})
        OPTIONAL MATCH (t)-[:PLAYED_MATCH]->(m:Match)-[:AT_STAGE]->(s)
        WHERE EXISTS { (m)-[:IN_EDITION]->(e) }
        RETURN t.name AS equipo, t.id AS id, s.order AS orden_fase, m.winnerTeamId AS winner_id
        """
    )
    if not filas:
        return "No hay datos suficientes en el grafo para calcular esto."

    puntajes: dict[str, int] = {}
    for f in filas:
        puntaje = (f["orden_fase"] or 0) + (2 if f.get("winner_id") == f["id"] else 0)
        puntajes[f["equipo"]] = puntajes.get(f["equipo"], 0) + puntaje

    ranking = sorted(puntajes.items(), key=lambda x: x[1], reverse=True)[:10]
    lineas = [
        "Ranking histórico de 'dominancia' (métrica compuesta, NO es un título oficial del torneo):",
        "Puntaje = suma del orden de fase alcanzada por edición, +2 extra si ganó esa fase.",
        "",
    ]
    for equipo, puntaje in ranking:
        lineas.append(f"  {equipo}: {puntaje} puntos")
    return "\n".join(lineas)


def historial_entre_equipos(equipo1: str, equipo2: str) -> str:
    """
    Head-to-head: todos los partidos jugados entre dos equipos.

    IMPORTANTE (fix del bug de la 'final inventada' de Barcelona-Milan):
    dos equipos pueden jugar MÁS DE UN partido en la misma edición (ej. fase
    de grupos Y la final). Antes esta función no distinguía la fase, y el
    Narrador terminó fusionando el resultado de un partido de grupos con el
    de la final en un marcador que no existe. Ahora cada fila trae su Fase
    explícita — cada partido debe presentarse por separado, nunca combinado
    con otro en un solo marcador.
    """
    filas = q(
        """
        MATCH (t1:Team)-[r1:PLAYED_MATCH]->(m:Match)<-[r2:PLAYED_MATCH]-(t2:Team)
        WHERE toLower(t1.name) CONTAINS toLower($equipo1)
          AND toLower(t2.name) CONTAINS toLower($equipo2)
          AND t1 <> t2
        MATCH (m)-[:IN_EDITION]->(e:Edition)
        MATCH (m)-[:AT_STAGE]->(s:Stage)
        RETURN e.name AS edicion, s.name AS fase, m.partido AS partido,
               t1.name AS equipo1, r1.goals AS goles1,
               t2.name AS equipo2, r2.goals AS goles2,
               m.resolutionMethod AS resolucion
        ORDER BY e.year, s.name
        """,
        {"equipo1": equipo1, "equipo2": equipo2},
    )
    if not filas:
        return f"No se encontraron partidos entre '{equipo1}' y '{equipo2}'."

    lineas = [
        f"Historial {equipo1} vs {equipo2} — CADA FILA ES UN PARTIDO DISTINTO, "
        "no combines marcadores de filas distintas:",
        "",
    ]
    for f in filas:
        resolucion = f" (definido por {f['resolucion']})" if f.get("resolucion") and f["resolucion"] != "REGULAR_TIME" else ""
        lineas.append(
            f"  - {f['edicion']}, {f['fase']}: {f['equipo1']} {f['goles1']} - "
            f"{f['goles2']} {f['equipo2']}{resolucion}"
        )
    lineas.append("")
    lineas.append("REGLA: Cada partido de arriba es independiente. NUNCA inventes un marcador "
                   "combinando goles de dos filas distintas, aunque sean la misma edición.")
    return "\n".join(lineas)
