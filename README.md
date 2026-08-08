## Cambridge College Lima - Campeonato Clausura 2026

Descripción

Aplicación web para la administración y publicación del Campeonato Cambridge College Lima – Clausura 2026.

La plataforma permite registrar:

Resultados
Tabla de posiciones
Goleadores
Tarjetas amarillas
Tarjetas rojas

Toda la información se publica automáticamente en Firestore y se visualiza en Streamlit.

Arquitectura
Google Forms (Goleadores)
                    │
Google Forms (Tarjetas)
                    │
Google Sheets (Resultados)
                    │
                    ▼
             GitHub Actions
                    │
                    ▼
            Pipeline Python
                    │
                    ▼
               Firestore
                    │
                    ▼
             Streamlit Cloud
Tecnologías
Python 3.12
Pandas
Firebase Firestore
Google Forms
Google Sheets
GitHub Actions
Streamlit
Estructura del proyecto
verbose-system/

├── app.py
├── assistant.py
├── data_processor.py
├── firestore_client.py
│
├── pipeline/
│   ├── pipeline_service.py
│   ├── pipeline_goleadores.py
│   ├── pipeline_tarjetas.py
│   └── sync_campeonato.py
│
├── CurrentTournament/
│   └── fixture.csv
│
├── assets/
│   └── logos_equipos.png
│
├── .github/
│   └── workflows/
│       └── sync_campeonato.yml
│
└── requirements.txt
Flujo de trabajo
1. Resultados

El responsable llena la Google Sheet de resultados.

Fecha
Equipo 1
Goles 1
Equipo 2
Goles 2

El pipeline:

valida el fixture
identifica fechas completas
calcula victoria/empate/derrota
publica únicamente documentos modificados en Firestore.
2. Goleadores

El responsable llena el Google Form.

Cada respuesta contiene:

Fecha
Equipo

Jugador1
Goles1

Jugador2
Goles2

...

Jugador7
Goles7

El pipeline:

normaliza nombres
verifica que la suma de goles coincida con el resultado oficial
acumula goles históricos
publica únicamente jugadores válidos.

Los jugadores con nombres temporales como:

Jugador 18
Jugador 30

quedan pendientes hasta ser corregidos.

3. Tarjetas

Google Form.

Cada registro contiene:

Fecha

Equipo

Jugador

Tipo

Cantidad

Tipos:

Amarilla
Roja

Regla especial:

Dos amarillas en una misma fecha generan automáticamente una roja adicional.

Ejemplo:

Fecha 3

Juan Perez

Amarilla

Cantidad = 2

Resultado:

Amarillas += 2

Rojas += 1

No existe acumulación entre fechas para producir una roja.

GitHub Actions

Toda la actualización del campeonato se realiza desde un único workflow.

Actualizar campeonato

El workflow ejecuta:

Resultados

↓

Goleadores

↓

Tarjetas

No requiere Cloud Run ni Cloud Functions.

Firestore

Colecciones utilizadas.

partidos_clausura_2026

goleadores_clausura_2026

tarjetas_clausura_2026
Frontend

La aplicación muestra:

Promedio de goles
Total de goles
Estadísticas por fecha
Tabla de posiciones
Resultados
Equipos más goleadores
Equipos con más amarillas
Top 8 goleadores
Top 8 amarillas
Top 8 rojas
Validaciones
Resultados
Fixture válido.
No existen partidos duplicados.
Dos equipos por partido.
Goleadores
La suma de goles coincide con el marcador oficial.
Nombres normalizados.
No se publican jugadores pendientes.
Tarjetas
Dos amarillas en la misma fecha generan una roja.
Las amarillas siguen contabilizándose.
Las rojas directas también se acumulan.
Actualizar el campeonato
Completar Google Sheets y Google Forms.
Ir al repositorio GitHub.
Abrir:
Actions

↓

Actualizar campeonato

↓

Run workflow
Esperar aproximadamente 20–30 segundos.
Abrir la aplicación Streamlit.
Aplicación
https://futbol-ccl-apafa.streamlit.app/
Autor

José Saravia

Cambridge College Lima – APAFA

Historial
Versión 2026
Nuevo pipeline basado en Google Forms.
Sin Cloud Run.
Sin Cloud Functions.
GitHub Actions como orquestador.
Firestore como única fuente de datos.
Streamlit como interfaz de consulta.
