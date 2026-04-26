import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# ── Firebase initialization ────────────────────────────────────────────────────
cred = credentials.Certificate("firebase_key.json")  # ← Keep this file locally, never upload to GitHub
firebase_admin.initialize_app(cred)
db = firestore.client()

# ── GitHub raw base URL ────────────────────────────────────────────────────────
BASE_URL = "https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/Data/"

# ── CSV files → Firestore collection mapping ───────────────────────────────────
# Format: (csv_filename, collection_name, id_column or None)
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

# ── Upload helper ──────────────────────────────────────────────────────────────
def sync_collection(filename: str, collection_name: str, id_col: str = None):
    """
    Reads a CSV from GitHub and syncs it to Firestore.
    - Overwrites existing documents (so edits in GitHub reflect in Firestore)
    - Drops fully empty rows and unnamed columns
    """
    url = BASE_URL + filename
    print(f"📥 Reading: {url}")

    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        return

    # Clean column names (strip spaces)
    df.columns = df.columns.str.strip()

    # Drop unnamed/empty columns (e.g. Unnamed: 9, Unnamed: 10)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Drop fully empty rows
    df = df.dropna(how="all")

    collection_ref = db.collection(collection_name)
    count = 0

    for i, row in df.iterrows():
        doc_data = row.dropna().to_dict()

        if id_col and id_col in doc_data:
            # Use the ID column as document ID so updates overwrite correctly
            doc_id = str(doc_data[id_col]).strip().replace(" ", "_")
        else:
            # For Partidos: use row index as stable ID
            doc_id = str(i)

        collection_ref.document(doc_id).set(doc_data)  # .set() overwrites on re-run
        count += 1

    print(f"  ✅ '{collection_name}': {count} documentos sincronizados\n")


# ── Run sync for all files ─────────────────────────────────────────────────────
print("🚀 Iniciando sincronización GitHub → Firestore...\n")

for filename, collection_name, id_col in FILES:
    sync_collection(filename, collection_name, id_col)

print("🎉 ¡Sincronización completa! Revisa tu Firestore en Firebase Console.")