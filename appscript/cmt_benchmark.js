// Configuration
const CONFIG = {
  DELAY_MS: 2000,          // Delay between API calls in milliseconds
  MAX_RETRIES: 3,          // Maximum number of retries for timeout errors
  RETRY_DELAY_MS: 5000,    // Delay between retries (5 seconds)
  ADMIN_EMAILS: ["jroggeveen@g.harvard.edu", "ek436@cornell.edu", "mpbrenner@gmail.com"], // Administrator email
  DEFAULT_COLUMNS: {       // Default column assignments
    promptCol: "A",        // Column A for prompt
    statusCol: "M",        // Column M for status
    geminiFlashCol: "N",   // Column N for Gemini 2.0 Flash response
    geminiFlashThinkingCol: "P", // Column P for Gemini 2.0 Flash Thinking response
    gemini25FlashThinkingCol: "R", // Column R for Gemini 2.5 Flash Thinking response
    gpt4oCol: "T",         // Column T for GPT-4o response
    gpt4oMiniCol: "V",     // Column V for GPT-4o-mini response
    gptO3MiniCol: "X",     // Column X for GPT-o3-mini response
    gptO1MiniCol: "Z",     // Column Z for GPT-o1-mini response
    gptO1Col: "AB"         // Column AB for GPT-o1 response
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

// Function to set the admin key (admin only)
function setAdminKey() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const response = ui.prompt(
    'Admin Key Configuration (ADMIN ONLY)',
    'Enter the admin key for API authentication:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() === ui.Button.OK) {
    const adminKey = response.getResponseText().trim();
    if (adminKey) {
      const documentProperties = PropertiesService.getDocumentProperties();
      documentProperties.setProperty('admin_key', adminKey);
      ui.alert('Admin key updated successfully!');
    } else {
      ui.alert('Admin key cannot be empty.');
    }
  }
}

// Function to get the admin key (private)
function getAdminKey() {
  if (!isAdmin()) {
    return null;
  }
  
  const documentProperties = PropertiesService.getDocumentProperties();
  return documentProperties.getProperty('admin_key');
}

// Function to update the prompt suffix (admin only)
function updatePromptSuffix() {
  const ui = SpreadsheetApp.getUi();
  
  // Verify the user is an admin
  if (!isAdmin()) {
    ui.alert('Error', 'You do not have permission to access this function.', ui.ButtonSet.OK);
    return;
  }
  
  const response = ui.prompt(
    'Prompt Suffix Configuration (ADMIN ONLY)',
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
    // For custom functions, we can't use Session.getActiveUser() to check admin status
    // Instead, directly access the API URL from script properties
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

// Function to query LLM for a single row
function queryLLM() {
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
  
  // Create a simple dialog with radio buttons
  const modelOptions = availableModels.map((model, index) => 
    `[${index + 1}] ${model}`
  ).join('\n');
  
  const modelResponse = ui.prompt(
    'Select Model',
    'Please select a model by entering its number:\n\n' + modelOptions,
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
  
  // Now ask for the row number
  const rowResponse = ui.prompt(
    'Row Selection',
    'Please enter the row number to process:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (rowResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  // Parse row number
  const rowNum = rowResponse.getResponseText().trim();
  const row = parseInt(rowNum);
  if (isNaN(row) || row < 1) {
    ui.alert('Invalid row number');
    return;
  }
  
  // Update status
  sheet.getRange(sheetConfig.statusCol + row).setValue("Processing...");
  
  // Get prompt from the specified column
  const prompt = sheet.getRange(sheetConfig.promptCol + row).getValue();
  
  if (!prompt) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: Empty prompt");
    return;
  }
  
  try {
    // Call the query API
    const apiResult = callQueryAPI(prompt, model);
    
    if (!apiResult.success) {
      sheet.getRange(sheetConfig.statusCol + row).setValue("Error: " + (apiResult.error || "API call failed"));
    } else {
      // Determine which column to write the response to
      let responseCol;
      if (model === "Gemini 2.0 Flash") {
        responseCol = sheetConfig.geminiFlashCol;
      } else if (model === "Gemini 2.0 Flash Thinking") {
        responseCol = sheetConfig.geminiFlashThinkingCol;
      } else if (model === "Gemini 2.5 Flash Thinking") {
        responseCol = sheetConfig.gemini25FlashThinkingCol;
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
      
      // Write the model response to the appropriate column
      sheet.getRange(responseCol + row).setValue(apiResult.result.response || "");
      
      // Update status
      sheet.getRange(sheetConfig.statusCol + row).setValue("Complete");
    }
  } catch (e) {
    sheet.getRange(sheetConfig.statusCol + row).setValue("Error: " + e.toString());
  }
}

// Function to call the query API
function callQueryAPI(prompt, model) {
  try {
    const apiBaseUrl = getApiBaseUrl();
    if (!apiBaseUrl) {
      return {
        success: false,
        error: "API URL not configured"
      };
    }
    
    // Get the prompt suffix and append it to the prompt
    const promptSuffix = getPromptSuffix();
    const fullPrompt = promptSuffix ? `${prompt} ${promptSuffix}` : prompt;
    
    const response = UrlFetchApp.fetch(apiBaseUrl + "/query", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({
        prompt: fullPrompt,
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
    `Status column (current: ${sheetConfig.statusCol}):\n` +
    `Gemini 2.0 Flash response column (current: ${sheetConfig.geminiFlashCol}):\n` +
    `Gemini 2.0 Flash Thinking response column (current: ${sheetConfig.geminiFlashThinkingCol}):\n` +
    `Gemini 2.5 Flash Thinking response column (current: ${sheetConfig.gemini25FlashThinkingCol}):\n` +
    `GPT-4o response column (current: ${sheetConfig.gpt4oCol}):\n` +
    `GPT-4o-mini response column (current: ${sheetConfig.gpt4oMiniCol}):\n` +
    `GPT-o3-mini response column (current: ${sheetConfig.gptO3MiniCol}):\n` +
    `GPT-o1-mini response column (current: ${sheetConfig.gptO1MiniCol}):\n` +
    `GPT-o1 response column (current: ${sheetConfig.gptO1Col}):\n\n` +
    `Enter column letters separated by commas (e.g., A,M,N,P,R,T,V,X,Z,AB):`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const columns = response.getResponseText().split(',').map(col => col.trim().toUpperCase());
  
  if (columns.length !== 10) {
    ui.alert('Error', 'Please provide exactly 10 column letters.', ui.ButtonSet.OK);
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
    statusCol: columns[1],
    geminiFlashCol: columns[2],
    geminiFlashThinkingCol: columns[3],
    gemini25FlashThinkingCol: columns[4],
    gpt4oCol: columns[5],
    gpt4oMiniCol: columns[6],
    gptO3MiniCol: columns[7],
    gptO1MiniCol: columns[8],
    gptO1Col: columns[9]
  };
  
  saveSheetConfig(sheet, newConfig);
  
  // Display configuration in the status column
  sheet.getRange(newConfig.statusCol + "1").setValue(
    `Columns: Prompt=${columns[0]}, Status=${columns[1]}, ` +
    `Flash=${columns[2]}, FlashT=${columns[3]}, Flash25T=${columns[4]}, ` +
    `GPT4o=${columns[5]}, GPT4oM=${columns[6]}, GPT3M=${columns[7]}, ` +
    `GPT1M=${columns[8]}, GPT1=${columns[9]}`
  );
  
  ui.alert('Success', `Sheet "${sheet.getName()}" configured with columns:\n` +
    `Prompt: ${newConfig.promptCol}\n` +
    `Status: ${newConfig.statusCol}\n` +
    `Gemini 2.0 Flash: ${newConfig.geminiFlashCol}\n` +
    `Gemini 2.0 Flash Thinking: ${newConfig.geminiFlashThinkingCol}\n` +
    `Gemini 2.5 Flash Thinking: ${newConfig.gemini25FlashThinkingCol}\n` +
    `GPT-4o: ${newConfig.gpt4oCol}\n` +
    `GPT-4o-mini: ${newConfig.gpt4oMiniCol}\n` +
    `GPT-o3-mini: ${newConfig.gptO3MiniCol}\n` +
    `GPT-o1-mini: ${newConfig.gptO1MiniCol}\n` +
    `GPT-o1: ${newConfig.gptO1Col}`, ui.ButtonSet.OK);
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
    // Update status
    sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Processing...");
    
    // Get prompt from the specified column
    const prompt = sheet.getRange(sheetConfig.promptCol + currentRow).getValue();
    
    if (!prompt) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Skipped: Empty prompt");
      continue;
    }
    
    try {
      // Call the query API
      const apiResult = callQueryAPI(prompt, model);
      
      if (!apiResult.success) {
        sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: " + (apiResult.error || "API call failed"));
      } else {
        // Determine which column to write the response to
        let responseCol;
        if (model === "Gemini 2.0 Flash") {
          responseCol = sheetConfig.geminiFlashCol;
        } else if (model === "Gemini 2.0 Flash Thinking") {
          responseCol = sheetConfig.geminiFlashThinkingCol;
        } else if (model === "Gemini 2.5 Flash Thinking") {
          responseCol = sheetConfig.gemini25FlashThinkingCol;
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
        
        // Write the model response to the appropriate column - now using just response property
        sheet.getRange(responseCol + currentRow).setValue(apiResult.result.response || "");
      }
      
      // Update status
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Complete");
      
      // Add delay between requests
      Utilities.sleep(CONFIG.DELAY_MS);
    } catch (e) {
      sheet.getRange(sheetConfig.statusCol + currentRow).setValue("Error: " + e.toString());
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
    .addItem('View Current Prompt Suffix', 'viewPromptSuffix');
  
  // Only show admin options to admins
  if (isAdmin()) {
    menu.addSeparator()
      .addItem('Admin: Configure API URL', 'adminConfigureApiUrl')
      .addItem('Admin: Set Admin Key', 'setAdminKey')
      .addItem('Admin: Update Prompt Suffix', 'updatePromptSuffix')
      .addItem('Admin: Setup Columns', 'setupColumns')
      .addItem('Admin: Toggle Model Availability', 'toggleModelAvailability');
  }
  
  menu.addToUi();
} 