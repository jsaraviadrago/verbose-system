import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import streamlit as st

# ── Firebase connection ────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    """Initialize Firebase only once across Streamlit reruns."""
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()


# ── Generic loader ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)  # Cache for 5 minutes — adjust as needed
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

def get_goleadores_clausura_2025() -> pd.DataFrame:
    return load_collection("goleadores_clausura_2025")

def get_tarjetas_apertura_2025() -> pd.DataFrame:
    return load_collection("tarjetas_apertura_2025")

def get_tarjetas_clausura_2025() -> pd.DataFrame:
    return load_collection("tarjetas_clausura_2025")

def get_partidos_apertura_2025() -> pd.DataFrame:
    return load_collection("partidos_apertura_2025")

def get_partidos_clausura_2025() -> pd.DataFrame:
    return load_collection("partidos_clausura_2025")
