/**
 * Fuse Antigravity Bridge Server
 * 
 * This service uses the opencode-antigravity-auth plugin directly
 * to make Antigravity API requests, ensuring exact compatibility
 * with OpenCode's authentication and request handling.
 */

import express from 'express';
import { createServer } from 'http';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync, existsSync } from 'fs';

// Get the plugin path
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pluginPath = join(__dirname, '..', '..', 'opencode-antigravity-auth');

// Dynamic import of the plugin modules
let prepareAntigravityRequest;
let transformAntigravityResponse;
let AccountManager;
let ensureProjectContext;
let refreshAccessToken;
let loadAccounts;
let ANTIGRAVITY_ENDPOINT_FALLBACKS;

async function loadPluginModules() {
  const pluginDistPath = join(pluginPath, 'dist');
  
  // Check if dist exists, if not suggest building
  if (!existsSync(pluginDistPath)) {
    console.error('Plugin dist not found. Please build the plugin first:');
    console.error(`cd ${pluginPath} && npm install && npm run build`);
    process.exit(1);
  }
  
  try {
    const requestModule = await import(join(pluginDistPath, 'plugin', 'request.js'));
    const accountsModule = await import(join(pluginDistPath, 'plugin', 'accounts.js'));
    const projectModule = await import(join(pluginDistPath, 'plugin', 'project.js'));
    const tokenModule = await import(join(pluginDistPath, 'plugin', 'token.js'));
    const storageModule = await import(join(pluginDistPath, 'plugin', 'storage.js'));
    const constantsModule = await import(join(pluginDistPath, 'constants.js'));
    
    prepareAntigravityRequest = requestModule.prepareAntigravityRequest;
    transformAntigravityResponse = requestModule.transformAntigravityResponse;
    AccountManager = accountsModule.AccountManager;
    ensureProjectContext = projectModule.ensureProjectContext;
    refreshAccessToken = tokenModule.refreshAccessToken;
    loadAccounts = storageModule.loadAccounts;
    ANTIGRAVITY_ENDPOINT_FALLBACKS = constantsModule.ANTIGRAVITY_ENDPOINT_FALLBACKS;
    
    console.log('Plugin modules loaded successfully');
  } catch (error) {
    console.error('Failed to load plugin modules:', error);
    process.exit(1);
  }
}

const app = express();
app.use(express.json({ limit: '50mb' }));

// Store the account manager instance
let accountManager = null;

// Initialize account manager
async function initAccountManager() {
  if (!accountManager) {
    accountManager = await AccountManager.loadFromDisk();
    console.log(`Loaded ${accountManager.count()} accounts`);
  }
  return accountManager;
}

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'fuse-antigravity-bridge' });
});

/**
 * Get available accounts
 */
app.get('/accounts', async (req, res) => {
  try {
    const manager = await initAccountManager();
    const accounts = [];
    for (let i = 0; i < manager.count(); i++) {
      const account = manager.getAccountByIndex(i);
      if (account) {
        accounts.push({
          index: i,
          email: account.email,
          projectId: account.parts?.managedProjectId || account.parts?.projectId,
        });
      }
    }
    res.json({ accounts });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

/**
 * Make an Antigravity API request
 * 
 * This endpoint mimics the OpenAI-compatible interface but routes through Antigravity
 */
app.post('/v1/chat/completions', async (req, res) => {
  try {
    const manager = await initAccountManager();
    const { model, messages, temperature, max_tokens, stream } = req.body;
    
    // Determine model family (claude vs gemini)
    const modelLower = (model || '').toLowerCase();
    const family = modelLower.includes('claude') ? 'claude' : 'gemini';
    
    // Get the best available account for this model family
    const accountInfo = manager.getActiveAccountForFamily(family);
    if (!accountInfo) {
      return res.status(503).json({ 
        error: { 
          message: 'No available account for ' + family,
          type: 'service_unavailable'
        } 
      });
    }
    
    const { account, index } = accountInfo;
    console.log(`Using account ${index} (${account.email}) for ${family} model: ${model}`);
    
    // Ensure we have valid access token
    let accessToken = account.access;
    const now = Date.now();
    
    if (!accessToken || (account.expires && now >= account.expires - 60000)) {
      console.log('Refreshing access token...');
      try {
        const refreshResult = await refreshAccessToken(account.parts.refreshToken);
        accessToken = refreshResult.access_token;
        manager.updateAccessToken(index, accessToken, refreshResult.expires_in);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        return res.status(401).json({ 
          error: { 
            message: 'Token refresh failed: ' + String(refreshError),
            type: 'authentication_error'
          } 
        });
      }
    }
    
    // Get project context
    const projectContext = await ensureProjectContext({
      access: accessToken,
      refresh: manager.getRefreshTokenForIndex(index),
    });
    
    const projectId = projectContext.effectiveProjectId;
    console.log(`Project ID: ${projectId}`);
    
    // Build the Gemini-style request body
    const contents = messages.map(msg => ({
      role: msg.role === 'assistant' ? 'model' : msg.role === 'system' ? 'user' : msg.role,
      parts: [{ text: msg.content }]
    }));
    
    // Extract system message if present
    const systemMessage = messages.find(m => m.role === 'system');
    
    const geminiRequestBody = {
      contents,
      generationConfig: {
        temperature: temperature || 0.7,
        maxOutputTokens: max_tokens || 8192,
      },
    };
    
    if (systemMessage) {
      geminiRequestBody.systemInstruction = {
        parts: [{ text: systemMessage.content }]
      };
    }
    
    // Prepare the Antigravity request using the plugin's function
    const fakeUrl = `https://generativelanguage.googleapis.com/v1beta/models/${model}:${stream ? 'streamGenerateContent' : 'generateContent'}`;
    
    const prepared = prepareAntigravityRequest(
      fakeUrl,
      {
        method: 'POST',
        body: JSON.stringify(geminiRequestBody),
        headers: { 'Content-Type': 'application/json' },
      },
      accessToken,
      projectId,
      undefined, // endpoint override
      'antigravity', // header style
    );
    
    console.log(`Making request to: ${prepared.endpoint}`);
    console.log(`Effective model: ${prepared.effectiveModel}`);
    
    // Make the actual request
    const response = await fetch(prepared.request, prepared.init);
    
    // Handle rate limit
    if (response.status === 429) {
      console.log(`Rate limit hit for account ${index}, marking as rate limited`);
      manager.markRateLimited(index, family, model);
      
      return res.status(429).json({
        error: {
          message: 'Rate limit exceeded',
          type: 'rate_limit_error'
        }
      });
    }
    
    // Transform the response
    const transformedResponse = await transformAntigravityResponse(
      response,
      prepared.streaming,
      null,
      model,
      projectId,
      prepared.endpoint,
      prepared.effectiveModel,
      prepared.sessionId,
    );
    
    if (!transformedResponse.ok) {
      const errorBody = await transformedResponse.text();
      console.error(`API error: ${transformedResponse.status} ${errorBody}`);
      return res.status(transformedResponse.status).json({
        error: {
          message: errorBody,
          type: 'api_error'
        }
      });
    }
    
    // Parse the response
    const responseBody = await transformedResponse.json();
    
    // Extract text from the response
    let content = '';
    if (responseBody.candidates && responseBody.candidates[0]) {
      const candidate = responseBody.candidates[0];
      if (candidate.content && candidate.content.parts) {
        content = candidate.content.parts
          .filter(p => p.text)
          .map(p => p.text)
          .join('');
      }
    }
    
    // Mark success
    manager.markSuccess(index);
    
    // Return OpenAI-compatible response
    res.json({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: model,
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: content,
        },
        finish_reason: 'stop',
      }],
      usage: {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0,
      }
    });
    
  } catch (error) {
    console.error('Request failed:', error);
    res.status(500).json({
      error: {
        message: String(error),
        type: 'internal_error'
      }
    });
  }
});

/**
 * Raw Antigravity request endpoint (for debugging)
 */
app.post('/v1/raw', async (req, res) => {
  try {
    const manager = await initAccountManager();
    const { model, prompt, account_index } = req.body;
    
    const index = account_index ?? 0;
    const account = manager.getAccountByIndex(index);
    
    if (!account) {
      return res.status(400).json({ error: 'Account not found' });
    }
    
    // Refresh token if needed
    let accessToken = account.access;
    if (!accessToken || (account.expires && Date.now() >= account.expires - 60000)) {
      const refreshResult = await refreshAccessToken(account.parts.refreshToken);
      accessToken = refreshResult.access_token;
      manager.updateAccessToken(index, accessToken, refreshResult.expires_in);
    }
    
    // Get project context
    const projectContext = await ensureProjectContext({
      access: accessToken,
      refresh: manager.getRefreshTokenForIndex(index),
    });
    
    // Try each endpoint
    for (const endpoint of ANTIGRAVITY_ENDPOINT_FALLBACKS) {
      try {
        const url = `${endpoint}/v1internal:generateContent`;
        
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
            'User-Agent': 'antigravity/1.11.5 windows/amd64',
            'X-Goog-Api-Client': 'google-cloud-sdk vscode_cloudshelleditor/0.1',
            'Client-Metadata': '{"ideType":"IDE_UNSPECIFIED","platform":"PLATFORM_UNSPECIFIED","pluginType":"GEMINI"}',
          },
          body: JSON.stringify({
            project: projectContext.effectiveProjectId,
            model: model || 'gemini-3-pro-low',
            request: {
              contents: [{ role: 'user', parts: [{ text: prompt }] }],
              sessionId: `fuse-${Date.now()}`,
            },
            requestType: 'agent',
            userAgent: 'antigravity',
            requestId: `agent-${Date.now()}`,
          }),
        });
        
        const responseBody = await response.json();
        
        return res.json({
          status: response.status,
          endpoint,
          body: responseBody,
        });
        
      } catch (endpointError) {
        console.log(`Endpoint ${endpoint} failed:`, endpointError);
        continue;
      }
    }
    
    res.status(500).json({ error: 'All endpoints failed' });
    
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});

// Start the server
const PORT = process.env.BRIDGE_PORT || 3456;

async function main() {
  await loadPluginModules();
  await initAccountManager();
  
  const server = createServer(app);
  server.listen(PORT, () => {
    console.log(`Fuse Antigravity Bridge running on http://localhost:${PORT}`);
    console.log('Endpoints:');
    console.log('  GET  /health - Health check');
    console.log('  GET  /accounts - List available accounts');
    console.log('  POST /v1/chat/completions - OpenAI-compatible chat endpoint');
    console.log('  POST /v1/raw - Raw Antigravity request');
  });
}

main().catch(console.error);
