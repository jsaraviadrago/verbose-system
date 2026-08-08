from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pipeline.pipeline_service import run_pipeline


def write_summary(result: dict) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines = [
        "## Actualización de resultados",
        "",
        f"- **Estado:** `{result.get('status', 'unknown')}`",
        f"- **Fechas completas detectadas:** {result.get('ready_dates', [])}",
        f"- **Fechas parciales:** {result.get('partial_dates', [])}",
        f"- **Escrituras en Firestore:** {result.get('writes', 0)}",
        f"- **Lecturas en Firestore:** {result.get('firestore_reads', 0)}",
        "",
    ]

    with Path(summary_path).open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    result = run_pipeline()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_summary(result)

    if result.get("status") != "ok":
        print(f"Estado inesperado: {result.get('status')}", file=sys.stderr)
        return 1

    ready = result.get("ready_dates", [])
    partial = result.get("partial_dates", [])
    writes = result.get("writes", 0)

    if not ready:
        print("No hay fechas completas para sincronizar.")
        return 0

    print(
        f"Sincronización completada. Fechas completas: {ready}. "
        f"Fechas parciales: {partial}. Documentos modificados: {writes}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
