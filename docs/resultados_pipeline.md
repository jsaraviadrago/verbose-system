# Pipeline de resultados - Clausura 2026

## Estructura

```text
repo/
├── app.py
├── firestore_client.py
├── data_processor.py
├── Dockerfile
├── deploy.sh
├── CurrentTournament/
│   └── fixture.csv
├── pipeline/
│   ├── pipeline_service.py
│   ├── requirements.txt
│   └── apps_script/
│       ├── Code.gs
│       └── appsscript.json
└── Data/
    └── historicos...
```

`Data/` queda reservado para historicos. `CurrentTournament/fixture.csv` solo contiene datos estaticos del fixture:
`Fecha, Partido, Cancha, Hora, Equipo_numero, Equipo`.

## Flujo

Google Sheet -> Apps Script `onEdit` instalable -> Cloud Run privado -> validacion -> calculo G/P/E -> Firestore -> Streamlit.

El trigger solo llama a Cloud Run cuando todos los partidos de la fecha editada tienen `Goles_1` y `Goles_2` validos. Cloud Run vuelve a validar antes de escribir.

## Google Sheet

Pestana: `Resultados`

Columnas exactas:
`Fecha, Partido, Equipo_1, Goles_1, Equipo_2, Goles_2`

Solo `Goles_1` y `Goles_2` deben ser editables.

## Firestore

Coleccion: `partidos_clausura_2026`

IDs deterministas: `f01_p001_e1`, `f01_p001_e2`, etc.

Campos: `FECHA, PARTIDO, CANCHA, HORA, EQUIPO_NUMERO, EQUIPO, GOLES, RESULTADO`.

## Cambio de torneo

Al terminar el torneo, exporta/archiva el dataset final en `Data/`. Para el siguiente torneo reemplaza `CurrentTournament/fixture.csv` y actualiza la coleccion configurada para Firestore.
