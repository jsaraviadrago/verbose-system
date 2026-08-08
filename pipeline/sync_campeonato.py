from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pipeline.pipeline_goleadores import run_goleadores_pipeline
from pipeline.pipeline_service import run_pipeline as run_resultados_pipeline


def write_summary(resultados: dict, goleadores: dict) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        return

    lines = [
        "# Actualizar campeonato",
        "",
        "## Resultados",
        f"- Estado: `{resultados.get('status')}`",
        f"- Fechas completas: {resultados.get('ready_dates', [])}",
        f"- Fechas parciales: {resultados.get('partial_dates', [])}",
        f"- Escrituras Firestore: {resultados.get('writes', 0)}",
        "",
        "## Goleadores",
        f"- Estado: `{goleadores.get('status')}`",
        f"- Equipos/fechas válidos: {goleadores.get('valid_team_entries', 0)}",
        f"- Jugadores acumulados: {goleadores.get('players', 0)}",
        f"- Escrituras Firestore: {goleadores.get('writes', 0)}",
        f"- Borrados Firestore: {goleadores.get('deletes', 0)}",
        f"- Pendientes: {len(goleadores.get('pending', []))}",
        f"- Inválidos: {len(goleadores.get('invalid', []))}",
        "",
    ]

    pending = goleadores.get("pending", [])
    if pending:
        lines.extend(["### Pendientes", ""])
        for item in pending:
            lines.append(
                f"- Fecha {item.get('fecha')} · {item.get('equipo')}: "
                f"{item.get('motivo')}"
            )
        lines.append("")

    invalid = goleadores.get("invalid", [])
    if invalid:
        lines.extend(["### Inválidos", ""])
        for item in invalid:
            lines.append(
                f"- Fecha {item.get('fecha')} · {item.get('equipo')}: "
                f"{item.get('motivo')}"
            )
        lines.append("")

    with Path(path).open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    print("=== RESULTADOS ===")
    resultados = run_resultados_pipeline()
    print(json.dumps(resultados, ensure_ascii=False, indent=2))

    if resultados.get("status") != "ok":
        print(
            "La sincronización de resultados no terminó correctamente. "
            "No se ejecutarán goleadores.",
            file=sys.stderr,
        )
        write_summary(resultados, {})
        return 1

    print("\n=== GOLEADORES ===")
    goleadores = run_goleadores_pipeline()
    print(json.dumps(goleadores, ensure_ascii=False, indent=2))

    write_summary(resultados, goleadores)

    if goleadores.get("status") not in {
        "ok",
        "waiting_results",
        "no_valid_scorers",
    }:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
