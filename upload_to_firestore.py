import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import os

# ── Firebase initialization ────────────────────────────────────────────────────
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(os.path.join(BASE_DIR, "firebase_key.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()

BASE_URL = "https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/Data/"

FILES = [
    ("Goleadores_apertura_2024_CLC.csv",  "goleadores_apertura_2024",  "NOMBRE Y APELLIDO"),
    ("Goleadores_apertura_2025_CLC.csv",  "goleadores_apertura_2025",  "NOMBRE Y APELLIDO"),
    ("Goleadores_clausura_2024_CLC.csv",  "goleadores_clausura_2024",  "NOMBRE Y APELLIDO"),
    ("Goleadores_clausura_2025_CLC.csv",  "goleadores_clausura_2025",  "NOMBRE Y APELLIDO"),
    ("Tarjetas_apertura_2025_CLC.csv",    "tarjetas_apertura_2025",    "JUGADOR"),
    ("Tarjetas_clausura_2025_CLC.csv",    "tarjetas_clausura_2025",    "JUGADOR"),
    ("Partidos_apertura_2024_CLC_1.csv",  "partidos_apertura_2024",    None),
    ("Partidos_apertura_2025_CLC_1.csv",  "partidos_apertura_2025",    None),
    ("Partidos_clausura_2024_CLC_1.csv",  "partidos_clausura_2024",    None),
    ("Partidos_clausura_2025_CLC_1.csv",  "partidos_clausura_2025",    None),
]


def delete_collection(collection_name: str):
    """Borra todos los documentos de una colección antes de re-subir."""
    docs = db.collection(collection_name).stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    if count > 0:
        print(f"  🗑️  Borrados {count} documentos anteriores de '{collection_name}'")


def sync_collection(filename: str, collection_name: str, id_col: str = None):
    url = BASE_URL + filename
    print(f"📥 Leyendo: {filename}")

    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"  ❌ Error leyendo archivo: {e}")
        return

    # Limpiar columnas
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.dropna(how="all")

    # ── Deduplicar antes de subir ──────────────────────────────────────────────
    if id_col and id_col in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=[id_col])
        after = len(df)
        if before != after:
            print(f"  ⚠️  Eliminados {before - after} duplicados en '{id_col}'")

    # Borrar colección existente para evitar residuos
    delete_collection(collection_name)

    # Subir documentos limpios
    collection_ref = db.collection(collection_name)
    count = 0

    for i, row in df.iterrows():
        doc_data = row.dropna().to_dict()

        if id_col and id_col in doc_data:
            doc_id = str(doc_data[id_col]).strip().replace(" ", "_")
        else:
            doc_id = str(i)

        collection_ref.document(doc_id).set(doc_data)
        count += 1

    print(f"  ✅ '{collection_name}': {count} documentos sincronizados\n")


# ── Run ────────────────────────────────────────────────────────────────────────
print("🚀 Iniciando sincronización GitHub → Firestore...\n")

for filename, collection_name, id_col in FILES:
    sync_collection(filename, collection_name, id_col)

print("🎉 ¡Sincronización completa! Revisa tu Firestore en Firebase Console.")
