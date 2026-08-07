#!/usr/bin/env bash
set -euo pipefail

# Ejecutar desde la RAIZ del repositorio, donde estan Dockerfile,
# CurrentTournament/ y pipeline/.

# COMPLETAR ANTES DE EJECUTAR
PROJECT_ID="TU_PROJECT_ID"
REGION="us-central1"
SERVICE="cambridge-results-2026"
SERVICE_ACCOUNT="cambridge-results-pipeline@${PROJECT_ID}.iam.gserviceaccount.com"
SHEET_ID="TU_GOOGLE_SHEET_ID"
SHEET_RANGE="Resultados!A1:F"
COLLECTION="partidos_clausura_2026"
FIXTURE_PATH="/app/CurrentTournament/fixture.csv"

# APIs necesarias
gcloud config set project "$PROJECT_ID"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sheets.googleapis.com \
  firestore.googleapis.com

# Service account. Si ya existe, continua.
gcloud iam service-accounts create cambridge-results-pipeline \
  --display-name="Cambridge results pipeline" || true

# Firestore: permiso para leer/escribir documentos.
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user"

# Despliega PRIVADO desde la raiz del repo.
# Cloud Run empaqueta CurrentTournament/fixture.csv dentro de la imagen.
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --service-account "$SERVICE_ACCOUNT" \
  --set-env-vars="GOOGLE_SHEET_ID=${SHEET_ID},GOOGLE_SHEET_RANGE=${SHEET_RANGE},FIRESTORE_COLLECTION=${COLLECTION},FIXTURE_PATH=${FIXTURE_PATH}" \
  --no-allow-unauthenticated \
  --min=0 \
  --max=1

# DESPUES DEL PRIMER DEPLOY:
# 1) Comparte la Google Sheet como Viewer con SERVICE_ACCOUNT.
# 2) En Apps Script pega pipeline/apps_script/Code.gs y appsscript.json.
# 3) Ejecuta logClientId() y copia el Client ID que aparece en el log.
# 4) Configura ese Client ID como custom audience:
#      gcloud run services update "$SERVICE" --region "$REGION" --add-custom-audiences="TU_APPS_SCRIPT_CLIENT_ID"
# 5) Concede roles/run.invoker al usuario propietario del trigger:
#      gcloud run services add-iam-policy-binding "$SERVICE" --region "$REGION" \
#        --member="user:TU_EMAIL_GOOGLE" --role="roles/run.invoker"
# 6) Obtiene la URL del servicio:
#      gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
#    y pegala en CONFIG.CLOUD_RUN_URL de pipeline/apps_script/Code.gs.
# 7) Ejecuta installTrigger() una sola vez y autoriza.
#
# En siguientes despliegues, si solo cambias codigo o CurrentTournament/fixture.csv,
# vuelve a ejecutar este deploy.sh. No necesitas reinstalar el trigger.
