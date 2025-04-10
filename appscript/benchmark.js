// Configuration
const CONFIG = {
  BATCH_SIZE: 10,           // Number of rows to process in each batch
  DELAY_MS: 2000,          // Delay between API calls in milliseconds
  MAX_RETRIES: 3,          // Maximum number of retries for timeout errors
  RETRY_DELAY_MS: 5000,    // Delay between retries (5 seconds)
  TRIGGER_NAME: "continuationTrigger",  // Name for our continuation trigger
  ADMIN_EMAILS: ["jroggeveen@g.harvard.edu"], // Administrator email
  DEFAULT_COLUMNS: {       // Default column assignments
    problemCol: "F",       // Column F for problem
    solutionCol: "G",      // Column G for solution
    paramsCol: "H",        // Column H for parameters
    statusCol: "I",        // Column I for status
    flashEquivCol: "J",    // Column J for Gemini 2.0 Flash equivalence
    flashThinkingEquivCol: "K", // Column K for Gemini 2.0 Flash Thinking equivalence
    outputStartCol: "L"    // Column L for detailed output start
  }
};

// Function to check if current user is an admin
function isAdmin() {
  const userEmail = Session.getActiveUser().getEmail();
  return CONFIG.ADMIN_EMAILS.includes(userEmail);
}

// Function to get the API base URL
function getApiBaseUrl() {
  const scriptProperties = PropertiesService.getScriptProperties();
  const apiUrl = scriptProperties.getProperty('API_BASE_URL');
  
  if (!apiUrl) {
    // If not set, show an error message to admins or return a default URL for non-admins
    if (isAdmin()) {
      const ui = SpreadsheetApp.getUi();
      ui.alert('API URL Not Configured', 'Please use the "Admin: Configure API URL" option to set up the API URL.', ui.ButtonSet.OK);
    }
    return null;
  }
  
  return apiUrl;
}

// Function to get sheet-specific column settings
function getSheetConfig(sheet) {
  const sheetId = sheet.getSheetId().toString();
  const documentProperties = PropertiesService.getDocumentProperties();
  const configJson = documentProperties.getProperty('sheet_config_' + sheetId);
  
  if (configJson) {
    try {
      return JSON.parse(configJson);
    } catch (e) {
      // If JSON parse fails, return default config
      return CONFIG.DEFAULT_COLUMNS;
    }
  }
  
  return CONFIG.DEFAULT_COLUMNS;
}

// Function to save sheet-specific column settings
function saveSheetConfig(sheet, config) {
  const sheetId = sheet.getSheetId().toString();
  const documentProperties = PropertiesService.getDocumentProperties();
  documentProperties.setProperty('sheet_config_' + sheetId, JSON.stringify(config));
}

// Function to render LaTeX to an image
/**
 * Renders LaTeX to an image.
 * 
 * @param {string} latex The LaTeX string to render
 * @return {string} URL of the rendered image or error message
 * @customfunction
 */
function RENDER_LATEX(latex) {
  if (!latex) return "";
  
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) return "Error: API URL not configured";
    
    const response = UrlFetchApp.fetch(apiBaseUrl + "/render", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({ latex: latex }),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    if (result.success && result.file_url) {
      return result.file_url;
    }
    return `Error: ${result.error || "Unknown error"}`;
  } catch (e) {
    return `Error: ${e.toString()}`;
  }
}

// Function to parse LaTeX with custom parameters
/**
 * Parses LaTeX with custom parameters.
 * 
 * @param {string} latex The LaTeX string to parse
 * @param {string} parameters Parameters for parsing (default = "")
 * @param {boolean} detailed Whether to return detailed output (default = true)
 * @return {Array} Parsing results as a 2D array
 * @customfunction
 */
function PARSE(latex, parameters = "", detailed = true) {
  if (!latex) return detailed ? [["", "", "", "", ""]] : [[false]];
  
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) return detailed ? [[false, "Error: API URL not configured", "", "", ""]] : [[false]];
    
    const response = UrlFetchApp.fetch(apiBaseUrl + "/parse", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({ 
        input: latex,
        parameters: parameters
      }),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    
    // Based on the ParsingResult class in parser.py, the API response will have:
    // - success: boolean indicating if parsing was successful
    // - error_message: string with any error message
    // - extracted_solutions: array of strings with the extracted LaTeX solutions
    // - intermediate_expressions: array of strings with the converted expressions
    // - sympy_expressions: array of strings with the SymPy expressions
    // - parameter_dict: object with parameter values
    // - evaluation_results: array of numeric results from evaluation

    // If detailed is false, just return the success value
    if (!detailed) {
      return [[result.success]];
    }
    
    // Otherwise return a 2D array that will display across multiple columns in the spreadsheet
    return [[
      result.success,                                                                // Success state
      result.error_message || "",                                                     // Error message
      Array.isArray(result.extracted_solutions) ? result.extracted_solutions.join("; ") : (result.extracted_solutions || ""), // LaTeX representation
      Array.isArray(result.intermediate_expressions) ? result.intermediate_expressions.join("; ") : (result.intermediate_expressions || ""), // Expression representation
      Array.isArray(result.evaluation_results) ? result.evaluation_results.join("; ") : (result.evaluation_results || "")     // Evaluated value
    ]];
  } catch (e) {
    return detailed ? [[false, `Error: ${e.toString()}`, "", "", ""]] : [[false]];
  }
}

// Wrapper function to call parseInput directly from spreadsheet
/**
 * Parses LaTeX with default parameter "$x$".
 * 
 * @param {string} latex The LaTeX string to parse
 * @param {boolean} detailed Whether to return detailed output (default = true)
 * @return {Array} Parsing results as a 2D array
 * @customfunction
 */
function PARSE_LATEX(latex, detailed = true) {
  return PARSE(latex, "$x$", detailed);
}

// Function to stop all triggers
function stopProcessing() {
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === "processMultipleRows") {
      ScriptApp.deleteTrigger(trigger);
    }
  }
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  sheet.getRange(sheetConfig.statusCol + "2").setValue("Processing stopped by user.");
}

// Shared function to process evaluation results
function processEvalResult(result, model, sheetConfig) {
  // Based on the EvaluationResult class in evaluator.py, the result has:
  // - success: boolean indicating if evaluation was successful
  // - error_message: string with any error message
  // - model_name: string with the name of the model used
  // - model_response: string with the raw model response
  // - is_equivalent: boolean indicating if solutions are equivalent
  // - solution: object containing the solution parsing result
  // - model: object containing the model parsing result
  
  try {
    // Extract the boolean value directly without using a ternary operator
    const isEquivalent = result.is_equivalent === true;
    
    // Prepare the detailed results (everything except the equivalence value)
    const detailedResults = [
      result.error_message || "",                                                // Error message
      result.model && result.model.evaluation_results ? 
        (Array.isArray(result.model.evaluation_results) ? 
          result.model.evaluation_results.join("; ") : 
          result.model.evaluation_results) : 
        "",                                                                     // Model evaluation results
      result.solution && result.solution.evaluation_results ? 
        (Array.isArray(result.solution.evaluation_results) ? 
          result.solution.evaluation_results.join("; ") : 
          result.solution.evaluation_results) : 
        "",                                                                     // Solution evaluation results
      result.model && result.model.extracted_solutions ? 
        (Array.isArray(result.model.extracted_solutions) ? 
          result.model.extracted_solutions.join("; ") : 
          result.model.extracted_solutions) : 
        "",                                                                     // Model latex
      result.model && result.model.intermediate_expressions ? 
        (Array.isArray(result.model.intermediate_expressions) ? 
          result.model.intermediate_expressions.join("; ") : 
          result.model.intermediate_expressions) : 
        "",                                                                     // Model expressions
      result.solution && result.solution.extracted_solutions ? 
        (Array.isArray(result.solution.extracted_solutions) ? 
          result.solution.extracted_solutions.join("; ") : 
          result.solution.extracted_solutions) : 
        "",                                                                     // Solution latex
      result.solution && result.solution.intermediate_expressions ? 
        (Array.isArray(result.solution.intermediate_expressions) ? 
          result.solution.intermediate_expressions.join("; ") : 
          result.solution.intermediate_expressions) : 
        "",                                                                     // Solution expressions
      result.model_response || ""                                                // Raw model response
    ];
    
    return {
      isEquivalent: isEquivalent,
      detailedResults: detailedResults
    };
  } catch (e) {
    return {
      isEquivalent: false,
      detailedResults: [
        "Error processing result: " + e.toString(),
        "", "", "", "", "", "",
        result.model_response || ""
      ]
    };
  }
}

// Shared function to call the evaluation API
function callEvalAPI(problem, solution, parameters, model) {
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) {
      return {
        success: false,
        error: "API URL not configured"
      };
    }
    
    const response = UrlFetchApp.fetch(apiBaseUrl + "/eval", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({
        input: problem,
        solution: solution,
        parameters: parameters || "",
        model: model
      }),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    
    return {
      success: true,
      result: result
    };
  } catch (e) {
    return {
      success: false,
      error: e.toString()
    };
  }
}

// Function to process a row with configurable columns
function processRowWithConfig() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Check if API URL is configured
  if (!getApiBaseUrl()) {
    if (isAdmin()) {
      const setupResponse = ui.alert(
        'API URL Not Configured',
        'The API URL is not configured. Would you like to configure it now?',
        ui.ButtonSet.YES_NO
      );
      
      if (setupResponse === ui.Button.YES) {
        adminConfigureApiUrl();
        // If they just set it up, continue, otherwise return
        if (!getApiBaseUrl()) return;
      } else {
        return;
      }
    } else {
      ui.alert('Error', 'The API URL is not configured. Please contact an administrator.', ui.ButtonSet.OK);
      return;
    }
  }
  
  // Get column assignments for this specific sheet
  const sheetConfig = getSheetConfig(sheet);
  
  // Create dialog for model selection
  const modelResponse = ui.prompt(
    'Model Selection',
    'Please select a model:\n' +
    '1. Gemini 2.0 Flash\n' +
    '2. Gemini 2.0 Flash Thinking',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (modelResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const modelChoice = modelResponse.getResponseText();
  let model;
  switch(modelChoice) {
    case "1":
      model = "Gemini 2.0 Flash";
      break;
    case "2":
      model = "Gemini 2.0 Flash Thinking";
      break;
    default:
      ui.alert('Invalid model selection. Please enter 1 or 2.');
      return;
  }
  
  // Only ask for the row number
  const response = ui.prompt(
    'Row Configuration',
    'Please enter the row number to process:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  // Parse row number
  const rowNum = response.getResponseText().trim();
  const row = parseInt(rowNum);
  if (isNaN(row) || row < 1) {
    ui.alert('Invalid row number');
    return;
  }
  
  // Update status
  sheet.getRange(sheetConfig.statusCol + row).setValue("Processing...");
  
  // Get values from specified columns
  const problem = sheet.getRange(sheetConfig.problemCol + row).getValue();
  const solution = sheet.getRange(sheetConfig.solutionCol + row).getValue();
  const parameters = sheet.getRange(sheetConfig.paramsCol + row).getValue();
  
  if (!problem || !solution) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: Empty input");
    return;
  }
  
  try {
    const apiResult = callEvalAPI(problem, solution, parameters, model);
    
    if (!apiResult.success) {
      sheet.getRange(sheetConfig.statusCol + row).setValue("Error: " + apiResult.error || "API call failed");
      return;
    }
    
    // Process the evaluation result
    const processedResult = processEvalResult(apiResult.result, model, sheetConfig);
    
    // Write the equivalence value to the appropriate column based on model
    let equivCol;
    if (model === "Gemini 2.0 Flash") {
      equivCol = sheetConfig.flashEquivCol;
    } else if (model === "Gemini 2.0 Flash Thinking") {
      equivCol = sheetConfig.flashThinkingEquivCol;
    } else {
      // Fallback to flash equivalence column
      equivCol = sheetConfig.flashEquivCol;
    }
    
    // Write the equivalence result to the model-specific column
    sheet.getRange(equivCol + row).setValue(processedResult.isEquivalent);
    
    // Write detailed results starting from the outputStartCol
    const outputCol = sheet.getRange(sheetConfig.outputStartCol + row).getColumn();
    const numColumns = processedResult.detailedResults.length;
    const outputRange = sheet.getRange(row, outputCol, 1, numColumns);
    outputRange.setValues([processedResult.detailedResults]);
    
    // Update status
    sheet.getRange(sheetConfig.statusCol + row).setValue("Complete");
  } catch (e) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: " + e.toString());
  }
}

// Function to process multiple rows automatically
function processMultipleRows() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Check if API URL is configured
  if (!getApiBaseUrl()) {
    if (isAdmin()) {
      const setupResponse = ui.alert(
        'API URL Not Configured',
        'The API URL is not configured. Would you like to configure it now?',
        ui.ButtonSet.YES_NO
      );
      
      if (setupResponse === ui.Button.YES) {
        adminConfigureApiUrl();
        // If they just set it up, continue, otherwise return
        if (!getApiBaseUrl()) return;
      } else {
        return;
      }
    } else {
      ui.alert('Error', 'The API URL is not configured. Please contact an administrator.', ui.ButtonSet.OK);
      return;
    }
  }
  
  // Get column assignments for this specific sheet
  const sheetConfig = getSheetConfig(sheet);
  
  // Create dialog for model selection
  const modelResponse = ui.prompt(
    'Model Selection',
    'Please select a model:\n' +
    '1. Gemini 2.0 Flash\n' +
    '2. Gemini 2.0 Flash Thinking',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (modelResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const modelChoice = modelResponse.getResponseText();
  let model;
  switch(modelChoice) {
    case "1":
      model = "Gemini 2.0 Flash";
      break;
    case "2":
      model = "Gemini 2.0 Flash Thinking";
      break;
    default:
      ui.alert('Invalid model selection. Please enter 1 or 2.');
      return;
  }
  
  // Only ask for start row
  const response = ui.prompt(
    'Automatic Processing Configuration',
    'Please enter the start row number:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const startRow = response.getResponseText().trim();
  const start = parseInt(startRow);
  
  if (isNaN(start) || start < 1) {
    ui.alert('Invalid start row number');
    return;
  }
  
  // Store configuration in Properties Service for trigger continuation
  const properties = PropertiesService.getScriptProperties();
  properties.setProperties({
    'startRow': start.toString(),
    'sheetId': sheet.getSheetId().toString(),
    'model': model
  });
  
  // Set up trigger for continuation
  const trigger = ScriptApp.newTrigger('processMultipleRows')
    .timeBased()
    .after(6 * 60 * 1000) // 6 minutes
    .create();
  
  // Process rows until we find an empty problem cell
  let currentRow = start;
  while (true) {
    // Update status
    sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Processing...");
    
    const problem = sheet.getRange(sheetConfig.problemCol + currentRow).getValue();
    if (!problem) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Stopped: Empty problem");
      break;
    }
    
    const solution = sheet.getRange(sheetConfig.solutionCol + currentRow).getValue();
    const parameters = sheet.getRange(sheetConfig.paramsCol + currentRow).getValue();
    
    if (!solution) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Skipped: Empty solution");
      currentRow++;
      continue;
    }
    
    try {
      const apiResult = callEvalAPI(problem, solution, parameters, model);
      
      if (!apiResult.success) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: " + apiResult.error || "API call failed");
        break;
      }
      
      // Process the evaluation result
      const processedResult = processEvalResult(apiResult.result, model, sheetConfig);
      
      // Write the equivalence value to the appropriate column based on model
      let equivCol;
      if (model === "Gemini 2.0 Flash") {
        equivCol = sheetConfig.flashEquivCol;
      } else if (model === "Gemini 2.0 Flash Thinking") {
        equivCol = sheetConfig.flashThinkingEquivCol;
      } else {
        // Fallback to flash equivalence column
        equivCol = sheetConfig.flashEquivCol;
      }
      
      // Write the equivalence result to the model-specific column
      sheet.getRange(equivCol + currentRow).setValue(processedResult.isEquivalent);
      
      // Write detailed results starting from the outputStartCol
      const outputCol = sheet.getRange(sheetConfig.outputStartCol + currentRow).getColumn();
      const numColumns = processedResult.detailedResults.length;
      const outputRange = sheet.getRange(currentRow, outputCol, 1, numColumns);
      outputRange.setValues([processedResult.detailedResults]);
      
      // Update status to Complete
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Complete");
      
      // Add delay between requests
      Utilities.sleep(CONFIG.DELAY_MS);
      currentRow++;
    } catch (e) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: " + e.toString());
      break;
    }
  }
  
  // Clean up trigger if we're done
  ScriptApp.deleteTrigger(trigger);
  properties.deleteAllProperties(); // Clear stored configuration
  
  // Add final status message to the first row
  sheet.getRange(sheetConfig.statusCol + start).setValue(`Completed rows ${start} to ${currentRow - 1}`);
}

// Admin function to set up column configuration for a specific sheet
function setupSheet() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Prompt for column configuration
  const response = ui.prompt(
    'Sheet Configuration (Admin Only)',
    `Configure column assignments for sheet "${sheet.getName()}":\n\n` +
    `Problem column (current: ${sheetConfig.problemCol}):\n` +
    `Solution column (current: ${sheetConfig.solutionCol}):\n` +
    `Parameters column (current: ${sheetConfig.paramsCol}):\n` +
    `Status column (current: ${sheetConfig.statusCol}):\n` +
    `Gemini 2.0 Flash equivalence column (current: ${sheetConfig.flashEquivCol}):\n` +
    `Gemini 2.0 Flash Thinking equivalence column (current: ${sheetConfig.flashThinkingEquivCol}):\n` +
    `Output start column (current: ${sheetConfig.outputStartCol}):\n\n` +
    `Enter column letters separated by commas (e.g., F,G,H,I,J,K,L):`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const columns = response.getResponseText().split(',').map(col => col.trim().toUpperCase());
  
  if (columns.length !== 7) {
    ui.alert('Error', 'Please provide exactly 7 column letters.', ui.ButtonSet.OK);
    return;
  }
  
  // Validate column letters
  const columnPattern = /^[A-Z]+$/;
  for (const col of columns) {
    if (!columnPattern.test(col)) {
      ui.alert('Error', `Invalid column letter: ${col}`, ui.ButtonSet.OK);
      return;
    }
  }
  
  // Save the configuration
  const newConfig = {
    problemCol: columns[0],
    solutionCol: columns[1],
    paramsCol: columns[2],
    statusCol: columns[3],
    flashEquivCol: columns[4],
    flashThinkingEquivCol: columns[5],
    outputStartCol: columns[6]
  };
  
  saveSheetConfig(sheet, newConfig);
  
  // Display configuration in the status column
  sheet.getRange(newConfig.statusCol + "1").setValue(`Columns: P=${columns[0]}, S=${columns[1]}, Params=${columns[2]}, Status=${columns[3]}, Flash=${columns[4]}, FlashT=${columns[5]}, Out=${columns[6]}`);
  
  ui.alert('Success', `Sheet "${sheet.getName()}" configured with columns:\n` +
    `Problem: ${newConfig.problemCol}\n` +
    `Solution: ${newConfig.solutionCol}\n` +
    `Parameters: ${newConfig.paramsCol}\n` +
    `Status: ${newConfig.statusCol}\n` +
    `Gemini 2.0 Flash equivalence: ${newConfig.flashEquivCol}\n` +
    `Gemini 2.0 Flash Thinking equivalence: ${newConfig.flashThinkingEquivCol}\n` +
    `Output: ${newConfig.outputStartCol}`, ui.ButtonSet.OK);
}

// Create custom menu when spreadsheet opens
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const menu = ui.createMenu('LLM Evaluation')
    .addItem('Process Single Row', 'processRowWithConfig')
    .addItem('Process Multiple Rows', 'processMultipleRows')
    .addItem('Stop Processing', 'stopProcessing');
  
  // Only show admin options to admins
  if (isAdmin()) {
    menu.addSeparator()
      .addItem('Admin: Configure API URL', 'adminConfigureApiUrl')
      .addItem('Admin: Setup Sheet Columns', 'setupSheet');
  }
  
  menu.addToUi();
}

// Function for admins to configure the API URL
function adminConfigureApiUrl() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const scriptProperties = PropertiesService.getScriptProperties();
  const currentUrl = scriptProperties.getProperty('API_BASE_URL') || '';
  
  const response = ui.prompt(
    'API Configuration (ADMIN ONLY)',
    `Current API URL: ${currentUrl}\n\nEnter new API Base URL:`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() === ui.Button.OK) {
    const newUrl = response.getResponseText().trim();
    if (newUrl) {
      scriptProperties.setProperty('API_BASE_URL', newUrl);
      ui.alert('API URL updated successfully!');
    } else {
      ui.alert('API URL cannot be empty.');
    }
  }
}
