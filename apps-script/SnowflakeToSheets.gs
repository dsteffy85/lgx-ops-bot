/**
 * Conduit: Snowflake → Google Sheets (Autonomous)
 * No external libraries needed.
 * 
 * Setup:
 *   1. Script Properties → SNOWFLAKE_KEY_PEM = full PEM private key (with headers)
 *   2. Run testKeyLoading() → testConnection() → createDailyTrigger()
 */

var CONFIG = {
  SNOWFLAKE_ACCOUNT: 'SQUARE',
  SNOWFLAKE_QUALIFIED_USER: 'SQUARE.LGX_OPS_BOT',
  SNOWFLAKE_PUBLIC_KEY_FP: 'SHA256:4JAOQb6kZIHNHyXB36pqvtIrRw8PhdZni8qakjiF54E=',
  SNOWFLAKE_API_URL: 'https://square.snowflakecomputing.com/api/v2/statements',
  SNOWFLAKE_WAREHOUSE: 'ETL__MEDIUM',
  SNOWFLAKE_ROLE: 'LGX_OPS_BOT__SNOWFLAKE__ADMIN',
  NA_SPREADSHEET_ID: '1repdjFbPTSnahq9xgpaBxefDAsvLtwvxp-WafEuSN78',
  NA_SHEET_NAME: 'NA Data',
  NA_LOOKBACK_DAYS: 30,
};

// ============================================================================
// JWT AUTH — tries multiple signing methods
// ============================================================================

function generateSnowflakeJWT_() {
  var props = PropertiesService.getScriptProperties();
  var keyData = props.getProperty('SNOWFLAKE_KEY_PEM');
  if (!keyData) throw new Error('SNOWFLAKE_KEY_PEM not set in Script Properties.');
  
  var formats = getKeyFormats_(keyData);
  var now = Math.floor(Date.now() / 1000);
  
  var headerB64 = b64url_(JSON.stringify({alg: 'RS256', typ: 'JWT'}));
  var payloadB64 = b64url_(JSON.stringify({
    iss: CONFIG.SNOWFLAKE_QUALIFIED_USER + '.' + CONFIG.SNOWFLAKE_PUBLIC_KEY_FP,
    sub: CONFIG.SNOWFLAKE_QUALIFIED_USER,
    iat: now,
    exp: now + 3600
  }));
  
  var signingInput = headerB64 + '.' + payloadB64;
  var inputBytes = Utilities.newBlob(signingInput, 'UTF-8').getBytes();
  
  // Try all methods until one works
  var methods = [
    function() { return Utilities.computeRsaSignature(Utilities.RsaAlgorithm.RSA_SHA_256, inputBytes, formats.pem); },
    function() { return Utilities.computeRsaSha256Signature(inputBytes, formats.pem); },
    function() { return Utilities.computeRsaSignature(Utilities.RsaAlgorithm.RSA_SHA_256, inputBytes, formats.derBytes); },
    function() { return Utilities.computeRsaSha256Signature(inputBytes, formats.derBytes); }
  ];
  
  for (var i = 0; i < methods.length; i++) {
    try {
      var sig = methods[i]();
      return signingInput + '.' + Utilities.base64EncodeWebSafe(sig).replace(/=+$/, '');
    } catch (e) { /* try next */ }
  }
  
  throw new Error('All signing methods failed.');
}

/**
 * Parse the key property into multiple formats for signing attempts.
 * Handles both: raw base64 body OR full PEM with headers.
 */
function getKeyFormats_(keyData) {
  var body, pem;
  
  if (keyData.indexOf('BEGIN') >= 0) {
    // Full PEM was stored — extract body
    body = keyData
      .replace(/-----BEGIN[^-]*-----/g, '')
      .replace(/-----END[^-]*-----/g, '')
      .replace(/[\r\n\s]/g, '');
    // Reconstruct clean PEM with proper line breaks
    var lines = [];
    for (var i = 0; i < body.length; i += 64) {
      lines.push(body.substring(i, Math.min(i + 64, body.length)));
    }
    pem = '-----BEGIN PRIVATE KEY-----\n' + lines.join('\n') + '\n-----END PRIVATE KEY-----';
  } else {
    // Raw base64 body was stored
    body = keyData.replace(/[\r\n\s]/g, '');
    var lines = [];
    for (var i = 0; i < body.length; i += 64) {
      lines.push(body.substring(i, Math.min(i + 64, body.length)));
    }
    pem = '-----BEGIN PRIVATE KEY-----\n' + lines.join('\n') + '\n-----END PRIVATE KEY-----';
  }
  
  var derBytes = Utilities.base64Decode(body);
  
  return { body: body, pem: pem, derBytes: derBytes };
}

function b64url_(str) {
  return Utilities.base64EncodeWebSafe(
    Utilities.newBlob(str, 'UTF-8').getBytes()
  ).replace(/=+$/, '');
}

// ============================================================================
// SNOWFLAKE REST API
// ============================================================================

function querySnowflake_(sql, database, schema) {
  var jwt = generateSnowflakeJWT_();
  
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      'Authorization': 'Bearer ' + jwt,
      'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT',
      'Accept': 'application/json'
    },
    'payload': JSON.stringify({
      'statement': sql, 'timeout': 300,
      'database': database || 'LGX_OPS_BOT',
      'schema': schema || 'WIGEON',
      'warehouse': CONFIG.SNOWFLAKE_WAREHOUSE,
      'role': CONFIG.SNOWFLAKE_ROLE
    }),
    'muteHttpExceptions': true
  };
  
  Logger.log('Querying: ' + sql.substring(0, 100) + '...');
  var response = UrlFetchApp.fetch(CONFIG.SNOWFLAKE_API_URL, options);
  var code = response.getResponseCode();
  var text = response.getContentText();
  
  if (code !== 200) {
    Logger.log('Error: ' + text.substring(0, 500));
    throw new Error('Snowflake API (' + code + '): ' + text.substring(0, 200));
  }
  
  var body = JSON.parse(text);
  if (body.code === '333334') return pollForResults_(body.statementHandle, jwt);
  
  var columns = body.resultSetMetaData.rowType.map(function(c) { return c.name; });
  Logger.log('Returned ' + (body.data || []).length + ' rows');
  return { columns: columns, data: body.data || [] };
}

function pollForResults_(handle, jwt) {
  for (var i = 0; i < 60; i++) {
    Utilities.sleep(5000);
    var r = UrlFetchApp.fetch(CONFIG.SNOWFLAKE_API_URL + '/' + handle, {
      'method': 'get',
      'headers': { 'Authorization': 'Bearer ' + jwt, 'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT', 'Accept': 'application/json' },
      'muteHttpExceptions': true
    });
    var b = JSON.parse(r.getContentText());
    if (b.code !== '333334') {
      return { columns: b.resultSetMetaData.rowType.map(function(c) { return c.name; }), data: b.data || [] };
    }
  }
  throw new Error('Query timed out');
}

// ============================================================================
// NA INBOUND GR REFRESH
// ============================================================================

function refreshNAInboundGR() {
  Logger.log('=== Conduit: NA Inbound GR Refresh ===');
  Logger.log('Started: ' + new Date().toISOString());
  
  try {
    var sql = 'SELECT ADJUSTMENT_DATE, FACILITY_ID, ITEM_CODE, ITEM_DESCRIPTION, ' +
      'PRODUCT_NAME, AVL_QUANTITY, UNAVL_QUANTITY ' +
      'FROM LGX_OPS_BOT.WIGEON.NA_INBOUND_GR ' +
      "WHERE ADJUSTMENT_DATE >= DATEADD('day', -" + CONFIG.NA_LOOKBACK_DAYS + ", CURRENT_DATE()) " +
      'ORDER BY ADJUSTMENT_DATE DESC, FACILITY_ID, ITEM_CODE';
    
    var result = querySnowflake_(sql, 'LGX_OPS_BOT', 'WIGEON');
    if (result.data.length === 0) { Logger.log('No data'); return; }
    
    var ss = SpreadsheetApp.openById(CONFIG.NA_SPREADSHEET_ID);
    var sheet = ss.getSheetByName(CONFIG.NA_SHEET_NAME);
    if (!sheet) throw new Error('Sheet not found');
    
    var lastRow = sheet.getLastRow();
    if (lastRow > 1) sheet.getRange(2, 1, lastRow - 1, 9).clearContent();
    
    sheet.getRange(1, 1, 1, 9).setValues([['Adjustment Date', 'Facility ID', 'Item Code',
      'Item Description', 'Product Name', 'AVL Quantity', 'UNAVL Quantity', '', 'Last Updated']]);
    
    var rows = result.data.map(function(r) {
      return [r[0], r[1], r[2], r[3], r[4], Number(r[5]) || 0, Number(r[6]) || 0, '', ''];
    });
    
    sheet.getRange(2, 1, rows.length, 9).setValues(rows);
    sheet.getRange(2, 9).setValue(
      Utilities.formatDate(new Date(), 'America/Los_Angeles', 'yyyy-MM-dd HH:mm') + ' PST');
    
    Logger.log('Wrote ' + rows.length + ' rows');
    updateCVUIMCIMUTab_(ss, result.data);
    Logger.log('Done: ' + new Date().toISOString());
    
  } catch (e) {
    Logger.log('ERROR: ' + e.message + '\n' + e.stack);
    try { MailApp.sendEmail(Session.getActiveUser().getEmail(),
      'Conduit: NA Inbound GR Failed', e.message + '\n' + e.stack); } catch(x) {}
  }
}

function updateCVUIMCIMUTab_(ss, data) {
  var sheet = ss.getSheetByName('CVU/IMC/IMU');
  if (!sheet) { Logger.log('CVU/IMC/IMU not found'); return; }
  var lastRow = sheet.getLastRow();
  if (lastRow > 1) sheet.getRange(2, 1, lastRow - 1, 8).clearContent();
  sheet.getRange(1, 1, 1, 8).setValues([['Adjustment Date', 'Facility ID', 'Item Code',
    'Item Description', 'Product Name', 'AVL Quantity', 'UNAVL Quantity', 'V+/-']]);
  var rows = data.map(function(r) {
    var a = Number(r[5]) || 0, u = Number(r[6]) || 0;
    return [r[0], r[1], r[2], r[3], r[4], a, u, a + u];
  });
  if (rows.length > 0) sheet.getRange(2, 1, rows.length, 8).setValues(rows);
  Logger.log('CVU/IMC/IMU: ' + rows.length + ' rows');
}

// ============================================================================
// SETUP & TEST
// ============================================================================

function testKeyLoading() {
  var props = PropertiesService.getScriptProperties();
  Logger.log('Properties: ' + JSON.stringify(props.getKeys()));
  
  var keyData = props.getProperty('SNOWFLAKE_KEY_PEM');
  if (!keyData) {
    Logger.log('ERROR: SNOWFLAKE_KEY_PEM not found!');
    return;
  }
  
  Logger.log('Raw property length: ' + keyData.length + ' chars');
  Logger.log('Starts with: ' + keyData.substring(0, 30) + '...');
  
  // Get the key in all formats for testing
  var formats = getKeyFormats_(keyData);
  Logger.log('PEM string length: ' + formats.pem.length);
  Logger.log('PEM starts with: ' + formats.pem.substring(0, 40));
  Logger.log('Key body length: ' + formats.body.length);
  Logger.log('DER bytes: ' + formats.derBytes.length);
  
  var testData = Utilities.newBlob('test-signing-input', 'UTF-8').getBytes();
  
  // Method 1: computeRsaSignature with reconstructed PEM string
  try {
    var sig = Utilities.computeRsaSignature(Utilities.RsaAlgorithm.RSA_SHA_256, testData, formats.pem);
    Logger.log('Method 1 SUCCESS (computeRsaSignature + PEM string): ' + sig.length + ' bytes');
  } catch (e) { Logger.log('Method 1 FAILED: ' + e.message); }
  
  // Method 2: computeRsaSha256Signature with reconstructed PEM string
  try {
    var sig = Utilities.computeRsaSha256Signature(testData, formats.pem);
    Logger.log('Method 2 SUCCESS (computeRsaSha256Signature + PEM string): ' + sig.length + ' bytes');
  } catch (e) { Logger.log('Method 2 FAILED: ' + e.message); }
  
  // Method 3: computeRsaSignature with DER bytes
  try {
    var sig = Utilities.computeRsaSignature(Utilities.RsaAlgorithm.RSA_SHA_256, testData, formats.derBytes);
    Logger.log('Method 3 SUCCESS (computeRsaSignature + DER bytes): ' + sig.length + ' bytes');
  } catch (e) { Logger.log('Method 3 FAILED: ' + e.message); }
  
  // Method 4: computeRsaSha256Signature with DER bytes
  try {
    var sig = Utilities.computeRsaSha256Signature(testData, formats.derBytes);
    Logger.log('Method 4 SUCCESS (computeRsaSha256Signature + DER bytes): ' + sig.length + ' bytes');
  } catch (e) { Logger.log('Method 4 FAILED: ' + e.message); }
  
  // Method 5: computeRsaSignature with PKCS1 PEM string
  try {
    var pkcs1Pem = '-----BEGIN RSA PRIVATE KEY-----\n' + formats.body + '\n-----END RSA PRIVATE KEY-----';
    var sig = Utilities.computeRsaSignature(Utilities.RsaAlgorithm.RSA_SHA_256, testData, pkcs1Pem);
    Logger.log('Method 5 SUCCESS (computeRsaSignature + PKCS1 PEM): ' + sig.length + ' bytes');
  } catch (e) { Logger.log('Method 5 FAILED: ' + e.message); }
}

function testConnection() {
  // Try multiple account/user combos
  var combos = [
    {account: 'SQUARE', user: 'SQUARE.LGX_OPS_BOT', url: 'https://square.snowflakecomputing.com/api/v2/statements'},
    {account: 'SQUARE', user: 'SQUARE.LGX_OPS_BOT@SQUAREUP.COM', url: 'https://square.snowflakecomputing.com/api/v2/statements'},
    {account: 'SQUAREINC-SQUARE', user: 'SQUAREINC-SQUARE.LGX_OPS_BOT', url: 'https://squareinc-square.snowflakecomputing.com/api/v2/statements'},
  ];
  
  for (var i = 0; i < combos.length; i++) {
    var c = combos[i];
    Logger.log('--- Trying combo ' + (i+1) + ': user=' + c.user + ', url=' + c.url.split('/')[2]);
    try {
      var jwt = generateJWTWithUser_(c.user);
      var options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': {
          'Authorization': 'Bearer ' + jwt,
          'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT',
          'Accept': 'application/json'
        },
        'payload': JSON.stringify({
          'statement': 'SELECT CURRENT_TIMESTAMP() AS ts, CURRENT_USER() AS usr',
          'timeout': 30,
          'warehouse': CONFIG.SNOWFLAKE_WAREHOUSE,
          'role': CONFIG.SNOWFLAKE_ROLE
        }),
        'muteHttpExceptions': true
      };
      var response = UrlFetchApp.fetch(c.url, options);
      var code = response.getResponseCode();
      if (code === 200) {
        var body = JSON.parse(response.getContentText());
        Logger.log('SUCCESS! User: ' + body.data[0][1]);
        Logger.log('Winning combo: user=' + c.user + ', url=' + c.url);
        return true;
      } else {
        var err = response.getContentText().substring(0, 100);
        Logger.log('Failed (' + code + '): ' + err);
      }
    } catch (e) {
      Logger.log('Error: ' + e.message);
    }
  }
  Logger.log('All combos failed.');
  return false;
}

function generateJWTWithUser_(qualifiedUser) {
  var props = PropertiesService.getScriptProperties();
  var keyData = props.getProperty('SNOWFLAKE_KEY_PEM');
  var formats = getKeyFormats_(keyData);
  var now = Math.floor(Date.now() / 1000);
  
  var headerB64 = b64url_(JSON.stringify({alg: 'RS256', typ: 'JWT'}));
  var payloadB64 = b64url_(JSON.stringify({
    iss: qualifiedUser + '.' + CONFIG.SNOWFLAKE_PUBLIC_KEY_FP,
    sub: qualifiedUser,
    iat: now,
    exp: now + 3600
  }));
  
  var signingInput = headerB64 + '.' + payloadB64;
  var inputBytes = Utilities.newBlob(signingInput, 'UTF-8').getBytes();
  var sig = Utilities.computeRsaSignature(Utilities.RsaAlgorithm.RSA_SHA_256, inputBytes, formats.pem);
  return signingInput + '.' + Utilities.base64EncodeWebSafe(sig).replace(/=+$/, '');
}

function createDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(function(t) {
    if (t.getHandlerFunction() === 'refreshNAInboundGR') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('refreshNAInboundGR')
    .timeBased().atHour(5).everyDays(1).inTimezone('America/Los_Angeles').create();
  Logger.log('Trigger set: refreshNAInboundGR daily at 5 AM PST');
}
