// Configuration
const CONFIG = {
  BATCH_SIZE: 10,           // Number of rows to process in each batch
  DELAY_MS: 2000,          // Delay between API calls in milliseconds
  MAX_RETRIES: 3,          // Maximum number of retries for timeout errors
  RETRY_DELAY_MS: 5000,    // Delay between retries (5 seconds)
  TRIGGER_NAME: "continuationTrigger",  // Name for our continuation trigger
  ADMIN_EMAILS: ["jroggeveen@g.harvard.edu"], // Administrator email
  DEFAULT_COLUMNS: {       // Default column assignments
    promptCol: undefined,        // Column for prompt
    solutionCol: undefined,      // Column for solution
    paramsCol: undefined,        // Column for parameters
    statusCol: undefined,        // Column for status
    parserCheckCol: undefined,   // Column for parser check result
    geminiFlashCol: undefined,   // Column for Gemini 2.0 Flash response
    geminiFlashThinkingCol: undefined, // Column for Gemini 2.0 Flash Thinking response
    gemini25FlashThinkingCol: undefined, // Column for Gemini 2.5 Flash Thinking response
    gemini25ProPreviewCol: undefined, // Column for Gemini 2.5 Pro Preview response
    gpt4oCol: undefined,         // Column for GPT-4o response
    gpt4oMiniCol: undefined,     // Column for GPT-4o-mini response
    gptO3MiniCol: undefined,     // Column for GPT-o3-mini response
    gptO1MiniCol: undefined,     // Column for GPT-o1-mini response
    gptO1Col: undefined,        // Column for GPT-o1 response
    geminiFlashEquivCol: undefined,   // Column for Gemini 2.0 Flash equivalence
    geminiFlashThinkingEquivCol: undefined, // Column for Gemini 2.0 Flash Thinking equivalence
    gemini25FlashThinkingEquivCol: undefined, // Column for Gemini 2.5 Flash Thinking equivalence
    gemini25ProPreviewEquivCol: undefined, // Column for Gemini 2.5 Pro Preview equivalence
    gpt4oEquivCol: undefined,         // Column for GPT-4o equivalence
    gpt4oMiniEquivCol: undefined,     // Column for GPT-4o-mini equivalence
    gptO3MiniEquivCol: undefined,     // Column for GPT-o3-mini equivalence
    gptO1MiniEquivCol: undefined,     // Column for GPT-o1-mini equivalence
    gptO1EquivCol: undefined,        // Column for GPT-o1 equivalence
    evalOutputStartCol: undefined // Column for evaluation outputs start
  },
  // Column name lookup table for automatic configuration
  COLUMN_NAMES: {
    // Basic columns
    "Prompt": "promptCol",
    "Solution": "solutionCol",
    "Parameters": "paramsCol",
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
  try {
    const userEmail = Session.getActiveUser().getEmail();
    return CONFIG.ADMIN_EMAILS.includes(userEmail);
  } catch (e) {
    console.log("Could not get active user: " + e.toString());
    return false;
  }
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

// Function to get the API base URL
function getApiBaseUrl() {
  const documentProperties = PropertiesService.getDocumentProperties();
  const apiUrl = documentProperties.getProperty('API_BASE_URL');
  
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

// Function to render LaTeX to an image
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
    
    if (!detailed) {
      return [[result.success]];
    }
    
    return [[
      result.success,
      result.error_message || "",
      Array.isArray(result.extracted_solutions) ? result.extracted_solutions.join("; ") : (result.extracted_solutions || ""),
      Array.isArray(result.intermediate_expressions) ? result.intermediate_expressions.join("; ") : (result.intermediate_expressions || ""),
      Array.isArray(result.evaluation_results) ? result.evaluation_results.join("; ") : (result.evaluation_results || "")
    ]];
  } catch (e) {
    return detailed ? [[false, `Error: ${e.toString()}`, "", "", ""]] : [[false]];
  }
}

// Wrapper function to call parseInput directly from spreadsheet
function PARSE_LATEX(latex, detailed = true) {
  return PARSE(latex, "$x$", detailed);
}

// Function to stop all triggers
function stopProcessing() {
  try {
    // Delete all triggers
    const triggers = ScriptApp.getProjectTriggers();
    for (const trigger of triggers) {
      if (trigger.getHandlerFunction() === "processMultipleRows") {
        ScriptApp.deleteTrigger(trigger);
      }
    }
    
    // Clear stored configuration
    const properties = PropertiesService.getScriptProperties();
    properties.deleteAllProperties();
    
    // Update status in the active sheet
    const sheet = SpreadsheetApp.getActiveSheet();
    const sheetConfig = getSheetConfig(sheet);
    if (sheetConfig.statusCol) {
      sheet.getRange(sheetConfig.statusCol + "2").setValue("Processing stopped by user.");
    }
    
    // Show confirmation to user
    const ui = SpreadsheetApp.getUi();
    ui.alert('Success', 'Processing has been stopped and all triggers have been cleared.', ui.ButtonSet.OK);
  } catch (e) {
    console.error('Error stopping processing:', e);
    const ui = SpreadsheetApp.getUi();
    ui.alert('Error', 'Failed to stop processing: ' + e.toString(), ui.ButtonSet.OK);
  }
}

// Function to process evaluation result
function processEvalResult(result) {
  try {
    // Log the raw result for debugging
    console.log("Raw evaluation result:", JSON.stringify(result));
    
    if (!result) {
      return {
        success: false,
        error: "No result received from API",
        isApiCallError: false,
        result: {
          detailedResults: ["No result received from API", "", "", "", "", "", "", ""]
        }
      };
    }
    
    if (!result.success) {
      return {
        success: false,
        error: result.error || result.error_message || "Unknown error",
        isApiCallError: false,
        result: {
          detailedResults: [
            result.error || result.error_message || "Unknown error",
            "", "", "", "", "", "", ""
          ]
        }
      };
    }
    
    // Extract the boolean value directly without using a ternary operator
    const isEquivalent = result.is_equivalent === true;
    
    // Debug log the model and solution results
    console.log("Model result:", JSON.stringify(result.model));
    console.log("Solution result:", JSON.stringify(result.solution));
    
    // Helper function to safely join arrays
    const safeJoin = (arr) => {
      if (!arr) return "";
      if (!Array.isArray(arr)) return String(arr);
      return arr.join("; ");
    };
    
    // Helper function to safely get nested property
    const safeGet = (obj, path) => {
      if (!obj) return "";
      const parts = path.split('.');
      let current = obj;
      for (const part of parts) {
        if (current === null || current === undefined) return "";
        current = current[part];
      }
      return current || "";
    };
    
    // Prepare the detailed results (everything except the equivalence value)
    const detailedResults = [
      result.error_message || "",                                                // Error message
      result.model_name || "",                                                  // Model name
      safeJoin(safeGet(result, 'model.evaluation_results')),                    // Model evaluation results
      safeJoin(safeGet(result, 'solution.evaluation_results')),                 // Solution evaluation results
      safeJoin(safeGet(result, 'model.extracted_solutions')),                   // Model extracted solutions
      safeJoin(safeGet(result, 'model.intermediate_expressions')),              // Model expressions
      safeJoin(safeGet(result, 'solution.extracted_solutions')),                // Solution extracted solutions
      safeJoin(safeGet(result, 'solution.intermediate_expressions'))            // Solution expressions
    ];
    
    // Debug log the detailed results
    console.log("Detailed results:", JSON.stringify(detailedResults));
    
    return {
      success: true,
      result: {
        is_equivalent: isEquivalent,
        model_response: result.model_response || "",
        error_message: result.error_message || "",
        model_result: result.model || {},
        solution_result: result.solution || {},
        model_name: result.model_name || "",
        detailedResults: detailedResults
      }
    };
  } catch (e) {
    console.error("Error processing result:", e);
    return {
      success: false,
      error: `Error processing result: ${e.toString()}`,
      isApiCallError: false,
      result: {
        detailedResults: [
          "Error processing result: " + e.toString(),
          "", "", "", "", "", "", ""
        ]
      }
    };
  }
}

// Function to call the evaluation API
function callEvalAPI(problem, solution, parameters, model) {
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) {
      return {
        success: false,
        error: "API URL not configured",
        isApiCallError: true
      };
    }
    
    console.log("Calling API with:", {
      input: problem,
      solution: solution,
      parameters: parameters || "",
      model: model
    });
    
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
    
    console.log("API Response Code:", response.getResponseCode());
    console.log("API Response Text:", response.getContentText());
    
    const result = JSON.parse(response.getContentText());
    console.log("Parsed API Response:", JSON.stringify(result));
    
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

// Function to clear output cells for a specific row
function clearOutputCells(sheet, row, sheetConfig, model) {
  // Clear only the equivalence cell for the specific model
  if (model === "Gemini 2.0 Flash") {
    sheet.getRange(sheetConfig.geminiFlashEquivCol + row).clearContent();
  } else if (model === "Gemini 2.0 Flash Thinking") {
    sheet.getRange(sheetConfig.geminiFlashThinkingEquivCol + row).clearContent();
  } else if (model === "Gemini 2.5 Flash Thinking") {
    sheet.getRange(sheetConfig.gemini25FlashThinkingEquivCol + row).clearContent();
  } else if (model === "Gemini 2.5 Pro Preview") {
    sheet.getRange(sheetConfig.gemini25ProPreviewEquivCol + row).clearContent();
  } else if (model === "GPT-4o") {
    sheet.getRange(sheetConfig.gpt4oEquivCol + row).clearContent();
  } else if (model === "GPT-4o-mini") {
    sheet.getRange(sheetConfig.gpt4oMiniEquivCol + row).clearContent();
  } else if (model === "GPT-o3-mini") {
    sheet.getRange(sheetConfig.gptO3MiniEquivCol + row).clearContent();
  } else if (model === "GPT-o1-mini") {
    sheet.getRange(sheetConfig.gptO1MiniEquivCol + row).clearContent();
  } else if (model === "GPT-o1") {
    sheet.getRange(sheetConfig.gptO1EquivCol + row).clearContent();
  }
  
  // Clear the detailed output cells
  const outputCol = sheet.getRange(sheetConfig.evalOutputStartCol + row).getColumn();
  const numColumns = 8; // Number of detailed output columns
  sheet.getRange(row, outputCol, 1, numColumns).clearContent();
  
  // Clear the model response column
  let responseCol;
  if (model === "Gemini 2.0 Flash") {
    responseCol = sheetConfig.geminiFlashCol;
  } else if (model === "Gemini 2.0 Flash Thinking") {
    responseCol = sheetConfig.geminiFlashThinkingCol;
  } else if (model === "Gemini 2.5 Flash Thinking") {
    responseCol = sheetConfig.gemini25FlashThinkingCol;
  } else if (model === "Gemini 2.5 Pro Preview") {
    responseCol = sheetConfig.gemini25ProPreviewCol;
  } else if (model === "GPT-4o") {
    responseCol = sheetConfig.gpt4oCol;
  } else if (model === "GPT-4o-mini") {
    responseCol = sheetConfig.gpt4oMiniCol;
  } else if (model === "GPT-o3-mini") {
    responseCol = sheetConfig.gptO3MiniCol;
  } else if (model === "GPT-o1-mini") {
    responseCol = sheetConfig.gptO1MiniCol;
  } else if (model === "GPT-o1") {
    responseCol = sheetConfig.gptO1Col;
  }
  
  if (responseCol) {
    sheet.getRange(responseCol + row).clearContent();
  }
}

// Function to get enabled models for a sheet
function getEnabledModels(sheet) {
  const documentProperties = PropertiesService.getDocumentProperties();
  const enabledModels = documentProperties.getProperty('ENABLED_MODELS');
  
  if (enabledModels) {
    return JSON.parse(enabledModels);
  }
  
  // Default to only Gemini 2.0 models enabled for public use
  return {
    "Gemini 2.0 Flash": true,
    "Gemini 2.0 Flash Thinking": true,
    "Gemini 2.5 Flash Thinking": false,
    "Gemini 2.5 Pro Preview": false,
    "GPT-4o": false,
    "GPT-4o-mini": false,
    "GPT-o3-mini": false,
    "GPT-o1-mini": false,
    "GPT-o1": false
  };
}

// Function to get all available models (admin only)
function getAllModels() {
  return {
    "Gemini 2.0 Flash": true,
    "Gemini 2.0 Flash Thinking": true,
    "Gemini 2.5 Flash Thinking": true,
    "Gemini 2.5 Pro Preview": true,
    "GPT-4o": true,
    "GPT-4o-mini": true,
    "GPT-o3-mini": true,
    "GPT-o1-mini": true,
    "GPT-o1": true
  };
}

// Function to set enabled models for a sheet
function setEnabledModels(sheet, models) {
  const documentProperties = PropertiesService.getDocumentProperties();
  documentProperties.setProperty('ENABLED_MODELS', JSON.stringify(models));
}

// Function to process multiple rows automatically
function processMultipleRows() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Check if API URL is configured
  if (!getApiBaseUrl()) {
    ui.alert('Error', 'API URL is not configured. Please contact an administrator.', ui.ButtonSet.OK);
    return;
  }
  
  // Get column assignments for this specific sheet
  const sheetConfig = getSheetConfig(sheet);
  
  // Get stored configuration
  const properties = PropertiesService.getScriptProperties();
  const storedConfig = properties.getProperties();
  
  // Generate a unique job ID for this processing run
  const jobId = Utilities.getUuid();
  
  // Check if we're resuming the same sheet and job
  const isResuming = storedConfig[`${jobId}_startRow`] && 
                    storedConfig[`${jobId}_model`] && 
                    storedConfig[`${jobId}_sheetId`] === sheet.getSheetId().toString();
  
  let start, model;
  if (isResuming) {
    start = parseInt(storedConfig[`${jobId}_startRow`]);
    model = storedConfig[`${jobId}_model`];
    console.log(`Resuming processing from row ${start} with model ${model}`);
  } else {
    // Get all available models (admin version)
    const availableModels = Object.keys(getAllModels());
    
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
    
    model = availableModels[modelIndex];
    
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
    start = parseInt(startRow);
    
    if (isNaN(start) || start < 1) {
      ui.alert('Invalid start row number');
      return;
    }
  }
  
  // Store configuration in Properties Service for trigger continuation
  properties.setProperties({
    [`${jobId}_startRow`]: start.toString(),
    [`${jobId}_sheetId`]: sheet.getSheetId().toString(),
    [`${jobId}_model`]: model
  });
  
  // Set up trigger for continuation with unique job ID
  const trigger = ScriptApp.newTrigger('processMultipleRows')
    .timeBased()
    .after(6 * 60 * 1000) // 6 minutes
    .create();
  
  // Store the job ID with the trigger
  properties.setProperty(`trigger_${trigger.getUniqueId()}`, jobId);
  
  // Process rows until we find an empty problem cell
  let currentRow = start;
  let processedCount = 0;
  let errorCount = 0;
  const MAX_ERRORS = 3; // Maximum number of consecutive errors before stopping
  
  while (true) {
    // Update status
    sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`Preparing evaluation for ${model}...`);
    SpreadsheetApp.flush();
    
    const problem = sheet.getRange(sheetConfig.promptCol + currentRow).getValue();
    if (!problem) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Stopped: Empty problem cell");
      break;
    }
    
    const solution = sheet.getRange(sheetConfig.solutionCol + currentRow).getValue();
    const parameters = sheet.getRange(sheetConfig.paramsCol + currentRow).getValue();
    
    if (!solution) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Skipped: Empty solution cell");
      currentRow++;
      continue;
    }

    // Check if we need to verify 2.0 Flash Thinking Equiv
    const needsVerification = [
      "Gemini 2.5 Flash Thinking",
      "Gemini 2.5 Pro Preview",
      "GPT-4o",
      "GPT-4o-mini",
      "GPT-o3-mini",
      "GPT-o1-mini",
      "GPT-o1"
    ].includes(model);

    if (needsVerification) {
      // Get the value from 2.0 Flash Thinking Equiv column
      const flashThinkingEquiv = sheet.getRange(sheetConfig.geminiFlashThinkingEquivCol + currentRow).getValue();
      
      // If it's not FALSE, skip processing
      if (flashThinkingEquiv !== false) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`Skipped: 2.0 Flash Thinking Equiv is not FALSE (value: ${flashThinkingEquiv})`);
        currentRow++;
        continue;
      }
    }
    
    try {
      // Clear previous results before processing
      clearOutputCells(sheet, currentRow, sheetConfig, model);
      
      // Update status to show we're making the API call
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`Sending request to ${model}...`);
      SpreadsheetApp.flush();
      
      const apiResult = callEvalAPI(problem, solution, parameters, model);
      
      // Get the correct response column based on model
      let responseCol;
      if (model === "Gemini 2.0 Flash") {
        responseCol = sheetConfig.geminiFlashCol;
      } else if (model === "Gemini 2.0 Flash Thinking") {
        responseCol = sheetConfig.geminiFlashThinkingCol;
      } else if (model === "Gemini 2.5 Flash Thinking") {
        responseCol = sheetConfig.gemini25FlashThinkingCol;
      } else if (model === "Gemini 2.5 Pro Preview") {
        responseCol = sheetConfig.gemini25ProPreviewCol;
      } else if (model === "GPT-4o") {
        responseCol = sheetConfig.gpt4oCol;
      } else if (model === "GPT-4o-mini") {
        responseCol = sheetConfig.gpt4oMiniCol;
      } else if (model === "GPT-o3-mini") {
        responseCol = sheetConfig.gptO3MiniCol;
      } else if (model === "GPT-o1-mini") {
        responseCol = sheetConfig.gptO1MiniCol;
      } else if (model === "GPT-o1") {
        responseCol = sheetConfig.gptO1Col;
      }
      
      // Write the model response if available
      if (responseCol && apiResult.result && apiResult.result.model_response) {
        sheet.getRange(responseCol + currentRow).setValue(apiResult.result.model_response);
      }
      
      // Process the evaluation result
      const processedResult = processEvalResult(apiResult.result);
      
      // Get the correct equivalence column based on model
      let equivalenceCol;
      if (model === "Gemini 2.0 Flash") {
        equivalenceCol = sheetConfig.geminiFlashEquivCol;
      } else if (model === "Gemini 2.0 Flash Thinking") {
        equivalenceCol = sheetConfig.geminiFlashThinkingEquivCol;
      } else if (model === "Gemini 2.5 Flash Thinking") {
        equivalenceCol = sheetConfig.gemini25FlashThinkingEquivCol;
      } else if (model === "Gemini 2.5 Pro Preview") {
        equivalenceCol = sheetConfig.gemini25ProPreviewEquivCol;
      } else if (model === "GPT-4o") {
        equivalenceCol = sheetConfig.gpt4oEquivCol;
      } else if (model === "GPT-4o-mini") {
        equivalenceCol = sheetConfig.gpt4oMiniEquivCol;
      } else if (model === "GPT-o3-mini") {
        equivalenceCol = sheetConfig.gptO3MiniEquivCol;
      } else if (model === "GPT-o1-mini") {
        equivalenceCol = sheetConfig.gptO1MiniEquivCol;
      } else if (model === "GPT-o1") {
        equivalenceCol = sheetConfig.gptO1EquivCol;
      }
      
      // Write the equivalence result
      if (equivalenceCol) {
        if (!processedResult.success) {
          // Write just "ERROR" to equivalence column
          sheet.getRange(equivalenceCol + currentRow).setValue("ERROR");
        } else if (typeof processedResult.result.is_equivalent === 'boolean') {
          // Write True/False based on equivalence result
          sheet.getRange(equivalenceCol + currentRow).setValue(processedResult.result.is_equivalent ? "True" : "False");
        } else {
          // Write ERROR if is_equivalent is not a boolean
          sheet.getRange(equivalenceCol + currentRow).setValue("ERROR");
        }
      }
      
      // Always write detailed results if available
      const detailedOutputCol = sheetConfig.evalOutputStartCol;
      if (detailedOutputCol) {
        // Debug logging
        console.log("Model result:", JSON.stringify(processedResult.result.model_result));
        console.log("Solution result:", JSON.stringify(processedResult.result.solution_result));
        
        const detailedResults = processedResult.result.detailedResults;
        const outputCol = sheet.getRange(detailedOutputCol + currentRow).getColumn();
        const numColumns = detailedResults.length;
        const outputRange = sheet.getRange(currentRow, outputCol, 1, numColumns);
        outputRange.setValues([detailedResults]);
      }
      
      // Update status with detailed completion message
      if (!processedResult.success) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: Processing Error - ${processedResult.error}`);
        errorCount++;
        if (errorCount >= MAX_ERRORS) {
          sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: Stopped due to ${MAX_ERRORS} consecutive errors`);
          break;
        }
      } else {
        const equivStatus = processedResult.result.is_equivalent ? "Equivalent" : "Not Equivalent";
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: Complete - ${equivStatus}`);
        errorCount = 0; // Reset error count on success
      }
      SpreadsheetApp.flush();
      
      // Increment processed count for successful processing
      processedCount++;
      
      // Add delay between requests
      Utilities.sleep(CONFIG.DELAY_MS);
      currentRow++;
    } catch (e) {
      const errorMsg = e.toString();
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: System Error - ${errorMsg}`);
      errorCount++;
      if (errorCount >= MAX_ERRORS) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: Stopped due to ${MAX_ERRORS} consecutive errors`);
        break;
      }
      currentRow++; // Continue to next row even after error
    }
  }
  
  // Add final status message with summary
  const endRow = currentRow - 1;
  sheet.getRange(sheetConfig.statusCol + start).setValue(
    `Completed ${processedCount} rows (${start} to ${endRow}) with ${model}`
  );
  
  // Clean up trigger and job properties
  try {
    const triggers = ScriptApp.getProjectTriggers();
    for (const t of triggers) {
      if (t.getHandlerFunction() === 'processMultipleRows') {
        const triggerJobId = properties.getProperty(`trigger_${t.getUniqueId()}`);
        if (triggerJobId === jobId) {
          ScriptApp.deleteTrigger(t);
          properties.deleteProperty(`trigger_${t.getUniqueId()}`);
        }
      }
    }
  } catch (e) {
    console.error('Error cleaning up trigger:', e);
  }
  
  // Clear only this job's stored configuration
  properties.deleteProperty(`${jobId}_startRow`);
  properties.deleteProperty(`${jobId}_sheetId`);
  properties.deleteProperty(`${jobId}_model`);
}

// Update the onOpen function to use the new function names
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const menu = ui.createMenu('LLM Evaluation')
    .addItem('Process Single Row', 'processRow')
    .addItem('Process Specific Rows', 'processSpecificRows')
    .addItem('View Current Prompt Suffix', 'viewPromptSuffix')
    .addItem('Update Prompt Suffix', 'updatePromptSuffix');
  
  // Only show admin options to admins
  if (isAdmin()) {
    menu.addSeparator()
      .addItem('Admin: Process Single Row', 'adminProcessRow')
      .addItem('Admin: Process Multiple Rows', 'processMultipleRows')
      .addItem('Admin: Stop Processing', 'stopProcessing')
      .addItem('Admin: Configure API URL', 'adminConfigureApiUrl')
      .addItem('Admin: View Column Configuration', 'viewColumnConfig')
      .addItem('Admin: Setup Basic Columns', 'setupBasicColumns')
      .addItem('Admin: Setup Model Columns', 'setupModelColumns')
      .addItem('Admin: Auto-Configure Columns', 'autoConfigureColumns')
      .addItem('Admin: Toggle Model Availability', 'toggleModelAvailability');
  }
  
  menu.addToUi();
  
  // Register custom functions on open
  registerCustomFunctions();
}

// Function to view current prompt suffix
function viewPromptSuffix() {
  const ui = SpreadsheetApp.getUi();
  const scriptProperties = PropertiesService.getScriptProperties();
  const currentSuffix = scriptProperties.getProperty('PROMPT_SUFFIX') || '';
  
  ui.alert(
    'Current Prompt Suffix',
    `The current prompt suffix is:\n\n${currentSuffix}`,
    ui.ButtonSet.OK
  );
}

// Function to update prompt suffix
function updatePromptSuffix() {
  const ui = SpreadsheetApp.getUi();
  const scriptProperties = PropertiesService.getScriptProperties();
  const currentSuffix = scriptProperties.getProperty('PROMPT_SUFFIX') || '';
  
  const response = ui.prompt(
    'Update Prompt Suffix',
    `Current suffix:\n${currentSuffix}\n\nEnter new prompt suffix:`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() === ui.Button.OK) {
    const newSuffix = response.getResponseText().trim();
    scriptProperties.setProperty('PROMPT_SUFFIX', newSuffix);
    ui.alert('Success', 'Prompt suffix has been updated.', ui.ButtonSet.OK);
  }
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
    
    // Register the functions silently
    SpreadsheetApp.getActive().getCustomFunctions().register(renderLatexFunction);
    SpreadsheetApp.getActive().getCustomFunctions().register(parseFunction);
    SpreadsheetApp.getActive().getCustomFunctions().register(parseLatexFunction);
  } catch (e) {
    console.error('Error in registerCustomFunctions: ' + e.toString());
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
  
  // Create new configuration starting with undefined values
  const newConfig = { ...CONFIG.DEFAULT_COLUMNS };
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
  
  // Show success message with configured columns
  const statusMessage = Object.entries(newConfig)
    .filter(([_, value]) => value !== undefined) // Only show configured values
    .map(([key, value]) => `${key}=${value}`)
    .join(', ');
  
  ui.alert('Success', `Configured ${configuredColumns} columns based on row 1 headers:\n${statusMessage}`, ui.ButtonSet.OK);
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

// Function to view current column configuration
function viewColumnConfig() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Create a formatted message showing all column assignments
  const message = `Current column configuration for sheet "${sheet.getName()}":\n\n` +
    `Basic Columns:\n` +
    `- Prompt: ${sheetConfig.promptCol}\n` +
    `- Solution: ${sheetConfig.solutionCol}\n` +
    `- Parameters: ${sheetConfig.paramsCol}\n` +
    `- Status: ${sheetConfig.statusCol}\n` +
    `- Parser Check: ${sheetConfig.parserCheckCol}\n\n` +
    `Model Response Columns:\n` +
    `- Gemini 2.0 Flash: ${sheetConfig.geminiFlashCol}\n` +
    `- Gemini 2.0 Flash Thinking: ${sheetConfig.geminiFlashThinkingCol}\n` +
    `- Gemini 2.5 Flash Thinking: ${sheetConfig.gemini25FlashThinkingCol}\n` +
    `- Gemini 2.5 Pro Preview: ${sheetConfig.gemini25ProPreviewCol}\n` +
    `- GPT-4o: ${sheetConfig.gpt4oCol}\n` +
    `- GPT-4o-mini: ${sheetConfig.gpt4oMiniCol}\n` +
    `- GPT-o3-mini: ${sheetConfig.gptO3MiniCol}\n` +
    `- GPT-o1-mini: ${sheetConfig.gptO1MiniCol}\n` +
    `- GPT-o1: ${sheetConfig.gptO1Col}\n\n` +
    `Equivalence Columns:\n` +
    `- Gemini 2.0 Flash: ${sheetConfig.geminiFlashEquivCol}\n` +
    `- Gemini 2.0 Flash Thinking: ${sheetConfig.geminiFlashThinkingEquivCol}\n` +
    `- Gemini 2.5 Flash Thinking: ${sheetConfig.gemini25FlashThinkingEquivCol}\n` +
    `- Gemini 2.5 Pro Preview: ${sheetConfig.gemini25ProPreviewEquivCol}\n` +
    `- GPT-4o: ${sheetConfig.gpt4oEquivCol}\n` +
    `- GPT-4o-mini: ${sheetConfig.gpt4oMiniEquivCol}\n` +
    `- GPT-o3-mini: ${sheetConfig.gptO3MiniEquivCol}\n` +
    `- GPT-o1-mini: ${sheetConfig.gptO1MiniEquivCol}\n` +
    `- GPT-o1: ${sheetConfig.gptO1EquivCol}\n\n` +
    `Evaluation Output:\n` +
    `- Start Column: ${sheetConfig.evalOutputStartCol}`;
  
  ui.alert('Column Configuration', message, ui.ButtonSet.OK);
}

// Function to process a row with a specific model
function processRowWithModel(sheet, sheetConfig, model) {
  const ui = SpreadsheetApp.getUi();
  
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

  // Check if we need to verify 2.0 Flash Thinking Equiv
  const needsVerification = [
    "Gemini 2.5 Flash Thinking",
    "Gemini 2.5 Pro Preview",
    "GPT-4o",
    "GPT-4o-mini",
    "GPT-o3-mini",
    "GPT-o1-mini",
    "GPT-o1"
  ].includes(model);

  if (needsVerification) {
    // Get the value from 2.0 Flash Thinking Equiv column
    const flashThinkingEquiv = sheet.getRange(sheetConfig.geminiFlashThinkingEquivCol + row).getValue();
    
    // If it's not FALSE, skip processing
    if (flashThinkingEquiv !== false) {
      sheet.getRange(sheetConfig.statusCol + row).setValue(`Skipped: 2.0 Flash Thinking Equiv is not FALSE (value: ${flashThinkingEquiv})`);
      return;
    }
  }
  
  // Clear output cells before processing
  clearOutputCells(sheet, row, sheetConfig, model);
  
  // Update status
  sheet.getRange(sheetConfig.statusCol + row).setValue(`Preparing evaluation for ${model}...`);
  SpreadsheetApp.flush();
  
  // Get values from specified columns
  const problem = sheet.getRange(sheetConfig.promptCol + row).getValue();
  const solution = sheet.getRange(sheetConfig.solutionCol + row).getValue();
  const parameters = sheet.getRange(sheetConfig.paramsCol + row).getValue();
  
  if (!problem || !solution) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: Empty input cell");
    return;
  }
  
  try {
    // Clear previous results before processing
    clearOutputCells(sheet, row, sheetConfig, model);
    
    // Update status to show we're making the API call
    sheet.getRange(sheetConfig.statusCol + row).setValue(`Sending request to ${model}...`);
    SpreadsheetApp.flush();
    
    const apiResult = callEvalAPI(problem, solution, parameters, model);
    
    // Get the correct response column based on model
    let responseCol;
    if (model === "Gemini 2.0 Flash") {
      responseCol = sheetConfig.geminiFlashCol;
    } else if (model === "Gemini 2.0 Flash Thinking") {
      responseCol = sheetConfig.geminiFlashThinkingCol;
    } else if (model === "Gemini 2.5 Flash Thinking") {
      responseCol = sheetConfig.gemini25FlashThinkingCol;
    } else if (model === "Gemini 2.5 Pro Preview") {
      responseCol = sheetConfig.gemini25ProPreviewCol;
    } else if (model === "GPT-4o") {
      responseCol = sheetConfig.gpt4oCol;
    } else if (model === "GPT-4o-mini") {
      responseCol = sheetConfig.gpt4oMiniCol;
    } else if (model === "GPT-o3-mini") {
      responseCol = sheetConfig.gptO3MiniCol;
    } else if (model === "GPT-o1-mini") {
      responseCol = sheetConfig.gptO1MiniCol;
    } else if (model === "GPT-o1") {
      responseCol = sheetConfig.gptO1Col;
    }
    
    // Write the model response if available
    if (responseCol && apiResult.result && apiResult.result.model_response) {
      sheet.getRange(responseCol + row).setValue(apiResult.result.model_response);
    }
    
    // Process the evaluation result
    const processedResult = processEvalResult(apiResult.result);
    
    // Get the correct equivalence column based on model
    let equivalenceCol;
    if (model === "Gemini 2.0 Flash") {
      equivalenceCol = sheetConfig.geminiFlashEquivCol;
    } else if (model === "Gemini 2.0 Flash Thinking") {
      equivalenceCol = sheetConfig.geminiFlashThinkingEquivCol;
    } else if (model === "Gemini 2.5 Flash Thinking") {
      equivalenceCol = sheetConfig.gemini25FlashThinkingEquivCol;
    } else if (model === "Gemini 2.5 Pro Preview") {
      equivalenceCol = sheetConfig.gemini25ProPreviewEquivCol;
    } else if (model === "GPT-4o") {
      equivalenceCol = sheetConfig.gpt4oEquivCol;
    } else if (model === "GPT-4o-mini") {
      equivalenceCol = sheetConfig.gpt4oMiniEquivCol;
    } else if (model === "GPT-o3-mini") {
      equivalenceCol = sheetConfig.gptO3MiniEquivCol;
    } else if (model === "GPT-o1-mini") {
      equivalenceCol = sheetConfig.gptO1MiniEquivCol;
    } else if (model === "GPT-o1") {
      equivalenceCol = sheetConfig.gptO1EquivCol;
    }
    
    // Write the equivalence result
    if (equivalenceCol) {
      if (!processedResult.success) {
        // Write just "ERROR" to equivalence column
        sheet.getRange(equivalenceCol + row).setValue("ERROR");
      } else if (typeof processedResult.result.is_equivalent === 'boolean') {
        // Write True/False based on equivalence result
        sheet.getRange(equivalenceCol + row).setValue(processedResult.result.is_equivalent ? "True" : "False");
      } else {
        // Write ERROR if is_equivalent is not a boolean
        sheet.getRange(equivalenceCol + row).setValue("ERROR");
      }
    }
    
    // Always write detailed results if available
    const detailedOutputCol = sheetConfig.evalOutputStartCol;
    if (detailedOutputCol) {
      // Debug logging
      console.log("Model result:", JSON.stringify(processedResult.result.model_result));
      console.log("Solution result:", JSON.stringify(processedResult.result.solution_result));
      
      const detailedResults = processedResult.result.detailedResults;
      const outputCol = sheet.getRange(detailedOutputCol + row).getColumn();
      const numColumns = detailedResults.length;
      const outputRange = sheet.getRange(row, outputCol, 1, numColumns);
      outputRange.setValues([detailedResults]);
    }
    
    // Update status with detailed completion message
    if (!processedResult.success) {
      sheet.getRange(sheetConfig.statusCol + row).setValue(`${model}: Processing Error - ${processedResult.error}`);
    } else {
      const equivStatus = processedResult.result.is_equivalent ? "Equivalent" : "Not Equivalent";
      sheet.getRange(sheetConfig.statusCol + row).setValue(`${model}: Complete - ${equivStatus}`);
    }
    SpreadsheetApp.flush();
  } catch (e) {
    const errorMsg = e.toString();
    sheet.getRange(sheetConfig.statusCol + row).setValue(`${model}: System Error - ${errorMsg}`);
  }
}

// Admin function to process a row with all models available
function adminProcessRow() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  // Check if API URL is configured
  if (!getApiBaseUrl()) {
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
  }
  
  // Get column assignments for this specific sheet
  const sheetConfig = getSheetConfig(sheet);
  
  // Get all available models (admin version)
  const availableModels = Object.keys(getAllModels());
  
  // Create dialog for model selection
  const modelOptions = availableModels.map((model, index) => `${index + 1}. ${model}`).join('\n');
  const modelResponse = ui.prompt(
    'Model Selection (Admin)',
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
  
  // Process the row with the selected model
  processRowWithModel(sheet, sheetConfig, model);
}

// Function for admins to configure the API URL
function adminConfigureApiUrl() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const documentProperties = PropertiesService.getDocumentProperties();
  const currentUrl = documentProperties.getProperty('API_BASE_URL') || '';
  
  const response = ui.prompt(
    'API Configuration (ADMIN ONLY)',
    `Current API URL: ${currentUrl}\n\nEnter new API Base URL:`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() === ui.Button.OK) {
    const newUrl = response.getResponseText().trim();
    if (newUrl) {
      documentProperties.setProperty('API_BASE_URL', newUrl);
      ui.alert('API URL updated successfully!');
    } else {
      ui.alert('API URL cannot be empty.');
    }
  }
}

// Function to process a single row with the selected model
function processRow() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Check if API URL is configured
  if (!getApiBaseUrl()) {
    ui.alert('Error', 'API URL is not configured. Please contact an administrator.', ui.ButtonSet.OK);
    return;
  }
  
  // Get column assignments for this specific sheet
  const sheetConfig = getSheetConfig(sheet);
  
  // Get enabled models for this sheet
  const enabledModels = getEnabledModels(sheet);
  const availableModels = Object.entries(enabledModels)
    .filter(([_, enabled]) => enabled)
    .map(([name]) => name);
  
  if (availableModels.length === 0) {
    ui.alert('Error', 'No models are currently enabled for this sheet.', ui.ButtonSet.OK);
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
  
  // Process the row with the selected model
  processRowWithModel(sheet, sheetConfig, model);
}

// Function to process specific rows with timeout handling
function processSpecificRows() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Check if API URL is configured
  if (!getApiBaseUrl()) {
    ui.alert('Error', 'API URL is not configured. Please contact an administrator.', ui.ButtonSet.OK);
    return;
  }
  
  // Get column assignments for this specific sheet
  const sheetConfig = getSheetConfig(sheet);
  
  // Get all available models (admin version)
  const availableModels = Object.keys(getAllModels());
  
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
  
  // Ask for row numbers
  const response = ui.prompt(
    'Row Selection',
    'Enter row numbers to process (comma-separated):',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const rowNumbers = response.getResponseText()
    .split(',')
    .map(num => parseInt(num.trim()))
    .filter(num => !isNaN(num) && num > 0);
  
  if (rowNumbers.length === 0) {
    ui.alert('Error', 'No valid row numbers provided.', ui.ButtonSet.OK);
    return;
  }
  
  // Generate a unique job ID for this processing run
  const jobId = Utilities.getUuid();
  
  // Store configuration in Properties Service for trigger continuation
  const properties = PropertiesService.getScriptProperties();
  properties.setProperties({
    [`${jobId}_rows`]: JSON.stringify(rowNumbers),
    [`${jobId}_currentIndex`]: '0',
    [`${jobId}_sheetId`]: sheet.getSheetId().toString(),
    [`${jobId}_model`]: model
  });
  
  // Set up trigger for continuation
  const trigger = ScriptApp.newTrigger('processSpecificRowsContinuation')
    .timeBased()
    .after(6 * 60 * 1000) // 6 minutes
    .create();
  
  // Store the job ID with the trigger
  properties.setProperty(`trigger_${trigger.getUniqueId()}`, jobId);
  
  // Start processing
  processNextRow(jobId);
}

// Function to process the next row in the sequence
function processNextRow(jobId) {
  const properties = PropertiesService.getScriptProperties();
  const storedConfig = properties.getProperties();
  
  // Get job configuration
  const rows = JSON.parse(storedConfig[`${jobId}_rows`]);
  const currentIndex = parseInt(storedConfig[`${jobId}_currentIndex`]);
  const sheetId = storedConfig[`${jobId}_sheetId`];
  const model = storedConfig[`${jobId}_model`];
  
  // Get the sheet
  const sheet = SpreadsheetApp.openById(sheetId).getActiveSheet();
  const sheetConfig = getSheetConfig(sheet);
  
  // Check if we've processed all rows
  if (currentIndex >= rows.length) {
    // Clean up
    const triggers = ScriptApp.getProjectTriggers();
    for (const t of triggers) {
      if (t.getHandlerFunction() === 'processSpecificRowsContinuation') {
        const triggerJobId = properties.getProperty(`trigger_${t.getUniqueId()}`);
        if (triggerJobId === jobId) {
          ScriptApp.deleteTrigger(t);
          properties.deleteProperty(`trigger_${t.getUniqueId()}`);
        }
      }
    }
    
    // Clear job properties
    properties.deleteProperty(`${jobId}_rows`);
    properties.deleteProperty(`${jobId}_currentIndex`);
    properties.deleteProperty(`${jobId}_sheetId`);
    properties.deleteProperty(`${jobId}_model`);
    
    // Update status
    sheet.getRange(sheetConfig.statusCol + rows[0]).setValue(
      `Completed processing ${rows.length} rows with ${model}`
    );
    return;
  }
  
  // Process current row
  const currentRow = rows[currentIndex];
  
  try {
    // Update status
    sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`Preparing evaluation for ${model}...`);
    SpreadsheetApp.flush();
    
    const problem = sheet.getRange(sheetConfig.promptCol + currentRow).getValue();
    const solution = sheet.getRange(sheetConfig.solutionCol + currentRow).getValue();
    const parameters = sheet.getRange(sheetConfig.paramsCol + currentRow).getValue();
    
    if (!problem || !solution) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Skipped: Empty input cell");
      // Move to next row
      properties.setProperty(`${jobId}_currentIndex`, (currentIndex + 1).toString());
      processNextRow(jobId);
      return;
    }
    
    // Check if we need to verify 2.0 Flash Thinking Equiv
    const needsVerification = [
      "Gemini 2.5 Flash Thinking",
      "Gemini 2.5 Pro Preview",
      "GPT-4o",
      "GPT-4o-mini",
      "GPT-o3-mini",
      "GPT-o1-mini",
      "GPT-o1"
    ].includes(model);
    
    if (needsVerification) {
      const flashThinkingEquiv = sheet.getRange(sheetConfig.geminiFlashThinkingEquivCol + currentRow).getValue();
      if (flashThinkingEquiv !== false) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`Skipped: 2.0 Flash Thinking Equiv is not FALSE (value: ${flashThinkingEquiv})`);
        // Move to next row
        properties.setProperty(`${jobId}_currentIndex`, (currentIndex + 1).toString());
        processNextRow(jobId);
        return;
      }
    }
    
    // Clear previous results
    clearOutputCells(sheet, currentRow, sheetConfig, model);
    
    // Update status
    sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`Sending request to ${model}...`);
    SpreadsheetApp.flush();
    
    const apiResult = callEvalAPI(problem, solution, parameters, model);
    
    // Process the result
    const processedResult = processEvalResult(apiResult.result);
    
    // Get the correct response column based on model
    let responseCol;
    if (model === "Gemini 2.0 Flash") {
      responseCol = sheetConfig.geminiFlashCol;
    } else if (model === "Gemini 2.0 Flash Thinking") {
      responseCol = sheetConfig.geminiFlashThinkingCol;
    } else if (model === "Gemini 2.5 Flash Thinking") {
      responseCol = sheetConfig.gemini25FlashThinkingCol;
    } else if (model === "Gemini 2.5 Pro Preview") {
      responseCol = sheetConfig.gemini25ProPreviewCol;
    } else if (model === "GPT-4o") {
      responseCol = sheetConfig.gpt4oCol;
    } else if (model === "GPT-4o-mini") {
      responseCol = sheetConfig.gpt4oMiniCol;
    } else if (model === "GPT-o3-mini") {
      responseCol = sheetConfig.gptO3MiniCol;
    } else if (model === "GPT-o1-mini") {
      responseCol = sheetConfig.gptO1MiniCol;
    } else if (model === "GPT-o1") {
      responseCol = sheetConfig.gptO1Col;
    }
    
    // Write the model response if available
    if (responseCol && apiResult.result && apiResult.result.model_response) {
      sheet.getRange(responseCol + currentRow).setValue(apiResult.result.model_response);
    }
    
    // Get the correct equivalence column based on model
    let equivalenceCol;
    if (model === "Gemini 2.0 Flash") {
      equivalenceCol = sheetConfig.geminiFlashEquivCol;
    } else if (model === "Gemini 2.0 Flash Thinking") {
      equivalenceCol = sheetConfig.geminiFlashThinkingEquivCol;
    } else if (model === "Gemini 2.5 Flash Thinking") {
      equivalenceCol = sheetConfig.gemini25FlashThinkingEquivCol;
    } else if (model === "Gemini 2.5 Pro Preview") {
      equivalenceCol = sheetConfig.gemini25ProPreviewEquivCol;
    } else if (model === "GPT-4o") {
      equivalenceCol = sheetConfig.gpt4oEquivCol;
    } else if (model === "GPT-4o-mini") {
      equivalenceCol = sheetConfig.gpt4oMiniEquivCol;
    } else if (model === "GPT-o3-mini") {
      equivalenceCol = sheetConfig.gptO3MiniEquivCol;
    } else if (model === "GPT-o1-mini") {
      equivalenceCol = sheetConfig.gptO1MiniEquivCol;
    } else if (model === "GPT-o1") {
      equivalenceCol = sheetConfig.gptO1EquivCol;
    }
    
    // Write the equivalence result
    if (equivalenceCol) {
      if (!processedResult.success) {
        sheet.getRange(equivalenceCol + currentRow).setValue("ERROR");
      } else if (typeof processedResult.result.is_equivalent === 'boolean') {
        sheet.getRange(equivalenceCol + currentRow).setValue(processedResult.result.is_equivalent ? "True" : "False");
      } else {
        sheet.getRange(equivalenceCol + currentRow).setValue("ERROR");
      }
    }
    
    // Write detailed results if available
    const detailedOutputCol = sheetConfig.evalOutputStartCol;
    if (detailedOutputCol) {
      const detailedResults = processedResult.result.detailedResults;
      const outputCol = sheet.getRange(detailedOutputCol + currentRow).getColumn();
      const numColumns = detailedResults.length;
      const outputRange = sheet.getRange(currentRow, outputCol, 1, numColumns);
      outputRange.setValues([detailedResults]);
    }
    
    // Update status
    if (!processedResult.success) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: Processing Error - ${processedResult.error}`);
    } else {
      const equivStatus = processedResult.result.is_equivalent ? "Equivalent" : "Not Equivalent";
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: Complete - ${equivStatus}`);
    }
    SpreadsheetApp.flush();
    
    // Add delay between requests
    Utilities.sleep(CONFIG.DELAY_MS);
    
    // Move to next row
    properties.setProperty(`${jobId}_currentIndex`, (currentIndex + 1).toString());
    processNextRow(jobId);
    
  } catch (e) {
    const errorMsg = e.toString();
    sheet.getRange(sheetConfig.statusCol + currentRow).setValue(`${model}: System Error - ${errorMsg}`);
    // Move to next row even after error
    properties.setProperty(`${jobId}_currentIndex`, (currentIndex + 1).toString());
    processNextRow(jobId);
  }
}

// Function to handle continuation after timeout
function processSpecificRowsContinuation() {
  const properties = PropertiesService.getScriptProperties();
  const triggers = ScriptApp.getProjectTriggers();
  
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'processSpecificRowsContinuation') {
      const jobId = properties.getProperty(`trigger_${trigger.getUniqueId()}`);
      if (jobId) {
        processNextRow(jobId);
        break;
      }
    }
  }
}
