import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import streamlit as st


@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        import os
        if "firebase_key" in st.secrets:
            cred = credentials.Certificate(dict(st.secrets["firebase_key"]))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cred = credentials.Certificate(os.path.join(base_dir, "firebase_key.json"))
        firebase_admin.initialize_app(cred)
    return firestore.client()


@st.cache_data(ttl=300)
def load_collection(collection_name: str) -> pd.DataFrame:
    docs = get_db().collection(collection_name).stream()
    data = [doc.to_dict() for doc in docs]
    return pd.DataFrame(data) if data else pd.DataFrame()


def get_partidos_clausura_2026() -> pd.DataFrame:
    return load_collection("partidos_clausura_2026")

def get_goleadores_clausura_2026() -> pd.DataFrame:
    return load_collection("goleadores_clausura_2026")

# Se conservan los historicos existentes.
def get_goleadores_apertura_2024(): return load_collection("goleadores_apertura_2024")
def get_goleadores_apertura_2025(): return load_collection("goleadores_apertura_2025")
def get_goleadores_clausura_2024(): return load_collection("goleadores_clausura_2024")
def get_goleadores_clausura_2025(): return load_collection("goleadores_clausura_2025")
def get_tarjetas_apertura_2025(): return load_collection("tarjetas_apertura_2025")
def get_tarjetas_clausura_2025(): return load_collection("tarjetas_clausura_2025")
def get_partidos_apertura_2024(): return load_collection("partidos_apertura_2024")
def get_partidos_apertura_2025(): return load_collection("partidos_apertura_2025")
def get_partidos_clausura_2024(): return load_collection("partidos_clausura_2024")
def get_partidos_clausura_2025(): return load_collection("partidos_clausura_2025")
