# ⚽ Cambridge College Lima — Clausura 2026

<p align="center">
  <strong>Plataforma de resultados, estadísticas, goleadores y disciplina del torneo CLC.</strong>
</p>

<p align="center">
  Google Sheets · Google Forms · GitHub Actions · Firebase Firestore · Streamlit
</p>

---

## 🏆 Sobre el proyecto

Este repositorio contiene la aplicación y los pipelines utilizados para administrar y publicar el **Campeonato Cambridge College Lima — Clausura 2026**.

El objetivo del sistema es mantener una operación sencilla durante cada fecha del campeonato:

- 📝 registrar los resultados;
- ⚽ registrar los goleadores;
- 🟨 registrar tarjetas amarillas;
- 🟥 registrar tarjetas rojas;
- 🔄 sincronizar todo con un único workflow;
- 🔥 publicar automáticamente estadísticas actualizadas;
- 📱 permitir que la operación pueda realizarse incluso desde un celular.

La aplicación pública está construida con **Streamlit**, mientras que **Firebase Firestore** funciona como la fuente de datos publicada.

### 🌐 Aplicación

**https://futbol-ccl-apafa.streamlit.app/**

---

## ✨ Funcionalidades

La aplicación muestra actualmente:

| Módulo | Funcionalidad |
|---|---|
| 🏆 Tabla | Tabla de posiciones actualizada |
| 📝 Resultados | Partidos jugados y marcadores |
| 📊 Estadísticas | Promedio de goles y total de goles |
| 📈 Fechas | Evolución de goles por fecha |
| ⚽ Equipos | Ranking de equipos más goleadores |
| 🟨 Disciplina | Ranking de equipos con más amarillas |
| 🥇 Goleadores | Top 8 de máximos goleadores |
| 🟨 Amarillas | Top 8 de jugadores con más amarillas |
| 🟥 Rojas | Top 8 de jugadores con más rojas |
| 🤖 Asistente | Módulo experimental del Asistente CLC |

---

## 🧱 Arquitectura

El sistema separa la **captura**, el **procesamiento**, la **persistencia** y el **frontend**.

```text
                ┌──────────────────────┐
                │   Google Sheets      │
                │     Resultados       │
                └──────────┬───────────┘
                           │
                ┌──────────▼───────────┐
                │    Google Forms      │
                │ Goleadores / Tarjetas│
                └──────────┬───────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  Google Sheets    │
                 │ respuestas Forms  │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  GitHub Actions   │
                 │ Actualizar torneo │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Pipelines Python  │
                 │ validación + ETL  │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Firebase Firestore│
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │     Streamlit     │
                 │   aplicación web  │
                 └───────────────────┘
```

La arquitectura no necesita un servidor permanentemente encendido.

---

## 📂 Estructura principal

```text
verbose-system/
│
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
├── requirements.txt
└── README.md
```

---

# 📝 Resultados

Los resultados oficiales se ingresan en una Google Sheet.

La hoja contiene información como:

```text
Fecha
Equipo_1
Goles_1
Equipo_2
Goles_2
```

El fixture oficial del campeonato permanece versionado en:

```text
CurrentTournament/fixture.csv
```

## 🔎 Validaciones

El pipeline de resultados:

- verifica los equipos contra el fixture;
- determina automáticamente el partido correspondiente;
- detecta fechas completas;
- evita publicar jornadas incompletas;
- calcula victoria, empate o derrota;
- conserva los metadatos oficiales del fixture;
- escribe únicamente documentos modificados.

## 🔁 Idempotencia

Los documentos utilizan IDs deterministas.

Ejemplo:

```text
f01_p001_e1
f01_p001_e2
```

Por eso, ejecutar el workflow varias veces con los mismos datos **no genera duplicados**.

---

# ⚽ Goleadores

Los goleadores se capturan mediante **Google Forms**.

Cada respuesta corresponde a un equipo y una fecha, con hasta siete jugadores:

```text
Fecha
Equipo

Jugador1
Goles1

Jugador2
Goles2

...

Jugador7
Goles7
```

## ✅ Validación contra resultados

Antes de publicar goleadores, el pipeline compara la suma de goles asignados a los jugadores contra el resultado oficial ya publicado.

Ejemplo:

```text
Manchester City → resultado oficial: 6 goles

Juan Pérez       3
Carlos Ruiz      2
Pedro Soto       1
                 ─
                 6 ✅
```

Si la suma no coincide, ese **equipo + fecha queda pendiente**.

Los demás equipos válidos sí pueden publicarse.

---

## 🧹 Normalización de jugadores

Los nombres se normalizan para evitar duplicados provocados por diferencias de escritura.

Por ejemplo:

```text
José Pérez
JOSE PEREZ
Jose   Perez
```

se reconocen como la misma identidad normalizada.

La clave lógica utiliza:

```text
Equipo + Nombre normalizado
```

Esto evita mezclar accidentalmente jugadores con el mismo nombre que pertenecen a equipos distintos.

> El pipeline no utiliza fuzzy matching agresivo.  
> `Perez` y `Peres` no se fusionan automáticamente.

---

## ⏳ Jugadores pendientes

Durante una fecha puede ocurrir que todavía no se conozca el nombre de un jugador.

Ejemplos:

```text
Jugador 18
Jugador 30
NN
Desconocido
```

Esos registros se consideran **pendientes**.

Cuando se conoce el nombre real, se corrige directamente la celda correspondiente en la Google Sheet.

Al volver a ejecutar el workflow:

- 🔄 se recalcula el histórico;
- 🧹 desaparece el placeholder;
- ⚽ se actualiza el acumulado correcto en Firestore.

---

# 🟨🟥 Tarjetas

Las tarjetas también se registran mediante **Google Forms**.

Cada bloque contiene:

```text
Jugador
Tarjeta
Cantidad
```

Las tarjetas disponibles son:

- 🟨 Amarilla
- 🟥 Roja

---

## 🟨 Regla de doble amarilla

La regla especial del campeonato es:

> **2 amarillas para el mismo jugador en la misma fecha generan 1 roja adicional.**

Ejemplo:

```text
Fecha 3
Juan Pérez
Amarilla
Cantidad = 2
```

Se contabiliza como:

```text
🟨 Amarillas +2
🟥 Rojas     +1
```

Las dos amarillas siguen contando.

---

## 🚫 Las amarillas no se convierten entre fechas

Esto:

```text
Fecha 1 → Amarilla 1
Fecha 2 → Amarilla 1
```

produce:

```text
🟨 Amarillas acumuladas = 2
🟥 Rojas acumuladas     = 0
```

La roja por doble amarilla solo se calcula dentro de la **misma fecha**.

---

## 🟥 Rojas directas

Una roja ingresada directamente en el Form también se acumula.

Por lo tanto, las rojas totales de un jugador pueden provenir de:

```text
🟥 rojas directas
+
🟨🟨 dobles amarillas en una fecha
```

---

# 🔥 Firestore

Las colecciones principales del Clausura 2026 son:

```text
partidos_clausura_2026
goleadores_clausura_2026
tarjetas_clausura_2026
```

---

## 🏟️ Partidos

Cada documento contiene campos similares a:

```text
FECHA
PARTIDO
CANCHA
HORA
EQUIPO_NUMERO
EQUIPO
GOLES
RESULTADO
```

---

## ⚽ Goleadores

Los documentos agregados contienen:

```text
PLAYER_KEY
NOMBRE Y APELLIDO
EQUIPO
GOLES
```

`GOLES` representa el acumulado del torneo.

---

## 🟨 Disciplina

Los documentos contienen:

```text
PLAYER_KEY
JUGADOR
EQUIPO
AMARILLAS
ROJAS
```

Los valores representan el acumulado del campeonato.

---

# 🔄 GitHub Actions

La operación del campeonato utiliza un único workflow:

## 🏆 `Actualizar campeonato`

Orden de ejecución:

```text
1. 📝 Resultados
        ↓
2. ⚽ Goleadores
        ↓
3. 🟨🟥 Tarjetas
        ↓
4. 🔥 Firestore
```

El workflow se encuentra en:

```text
.github/workflows/sync_campeonato.yml
```

---

## 📱 Cómo actualizar el campeonato

Después de ingresar la información:

1. Abrir el repositorio en GitHub.
2. Entrar a **Actions**.
3. Seleccionar **Actualizar campeonato**.
4. Pulsar **Run workflow**.
5. Esperar a que el workflow termine en verde ✅.
6. Abrir o actualizar Streamlit.

Esto puede hacerse desde una computadora o desde el navegador del celular.

---

# 🔐 Credenciales

GitHub Actions utiliza el secret:

```text
FIREBASE_SERVICE_ACCOUNT_JSON
```

El valor corresponde a una Service Account de Firebase/Google Cloud autorizada para trabajar con Firestore.

> ⚠️ Nunca subir el JSON de la Service Account directamente al repositorio.

Streamlit utiliza la misma clase de credencial mediante:

```toml
[firebase_key]
```

en los Secrets de Streamlit Cloud.

---

# 🌐 Google Sheets

Los pipelines leen las hojas mediante su salida CSV pública.

Por este motivo, las hojas utilizadas por el pipeline deben estar configuradas como:

```text
Cualquier persona con el enlace
→ Lector
```

No debe publicarse información sensible en esas hojas.

---

# 🖥️ Frontend Streamlit

La aplicación principal está en:

```text
app.py
```

El frontend consulta Firestore mediante:

```text
firestore_client.py
```

El cliente utiliza caché de Streamlit para reducir lecturas repetidas.

---

## 📊 Estadísticas por equipo

Después de los resultados se muestran dos gráficos:

### ⚽ Equipos más goleadores

Suma todos los goles oficiales publicados por equipo.

### 🟨 Equipos con más amarillas

Suma las amarillas acumuladas por cada equipo.

Ambos rankings se muestran ordenados de mayor a menor.

---

## 🥇 Rankings individuales

La aplicación muestra:

- 🥇 Top 8 goleadores;
- 🟨 Top 8 amarillas;
- 🟥 Top 8 rojas.

Los tres primeros puestos se destacan con:

```text
🥇
🥈
🥉
```

La tabla de rojas se muestra aunque todavía no existan jugadores con tarjetas rojas.

---

# 🛡️ Principios del diseño

El proyecto intenta mantener cuatro principios.

### ✅ Validar antes de publicar

Los datos capturados no se consideran automáticamente datos oficiales.

### 🔁 Poder ejecutar nuevamente

Los pipelines están diseñados para tolerar ejecuciones repetidas.

### ✏️ Permitir correcciones

Si un dato antiguo cambia en Google Sheets, una nueva ejecución recalcula el estado publicado.

### 📱 Operación simple

La persona encargada del torneo no necesita ejecutar Python ni administrar servidores.

---

# 🧰 Tecnologías

| Tecnología | Uso |
|---|---|
| 🐍 Python | Pipelines y backend |
| 🐼 Pandas | Transformación de datos |
| 🔥 Firebase Firestore | Base de datos publicada |
| 📋 Google Forms | Captura de goleadores y tarjetas |
| 📊 Google Sheets | Resultados y respuestas |
| ⚙️ GitHub Actions | Orquestación |
| 🎈 Streamlit | Frontend |
| 📈 Altair | Visualizaciones |

---

# 🚀 Flujo operativo de una fecha

Una operación típica queda así:

```text
1️⃣ Terminan los partidos

2️⃣ Se completan los resultados en Google Sheets

3️⃣ Se registran goleadores en Google Forms

4️⃣ Se registran tarjetas en Google Forms

5️⃣ Se corrigen nombres pendientes si fuera necesario

6️⃣ GitHub → Actions → Actualizar campeonato → Run workflow

7️⃣ El pipeline valida y sincroniza Firestore

8️⃣ Streamlit muestra la información actualizada
```

---

# 🧪 Correcciones

Si se detecta un error después de publicar:

### Resultado incorrecto

Corregir la Google Sheet de resultados y ejecutar nuevamente el workflow.

### Nombre incorrecto de goleador

Corregir la celda en la hoja de respuestas del Form y ejecutar nuevamente.

### Tarjeta incorrecta

Corregir la hoja de respuestas correspondiente y volver a ejecutar.

La intención es que **Google Sheets sea el origen corregible** y Firestore represente el estado publicado.

---

# 🗺️ Posibles mejoras futuras

Algunas extensiones posibles:

- 🤖 ampliar el Asistente CLC;
- 📅 mostrar próxima fecha;
- 📱 optimizar aún más el layout móvil;
- 🏆 historial de campeones;
- 👤 perfiles individuales de jugadores;
- 📊 estadísticas históricas entre torneos;
- 📸 fotografías de equipos;
- 🔔 notificaciones después de cada actualización.

---

# 📌 Estado del proyecto

### Clausura 2026

- ✅ Resultados
- ✅ Tabla de posiciones
- ✅ Goleadores
- ✅ Tarjetas amarillas
- ✅ Tarjetas rojas
- ✅ Gráficos por equipo
- ✅ Firestore
- ✅ GitHub Actions
- ✅ Streamlit
- 🧪 Asistente CLC en desarrollo

---

## 👨‍💻 Proyecto

Desarrollado para la gestión y publicación del **Campeonato Cambridge College Lima — Clausura 2026**.

⚽🏆
