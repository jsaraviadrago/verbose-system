# Auditoria de preproduccion - Clausura 2026

## Corregido en esta copia
- Eliminados pipelines y CSV duplicados/obsoletos de la raiz.
- `CurrentTournament/fixture.csv` contiene solo datos estaticos.
- Apps Script consolidado en `pipeline/apps_script/`.
- Clausura 2026 agregado al selector del asistente para consultas de partidos.
- Consultas de tarjetas del asistente ya no redirigen silenciosamente Clausura 2026 a Clausura 2025.
- Lista de equipos del asistente actualizada al fixture 2026.
- `requirements.txt` de Streamlit separado de dependencias de Cloud Run.
- `.gitignore` reforzado para secretos, venv y cache Python.
- Documentacion y `deploy.sh` alineados con la estructura real.

## Verificado
- Todos los archivos Python parsean/compilan.
- DataProcessor procesa correctamente los 5 partidos cargados de Fecha 1.
- Fixture actual: 9 fechas, 45 partidos, 90 filas de equipo.
- No hay archivos de credenciales detectados en el ZIP revisado.

## Antes de desplegar
- Completar PROJECT_ID y SHEET_ID en `deploy.sh`.
- Crear/importar la Google Sheet `Resultados` con las columnas esperadas.
- Compartir la Sheet con la service account de Cloud Run.
- Configurar custom audience e IAM `run.invoker` siguiendo comentarios de `deploy.sh`.
- Probar primero `/health` y luego una llamada `/sync` controlada.
