const CONFIG = {
  SHEET_NAME: 'Resultados',
  CLOUD_RUN_URL: 'PEGAR_AQUI_URL_CLOUD_RUN',
};

function handleEdit(e) {
  const sheet = e.range.getSheet();
  if (sheet.getName() !== CONFIG.SHEET_NAME) return;
  if (e.range.getRow() === 1) return;

  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const idx = Object.fromEntries(headers.map((h, i) => [String(h).trim(), i + 1]));
  const required = ['Fecha', 'Goles_1', 'Goles_2'];
  if (!required.every(k => idx[k])) throw new Error('Faltan columnas requeridas en la Sheet.');

  const editedCol = e.range.getColumn();
  if (![idx['Goles_1'], idx['Goles_2']].includes(editedCol)) return;

  const fecha = Number(sheet.getRange(e.range.getRow(), idx['Fecha']).getValue());
  if (!Number.isInteger(fecha)) return;

  // Solo llama Cloud Run cuando TODA la fecha tiene los dos marcadores.
  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();
  const rowsFecha = values.filter(r => Number(r[idx['Fecha'] - 1]) === fecha);
  if (!rowsFecha.length) return;

  const complete = rowsFecha.every(r => {
    const g1 = r[idx['Goles_1'] - 1];
    const g2 = r[idx['Goles_2'] - 1];
    return isValidGoal_(g1) && isValidGoal_(g2);
  });
  if (!complete) return;

  callCloudRun_(fecha);
}

function isValidGoal_(value) {
  if (value === '' || value === null) return false;
  const n = Number(value);
  return Number.isInteger(n) && n >= 0;
}

function callCloudRun_(fecha) {
  const idToken = ScriptApp.getIdentityToken();
  const response = UrlFetchApp.fetch(CONFIG.CLOUD_RUN_URL + '/sync', {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({fecha: fecha}),
    headers: {'Authorization': 'Bearer ' + idToken},
    muteHttpExceptions: true,
  });

  const code = response.getResponseCode();
  if (code < 200 || code >= 300) {
    throw new Error('Cloud Run respondio ' + code + ': ' + response.getContentText());
  }
}

function installTrigger() {
  const ss = SpreadsheetApp.getActive();
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'handleEdit')
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger('handleEdit')
    .forSpreadsheet(ss)
    .onEdit()
    .create();
}

function logClientId() {
  const idToken = ScriptApp.getIdentityToken();
  const body = idToken.split('.')[1];
  const decoded = Utilities.newBlob(Utilities.base64DecodeWebSafe(body)).getDataAsString();
  Logger.log(JSON.parse(decoded).aud);
}
