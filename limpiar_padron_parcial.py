"""
Borra los documentos parciales de jugadores_privado_2025 que quedaron de
una carga interrumpida (sin metadata final) — para poder reintentar
player_identity.py upload desde cero, limpio.

SOLO corre esto si diagnostico_padron.py confirmó que el metadata final
NO existe. Si el metadata SÍ existe, la carga terminó bien y este script
no debe correrse.

Uso:
    export GOOGLE_CLOUD_PROJECT="futbol-ccl"
    export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/firebase_key.json"
    python limpiar_padron_parcial.py
"""
import os
from google.cloud import firestore

PRIVATE_COLLECTION = "jugadores_privado_2025"
META_COLLECTION = "padrones_metadata"
META_DOCUMENT = "padron_2025"


def main():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "futbol-ccl")
    db = firestore.Client(project=project_id)

    meta_ref = db.collection(META_COLLECTION).document(META_DOCUMENT)
    if meta_ref.get().exists:
        print("El metadata final SÍ existe — la carga anterior terminó bien.")
        print("NO se borra nada. Si ves esto, avísame antes de continuar.")
        return

    docs = list(db.collection(PRIVATE_COLLECTION).stream())
    print(f"Se van a borrar {len(docs)} documentos de '{PRIVATE_COLLECTION}'.")
    confirm = input("Escribe 'BORRAR' para confirmar: ").strip()
    if confirm != "BORRAR":
        print("Cancelado, no se borró nada.")
        return

    batch = db.batch()
    count = 0
    for doc in docs:
        batch.delete(doc.reference)
        count += 1
        if count % 400 == 0:  # límite de Firestore por batch
            batch.commit()
            batch = db.batch()
    batch.commit()

    print(f"Listo — {count} documentos borrados. Ya puedes reintentar el upload desde cero.")


if __name__ == "__main__":
    main()
