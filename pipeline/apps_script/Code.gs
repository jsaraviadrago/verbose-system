const CONFIG = {
  SHEET_NAME: 'Resultados',

  // Reemplazar después del primer deploy con la URL real de Cloud Run.
  // Ejemplo:
  // https://cambridge-results-2026-xxxxx-uc.a.run.app
  CLOUD_RUN_URL: 'PEGAR_AQUI_URL_CLOUD_RUN',
};


/**
 * Instala el trigger onEdit una sola vez.
 * Ejecutar manualmente desde Apps Script y autorizar permisos.
 */
function installTrigger() {
  const ss = SpreadsheetApp.getActive();

  // Evita duplicar triggers si se ejecuta más de una vez.
  ScriptApp.getProjectTriggers()
    .filter(trigger => trigger.getHandlerFunction() === 'handleEdit')
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));

  ScriptApp.newTrigger('handleEdit')
    .forSpreadsheet(ss)
    .onEdit()
    .create();

  console.log('Trigger instalado correctamente.');
}


/**
 * Trigger principal.
 *
 * Solo actúa cuando se modifican columnas Goles_1 o Goles_2.
 * Soporta:
 * - edición de una celda;
 * - pegar varias celdas;
 * - pegar varias filas;
 * - modificar varias fechas en una misma operación.
 *
 * Cloud Run solo se invoca cuando TODOS los partidos
 * de una fecha tienen ambos marcadores válidos.
 */
function handleEdit(e) {
  if (!e || !e.range) return;

  const sheet = e.range.getSheet();

  if (sheet.getName() !== CONFIG.SHEET_NAME) {
    return;
  }

  // Ignorar ediciones en encabezados.
  if (e.range.getRow() === 1) {
    return;
  }

  const headers = sheet
    .getRange(1, 1, 1, sheet.getLastColumn())
    .getValues()[0]
    .map(value => String(value).trim());

  const idx = Object.fromEntries(
    headers.map((header, i) => [header, i + 1])
  );

  const required = [
    'Fecha',
    'Goles_1',
    'Goles_2',
  ];

  if (!required.every(column => idx[column])) {
    throw new Error(
      'Faltan columnas requeridas en la Sheet: ' +
      required.join(', ')
    );
  }

  /*
   * Comprobar si el rango editado toca Goles_1 o Goles_2.
   * Esto permite pegar múltiples columnas/filas.
   */
  const firstEditedColumn = e.range.getColumn();
  const lastEditedColumn =
    firstEditedColumn + e.range.getNumColumns() - 1;

  const goalColumns = [
    idx['Goles_1'],
    idx['Goles_2'],
  ];

  const touchesGoals = goalColumns.some(
    column =>
      column >= firstEditedColumn &&
      column <= lastEditedColumn
  );

  if (!touchesGoals) {
    return;
  }

  /*
   * Detectar todas las fechas afectadas por la edición.
   * Si se pegaron resultados de varias filas,
   * una fecha se procesa una sola vez.
   */
  const firstRow = e.range.getRow();
  const lastRow =
    firstRow + e.range.getNumRows() - 1;

  const fechas = new Set();

  for (let row = firstRow; row <= lastRow; row++) {
    const fecha = Number(
      sheet.getRange(row, idx['Fecha']).getValue()
    );

    if (Number.isInteger(fecha) && fecha > 0) {
      fechas.add(fecha);
    }
  }

  if (fechas.size === 0) {
    return;
  }

  /*
   * Leer toda la tabla una sola vez.
   */
  const lastSheetRow = sheet.getLastRow();

  if (lastSheetRow < 2) {
    return;
  }

  const values = sheet
    .getRange(
      2,
      1,
      lastSheetRow - 1,
      sheet.getLastColumn()
    )
    .getValues();

  /*
   * Revisar cada fecha afectada.
   */
  fechas.forEach(fecha => {
    const rowsFecha = values.filter(
      row =>
        Number(row[idx['Fecha'] - 1]) === fecha
    );

    if (rowsFecha.length === 0) {
      return;
    }

    const complete = rowsFecha.every(row => {
      const goles1 =
        row[idx['Goles_1'] - 1];

      const goles2 =
        row[idx['Goles_2'] - 1];

      return (
        isValidGoal_(goles1) &&
        isValidGoal_(goles2)
      );
    });

    /*
     * Si falta aunque sea un marcador,
     * no se llama a Cloud Run.
     */
    if (!complete) {
      console.log(
        `Fecha ${fecha} incompleta. No se sincroniza.`
      );
      return;
    }

    console.log(
      `Fecha ${fecha} completa. Iniciando sincronización.`
    );

    callCloudRun_(fecha);
  });
}


/**
 * Un marcador válido:
 * - no está vacío;
 * - es entero;
 * - es >= 0.
 *
 * 0 es válido.
 */
function isValidGoal_(value) {
  if (
    value === '' ||
    value === null ||
    typeof value === 'undefined'
  ) {
    return false;
  }

  const n = Number(value);

  return (
    Number.isInteger(n) &&
    n >= 0
  );
}


/**
 * Llama al endpoint privado /sync de Cloud Run.
 */
function callCloudRun_(fecha) {
  validateCloudRunUrl_();

  const idToken =
    ScriptApp.getIdentityToken();

  if (!idToken) {
    throw new Error(
      'No se pudo obtener identity token. ' +
      'Revisa appsscript.json y sus OAuth scopes.'
    );
  }

  const url =
    CONFIG.CLOUD_RUN_URL.replace(/\/+$/, '') +
    '/sync';

  const response = UrlFetchApp.fetch(
    url,
    {
      method: 'post',

      contentType: 'application/json',

      payload: JSON.stringify({
        fecha: fecha,
      }),

      headers: {
        Authorization:
          'Bearer ' + idToken,
      },

      muteHttpExceptions: true,
    }
  );

  const code =
    response.getResponseCode();

  const body =
    response.getContentText();

  console.log(
    `Cloud Run Fecha ${fecha}: HTTP ${code}`
  );

  console.log(body);

  if (code < 200 || code >= 300) {
    throw new Error(
      `Cloud Run respondió HTTP ${code}: ${body}`
    );
  }
}


/**
 * Evita ejecutar accidentalmente con el placeholder.
 */
function validateCloudRunUrl_() {
  const url = String(
    CONFIG.CLOUD_RUN_URL || ''
  ).trim();

  if (
    !url ||
    url.includes('PEGAR_AQUI') ||
    !url.startsWith('https://')
  ) {
    throw new Error(
      'CONFIG.CLOUD_RUN_URL todavía no está configurado.'
    );
  }
}


/**
 * Ejecutar manualmente para obtener el OAuth Client ID
 * del proyecto de Apps Script.
 *
 * Se usa después como custom audience en Cloud Run.
 */
function logClientId() {
  const token =
    ScriptApp.getIdentityToken();

  if (!token) {
    throw new Error(
      'No se pudo generar identity token. ' +
      'Revisa los OAuth scopes de appsscript.json.'
    );
  }

  const payloadPart =
    token.split('.')[1];

  const normalized =
    payloadPart
      .replace(/-/g, '+')
      .replace(/_/g, '/');

  const decoded =
    Utilities.newBlob(
      Utilities.base64Decode(
        normalized
      )
    ).getDataAsString();

  const payload =
    JSON.parse(decoded);

  console.log(
    'Identity token payload:'
  );

  console.log(
    JSON.stringify(
      payload,
      null,
      2
    )
  );

  console.log(
    'Usa el valor de aud como custom audience de Cloud Run.'
  );
}


/**
 * Prueba manual opcional.
 *
 * Cambia la fecha si quieres probar otra.
 * No depende de una edición de la Sheet.
 */
function testSync() {
  callCloudRun_(1);
}