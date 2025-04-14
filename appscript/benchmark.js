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
    flash25ThinkingEquivCol: "L", // Column L for Gemini 2.5 Flash Thinking equivalence
    outputStartCol: "M"    // Column M for detailed output start
  }
};

// Function to check if current user is an admin
function isAdmin() {
  try {
    const userEmail = Session.getActiveUser().getEmail();
    return CONFIG.ADMIN_EMAILS.includes(userEmail);
  } catch (e) {
    console.log("Could not get active user: " + e.toString());
    return false;
  }
}

// Function to get the API base URL
function getApiBaseUrl() {
  const scriptProperties = PropertiesService.getScriptProperties();
  const apiUrl = scriptProperties.getProperty('API_BASE_URL');
  
  if (!apiUrl) {
    try {
      // Only try to check admin status if we can get the active user
      if (isAdmin()) {
        const ui = SpreadsheetApp.getUi();
        ui.alert('API URL Not Configured', 'Please use the "Admin: Configure API URL" option to set up the API URL.', ui.ButtonSet.OK);
      }
    } catch (e) {
      // If we can't get the active user, just return null
      console.log("Could not check admin status: " + e.toString());
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
 * Renders LaTeX to an image URL.
 * 
 * @param {string} latex The LaTeX string to render
 * @return {string} URL of the rendered image or error message
 * @customfunction
 */
function RENDER_LATEX(latex) {
  if (!latex) return "";
  
  try {
    // Ensure the API is configured
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) {
      console.error("API URL not configured");
      return "Error: API URL not configured. Please contact an administrator.";
    }
    
    // Validate the LaTeX input
    if (typeof latex !== 'string') {
      console.error("Invalid LaTeX input type");
      return "Error: Invalid LaTeX input. Must be a string.";
    }
    
    // Make the API request
    const response = UrlFetchApp.fetch(apiBaseUrl + "/render", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({ latex: latex }),
      muteHttpExceptions: true,
      timeout: 30000 // 30 second timeout
    });
    
    // Parse the response
    const result = JSON.parse(response.getContentText());
    
    // Check for success
    if (result.success && result.file_url) {
      return result.file_url;
    }
    
    // Handle specific error cases
    if (result.error) {
      console.error("API Error: " + result.error);
      return "Error: " + result.error;
    }
    
    // Unknown error
    console.error("Unknown API response: " + JSON.stringify(result));
    return "Error: Unknown error occurred";
    
  } catch (e) {
    console.error("RENDER_LATEX Error: " + e.toString());
    return "Error: " + e.toString();
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

// Function to clear output cells for a specific row
function clearOutputCells(sheet, row, sheetConfig, model) {
  // Clear only the equivalence cell for the specific model
  if (model === "Gemini 2.0 Flash") {
    sheet.getRange(sheetConfig.flashEquivCol + row).clearContent();
  } else if (model === "Gemini 2.0 Flash Thinking") {
    sheet.getRange(sheetConfig.flashThinkingEquivCol + row).clearContent();
  } else if (model === "Gemini 2.5 Flash Thinking") {
    sheet.getRange(sheetConfig.flash25ThinkingEquivCol + row).clearContent();
  }
  
  // Clear the detailed output cells
  const outputCol = sheet.getRange(sheetConfig.outputStartCol + row).getColumn();
  const numColumns = 8; // Number of detailed output columns
  sheet.getRange(row, outputCol, 1, numColumns).clearContent();
}

// Function to get enabled models for a sheet
function getEnabledModels(sheet) {
  const sheetId = sheet.getSheetId().toString();
  const documentProperties = PropertiesService.getDocumentProperties();
  const enabledModels = documentProperties.getProperty('enabled_models_' + sheetId);
  
  if (enabledModels) {
    return JSON.parse(enabledModels);
  }
  
  // Default to all models enabled
  return {
    "Gemini 2.0 Flash": true,
    "Gemini 2.0 Flash Thinking": true,
    "Gemini 2.5 Flash Thinking": false
  };
}

// Function to set enabled models for a sheet
function setEnabledModels(sheet, models) {
  const sheetId = sheet.getSheetId().toString();
  const documentProperties = PropertiesService.getDocumentProperties();
  documentProperties.setProperty('enabled_models_' + sheetId, JSON.stringify(models));
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
  
  // Get enabled models
  const enabledModels = getEnabledModels(sheet);
  const availableModels = Object.entries(enabledModels)
    .filter(([_, enabled]) => enabled)
    .map(([name]) => name);
  
  if (availableModels.length === 0) {
    ui.alert('Error', 'No models are currently enabled. Please contact an administrator.', ui.ButtonSet.OK);
    return;
  }
  
  // Create dialog for model selection
  const modelOptions = availableModels.map((model, index) => `${index + 1}. ${model}`).join('\n');
  const modelResponse = ui.prompt(
    'Model Selection',
    'Please select a model:\n' + modelOptions,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (modelResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const modelChoice = modelResponse.getResponseText();
  const modelIndex = parseInt(modelChoice) - 1;
  
  if (isNaN(modelIndex) || modelIndex < 0 || modelIndex >= availableModels.length) {
    ui.alert('Invalid model selection. Please enter a number between 1 and ' + availableModels.length);
    return;
  }
  
  const model = availableModels[modelIndex];
  
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
  
  // Clear output cells before processing
  clearOutputCells(sheet, row, sheetConfig, model);
  
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
    } else if (model === "Gemini 2.5 Flash Thinking") {
      equivCol = sheetConfig.flash25ThinkingEquivCol;
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
    '2. Gemini 2.0 Flash Thinking\n' +
    '3. Gemini 2.5 Flash Thinking',
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
    case "3":
      model = "Gemini 2.5 Flash Thinking";
      break;
    default:
      ui.alert('Invalid model selection. Please enter 1, 2, or 3.');
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
      } else if (model === "Gemini 2.5 Flash Thinking") {
        equivCol = sheetConfig.flash25ThinkingEquivCol;
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
    `Gemini 2.5 Flash Thinking equivalence column (current: ${sheetConfig.flash25ThinkingEquivCol}):\n` +
    `Output start column (current: ${sheetConfig.outputStartCol}):\n\n` +
    `Enter column letters separated by commas (e.g., F,G,H,I,J,K,L,M):`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const columns = response.getResponseText().split(',').map(col => col.trim().toUpperCase());
  
  if (columns.length !== 8) {
    ui.alert('Error', 'Please provide exactly 8 column letters.', ui.ButtonSet.OK);
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
    flash25ThinkingEquivCol: columns[6],
    outputStartCol: columns[7]
  };
  
  saveSheetConfig(sheet, newConfig);
  
  ui.alert('Success', `Sheet "${sheet.getName()}" configured with columns:\n` +
    `Problem: ${newConfig.problemCol}\n` +
    `Solution: ${newConfig.solutionCol}\n` +
    `Parameters: ${newConfig.paramsCol}\n` +
    `Status: ${newConfig.statusCol}\n` +
    `Gemini 2.0 Flash equivalence: ${newConfig.flashEquivCol}\n` +
    `Gemini 2.0 Flash Thinking equivalence: ${newConfig.flashThinkingEquivCol}\n` +
    `Gemini 2.5 Flash Thinking equivalence: ${newConfig.flash25ThinkingEquivCol}\n` +
    `Output: ${newConfig.outputStartCol}`, ui.ButtonSet.OK);
}

// Function to register custom functions
function registerCustomFunctions() {
  try {
    // Register RENDER_LATEX
    const renderLatexFunction = {
      name: 'RENDER_LATEX',
      description: 'Renders LaTeX to an image URL',
      parameters: [
        {
          name: 'latex',
          description: 'The LaTeX string to render',
          type: 'string'
        }
      ]
    };
    
    // Register PARSE
    const parseFunction = {
      name: 'PARSE',
      description: 'Parses LaTeX with custom parameters',
      parameters: [
        {
          name: 'latex',
          description: 'The LaTeX string to parse',
          type: 'string'
        },
        {
          name: 'parameters',
          description: 'Parameters for parsing',
          type: 'string',
          optional: true
        },
        {
          name: 'detailed',
          description: 'Whether to return detailed output',
          type: 'boolean',
          optional: true
        }
      ]
    };
    
    // Register PARSE_LATEX
    const parseLatexFunction = {
      name: 'PARSE_LATEX',
      description: 'Parses LaTeX with default parameters',
      parameters: [
        {
          name: 'latex',
          description: 'The LaTeX string to parse',
          type: 'string'
        },
        {
          name: 'detailed',
          description: 'Whether to return detailed output',
          type: 'boolean',
          optional: true
        }
      ]
    };
    
    // Register the functions
    const ui = SpreadsheetApp.getUi();
    try {
      ui.alert('Registering custom functions...');
      SpreadsheetApp.getActive().getCustomFunctions().register(renderLatexFunction);
      SpreadsheetApp.getActive().getCustomFunctions().register(parseFunction);
      SpreadsheetApp.getActive().getCustomFunctions().register(parseLatexFunction);
      ui.alert('Custom functions registered successfully!');
    } catch (e) {
      console.error('Error registering custom functions: ' + e.toString());
    }
  } catch (e) {
    console.error('Error in registerCustomFunctions: ' + e.toString());
  }
}

// Update the onOpen function to register custom functions
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
      .addItem('Admin: Setup Sheet Columns', 'setupSheet')
      .addItem('Admin: Toggle Model Availability', 'toggleModelAvailability')
      .addItem('Admin: Register Functions', 'registerCustomFunctions');
  }
  
  menu.addToUi();
  
  // Register custom functions on open
  registerCustomFunctions();
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

// Admin function to toggle model availability
function toggleModelAvailability() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const enabledModels = getEnabledModels(sheet);
  
  // Create dialog for model selection
  const modelOptions = Object.entries(enabledModels)
    .map(([name, enabled], index) => `${index + 1}. ${name} (${enabled ? 'Enabled' : 'Disabled'})`)
    .join('\n');
  
  const modelResponse = ui.prompt(
    'Toggle Model Availability',
    'Select a model to toggle:\n' + modelOptions,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (modelResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const modelChoice = modelResponse.getResponseText();
  const modelIndex = parseInt(modelChoice) - 1;
  const modelNames = Object.keys(enabledModels);
  
  if (isNaN(modelIndex) || modelIndex < 0 || modelIndex >= modelNames.length) {
    ui.alert('Invalid model selection. Please enter a number between 1 and ' + modelNames.length);
    return;
  }
  
  const modelName = modelNames[modelIndex];
  enabledModels[modelName] = !enabledModels[modelName];
  setEnabledModels(sheet, enabledModels);
  
  ui.alert('Success', `${modelName} is now ${enabledModels[modelName] ? 'enabled' : 'disabled'}.`, ui.ButtonSet.OK);
}
