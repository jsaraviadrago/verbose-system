import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import os

# ── Firebase initialization ────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = credentials.Certificate(os.path.join(BASE_DIR, "firebase_key.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()

# ── GitHub raw base URL ────────────────────────────────────────────────────────
BASE_URL = "https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/Data/"

# ── Files to apply data quality ───────────────────────────────────────────────
# Format: (csv_filename, collection_name, name_column)
FILES = [
    ("Goleadores_apertura_2024_CLC.csv", "goleadores_apertura_2024", "NOMBRE Y APELLIDO"),
    ("Goleadores_apertura_2025_CLC.csv", "goleadores_apertura_2025", "NOMBRE Y APELLIDO"),
    ("Goleadores_clausura_2024_CLC.csv", "goleadores_clausura_2024", "NOMBRE Y APELLIDO"),
    ("Goleadores_clausura_2025_CLC.csv", "goleadores_clausura_2025", "NOMBRE Y APELLIDO"),
]


# ── Data quality function ──────────────────────────────────────────────────────
def apply_data_quality(df: pd.DataFrame, name_col: str) -> pd.DataFrame:
    # 1. Strip spaces from column names
    df.columns = df.columns.str.strip()

    # 2. Strip spaces from all string values in every column
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    # 3. Uppercase the first column (names)
    if name_col in df.columns:
        df[name_col] = df[name_col].str.upper()

    return df


# ── Sync to Firestore with data quality applied ────────────────────────────────
def sync_with_quality(filename: str, collection_name: str, name_col: str):
    url = BASE_URL + filename
    print(f"📥 Reading: {filename}")

    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        return

    # Drop unnamed/empty columns and rows
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.dropna(how="all")

    # Apply data quality
    df = apply_data_quality(df, name_col)

    print(f"  🔍 Preview after cleaning:")
    print(df.head(3).to_string(index=False))
    print()

    # Sync to Firestore
    collection_ref = db.collection(collection_name)
    count = 0

    for _, row in df.iterrows():
        doc_data = row.dropna().to_dict()
        doc_id = str(doc_data[name_col]).replace(" ", "_")
        collection_ref.document(doc_id).set(doc_data)
        count += 1

    print(f"  ✅ '{collection_name}': {count} documentos actualizados\n")


# ── Run ────────────────────────────────────────────────────────────────────────
print("🧹 Iniciando limpieza de datos y sincronización con Firestore...\n")

for filename, collection_name, name_col in FILES:
    sync_with_quality(filename, collection_name, name_col)

print("🎉 ¡Limpieza y sincronización completa!")
