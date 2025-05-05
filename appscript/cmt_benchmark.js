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
    functionsCol: "D",     // Column D for functions
    statusCol: "M",        // Column M for status
    parserCheckCol: "N",   // Column N for parser check result
    geminiFlashCol: "O",   // Column O for Gemini 2.0 Flash response
    geminiFlashThinkingCol: "P", // Column P for Gemini 2.0 Flash Thinking response
    gemini25FlashThinkingCol: "R", // Column R for Gemini 2.5 Flash Thinking response
    gemini25ProPreviewCol: "S", // Column S for Gemini 2.5 Pro Preview response
    gpt4oCol: "T",         // Column T for GPT-4o response
    gpt4oMiniCol: "V",     // Column V for GPT-4o-mini response
    gptO3MiniCol: "X",     // Column X for GPT-o3-mini response
    gptO1MiniCol: "Z",     // Column Z for GPT-o1-mini response
    gptO1Col: "AB",        // Column AB for GPT-o1 response
    geminiFlashEquivCol: "AC",   // Column AC for Gemini 2.0 Flash equivalence
    geminiFlashThinkingEquivCol: "AD", // Column AD for Gemini 2.0 Flash Thinking equivalence
    gemini25FlashThinkingEquivCol: "AE", // Column AE for Gemini 2.5 Flash Thinking equivalence
    gemini25ProPreviewEquivCol: "AF", // Column AF for Gemini 2.5 Pro Preview equivalence
    gpt4oEquivCol: "AG",         // Column AG for GPT-4o equivalence
    gpt4oMiniEquivCol: "AH",     // Column AH for GPT-4o-mini equivalence
    gptO3MiniEquivCol: "AI",     // Column AI for GPT-o3-mini equivalence
    gptO1MiniEquivCol: "AJ",     // Column AJ for GPT-o1-mini equivalence
    gptO1EquivCol: "AK",        // Column AK for GPT-o1 equivalence
    evalOutputStartCol: "AL" // Column AL for evaluation outputs start
  },
  // Column name lookup table for automatic configuration
  COLUMN_NAMES: {
    // Basic columns
    "Prompt": "promptCol",
    "Solution": "solutionCol",
    "Parameters": "paramsCol",
    "Functions": "functionsCol",
    "Status": "statusCol",
    "Parser Check": "parserCheckCol",
    // Model response columns
    "Gemini 2.0 Flash": "geminiFlashCol",
    "Gemini 2.0 Flash Thinking": "geminiFlashThinkingCol",
    "Gemini 2.5 Flash Thinking": "gemini25FlashThinkingCol",
    "Gemini 2.5 Pro Preview": "gemini25ProPreviewCol",
    "GPT-4o": "gpt4oCol",
    "GPT-4o-mini": "gpt4oMiniCol",
    "GPT-o3-mini": "gptO3MiniCol",
    "GPT-o1-mini": "gptO1MiniCol",
    "GPT-o1": "gptO1Col",
    // Equivalence columns
    "Gemini 2.0 Flash Equiv": "geminiFlashEquivCol",
    "Gemini 2.0 Flash Thinking Equiv": "geminiFlashThinkingEquivCol",
    "Gemini 2.5 Flash Thinking Equiv": "gemini25FlashThinkingEquivCol",
    "Gemini 2.5 Pro Preview Equiv": "gemini25ProPreviewEquivCol",
    "GPT-4o Equiv": "gpt4oEquivCol",
    "GPT-4o-mini Equiv": "gpt4oMiniEquivCol",
    "GPT-o3-mini Equiv": "gptO3MiniEquivCol",
    "GPT-o1-mini Equiv": "gptO1MiniEquivCol",
    "GPT-o1 Equiv": "gptO1EquivCol",
    // Evaluation output
    "Eval Output Start": "evalOutputStartCol"
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
    case "Gemini 2.5 Pro Preview":
      responseCol = sheetConfig.gemini25ProPreviewCol;
      equivCol = sheetConfig.gemini25ProPreviewEquivCol;
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

// Function to call the evaluation API
function callEvalAPI(prompt, solution, parameters, functions, model) {
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
    
    const response = UrlFetchApp.fetch(apiBaseUrl + "/eval_cmt", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({
        input: fullPrompt,
        solution: solution,
        parameters: parameters || "",
        functions: functions || "",
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
        isEquivalent: false,
        detailedResults: [
          result.model_name || "",                // Model name first
          result.model_response || "",            // Then model response
          "ERROR: " + (result.error || result.error_message || "Unknown error"),
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
        "ERROR: Error processing result: " + e.toString(),
        "", "", "", "", ""
      ]
    };
  }
}

// Function to prepare API request for a model
function prepareEvalRequest(apiBaseUrl, prompt, solution, parameters, functions, model) {
  const promptSuffix = getPromptSuffix();
  const fullPrompt = promptSuffix ? `${prompt} ${promptSuffix}` : prompt;
  
  return {
    url: apiBaseUrl + "/eval_cmt",
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({
      input: fullPrompt,
      solution: solution,
      parameters: parameters || "",
      functions: functions || "",
      model: model
    }),
    muteHttpExceptions: true
  };
}

// Function to call the parse_cmt endpoint
function callParseCmtAPI(solution, parameters, functions) {
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) {
      return {
        success: false,
        error: "API URL not configured",
        isApiCallError: true
      };
    }
    
    const response = UrlFetchApp.fetch(apiBaseUrl + "/parse_cmt", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({
        input: solution,
        parameters: parameters || "",
        functions: functions || ""
      }),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    console.log("Parse API Response:", result);
    
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
  const functions = sheet.getRange(sheetConfig.functionsCol + row).getValue();
  
  if (!prompt || !solution) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: Empty input or solution");
    SpreadsheetApp.flush();
    return;
  }
  
  // First, run the parse_cmt endpoint to check if the solution is valid
  sheet.getRange(sheetConfig.statusCol + row).setValue("Checking solution validity...");
  SpreadsheetApp.flush();
  
  const parseResult = callParseCmtAPI(solution, parameters, functions);
  if (!parseResult.success) {
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Error: ${parseResult.error}`);
    sheet.getRange(sheetConfig.parserCheckCol + row).setValue(false);
    SpreadsheetApp.flush();
    return;
  }
  
  // Set parser check result
  sheet.getRange(sheetConfig.parserCheckCol + row).setValue(true);
  
  // Clear evaluation output columns before starting
  const outputCol = sheet.getRange(sheetConfig.evalOutputStartCol + row).getColumn();
  const numOutputCols = 8; // Model name, response, error, parsed model, parsed solution, eval result, comparison, spacing
  sheet.getRange(row, outputCol, 1, numOutputCols).clearContent();
  SpreadsheetApp.flush();
  
  // Clear previous results for all selected models
  selectedModels.forEach(model => {
    clearModelColumns(sheet, row, sheetConfig, model);
  });
  
  // Update initial status
  sheet.getRange(sheetConfig.statusCol + row).setValue(`Preparing evaluation of ${selectedModels.length} models...`);
  SpreadsheetApp.flush();
  
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) {
      throw new Error("API URL not configured");
    }
    
    // Prepare all API requests
    const requests = selectedModels.map(model => 
      prepareEvalRequest(apiBaseUrl, prompt, solution, parameters, functions, model)
    );
    
    // Make concurrent API calls
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Sending requests to ${selectedModels.length} models...`);
    SpreadsheetApp.flush();
    
    const responses = UrlFetchApp.fetchAll(requests);
    
    // Process all responses
    responses.forEach((response, index) => {
      const model = selectedModels[index];
      const columns = getModelColumns(sheetConfig, model);
      
      try {
        const result = JSON.parse(response.getContentText());
        const isApiCallError = response.getResponseCode() !== 200;
        
        if (isApiCallError || !result.success) {
          const errorPrefix = isApiCallError ? "API Call Error: " : "API Response Error: ";
          const errorMsg = errorPrefix + (result.error || result.error_message || "Unknown error");
          console.error(errorMsg);
          
          // Write error message to status
          sheet.getRange(sheetConfig.statusCol + row).setValue(`${model}: ${errorMsg}`);
          
          // Write model response if available
          if (result.model_response) {
            sheet.getRange(columns.responseCol + row).setValue(result.model_response);
          }
          
          // Write error message to equivalence column
          sheet.getRange(columns.equivCol + row).setValue(errorMsg);
          
          // Write debug info to eval output
          const detailedResults = [
            model,                    // Model name
            result.model_response || "",  // Model response
            errorMsg,                 // Error message
            "", "", "", "", ""       // Empty columns
          ];
          sheet.getRange(row, outputCol, 1, detailedResults.length).setValues([detailedResults]);
        } else {
          // Process successful result
          const processedResult = processEvalCmtResult(result);
          
          // Write model response to its column
          sheet.getRange(columns.responseCol + row).setValue(result.model_response || "");
          
          // Write equivalence result to its column
          sheet.getRange(columns.equivCol + row).setValue(processedResult.isEquivalent);
          
          // Write detailed results to eval output for debugging
          const detailedResults = [model, ...processedResult.detailedResults];
          sheet.getRange(row, outputCol, 1, detailedResults.length).setValues([detailedResults]);
        }
        
        SpreadsheetApp.flush();
      } catch (e) {
        console.error("Error processing response for model", model, e);
        const errorMsg = "Error processing response: " + e.toString();
        sheet.getRange(sheetConfig.statusCol + row).setValue(`${model}: ${errorMsg}`);
        sheet.getRange(columns.equivCol + row).setValue(errorMsg);
        const detailedResults = [model, "", errorMsg, "", "", "", "", ""];
        sheet.getRange(row, outputCol, 1, detailedResults.length).setValues([detailedResults]);
        SpreadsheetApp.flush();
      }
    });
    
    // Update final status
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Completed all ${selectedModels.length} models`);
    SpreadsheetApp.flush();
    
  } catch (e) {
    console.error("Unexpected error during evaluation:", e);
    const errorMsg = "System Error: " + e.toString();
    sheet.getRange(sheetConfig.statusCol + row).setValue(errorMsg);
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
    `Functions column (current: ${sheetConfig.functionsCol}):\n` +
    `Status column (current: ${sheetConfig.statusCol}):\n` +
    `Parser check column (current: ${sheetConfig.parserCheckCol}):\n` +
    `Gemini 2.0 Flash response column (current: ${sheetConfig.geminiFlashCol}):\n` +
    `Gemini 2.0 Flash Thinking response column (current: ${sheetConfig.geminiFlashThinkingCol}):\n` +
    `Gemini 2.5 Flash Thinking response column (current: ${sheetConfig.gemini25FlashThinkingCol}):\n` +
    `Gemini 2.5 Pro Preview response column (current: ${sheetConfig.gemini25ProPreviewCol}):\n` +
    `GPT-4o response column (current: ${sheetConfig.gpt4oCol}):\n` +
    `GPT-4o-mini response column (current: ${sheetConfig.gpt4oMiniCol}):\n` +
    `GPT-o3-mini response column (current: ${sheetConfig.gptO3MiniCol}):\n` +
    `GPT-o1-mini response column (current: ${sheetConfig.gptO1MiniCol}):\n` +
    `GPT-o1 response column (current: ${sheetConfig.gptO1Col}):\n` +
    `Equivalence result columns:\n` +
    `Gemini 2.0 Flash equivalence column (current: ${sheetConfig.geminiFlashEquivCol}):\n` +
    `Gemini 2.0 Flash Thinking equivalence column (current: ${sheetConfig.geminiFlashThinkingEquivCol}):\n` +
    `Gemini 2.5 Flash Thinking equivalence column (current: ${sheetConfig.gemini25FlashThinkingEquivCol}):\n` +
    `Gemini 2.5 Pro Preview equivalence column (current: ${sheetConfig.gemini25ProPreviewEquivCol}):\n` +
    `GPT-4o equivalence column (current: ${sheetConfig.gpt4oEquivCol}):\n` +
    `GPT-4o-mini equivalence column (current: ${sheetConfig.gpt4oMiniEquivCol}):\n` +
    `GPT-o3-mini equivalence column (current: ${sheetConfig.gptO3MiniEquivCol}):\n` +
    `GPT-o1-mini equivalence column (current: ${sheetConfig.gptO1MiniEquivCol}):\n` +
    `GPT-o1 equivalence column (current: ${sheetConfig.gptO1EquivCol}):\n` +
    `Evaluation output start column (current: ${sheetConfig.evalOutputStartCol}):\n\n` +
    `Enter column letters separated by commas (e.g., A,B,C,D,M,N,P,R,T,V,X,Z,AB,O,Q,S,U,W,Y,AA,AC,AD,AF):`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const columns = response.getResponseText().split(',').map(col => col.trim().toUpperCase());
  
  if (columns.length !== 23) {
    ui.alert('Error', 'Please provide exactly 23 column letters.', ui.ButtonSet.OK);
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
    functionsCol: columns[3],
    statusCol: columns[4],
    parserCheckCol: columns[5],
    geminiFlashCol: columns[6],
    geminiFlashThinkingCol: columns[7],
    gemini25FlashThinkingCol: columns[8],
    gemini25ProPreviewCol: columns[9],
    gpt4oCol: columns[10],
    gpt4oMiniCol: columns[11],
    gptO3MiniCol: columns[12],
    gptO1MiniCol: columns[13],
    gptO1Col: columns[14],
    geminiFlashEquivCol: columns[15],
    geminiFlashThinkingEquivCol: columns[16],
    gemini25FlashThinkingEquivCol: columns[17],
    gemini25ProPreviewEquivCol: columns[18],
    gpt4oEquivCol: columns[19],
    gpt4oMiniEquivCol: columns[20],
    gptO3MiniEquivCol: columns[21],
    gptO1MiniEquivCol: columns[22],
    gptO1EquivCol: columns[23],
    evalOutputStartCol: columns[24]
  };
  
  saveSheetConfig(sheet, newConfig);
  
  // Display configuration in the status column
  sheet.getRange(newConfig.statusCol + "1").setValue(
    `Columns: Prompt=${columns[0]}, Solution=${columns[1]}, Parameters=${columns[2]}, ` +
    `Functions=${columns[3]}, Status=${columns[4]}, Parser=${columns[5]}, Flash=${columns[6]}, FlashT=${columns[7]}, ` +
    `Flash25T=${columns[8]}, Flash25P=${columns[9]}, GPT4o=${columns[10]}, GPT4oM=${columns[11]}, GPT3M=${columns[12]}, ` +
    `GPT1M=${columns[13]}, GPT1=${columns[14]}, Eval Output Start=${columns[24]}`
  );
  
  ui.alert('Success', `Sheet "${sheet.getName()}" configured with columns:\n` +
    `Prompt: ${newConfig.promptCol}\n` +
    `Solution: ${newConfig.solutionCol}\n` +
    `Parameters: ${newConfig.paramsCol}\n` +
    `Functions: ${newConfig.functionsCol}\n` +
    `Status: ${newConfig.statusCol}\n` +
    `Parser: ${newConfig.parserCheckCol}\n` +
    `Gemini 2.0 Flash: ${newConfig.geminiFlashCol}\n` +
    `Gemini 2.0 Flash Thinking: ${newConfig.geminiFlashThinkingCol}\n` +
    `Gemini 2.5 Flash Thinking: ${newConfig.gemini25FlashThinkingCol}\n` +
    `Gemini 2.5 Pro Preview: ${newConfig.gemini25ProPreviewCol}\n` +
    `GPT-4o: ${newConfig.gpt4oCol}\n` +
    `GPT-4o-mini: ${newConfig.gpt4oMiniCol}\n` +
    `GPT-o3-mini: ${newConfig.gptO3MiniCol}\n` +
    `GPT-o1-mini: ${newConfig.gptO1MiniCol}\n` +
    `GPT-o1: ${newConfig.gptO1Col}\n` +
    `Equivalence: ${columns[15]}, ${columns[16]}, ${columns[17]}, ${columns[18]}, ${columns[19]}, ${columns[20]}, ${columns[21]}, ${columns[22]}\n` +
    `Eval Output Start: ${columns[24]}`, ui.ButtonSet.OK);
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

// Function to run parse check on a single row
function runParseCheck() {
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
  
  // Ask for row number
  const rowResponse = ui.prompt(
    'Row Selection',
    'Please enter the row number to check:',
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
  const solution = sheet.getRange(sheetConfig.solutionCol + row).getValue();
  const parameters = sheet.getRange(sheetConfig.paramsCol + row).getValue();
  const functions = sheet.getRange(sheetConfig.functionsCol + row).getValue();
  
  if (!solution) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: Empty solution");
    SpreadsheetApp.flush();
    return;
  }
  
  // Run the parse_cmt endpoint to check if the solution is valid
  sheet.getRange(sheetConfig.statusCol + row).setValue("Checking solution validity...");
  SpreadsheetApp.flush();
  
  const parseResult = callParseCmtAPI(solution, parameters, functions);
  if (!parseResult.success) {
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Error: ${parseResult.error}`);
    sheet.getRange(sheetConfig.parserCheckCol + row).setValue(false);
    SpreadsheetApp.flush();
    return;
  }
  
  // Set parser check result
  sheet.getRange(sheetConfig.parserCheckCol + row).setValue(true);
  sheet.getRange(sheetConfig.statusCol + row).setValue("Solution is valid");
  SpreadsheetApp.flush();
}

// Function to view current column configuration
function viewColumnConfig() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Format the configuration for display
  const configDisplay = [
    "Basic Columns:",
    `Prompt: ${sheetConfig.promptCol}`,
    `Solution: ${sheetConfig.solutionCol}`,
    `Parameters: ${sheetConfig.paramsCol}`,
    `Functions: ${sheetConfig.functionsCol}`,
    `Status: ${sheetConfig.statusCol}`,
    `Parser Check: ${sheetConfig.parserCheckCol}`,
    "",
    "Model Response Columns:",
    `Gemini 2.0 Flash: ${sheetConfig.geminiFlashCol}`,
    `Gemini 2.0 Flash Thinking: ${sheetConfig.geminiFlashThinkingCol}`,
    `Gemini 2.5 Flash Thinking: ${sheetConfig.gemini25FlashThinkingCol}`,
    `Gemini 2.5 Pro Preview: ${sheetConfig.gemini25ProPreviewCol}`,
    `GPT-4o: ${sheetConfig.gpt4oCol}`,
    `GPT-4o-mini: ${sheetConfig.gpt4oMiniCol}`,
    `GPT-o3-mini: ${sheetConfig.gptO3MiniCol}`,
    `GPT-o1-mini: ${sheetConfig.gptO1MiniCol}`,
    `GPT-o1: ${sheetConfig.gptO1Col}`,
    "",
    "Equivalence Columns:",
    `Gemini 2.0 Flash: ${sheetConfig.geminiFlashEquivCol}`,
    `Gemini 2.0 Flash Thinking Equiv": ${sheetConfig.geminiFlashThinkingEquivCol}`,
    `Gemini 2.5 Flash Thinking Equiv": ${sheetConfig.gemini25FlashThinkingEquivCol}`,
    `Gemini 2.5 Pro Preview Equiv": ${sheetConfig.gemini25ProPreviewEquivCol}`,
    `GPT-4o: ${sheetConfig.gpt4oEquivCol}`,
    `GPT-4o-mini: ${sheetConfig.gpt4oMiniEquivCol}`,
    `GPT-o3-mini: ${sheetConfig.gptO3MiniEquivCol}`,
    `GPT-o1-mini: ${sheetConfig.gptO1MiniEquivCol}`,
    `GPT-o1: ${sheetConfig.gptO1EquivCol}`,
    "",
    `Evaluation Output Start: ${sheetConfig.evalOutputStartCol}`
  ].join('\n');
  
  ui.alert(
    `Column Configuration for "${sheet.getName()}"`,
    configDisplay,
    ui.ButtonSet.OK
  );
}

// Function to set headers in row 1 based on current configuration
function setColumnHeaders() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Create a map of column letters to header names
  const columnHeaders = {};
  
  // Add basic columns
  columnHeaders[sheetConfig.promptCol] = "Prompt";
  columnHeaders[sheetConfig.solutionCol] = "Solution";
  columnHeaders[sheetConfig.paramsCol] = "Parameters";
  columnHeaders[sheetConfig.functionsCol] = "Functions";
  columnHeaders[sheetConfig.statusCol] = "Status";
  columnHeaders[sheetConfig.parserCheckCol] = "Parser Check";
  
  // Add model response columns
  columnHeaders[sheetConfig.geminiFlashCol] = "Gemini 2.0 Flash";
  columnHeaders[sheetConfig.geminiFlashThinkingCol] = "Gemini 2.0 Flash Thinking";
  columnHeaders[sheetConfig.gemini25FlashThinkingCol] = "Gemini 2.5 Flash Thinking";
  columnHeaders[sheetConfig.gemini25ProPreviewCol] = "Gemini 2.5 Pro Preview";
  columnHeaders[sheetConfig.gpt4oCol] = "GPT-4o";
  columnHeaders[sheetConfig.gpt4oMiniCol] = "GPT-4o-mini";
  columnHeaders[sheetConfig.gptO3MiniCol] = "GPT-o3-mini";
  columnHeaders[sheetConfig.gptO1MiniCol] = "GPT-o1-mini";
  columnHeaders[sheetConfig.gptO1Col] = "GPT-o1";
  
  // Add equivalence columns
  columnHeaders[sheetConfig.geminiFlashEquivCol] = "Gemini 2.0 Flash Equiv";
  columnHeaders[sheetConfig.geminiFlashThinkingEquivCol] = "Gemini 2.0 Flash Thinking Equiv";
  columnHeaders[sheetConfig.gemini25FlashThinkingEquivCol] = "Gemini 2.5 Flash Thinking Equiv";
  columnHeaders[sheetConfig.gemini25ProPreviewEquivCol] = "Gemini 2.5 Pro Preview Equiv";
  columnHeaders[sheetConfig.gpt4oEquivCol] = "GPT-4o Equiv";
  columnHeaders[sheetConfig.gpt4oMiniEquivCol] = "GPT-4o-mini Equiv";
  columnHeaders[sheetConfig.gptO3MiniEquivCol] = "GPT-o3-mini Equiv";
  columnHeaders[sheetConfig.gptO1MiniEquivCol] = "GPT-o1-mini Equiv";
  columnHeaders[sheetConfig.gptO1EquivCol] = "GPT-o1 Equiv";
  
  // Add evaluation output
  columnHeaders[sheetConfig.evalOutputStartCol] = "Eval Output Start";
  
  // Get the last column that needs a header
  const lastColumn = Math.max(
    ...Object.keys(columnHeaders).map(col => {
      let num = 0;
      for (let i = 0; i < col.length; i++) {
        num = num * 26 + (col.charCodeAt(i) - 64);
      }
      return num;
    })
  );
  
  // Create an array of headers for all columns
  const headers = new Array(lastColumn).fill("");
  Object.entries(columnHeaders).forEach(([col, header]) => {
    let colNum = 0;
    for (let i = 0; i < col.length; i++) {
      colNum = colNum * 26 + (col.charCodeAt(i) - 64);
    }
    headers[colNum - 1] = header;
  });
  
  // Set the headers in row 1
  sheet.getRange(1, 1, 1, lastColumn).setValues([headers]);
  
  ui.alert('Success', `Headers have been set in row 1 for sheet "${sheet.getName()}"`, ui.ButtonSet.OK);
}

// Function to set basic column configuration
function setupBasicColumns() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Prompt for basic column configuration
  const response = ui.prompt(
    'Basic Column Configuration (Admin Only)',
    `Configure basic column assignments for sheet "${sheet.getName()}":\n\n` +
    `Prompt column (current: ${sheetConfig.promptCol}):\n` +
    `Solution column (current: ${sheetConfig.solutionCol}):\n` +
    `Parameters column (current: ${sheetConfig.paramsCol}):\n` +
    `Functions column (current: ${sheetConfig.functionsCol}):\n` +
    `Status column (current: ${sheetConfig.statusCol}):\n` +
    `Parser check column (current: ${sheetConfig.parserCheckCol}):\n\n` +
    `Enter column letters separated by commas (e.g., A,B,C,D,M,N):`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const columns = response.getResponseText().split(',').map(col => col.trim().toUpperCase());
  
  if (columns.length !== 6) {
    ui.alert('Error', 'Please provide exactly 6 column letters.', ui.ButtonSet.OK);
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
  
  // Update only the basic columns in the configuration
  const newConfig = { ...sheetConfig };
  newConfig.promptCol = columns[0];
  newConfig.solutionCol = columns[1];
  newConfig.paramsCol = columns[2];
  newConfig.functionsCol = columns[3];
  newConfig.statusCol = columns[4];
  newConfig.parserCheckCol = columns[5];
  
  saveSheetConfig(sheet, newConfig);
  
  // Display configuration in the status column
  sheet.getRange(newConfig.statusCol + "1").setValue(
    `Basic Columns: Prompt=${columns[0]}, Solution=${columns[1]}, Parameters=${columns[2]}, ` +
    `Functions=${columns[3]}, Status=${columns[4]}, Parser=${columns[5]}`
  );
  
  ui.alert('Success', `Basic columns configured for sheet "${sheet.getName()}"`, ui.ButtonSet.OK);
}

// Function to set model column configuration
function setupModelColumns() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Prompt for model column configuration
  const response = ui.prompt(
    'Model Column Configuration (Admin Only)',
    `Configure model column assignments for sheet "${sheet.getName()}":\n\n` +
    `Gemini 2.0 Flash response column (current: ${sheetConfig.geminiFlashCol}):\n` +
    `Gemini 2.0 Flash Thinking response column (current: ${sheetConfig.geminiFlashThinkingCol}):\n` +
    `Gemini 2.5 Flash Thinking response column (current: ${sheetConfig.gemini25FlashThinkingCol}):\n` +
    `Gemini 2.5 Pro Preview response column (current: ${sheetConfig.gemini25ProPreviewCol}):\n` +
    `GPT-4o response column (current: ${sheetConfig.gpt4oCol}):\n` +
    `GPT-4o-mini response column (current: ${sheetConfig.gpt4oMiniCol}):\n` +
    `GPT-o3-mini response column (current: ${sheetConfig.gptO3MiniCol}):\n` +
    `GPT-o1-mini response column (current: ${sheetConfig.gptO1MiniCol}):\n` +
    `GPT-o1 response column (current: ${sheetConfig.gptO1Col}):\n` +
    `Equivalence result columns:\n` +
    `Gemini 2.0 Flash equivalence column (current: ${sheetConfig.geminiFlashEquivCol}):\n` +
    `Gemini 2.0 Flash Thinking equivalence column (current: ${sheetConfig.geminiFlashThinkingEquivCol}):\n` +
    `Gemini 2.5 Flash Thinking equivalence column (current: ${sheetConfig.gemini25FlashThinkingEquivCol}):\n` +
    `Gemini 2.5 Pro Preview equivalence column (current: ${sheetConfig.gemini25ProPreviewEquivCol}):\n` +
    `GPT-4o equivalence column (current: ${sheetConfig.gpt4oEquivCol}):\n` +
    `GPT-4o-mini equivalence column (current: ${sheetConfig.gpt4oMiniEquivCol}):\n` +
    `GPT-o3-mini equivalence column (current: ${sheetConfig.gptO3MiniEquivCol}):\n` +
    `GPT-o1-mini equivalence column (current: ${sheetConfig.gptO1MiniEquivCol}):\n` +
    `GPT-o1 equivalence column (current: ${sheetConfig.gptO1EquivCol}):\n` +
    `Evaluation output start column (current: ${sheetConfig.evalOutputStartCol}):\n\n` +
    `Enter column letters separated by commas:`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const columns = response.getResponseText().split(',').map(col => col.trim().toUpperCase());
  
  if (columns.length !== 16) {
    ui.alert('Error', 'Please provide exactly 16 column letters.', ui.ButtonSet.OK);
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
  
  // Update only the model columns in the configuration
  const newConfig = { ...sheetConfig };
  newConfig.geminiFlashCol = columns[0];
  newConfig.geminiFlashThinkingCol = columns[1];
  newConfig.gemini25FlashThinkingCol = columns[2];
  newConfig.gemini25ProPreviewCol = columns[3];
  newConfig.gpt4oCol = columns[4];
  newConfig.gpt4oMiniCol = columns[5];
  newConfig.gptO3MiniCol = columns[6];
  newConfig.gptO1MiniCol = columns[7];
  newConfig.gptO1Col = columns[8];
  newConfig.geminiFlashEquivCol = columns[9];
  newConfig.geminiFlashThinkingEquivCol = columns[10];
  newConfig.gemini25FlashThinkingEquivCol = columns[11];
  newConfig.gemini25ProPreviewEquivCol = columns[12];
  newConfig.gpt4oEquivCol = columns[13];
  newConfig.gpt4oMiniEquivCol = columns[14];
  newConfig.gptO3MiniEquivCol = columns[15];
  newConfig.gptO1MiniEquivCol = columns[16];
  newConfig.gptO1EquivCol = columns[17];
  newConfig.evalOutputStartCol = columns[18];
  
  saveSheetConfig(sheet, newConfig);
  
  // Display configuration in the status column
  sheet.getRange(newConfig.statusCol + "1").setValue(
    `Model Columns: Flash=${columns[0]}, FlashT=${columns[1]}, Flash25T=${columns[2]}, ` +
    `Flash25P=${columns[3]}, GPT4o=${columns[4]}, GPT4oM=${columns[5]}, GPT3M=${columns[6]}, ` +
    `GPT1M=${columns[7]}, GPT1=${columns[8]}, Eval Output Start=${columns[18]}`
  );
  
  ui.alert('Success', `Model columns configured for sheet "${sheet.getName()}"`, ui.ButtonSet.OK);
}

// Function to automatically set columns based on row 1 headers
function autoConfigureColumns() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Get all values from row 1
  const lastCol = sheet.getLastColumn();
  const headerRange = sheet.getRange(1, 1, 1, lastCol);
  const headers = headerRange.getValues()[0];
  
  // Create new configuration starting with current values
  const newConfig = { ...sheetConfig };
  let configuredColumns = 0;
  
  // Process each header
  headers.forEach((header, index) => {
    if (!header) return; // Skip empty cells
    
    const columnName = header.toString().trim();
    const configKey = CONFIG.COLUMN_NAMES[columnName];
    
    if (configKey) {
      // Convert column index to letter
      const columnLetter = columnIndexToLetter(index + 1);
      newConfig[configKey] = columnLetter;
      configuredColumns++;
    }
  });
  
  if (configuredColumns === 0) {
    ui.alert('Error', 'No valid column headers found in row 1.', ui.ButtonSet.OK);
    return;
  }
  
  // Save the new configuration
  saveSheetConfig(sheet, newConfig);
  
  // Display configuration in the status column
  const statusMessage = Object.entries(newConfig)
    .filter(([key, value]) => value !== sheetConfig[key]) // Only show changed values
    .map(([key, value]) => `${key}=${value}`)
    .join(', ');
  
  sheet.getRange(newConfig.statusCol + "1").setValue(
    `Auto-configured columns: ${statusMessage}`
  );
  
  ui.alert('Success', `Configured ${configuredColumns} columns based on row 1 headers.`, ui.ButtonSet.OK);
}

// Helper function to convert column index to letter
function columnIndexToLetter(index) {
  let letter = '';
  while (index > 0) {
    const remainder = (index - 1) % 26;
    letter = String.fromCharCode(65 + remainder) + letter;
    index = Math.floor((index - 1) / 26);
  }
  return letter;
}

// Create custom menu when spreadsheet opens
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const menu = ui.createMenu('LLM Query')
    .addItem('Query Single Row', 'queryLLM')
    .addItem('Query Multiple Rows', 'processMultipleRows')
    .addItem('Evaluate Row', 'evaluateRow')
    .addItem('Run Parse Check', 'runParseCheck')
    .addItem('View Current Prompt Suffix', 'viewPromptSuffix')
    .addItem('Update Prompt Suffix', 'updatePromptSuffix');
  
  // Only show admin options to admins
  if (isAdmin()) {
    menu.addSeparator()
      .addItem('Admin: Configure API URL', 'adminConfigureApiUrl')
      .addItem('Admin: View Column Configuration', 'viewColumnConfig')
      .addItem('Admin: Setup Basic Columns', 'setupBasicColumns')
      .addItem('Admin: Setup Model Columns', 'setupModelColumns')
      .addItem('Admin: Auto-Configure Columns', 'autoConfigureColumns')
      .addItem('Admin: Set Column Headers', 'setColumnHeaders')
      .addItem('Admin: Toggle Model Availability', 'toggleModelAvailability');
  }
  
  menu.addToUi();
} 