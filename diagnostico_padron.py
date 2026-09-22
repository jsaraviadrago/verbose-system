"""
Diagnóstico rápido: ¿la carga anterior de player_identity.py se cortó a
medias? Cuenta cuántos documentos de jugador ya existen en Firestore, y
confirma si el metadata final (que solo se crea si TODO terminó bien)
está presente.

Uso:
    export GOOGLE_CLOUD_PROJECT="futbol-ccl"
    export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/firebase_key.json"
    python diagnostico_padron.py
"""
import os
from google.cloud import firestore

PRIVATE_COLLECTION = "jugadores_privado_2025"
META_COLLECTION = "padrones_metadata"
META_DOCUMENT = "padron_2025"


def main():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "futbol-ccl")
    db = firestore.Client(project=project_id)

    docs = list(db.collection(PRIVATE_COLLECTION).stream())
    print(f"Documentos existentes en '{PRIVATE_COLLECTION}': {len(docs)} (deberían ser 242 si terminó bien)")

    meta_ref = db.collection(META_COLLECTION).document(META_DOCUMENT)
    meta = meta_ref.get()
    print(f"¿Existe el metadata final ({META_COLLECTION}/{META_DOCUMENT})?: {meta.exists}")

    if meta.exists:
        print("→ La carga SÍ se completó exitosamente en algún momento. No hace falta hacer nada más.")
    elif len(docs) == 0:
        print("→ No hay nada creado todavía. Puedes correr el upload normal, sin problema.")
    else:
        print(f"→ Quedó a medias: {len(docs)} documentos creados, pero sin metadata final.")
        print("  Hay que borrar estos documentos parciales y volver a correr desde cero.")


if __name__ == "__main__":
    main()
