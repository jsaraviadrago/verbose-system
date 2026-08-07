#!/usr/bin/env bash
set -euo pipefail

# Ejecutar desde la RAIZ del repositorio, donde estan Dockerfile,
# CurrentTournament/ y pipeline/.

# -----------------------------------------------------------------------------
# COMPLETAR ANTES DEL PRIMER DEPLOY
# -----------------------------------------------------------------------------
PROJECT_ID="futbol-ccl"
REGION="us-central1"
SERVICE="cambridge-results-2026"
SERVICE_ACCOUNT_NAME="cambridge-results-pipeline"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Google Sheet real de Cambridge League Clausura 2026.
SHEET_ID="1W_2_TOEyyh8LBJe6MA9NCK_ivx89dEjFO_8NUyvwMO4"
SHEET_RANGE="Resultados!A:F"

COLLECTION="partidos_clausura_2026"
FIXTURE_PATH="/app/CurrentTournament/fixture.csv"

if [[ "$PROJECT_ID" == "TU_PROJECT_ID" ]]; then
  echo "ERROR: reemplaza TU_PROJECT_ID por tu Google Cloud/Firebase Project ID."
  exit 1
fi

# -----------------------------------------------------------------------------
# APIs necesarias
# -----------------------------------------------------------------------------
gcloud config set project "$PROJECT_ID"

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sheets.googleapis.com \
  firestore.googleapis.com

# -----------------------------------------------------------------------------
# Service account del pipeline
# -----------------------------------------------------------------------------
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name="Cambridge results pipeline"
fi

# Firestore: leer/escribir documentos de la coleccion del torneo actual.
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user" \
  --quiet

# -----------------------------------------------------------------------------
# Deploy PRIVADO a Cloud Run
# -----------------------------------------------------------------------------
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --service-account "$SERVICE_ACCOUNT" \
  --set-env-vars="GOOGLE_SHEET_ID=${SHEET_ID},GOOGLE_SHEET_RANGE=${SHEET_RANGE},FIRESTORE_COLLECTION=${COLLECTION},FIXTURE_PATH=${FIXTURE_PATH}" \
  --no-allow-unauthenticated \
  --min=0 \
  --max=1 \
  --quiet

SERVICE_URL="$(
  gcloud run services describe "$SERVICE" \
    --region "$REGION" \
    --format='value(status.url)'
)"

echo
echo "Deploy terminado."
echo "Cloud Run URL: ${SERVICE_URL}"
echo "Service account: ${SERVICE_ACCOUNT}"
echo
echo "SIGUIENTES PASOS DEL PRIMER DEPLOY:"
echo "1. Comparte la Google Sheet como Viewer con:"
echo "   ${SERVICE_ACCOUNT}"
echo "2. En Apps Script usa pipeline/apps_script/Code.gs y appsscript.json."
echo "3. Ejecuta logClientId() y copia el Client ID/audience del log."
echo "4. Configura el custom audience:"
echo "   gcloud run services update ${SERVICE} --region ${REGION} --add-custom-audiences=TU_APPS_SCRIPT_CLIENT_ID"
echo "5. Concede roles/run.invoker al usuario Google que creo el trigger:"
echo "   gcloud run services add-iam-policy-binding ${SERVICE} --region ${REGION} --member=user:TU_EMAIL_GOOGLE --role=roles/run.invoker"
echo "6. Pega esta URL en CONFIG.CLOUD_RUN_URL de Code.gs:"
echo "   ${SERVICE_URL}"
echo "7. Ejecuta installTrigger() una sola vez y autoriza."
echo
echo "En despliegues siguientes por cambios de codigo/fixture, vuelve a ejecutar este script."
echo "No es necesario reinstalar el trigger."
