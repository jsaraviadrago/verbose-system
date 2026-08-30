from __future__ import annotations

"""
player_identity.py
==================

Capa privada de identidad de jugadores para Cambridge League.

Objetivos
---------
1. Cargar UNA VEZ el padron 2025 desde Excel a Firestore.
2. Generar un PLAYER_ID estable mediante HMAC-SHA256.
3. Mantener DOCUMENTO_ID exclusivamente en una coleccion privada.
4. Exponer al agente unicamente datos deportivos/identidad no sensibles.
5. Evitar sobrescribir el padron 2025 usando Firestore create().

Uso inicial
-----------
export GOOGLE_CLOUD_PROJECT="futbol-ccl"
export PLAYER_ID_SECRET="un-secreto-largo-y-privado"

python player_identity.py upload --excel "ruta/al/padron_2025.xlsx"

Despues de la carga inicial, el agente NO necesita leer el Excel.
Puede importar, por ejemplo:

    from player_identity import resolve_player_for_agent

    result = resolve_player_for_agent("Anibal Pacheco")

IMPORTANTE
----------
- Nunca publiques PLAYER_ID_SECRET en GitHub.
- Nunca devuelvas DOCUMENTO_ID al modelo/LLM.
- La coleccion privada NO debe ser consumida directamente por Streamlit.
"""

import argparse
import hashlib
import hmac
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


DEFAULT_PROJECT_ID = "futbol-ccl"
PRIVATE_COLLECTION = "jugadores_privado_2025"
META_COLLECTION = "padrones_metadata"
META_DOCUMENT = "padron_2025"
PADRON_SHEET = "Padron_2025"

REQUIRED_COLUMNS = {
    "AÑO",
    "CATEGORIA",
    "EQUIPO",
    "JUGADOR",
    "DOCUMENTO_ID",
}

FORBIDDEN_AGENT_FIELDS = {
    "DNI",
    "DOCUMENTO",
    "DOCUMENTO_ID",
    "DOCUMENTO_ID_INTERNO",
    "PRIVATE_KEY",
}


def get_project_id() -> str:
    return os.getenv("GOOGLE_CLOUD_PROJECT", DEFAULT_PROJECT_ID).strip()


def get_player_secret() -> str:
    secret = os.getenv("PLAYER_ID_SECRET", "").strip()
    if not secret:
        raise RuntimeError(
            "Falta PLAYER_ID_SECRET. Define un secreto privado antes de generar PLAYER_ID."
        )
    if len(secret) < 32:
        raise RuntimeError(
            "PLAYER_ID_SECRET es demasiado corto. Usa al menos 32 caracteres aleatorios."
        )
    return secret


def get_db() -> firestore.Client:
    return firestore.Client(project=get_project_id())


def normalize_document(value: Any) -> str:
    """Normaliza el documento a 8 caracteres con ceros a la izquierda."""
    if pd.isna(value):
        raise ValueError("Documento vacio en el padron.")

    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]

    digits = re.sub(r"\D", "", text)
    if not digits:
        raise ValueError(f"Documento invalido: {value!r}")
    if len(digits) > 8:
        raise ValueError(f"Documento con mas de 8 digitos: {value!r}")

    return digits.zfill(8)


def remove_accents_keep_enye(value: Any) -> str:
    """Quita tildes, pero conserva Ñ/ñ como caracter distinto."""
    text = str(value).strip()
    text = text.replace("Ñ", "__ENYE_UPPER__")
    text = text.replace("ñ", "__ENYE_LOWER__")
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        char for char in text if unicodedata.category(char) != "Mn"
    )
    text = text.replace("__ENYE_UPPER__", "Ñ")
    text = text.replace("__ENYE_LOWER__", "ñ")
    return text


def normalize_name(value: Any) -> str:
    text = remove_accents_keep_enye(value)
    text = text.upper()
    return re.sub(r"\s+", " ", text).strip()


def clean_display_name(value: Any) -> str:
    text = remove_accents_keep_enye(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text.title()


def make_player_id(document_id: str) -> str:
    """Genera un PLAYER_ID estable usando HMAC-SHA256."""
    secret = get_player_secret()
    digest = hmac.new(
        secret.encode("utf-8"),
        document_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"pl_{digest[:20]}"


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def participation_document_id(
    player_id: str,
    year: int,
    team: str,
    category: str,
) -> str:
    raw = (
        f"{player_id}|{year}|{normalize_name(team)}|{normalize_name(category)}"
    ).encode("utf-8")
    return "p_" + hashlib.sha256(raw).hexdigest()[:30]


def read_padron_excel(excel_path: str | Path) -> pd.DataFrame:
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el Excel del padron: {path}")

    df = pd.read_excel(
        path,
        sheet_name=PADRON_SHEET,
        dtype={"DOCUMENTO_ID": str},
    )

    df.columns = df.columns.astype(str).str.strip().str.upper()
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(
            "El padron no contiene las columnas requeridas: "
            f"{sorted(missing)}"
        )

    df = df[
        ["AÑO", "CATEGORIA", "EQUIPO", "JUGADOR", "DOCUMENTO_ID"]
    ].copy()
    df = df.dropna(how="all")

    df["AÑO"] = pd.to_numeric(df["AÑO"], errors="raise").astype(int)
    if not df["AÑO"].eq(2025).all():
        bad_years = sorted(df.loc[~df["AÑO"].eq(2025), "AÑO"].unique())
        raise ValueError(
            "Este uploader es exclusivamente para el snapshot 2025. "
            f"Se encontraron otros años: {bad_years}"
        )

    df["DOCUMENTO_ID"] = df["DOCUMENTO_ID"].map(normalize_document)
    df["JUGADOR"] = df["JUGADOR"].map(clean_display_name)
    df["NOMBRE_NORMALIZADO"] = df["JUGADOR"].map(normalize_name)
    df["EQUIPO"] = df["EQUIPO"].astype(str).str.strip()
    df["CATEGORIA"] = df["CATEGORIA"].astype(str).str.strip()

    # Correccion confirmada durante la auditoria del padron.
    typo_mask = (
        df["DOCUMENTO_ID"].eq("07866497")
        & df["NOMBRE_NORMALIZADO"].eq("ALBERTO PACHECO")
    )
    if typo_mask.any():
        df.loc[typo_mask, "JUGADOR"] = "Anibal Pacheco"
        df.loc[typo_mask, "NOMBRE_NORMALIZADO"] = "ANIBAL PACHECO"

    df["PLAYER_ID"] = df["DOCUMENTO_ID"].map(make_player_id)
    return df


def upload_padron_2025(
    excel_path: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Carga el padron 2025 como snapshot write-once.

    - Usa create(), nunca set/update.
    - Si metadata ya existe, aborta.
    - Si un documento individual ya existe, aborta.
    """
    path = Path(excel_path)
    df = read_padron_excel(path)
    file_hash = file_sha256(path)

    result = {
        "status": "dry_run" if dry_run else "ok",
        "project": get_project_id(),
        "collection": PRIVATE_COLLECTION,
        "records": int(len(df)),
        "players_unique": int(df["PLAYER_ID"].nunique()),
        "file_sha256": file_hash,
    }

    if dry_run:
        return result

    db = get_db()
    meta_ref = db.collection(META_COLLECTION).document(META_DOCUMENT)

    if meta_ref.get().exists:
        raise RuntimeError(
            "El snapshot padron_2025 ya existe en Firestore. No se sobrescribira."
        )

    collection = db.collection(PRIVATE_COLLECTION)
    rows_to_create: list[tuple[str, dict[str, Any]]] = []

    for row in df.to_dict(orient="records"):
        doc_id = participation_document_id(
            player_id=row["PLAYER_ID"],
            year=int(row["AÑO"]),
            team=row["EQUIPO"],
            category=row["CATEGORIA"],
        )

        payload = {
            "PLAYER_ID": row["PLAYER_ID"],
            # PRIVADO. Nunca devolver al agente.
            "DOCUMENTO_ID": row["DOCUMENTO_ID"],
            "NOMBRE_OFICIAL": row["JUGADOR"],
            "NOMBRE_NORMALIZADO": row["NOMBRE_NORMALIZADO"],
            "AÑO": int(row["AÑO"]),
            "EQUIPO": row["EQUIPO"],
            "CATEGORIA": row["CATEGORIA"],
            "FUENTE": "padron_2025",
        }

        ref = collection.document(doc_id)
        if ref.get().exists:
            raise RuntimeError(
                f"El documento {doc_id} ya existe. "
                "La carga se cancela para preservar inmutabilidad."
            )

        rows_to_create.append((doc_id, payload))

    created = 0
    try:
        for doc_id, payload in rows_to_create:
            collection.document(doc_id).create(payload)
            created += 1

        meta_ref.create(
            {
                "AÑO": 2025,
                "SHA256": file_hash,
                "REGISTROS": int(len(df)),
                "JUGADORES_UNICOS": int(df["PLAYER_ID"].nunique()),
                "COLECCION": PRIVATE_COLLECTION,
                "ESTADO": "INMUTABLE",
                "FUENTE_ARCHIVO": path.name,
            }
        )

    except AlreadyExists as exc:
        raise RuntimeError(
            "Firestore detecto un documento ya existente. "
            "No se sobrescribio ese documento."
        ) from exc

    result["created"] = created
    return result


def sanitize_for_agent(value: Any) -> Any:
    """Elimina campos sensibles antes de entregar resultados al agente."""
    if isinstance(value, dict):
        return {
            key: sanitize_for_agent(val)
            for key, val in value.items()
            if key.upper() not in FORBIDDEN_AGENT_FIELDS
        }
    if isinstance(value, list):
        return [sanitize_for_agent(item) for item in value]
    return value


def resolve_player_for_agent(player_name: str) -> list[dict[str, Any]]:
    """
    Busca por nombre normalizado y devuelve SOLO datos permitidos.

    Puede devolver mas de una persona si existen homonimos.
    En ese caso el agente debe desambiguar y nunca adivinar.
    """
    normalized = normalize_name(player_name)
    db = get_db()

    docs = (
        db.collection(PRIVATE_COLLECTION)
        .where(
            filter=FieldFilter(
                "NOMBRE_NORMALIZADO",
                "==",
                normalized,
            )
        )
        .stream()
    )

    players: dict[str, dict[str, Any]] = {}

    for snap in docs:
        data = snap.to_dict()
        player_id = data["PLAYER_ID"]

        if player_id not in players:
            players[player_id] = {
                "PLAYER_ID": player_id,
                "NOMBRE": data["NOMBRE_OFICIAL"],
                "PARTICIPACIONES": [],
            }

        participation = {
            "AÑO": data["AÑO"],
            "EQUIPO": data["EQUIPO"],
            "CATEGORIA": data["CATEGORIA"],
        }

        if participation not in players[player_id]["PARTICIPACIONES"]:
            players[player_id]["PARTICIPACIONES"].append(participation)

    result = list(players.values())

    for player in result:
        player["PARTICIPACIONES"] = sorted(
            player["PARTICIPACIONES"],
            key=lambda item: (
                item["AÑO"],
                item["EQUIPO"],
                item["CATEGORIA"],
            ),
        )

    return sanitize_for_agent(result)


def get_player_public_profile(player_id: str) -> dict[str, Any] | None:
    """Perfil seguro para el agente; nunca incluye DOCUMENTO_ID."""
    db = get_db()

    docs = (
        db.collection(PRIVATE_COLLECTION)
        .where(
            filter=FieldFilter(
                "PLAYER_ID",
                "==",
                player_id,
            )
        )
        .stream()
    )

    profile: dict[str, Any] | None = None

    for snap in docs:
        data = snap.to_dict()

        if profile is None:
            profile = {
                "PLAYER_ID": data["PLAYER_ID"],
                "NOMBRE": data["NOMBRE_OFICIAL"],
                "PARTICIPACIONES": [],
            }

        participation = {
            "AÑO": data["AÑO"],
            "EQUIPO": data["EQUIPO"],
            "CATEGORIA": data["CATEGORIA"],
        }

        if participation not in profile["PARTICIPACIONES"]:
            profile["PARTICIPACIONES"].append(participation)

    if profile is None:
        return None

    profile["PARTICIPACIONES"] = sorted(
        profile["PARTICIPACIONES"],
        key=lambda item: (
            item["AÑO"],
            item["EQUIPO"],
            item["CATEGORIA"],
        ),
    )

    return sanitize_for_agent(profile)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Carga privada del padron 2025 y resolucion segura "
            "de identidad de jugadores."
        )
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    upload = subparsers.add_parser(
        "upload",
        help="Carga una sola vez el padron 2025 a Firestore.",
    )
    upload.add_argument(
        "--excel",
        required=True,
        help="Ruta al Excel que contiene la pestana Padron_2025.",
    )
    upload.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida el archivo sin escribir en Firestore.",
    )

    resolve = subparsers.add_parser(
        "resolve",
        help="Prueba una busqueda segura por nombre.",
    )
    resolve.add_argument(
        "--name",
        required=True,
        help="Nombre del jugador.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "upload":
        result = upload_padron_2025(
            excel_path=args.excel,
            dry_run=args.dry_run,
        )
    elif args.command == "resolve":
        result = resolve_player_for_agent(args.name)
    else:
        parser.error("Comando no soportado.")
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
