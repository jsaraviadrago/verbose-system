import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import streamlit as st


# ── Firebase connection ────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        import json, os
        if "firebase_key" in st.secrets:
            # Streamlit Cloud — usa secrets
            key_dict = json.loads(st.secrets["firebase_key"])
            cred = credentials.Certificate(key_dict)
        else:
            # Local — usa firebase_key.json
            base_dir = os.path.dirname(os.path.abspath(__file__))
            key_path = os.path.join(base_dir, "firebase_key.json")
            cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# ── Generic loader ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_collection(collection_name: str) -> pd.DataFrame:
    """Load an entire Firestore collection into a DataFrame."""
    db = get_db()
    docs = db.collection(collection_name).stream()
    data = [doc.to_dict() for doc in docs]
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# ── Named loaders (use these in your app) ─────────────────────────────────────
def get_goleadores_apertura_2024() -> pd.DataFrame:
    return load_collection("goleadores_apertura_2024")

def get_goleadores_apertura_2025() -> pd.DataFrame:
    return load_collection("goleadores_apertura_2025")

def get_goleadores_clausura_2024() -> pd.DataFrame:
    return load_collection("goleadores_clausura_2024")

def get_goleadores_clausura_2025() -> pd.DataFrame:
    return load_collection("goleadores_clausura_2025")

def get_tarjetas_apertura_2025() -> pd.DataFrame:
    return load_collection("tarjetas_apertura_2025")

def get_tarjetas_clausura_2025() -> pd.DataFrame:
    return load_collection("tarjetas_clausura_2025")

def get_partidos_apertura_2024() -> pd.DataFrame:
    return load_collection("partidos_apertura_2024")

def get_partidos_apertura_2025() -> pd.DataFrame:
    return load_collection("partidos_apertura_2025")

def get_partidos_clausura_2024() -> pd.DataFrame:
    return load_collection("partidos_clausura_2024")

def get_partidos_clausura_2025() -> pd.DataFrame:
    return load_collection("partidos_clausura_2025")
