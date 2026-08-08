from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pipeline.pipeline_goleadores import run_goleadores_pipeline
from pipeline.pipeline_service import run_pipeline as run_resultados_pipeline
from pipeline.pipeline_tarjetas import run_tarjetas_pipeline


def write_summary(
    resultados: dict,
    goleadores: dict,
    tarjetas: dict,
) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        return

    lines = [
        "# Actualizar campeonato",
        "",
        "## ✅ Resultados",
        f"- Estado: `{resultados.get('status')}`",
        f"- Fechas completas: {resultados.get('ready_dates', [])}",
        f"- Fechas parciales: {resultados.get('partial_dates', [])}",
        f"- Escrituras Firestore: {resultados.get('writes', 0)}",
        "",
        "## ⚽ Goleadores",
        f"- Estado: `{goleadores.get('status')}`",
        f"- Equipos/fechas válidos: {goleadores.get('valid_team_entries', 0)}",
        f"- Jugadores acumulados: {goleadores.get('players', 0)}",
        f"- Escrituras Firestore: {goleadores.get('writes', 0)}",
        f"- Borrados Firestore: {goleadores.get('deletes', 0)}",
        f"- Pendientes: {len(goleadores.get('pending', []))}",
        f"- Inválidos: {len(goleadores.get('invalid', []))}",
        "",
        "## 🟨🟥 Tarjetas",
        f"- Estado: `{tarjetas.get('status')}`",
        f"- Registros válidos: {tarjetas.get('records', 0)}",
        f"- Jugadores acumulados: {tarjetas.get('players', 0)}",
        f"- Escrituras Firestore: {tarjetas.get('writes', 0)}",
        f"- Borrados Firestore: {tarjetas.get('deletes', 0)}",
        f"- Pendientes: {len(tarjetas.get('pending', []))}",
        f"- Inválidos: {len(tarjetas.get('invalid', []))}",
        "",
    ]

    for title, payload in (
        ("Goleadores pendientes", goleadores.get("pending", [])),
        ("Tarjetas pendientes", tarjetas.get("pending", [])),
        ("Tarjetas inválidas", tarjetas.get("invalid", [])),
    ):
        if payload:
            lines.extend([f"### {title}", ""])
            for item in payload:
                detail = (
                    f"Fecha {item.get('fecha')} · {item.get('equipo')}"
                )
                if item.get("jugador"):
                    detail += f" · {item.get('jugador')}"
                detail += f": {item.get('motivo')}"
                lines.append(f"- {detail}")
            lines.append("")

    with Path(path).open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    print("=== RESULTADOS ===")
    resultados = run_resultados_pipeline()
    print(json.dumps(resultados, ensure_ascii=False, indent=2))

    if resultados.get("status") != "ok":
        print(
            "Resultados no terminó correctamente. "
            "No se ejecutarán goleadores ni tarjetas.",
            file=sys.stderr,
        )
        write_summary(resultados, {}, {})
        return 1

    print("\n=== GOLEADORES ===")
    goleadores = run_goleadores_pipeline()
    print(json.dumps(goleadores, ensure_ascii=False, indent=2))

    if goleadores.get("status") not in {
        "ok",
        "waiting_results",
        "no_valid_scorers",
    }:
        write_summary(resultados, goleadores, {})
        return 1

    print("\n=== TARJETAS ===")
    tarjetas = run_tarjetas_pipeline()
    print(json.dumps(tarjetas, ensure_ascii=False, indent=2))

    write_summary(resultados, goleadores, tarjetas)

    if tarjetas.get("status") not in {
        "ok",
        "waiting_results",
        "no_cards",
        "no_valid_cards",
    }:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
