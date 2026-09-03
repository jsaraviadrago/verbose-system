# 🏆 Cambridge League — Arquitectura y Flujo Funcional

Este documento presenta dos vistas complementarias de la solución: una **arquitectura técnica End-to-End**, enfocada en componentes, integraciones y movimiento de datos; y un **flujo funcional**, enfocado en cómo el usuario registra, procesa y publica la información del campeonato.

---

## 🏗️ 1. Arquitectura técnica End-to-End

![Arquitectura End-to-End](https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/Arquitectura_E2E.png)

[Ver imagen en GitHub](https://github.com/jsaraviadrago/verbose-system/blob/main/Arquitectura_E2E.png)

### 🎯 Objetivo

La arquitectura automatiza la gestión de **resultados, goleadores y tarjetas**, separando captura, almacenamiento operativo, procesamiento, publicación, consulta y notificaciones.

### ⌨️ Data Entry

La información se registra mediante tres aplicaciones web desarrolladas con **Google Apps Script**:

- 📝 **Resultados:** permite ingresar los marcadores de cada partido.
- ⚽ **Goleadores:** permite buscar/seleccionar jugadores e ingresar sus goles. Reemplazó al Google Form utilizado inicialmente.
- 🟨🟥 **Tarjetas:** permite buscar jugadores e ingresar amarillas y rojas. También reemplazó al Google Form original.

Cada aplicación escribe en su correspondiente hoja de **Google Sheets**.

### 📊 Google Sheets — capa operativa

Google Sheets funciona como la capa editable y corregible del proceso:

```text
Resultados
Goleadores
Tarjetas
```

Las hojas mantienen la información de entrada antes de su procesamiento y permiten corregir datos y reprocesarlos.

### ⚡ Trigger automático

La hoja de **Resultados** determina actualmente el cierre de una fecha.

```text
¿Todos los partidos tienen Goles_1 y Goles_2?

NO → esperar
SÍ → disparar GitHub Actions
```

Por ello, el orden operativo recomendado es:

```text
1. ⚽ Goleadores
2. 🟨🟥 Tarjetas
3. 📝 Resultados
```

El último resultado completo actúa funcionalmente como el cierre de la fecha.

### ⚙️ GitHub Actions

GitHub Actions orquesta el procesamiento secuencial:

```text
Resultados
    ↓
Goleadores
    ↓
Tarjetas
```

Los pipelines Python leen las hojas, validan y transforman los datos, comparan contra el estado existente y escriben los cambios en Firestore.

El workflow dispone de tres mecanismos:

- ⚡ **Automático:** disparado por Apps Script al completarse una fecha.
- ▶️ **Manual:** `workflow_dispatch` desde GitHub.
- ⏰ **Respaldo:** ejecución programada los domingos a las 15:00 hora de Lima.

### 🔥 Firestore

Firestore funciona como la base publicada de la solución. Entre las principales colecciones se encuentran:

```text
partidos_clausura_2026
goleadores_clausura_2026
tarjetas_clausura_2026
```

Esto desacopla la captura operativa del frontend público.

### 👤 Identidad de jugadores

Existe además un padrón histórico 2025 enriquecido con información disponible de 2026. Su objetivo es permitir posteriormente consolidar identidad, cambios de equipo y estadísticas históricas.

El documento de identidad es **información privada**: puede utilizarse internamente para cruces, pero nunca debe mostrarse en Streamlit ni ser entregado por el agente. La capa pública deberá trabajar con `PLAYER_ID`.

### 🌐 Streamlit

Streamlit consume Firestore y presenta:

- 🏆 tabla de posiciones;
- 📅 fixture pendiente;
- 📝 resultados;
- 📊 estadísticas;
- ⚽ rankings de equipos y goleadores;
- 🟨🟥 disciplina;
- 🤖 asistente CLC.

### 📲 Telegram

Cada ejecución del workflow envía una notificación de éxito o error mediante Telegram, permitiendo supervisar las actualizaciones desde el celular.

---

## 🔄 2. Flujo funcional

![Flujo funcional](https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/mermaid-diagram_flujo_funcional.png)

[Ver imagen en GitHub](https://github.com/jsaraviadrago/verbose-system/blob/main/mermaid-diagram_flujo_funcional.png)

La vista funcional abstrae los componentes técnicos y explica el proceso desde el punto de vista de la operación.

### 1️⃣ Captura

El operador registra goleadores, tarjetas y resultados mediante las aplicaciones de captura.

### 2️⃣ Persistencia operativa

Cada aplicación escribe la información en su correspondiente Google Sheet.

### 3️⃣ Validación del cierre

El sistema comprueba si todos los partidos de la fecha tienen marcador completo.

```text
¿Fecha completa?

NO → esperar
SÍ → continuar
```

### 4️⃣ Procesamiento

GitHub Actions procesa:

```text
Resultados → Goleadores → Tarjetas
```

### 5️⃣ Publicación

Los datos validados se sincronizan con Firestore.

### 6️⃣ Consulta

Streamlit consulta Firestore y presenta la información actualizada del campeonato.

### 7️⃣ Notificación

Telegram informa el resultado de la ejecución.

---

## 🔁 Flujo resumido End-to-End

```text
👤 OPERADOR
     │
     ├── ⚽ Goleadores
     ├── 🟨🟥 Tarjetas
     └── 📝 Resultados
              │
              ▼
       📱 APPS SCRIPT
              │
              ▼
       📊 GOOGLE SHEETS
              │
              ▼
     ¿FECHA COMPLETA?
              │
        ┌─────┴─────┐
        │           │
       NO          SÍ
        │           │
     Esperar        ▼
              ⚙️ GITHUB ACTIONS
                    │
              Resultados
                    ↓
              Goleadores
                    ↓
               Tarjetas
                    │
                    ▼
              🔥 FIRESTORE
               ┌────┴────┐
               │         │
               ▼         ▼
          🌐 STREAMLIT  📲 TELEGRAM
```

---

## 🛡️ Principios de diseño

| Principio | Aplicación |
|---|---|
| 📊 Fuente corregible | Google Sheets mantiene la información operativa editable |
| 🔁 Idempotencia | Reprocesar sin cambios no debe duplicar información |
| 🔐 Privacidad | Los identificadores personales privados no llegan al frontend/agente |
| ⚙️ Automatización | Trigger automático + manual + schedule de respaldo |
| 📲 Observabilidad | Telegram informa el resultado de cada ejecución |
| 🧩 Separación | Captura, procesamiento, persistencia y visualización están desacoplados |

---

## 🧩 Responsabilidad por componente

| Componente | Responsabilidad |
|---|---|
| 📱 Apps Script | Captura y trigger automático |
| 📊 Google Sheets | Persistencia operativa y correcciones |
| ⚙️ GitHub Actions | Orquestación |
| 🐍 Python | Validación y procesamiento |
| 🔥 Firestore | Persistencia publicada |
| 🌐 Streamlit | Visualización pública |
| 📲 Telegram | Notificaciones |

---

## 📌 Estado actual

| Capacidad | Estado |
|---|---|
| 📝 Captura de resultados | ✅ Operativa |
| ⚽ Captura de goleadores | ✅ Operativa |
| 🟨🟥 Captura de tarjetas | ✅ Operativa |
| ⚡ Trigger automático | ✅ Operativo |
| ▶️ Ejecución manual | ✅ Operativa |
| ⏰ Respaldo programado | ✅ Configurado |
| 📲 Telegram | ✅ Operativo |
| 🔥 Firestore | ✅ Operativo |
| 🌐 Streamlit | ✅ Operativo |
| 👤 Padrón histórico en Firestore | ⏳ Pendiente |
| 🤖 Evolución del agente | 🔄 Evolutivo |

---

La solución mantiene un flujo ligero y trazable desde el registro de información hasta su publicación, combinando Apps Script, Google Sheets, GitHub Actions, Python, Firestore, Streamlit y Telegram.
