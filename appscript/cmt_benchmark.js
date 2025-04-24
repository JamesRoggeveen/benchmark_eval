// Configuration
const CONFIG = {
  DELAY_MS: 2000,          // Delay between API calls in milliseconds
  MAX_RETRIES: 3,          // Maximum number of retries for timeout errors
  RETRY_DELAY_MS: 5000,    // Delay between retries (5 seconds)
  ADMIN_EMAILS: ["jroggeveen@g.harvard.edu", "ek436@cornell.edu", "mpbrenner@gmail.com","hnpan@terpmail.umd.edu"], // Administrator email
  DEFAULT_COLUMNS: {       // Default column assignments
    promptCol: "A",        // Column A for prompt
    solutionCol: "B",      // Column B for solution
    paramsCol: "C",        // Column C for parameters
    evalTypeCol: "D",      // Column D for evaluation type (numeric/expression)
    statusCol: "M",        // Column M for status
    geminiFlashCol: "N",   // Column N for Gemini 2.0 Flash response
    geminiFlashThinkingCol: "P", // Column P for Gemini 2.0 Flash Thinking response
    gemini25FlashThinkingCol: "R", // Column R for Gemini 2.5 Flash Thinking response
    gpt4oCol: "T",         // Column T for GPT-4o response
    gpt4oMiniCol: "V",     // Column V for GPT-4o-mini response
    gptO3MiniCol: "X",     // Column X for GPT-o3-mini response
    gptO1MiniCol: "Z",     // Column Z for GPT-o1-mini response
    gptO1Col: "AB",        // Column AB for GPT-o1 response
    geminiFlashEquivCol: "O",   // Column O for Gemini 2.0 Flash equivalence
    geminiFlashThinkingEquivCol: "Q", // Column Q for Gemini 2.0 Flash Thinking equivalence
    gemini25FlashThinkingEquivCol: "S", // Column S for Gemini 2.5 Flash Thinking equivalence
    gpt4oEquivCol: "U",         // Column U for GPT-4o equivalence
    gpt4oMiniEquivCol: "W",     // Column W for GPT-4o-mini equivalence
    gptO3MiniEquivCol: "Y",     // Column Y for GPT-o3-mini equivalence
    gptO1MiniEquivCol: "AA",     // Column AA for GPT-o1-mini equivalence
    gptO1EquivCol: "AC",        // Column AC for GPT-o1 equivalence
    evalOutputStartCol: "AD" // Column AD for evaluation outputs start
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

// Function to update the prompt suffix (now available to all users)
function updatePromptSuffix() {
  const ui = SpreadsheetApp.getUi();
  
  const response = ui.prompt(
    'Prompt Suffix Configuration',
    'Enter the new prompt suffix to be added to all queries:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() === ui.Button.OK) {
    const promptSuffix = response.getResponseText().trim();
    const documentProperties = PropertiesService.getDocumentProperties();
    documentProperties.setProperty('prompt_suffix', promptSuffix);
    ui.alert('Success', 'Prompt suffix updated successfully!', ui.ButtonSet.OK);
  }
}

// Function to view the current prompt suffix (public)
function viewPromptSuffix() {
  const ui = SpreadsheetApp.getUi();
  const documentProperties = PropertiesService.getDocumentProperties();
  const promptSuffix = documentProperties.getProperty('prompt_suffix') || '(No suffix configured)';
  ui.alert('Current Prompt Suffix', promptSuffix, ui.ButtonSet.OK);
}

// Function to get the current prompt suffix
function getPromptSuffix() {
  const documentProperties = PropertiesService.getDocumentProperties();
  return documentProperties.getProperty('prompt_suffix') || '';
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
    const scriptProperties = PropertiesService.getScriptProperties();
    const apiBaseUrl = scriptProperties.getProperty('API_BASE_URL');
    
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

// Function to get enabled models for a sheet
function getEnabledModels(sheet) {
  const sheetId = sheet.getSheetId().toString();
  const documentProperties = PropertiesService.getDocumentProperties();
  const enabledModels = documentProperties.getProperty('enabled_models_' + sheetId);
  
  if (enabledModels) {
    return JSON.parse(enabledModels);
  }
  
  // Default to only Gemini models enabled
  return {
    "Gemini 2.0 Flash": true,
    "Gemini 2.0 Flash Thinking": true,
    "Gemini 2.5 Flash Thinking": true,
    "GPT-4o": false,
    "GPT-4o-mini": false,
    "GPT-o3-mini": false,
    "GPT-o1-mini": false,
    "GPT-o1": false
  };
}

// Function to set enabled models for a sheet
function setEnabledModels(sheet, models) {
  const sheetId = sheet.getSheetId().toString();
  const documentProperties = PropertiesService.getDocumentProperties();
  documentProperties.setProperty('enabled_models_' + sheetId, JSON.stringify(models));
}

// Function to get response and equivalence columns for a model
function getModelColumns(sheetConfig, model) {
  let responseCol, equivCol;
  switch(model) {
    case "Gemini 2.0 Flash":
      responseCol = sheetConfig.geminiFlashCol;
      equivCol = sheetConfig.geminiFlashEquivCol;
      break;
    case "Gemini 2.0 Flash Thinking":
      responseCol = sheetConfig.geminiFlashThinkingCol;
      equivCol = sheetConfig.geminiFlashThinkingEquivCol;
      break;
    case "Gemini 2.5 Flash Thinking":
      responseCol = sheetConfig.gemini25FlashThinkingCol;
      equivCol = sheetConfig.gemini25FlashThinkingEquivCol;
      break;
    case "GPT-4o":
      responseCol = sheetConfig.gpt4oCol;
      equivCol = sheetConfig.gpt4oEquivCol;
      break;
    case "GPT-4o-mini":
      responseCol = sheetConfig.gpt4oMiniCol;
      equivCol = sheetConfig.gpt4oMiniEquivCol;
      break;
    case "GPT-o3-mini":
      responseCol = sheetConfig.gptO3MiniCol;
      equivCol = sheetConfig.gptO3MiniEquivCol;
      break;
    case "GPT-o1-mini":
      responseCol = sheetConfig.gptO1MiniCol;
      equivCol = sheetConfig.gptO1MiniEquivCol;
      break;
    case "GPT-o1":
      responseCol = sheetConfig.gptO1Col;
      equivCol = sheetConfig.gptO1EquivCol;
      break;
    default:
      return null;
  }
  return { responseCol, equivCol };
}

// Function to clear model-specific columns for a row
function clearModelColumns(sheet, row, sheetConfig, model) {
  const columns = getModelColumns(sheetConfig, model);
  if (!columns) return;
  
  // Clear response and equivalence columns
  sheet.getRange(columns.responseCol + row).clearContent();
  sheet.getRange(columns.equivCol + row).clearContent();
}

// Function to call the evaluation API (either numeric or expression)
function callEvalAPI(prompt, solution, parameters, model, evalType) {
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) {
      return {
        success: false,
        error: "API URL not configured",
        isApiCallError: true
      };
    }
    
    // Get the prompt suffix and append it to the prompt
    const promptSuffix = getPromptSuffix();
    const fullPrompt = promptSuffix ? `${prompt} ${promptSuffix}` : prompt;
    
    // Choose endpoint based on evaluation type
    const endpoint = evalType.toLowerCase() === 'numeric' ? '/eval_cmt_numerics' : '/eval';
    
    const response = UrlFetchApp.fetch(apiBaseUrl + endpoint, {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({
        input: fullPrompt,
        solution: solution,
        parameters: parameters || "",
        model: model
      }),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    console.log("API Response:", result);
    
    if (response.getResponseCode() !== 200) {
      return {
        success: false,
        error: `API HTTP Error (${response.getResponseCode()}): ${result.error || result.error_message || "Unknown error"}`,
        isApiCallError: true,
        result: result
      };
    }
    
    if (!result.success) {
      return {
        success: false,
        error: result.error || result.error_message || "Unknown error from API",
        isApiCallError: false,
        result: result
      };
    }
    
    return {
      success: true,
      result: result
    };
  } catch (e) {
    console.error("API call error:", e);
    return {
      success: false,
      error: `API Call Failed: ${e.toString()}`,
      isApiCallError: true
    };
  }
}

// Function to process evaluation results
function processEvalCmtResult(result) {
  try {
    // Log the raw result for debugging
    console.log("Raw evaluation result:", JSON.stringify(result));
    
    if (!result.success) {
      return {
        success: false,
        isEquivalent: false,  // Add equivalence result
        detailedResults: [
          result.model_name || "",                // Model name first
          result.model_response || "",            // Then model response
          result.error || result.error_message || "Unknown error",
          "", "", "", "", ""
        ]
      };
    }
    
    return {
      success: true,
      isEquivalent: result.is_equivalent === true,  // Explicitly check for true
      detailedResults: [
        result.model_name || "",                 // Model name first
        result.model_response || "",             // Then raw model response
        result.error_message || "",              // Error message
        result.model_parsed || "",               // Parsed model response
        result.solution_parsed || "",            // Parsed solution
        result.evaluation_result || "",          // Evaluation result
        result.comparison_details || "",         // Comparison details
        ""                                       // Empty column for spacing
      ]
    };
  } catch (e) {
    console.error("Error processing result:", e);
    return {
      success: false,
      isEquivalent: false,
      detailedResults: [
        result && result.model_name || "",       // Model name first
        result && result.model_response || "",   // Then model response
        "Error processing result: " + e.toString(),
        "", "", "", "", ""
      ]
    };
  }
}

// Function to evaluate a single row
function evaluateRow() {
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
  
  // Create dialog for model selection, adding "All Enabled Models" option
  const modelOptions = [`[0] All Enabled Models`]
    .concat(availableModels.map((model, index) => 
      `[${index + 1}] ${model}`
    )).join('\n');
  
  const modelResponse = ui.prompt(
    'Select Model',
    'Please select a model by entering its number:\n\n' + modelOptions,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (modelResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const modelChoice = modelResponse.getResponseText();
  const modelIndex = parseInt(modelChoice);
  
  if (isNaN(modelIndex) || modelIndex < 0 || modelIndex > availableModels.length) {
    ui.alert('Invalid model selection. Please enter a number between 0 and ' + availableModels.length);
    return;
  }
  
  // Get selected models (either all or single)
  const selectedModels = modelIndex === 0 ? availableModels : [availableModels[modelIndex - 1]];
  
  // Ask for row number
  const rowResponse = ui.prompt(
    'Row Selection',
    'Please enter the row number to process:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (rowResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const rowNum = rowResponse.getResponseText().trim();
  const row = parseInt(rowNum);
  if (isNaN(row) || row < 1) {
    ui.alert('Invalid row number');
    return;
  }
  
  // Get values from specified columns
  const prompt = sheet.getRange(sheetConfig.promptCol + row).getValue();
  const solution = sheet.getRange(sheetConfig.solutionCol + row).getValue();
  const parameters = sheet.getRange(sheetConfig.paramsCol + row).getValue();
  const evalType = (sheet.getRange(sheetConfig.evalTypeCol + row).getValue() || 'numeric').toLowerCase();
  
  if (!prompt || !solution) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: Empty input or solution");
    SpreadsheetApp.flush();
    return;
  }
  
  if (evalType !== 'numeric' && evalType !== 'expression') {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: Invalid evaluation type. Must be 'numeric' or 'expression'");
    SpreadsheetApp.flush();
    return;
  }
  
  // Clear evaluation output columns before starting
  const outputCol = sheet.getRange(sheetConfig.evalOutputStartCol + row).getColumn();
  const numOutputCols = 8; // Model name, response, error, parsed model, parsed solution, eval result, comparison, spacing
  sheet.getRange(row, outputCol, 1, numOutputCols).clearContent();
  SpreadsheetApp.flush();
  
  // Update initial status
  if (selectedModels.length > 1) {
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Starting evaluation of ${selectedModels.length} models...`);
    SpreadsheetApp.flush();
  }
  
  let completedModels = 0;
  
  // Process each selected model
  for (const model of selectedModels) {
    // Clear previous results and update status
    clearModelColumns(sheet, row, sheetConfig, model);
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Processing ${model}... (${++completedModels}/${selectedModels.length})`);
    SpreadsheetApp.flush();
    
    try {
      const apiResult = callEvalAPI(prompt, solution, parameters, model, evalType);
      const columns = getModelColumns(sheetConfig, model);
      
      if (!apiResult.success) {
        const errorPrefix = apiResult.isApiCallError ? "API Call Error: " : "API Response Error: ";
        const errorMsg = errorPrefix + apiResult.error;
        console.error(errorMsg);
        
        // Write error message to status
        sheet.getRange(sheetConfig.statusCol + row).setValue(`${model}: ${errorMsg} (${completedModels}/${selectedModels.length})`);
        
        // Write model response if available
        if (apiResult.result && apiResult.result.model_response) {
          sheet.getRange(columns.responseCol + row).setValue(apiResult.result.model_response);
        }
        
        // Set equivalence to false
        sheet.getRange(columns.equivCol + row).setValue(false);
        
        // Write debug info to eval output
        const detailedResults = [
          model,                                                          // Model name
          apiResult.result && apiResult.result.model_response || "",     // Model response
          errorMsg,                                                      // Error message
          "", "", "", "", ""                                            // Empty columns
        ];
        sheet.getRange(row, outputCol, 1, detailedResults.length).setValues([detailedResults]);
        SpreadsheetApp.flush();
        continue;
      }
      
      // Process the evaluation result
      const processedResult = processEvalCmtResult(apiResult.result);
      
      // Write model response to its column
      sheet.getRange(columns.responseCol + row).setValue(apiResult.result.model_response || "");
      
      // Write equivalence result to its column
      sheet.getRange(columns.equivCol + row).setValue(processedResult.isEquivalent);
      
      // Write detailed results to eval output for debugging
      const detailedResults = [model, ...processedResult.detailedResults];
      sheet.getRange(row, outputCol, 1, detailedResults.length).setValues([detailedResults]);
      
      // Update status with current progress
      const statusMessage = processedResult.success ? 
        `${model}: Complete (${completedModels}/${selectedModels.length})` : 
        `${model}: Failed - ${processedResult.detailedResults[0]} (${completedModels}/${selectedModels.length})`;
      sheet.getRange(sheetConfig.statusCol + row).setValue(statusMessage);
      
      // Flush all pending changes
      SpreadsheetApp.flush();
      
      // Add delay between model calls if processing multiple models
      if (selectedModels.length > 1 && completedModels < selectedModels.length) {
        Utilities.sleep(CONFIG.DELAY_MS);
      }
      
    } catch (e) {
      console.error("Unexpected error during evaluation:", e);
      const errorMsg = "System Error: " + e.toString();
      sheet.getRange(sheetConfig.statusCol + row).setValue(`${model}: ${errorMsg} (${completedModels}/${selectedModels.length})`);
      
      // Clear model response and set equivalence to false
      const columns = getModelColumns(sheetConfig, model);
      sheet.getRange(columns.responseCol + row).clearContent();
      sheet.getRange(columns.equivCol + row).setValue(false);
      
      // Write error to eval output
      const detailedResults = [model, "", errorMsg, "", "", "", "", ""];
      sheet.getRange(row, outputCol, 1, detailedResults.length).setValues([detailedResults]);
      SpreadsheetApp.flush();
    }
  }
  
  // Update final status
  if (selectedModels.length > 1) {
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Completed all ${selectedModels.length} models`);
    SpreadsheetApp.flush();
  }
}

// Admin function to set up column configuration for a specific sheet
function setupColumns() {
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
    'Column Configuration (Admin Only)',
    `Configure column assignments for sheet "${sheet.getName()}":\n\n` +
    `Prompt column (current: ${sheetConfig.promptCol}):\n` +
    `Solution column (current: ${sheetConfig.solutionCol}):\n` +
    `Parameters column (current: ${sheetConfig.paramsCol}):\n` +
    `Evaluation type column (current: ${sheetConfig.evalTypeCol}):\n` +
    `Status column (current: ${sheetConfig.statusCol}):\n` +
    `Gemini 2.0 Flash response column (current: ${sheetConfig.geminiFlashCol}):\n` +
    `Gemini 2.0 Flash Thinking response column (current: ${sheetConfig.geminiFlashThinkingCol}):\n` +
    `Gemini 2.5 Flash Thinking response column (current: ${sheetConfig.gemini25FlashThinkingCol}):\n` +
    `GPT-4o response column (current: ${sheetConfig.gpt4oCol}):\n` +
    `GPT-4o-mini response column (current: ${sheetConfig.gpt4oMiniCol}):\n` +
    `GPT-o3-mini response column (current: ${sheetConfig.gptO3MiniCol}):\n` +
    `GPT-o1-mini response column (current: ${sheetConfig.gptO1MiniCol}):\n` +
    `GPT-o1 response column (current: ${sheetConfig.gptO1Col}):\n` +
    `Equivalence result columns:\n` +
    `Gemini 2.0 Flash equivalence column (current: ${sheetConfig.geminiFlashEquivCol}):\n` +
    `Gemini 2.0 Flash Thinking equivalence column (current: ${sheetConfig.geminiFlashThinkingEquivCol}):\n` +
    `Gemini 2.5 Flash Thinking equivalence column (current: ${sheetConfig.gemini25FlashThinkingEquivCol}):\n` +
    `GPT-4o equivalence column (current: ${sheetConfig.gpt4oEquivCol}):\n` +
    `GPT-4o-mini equivalence column (current: ${sheetConfig.gpt4oMiniEquivCol}):\n` +
    `GPT-o3-mini equivalence column (current: ${sheetConfig.gptO3MiniEquivCol}):\n` +
    `GPT-o1-mini equivalence column (current: ${sheetConfig.gptO1MiniEquivCol}):\n` +
    `GPT-o1 equivalence column (current: ${sheetConfig.gptO1EquivCol}):\n` +
    `Evaluation output start column (current: ${sheetConfig.evalOutputStartCol}):\n\n` +
    `Enter column letters separated by commas (e.g., A,B,C,D,M,N,P,R,T,V,X,Z,AB,O,Q,S,U,W,Y,AA,AC,AD):`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const columns = response.getResponseText().split(',').map(col => col.trim().toUpperCase());
  
  if (columns.length !== 22) {
    ui.alert('Error', 'Please provide exactly 22 column letters.', ui.ButtonSet.OK);
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
    promptCol: columns[0],
    solutionCol: columns[1],
    paramsCol: columns[2],
    evalTypeCol: columns[3],
    statusCol: columns[4],
    geminiFlashCol: columns[5],
    geminiFlashThinkingCol: columns[6],
    gemini25FlashThinkingCol: columns[7],
    gpt4oCol: columns[8],
    gpt4oMiniCol: columns[9],
    gptO3MiniCol: columns[10],
    gptO1MiniCol: columns[11],
    gptO1Col: columns[12],
    geminiFlashEquivCol: columns[13],
    geminiFlashThinkingEquivCol: columns[14],
    gemini25FlashThinkingEquivCol: columns[15],
    gpt4oEquivCol: columns[16],
    gpt4oMiniEquivCol: columns[17],
    gptO3MiniEquivCol: columns[18],
    gptO1MiniEquivCol: columns[19],
    gptO1EquivCol: columns[20],
    evalOutputStartCol: columns[21]
  };
  
  saveSheetConfig(sheet, newConfig);
  
  // Display configuration in the status column
  sheet.getRange(newConfig.statusCol + "1").setValue(
    `Columns: Prompt=${columns[0]}, Solution=${columns[1]}, Parameters=${columns[2]}, ` +
    `EvalType=${columns[3]}, Status=${columns[4]}, Flash=${columns[5]}, FlashT=${columns[6]}, Flash25T=${columns[7]}, ` +
    `GPT4o=${columns[8]}, GPT4oM=${columns[9]}, GPT3M=${columns[10]}, GPT1M=${columns[11]}, ` +
    `GPT1=${columns[12]}, Eval Output Start=${columns[21]}`
  );
  
  ui.alert('Success', `Sheet "${sheet.getName()}" configured with columns:\n` +
    `Prompt: ${newConfig.promptCol}\n` +
    `Solution: ${newConfig.solutionCol}\n` +
    `Parameters: ${newConfig.paramsCol}\n` +
    `Evaluation Type: ${newConfig.evalTypeCol}\n` +
    `Status: ${newConfig.statusCol}\n` +
    `Gemini 2.0 Flash: ${newConfig.geminiFlashCol}\n` +
    `Gemini 2.0 Flash Thinking: ${newConfig.geminiFlashThinkingCol}\n` +
    `Gemini 2.5 Flash Thinking: ${newConfig.gemini25FlashThinkingCol}\n` +
    `GPT-4o: ${newConfig.gpt4oCol}\n` +
    `GPT-4o-mini: ${newConfig.gpt4oMiniCol}\n` +
    `GPT-o3-mini: ${newConfig.gptO3MiniCol}\n` +
    `GPT-o1-mini: ${newConfig.gptO1MiniCol}\n` +
    `GPT-o1: ${newConfig.gptO1Col}\n` +
    `Equivalence: ${columns[13]}, ${columns[14]}, ${columns[15]}, ${columns[16]}, ${columns[17]}, ${columns[18]}, ${columns[19]}, ${columns[20]}\n` +
    `Eval Output Start: ${columns[21]}`, ui.ButtonSet.OK);
}

// Admin function to configure the API URL
function adminConfigureApiUrl() {
  const ui = SpreadsheetApp.getUi();
  const scriptProperties = PropertiesService.getScriptProperties();
  
  const currentUrl = scriptProperties.getProperty('API_BASE_URL') || '';
  const result = ui.prompt(
    'Configure API URL',
    'Enter the base URL for the API (e.g., http://localhost:8000):',
    ui.ButtonSet.OK_CANCEL);

  const button = result.getSelectedButton();
  if (button === ui.Button.OK) {
    const url = result.getResponseText().trim();
    if (url) {
      scriptProperties.setProperty('API_BASE_URL', url);
      ui.alert('Success', 'API URL has been updated.', ui.ButtonSet.OK);
    } else {
      ui.alert('Error', 'Please enter a valid URL.', ui.ButtonSet.OK);
    }
  }
}

// Process multiple rows with the same model
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
  
  // Ask for start and end rows
  const response = ui.prompt(
    'Range Selection',
    'Please enter the start and end row numbers separated by a comma (e.g., 2,10):',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  // Parse row range
  const rowRange = response.getResponseText().split(',').map(r => parseInt(r.trim()));
  if (rowRange.length !== 2 || isNaN(rowRange[0]) || isNaN(rowRange[1]) || rowRange[0] < 1 || rowRange[1] < rowRange[0]) {
    ui.alert('Invalid row range. Please enter two numbers separated by a comma, with the second number greater than or equal to the first.');
    return;
  }
  
  const startRow = rowRange[0];
  const endRow = rowRange[1];
  
  // Process each row
  for (let currentRow = startRow; currentRow <= endRow; currentRow++) {
    try {
      // Get prompt from the specified column
      const prompt = sheet.getRange(sheetConfig.promptCol + currentRow).getValue();
      
      if (!prompt) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: Empty prompt");
        continue;
      }
      
      // Get the response column for this model
      const responseCol = getResponseColumn(sheetConfig, model);
      if (!responseCol) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: Could not determine response column");
        continue;
      }
      
      // Clear previous response before processing
      clearResponseCell(sheet, currentRow, sheetConfig, model);
      
      // Update status
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Processing...");
      
      // Call the query API
      const apiResult = callQueryAPI(prompt, model);
      
      if (!apiResult.success) {
        // API call succeeded but returned an error
        const errorMsg = apiResult.error || "Unknown error";
        sheet.getRange(responseCol + currentRow).setValue("Error: " + errorMsg);
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: " + errorMsg);
        continue;
      }
      
      // Check if we have a valid result object
      if (!apiResult.result) {
        const errorMsg = "No result returned from API";
        sheet.getRange(responseCol + currentRow).setValue("Error: " + errorMsg);
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: " + errorMsg);
        continue;
      }
      
      // Write the model response to the appropriate column
      sheet.getRange(responseCol + currentRow).setValue(apiResult.result.response || "");
      // Update status
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Complete");
      
      // Add delay between requests
      Utilities.sleep(CONFIG.DELAY_MS);
    } catch (e) {
      // API call failed entirely
      const errorMsg = e.toString();
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: " + errorMsg);
      sheet.getRange(responseCol + currentRow).setValue("Error: " + errorMsg);
    }
  }
  
  // Add final status message
  sheet.getRange(sheetConfig.statusCol + startRow).setValue(`Completed rows ${startRow} to ${endRow}`);
}

// Add the toggleModelAvailability function
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

// Create custom menu when spreadsheet opens
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const menu = ui.createMenu('LLM Query')
    .addItem('Query Single Row', 'queryLLM')
    .addItem('Query Multiple Rows', 'processMultipleRows')
    .addItem('Evaluate Row', 'evaluateRow')
    .addItem('View Current Prompt Suffix', 'viewPromptSuffix')
    .addItem('Update Prompt Suffix', 'updatePromptSuffix');
  
  // Only show admin options to admins
  if (isAdmin()) {
    menu.addSeparator()
      .addItem('Admin: Configure API URL', 'adminConfigureApiUrl')
      .addItem('Admin: Setup Columns', 'setupColumns')
      .addItem('Admin: Toggle Model Availability', 'toggleModelAvailability');
  }
  
  menu.addToUi();
} 