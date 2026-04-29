import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import os

# Firebase initialization
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
    docs = db.collection(collection_name).stream()
    for doc in docs:
        doc.reference.delete()

ddef sync_collection(filename: str, collection_name: str, id_col: str = None):
    url = BASE_URL + filename
    print(f"📥 Leyendo: {filename}")
    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    # 1. Limpieza de columnas (Normalizamos a Mayúsculas para evitar errores de espacios)
    df.columns = df.columns.str.strip().str.upper()
    df = df.loc[:, ~df.columns.str.startswith("UNNAMED")]
    df = df.dropna(how="all")

    # 2. LÓGICA ESPECIAL PARA TARJETAS: Combinar filas del mismo jugador
    # Esto asegura que si Alvaro Galarreta tiene '2A' en una fila y '1R' en otra, se unan.
    if "JUGADOR" in df.columns:
        df = df.fillna("")
        # Agrupamos por Jugador y Equipo, uniendo los textos de las sanciones
        df = df.groupby(["JUGADOR", "EQUIPO"]).agg(lambda x: " ".join(filter(None, x.astype(str)))).reset_index()
        print(f"  🔄 Filas combinadas para procesar múltiples tarjetas/rojas.")

    # 3. Deduplicar para el resto de archivos (Goleadores, etc.)
    elif id_col and id_col in df.columns:
        subset = [id_col, "EQUIPO", "GOLES"] if "GOLES" in df.columns else [id_col]
        df = df.drop_duplicates(subset=subset)

    # Borrar colección existente
    delete_collection(collection_name)
    collection_ref = db.collection(collection_name)
    count = 0

    # 4. Subida a Firestore
    for i, row in df.iterrows():
        doc_data = row.to_dict()

        # Generar ID único usando el nombre del jugador y el equipo
        doc_id = str(doc_data["JUGADOR" if "JUGADOR" in doc_data else id_col]).strip().replace(" ", "_")
        if "EQUIPO" in doc_data:
            equipo = str(doc_data["EQUIPO"]).strip().replace(" ", "_")
            doc_id = f"{doc_id}__{equipo}"
        else:
            doc_id = str(i)

        collection_ref.document(doc_id).set(doc_data)
        count += 1

    print(f"  ✅ '{collection_name}': {count} sincronizados\n")

print("🚀 Sincronizando GitHub → Firestore...\n")
for filename, collection_name, id_col in FILES:
    sync_collection(filename, collection_name, id_col)
print("🎉 ¡Sincronización completa!")