import json
import logging
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from google import genai
from openai import OpenAI
from fuse.config import settings
from fuse.utils.circuit_breaker import CircuitBreakerOpenError, CircuitBreakers
import httpx

logger = logging.getLogger(__name__)
# Import nodes to ensure they are registered
import fuse.workflows.engine.nodes  # noqa

# No longer importing WorkflowNodePublic, WorkflowEdgePublic, NodeData as we use V2 structure in response parsing
from fuse.workflows.engine.nodes.registry import NodeRegistry


class AIWorkflowService:
    def __init__(self):
        # Initialize AI clients using settings
        self.gemini_api_key = settings.GOOGLE_AI_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY

        # Initialize models as None
        self.gemini_client = None
        self.openai_client = None
        self.anthropic_client = None
        self.openrouter_client = None

        if self.gemini_api_key:
            self.gemini_client = genai.Client(api_key=self.gemini_api_key)

        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)

        if self.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)

        self.openrouter_api_key = settings.OPENROUTER_API_KEY
        if self.openrouter_api_key:
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": settings.server_host,
                    "X-Title": settings.PROJECT_NAME,
                },
            )

    async def get_available_models(self, credential_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Fetch available models for the given credential."""
        provider = (credential_data.get("provider") or credential_data.get("type", "unknown")).lower()
        if provider == "ai_provider":
             provider = credential_data.get("data", {}).get("provider", "unknown").lower()
        
        models = []
        
        # Google AI
        if provider == "gemini" or provider == "google_ai":
             # Use genai to list models
             cred_data = credential_data.get("data", {})
             api_key = cred_data.get("api_key")
             access_token = cred_data.get("access_token")
             
             try:
                 # Standard listing with API Key
                 if api_key:
                     client = genai.Client(api_key=api_key)
                     # list_models returns an iterator
                     for m in client.models.list_models():
                         if "generateContent" in m.supported_generation_methods:
                             models.append({
                                 "id": m.name.replace("models/", ""), 
                                 "label": m.display_name, 
                                 "provider": "google"
                             })
                 else:
                     # Fallback for OAuth - Use public listing or hardcoded if scope issues
                     # We try REST API
                     async with httpx.AsyncClient() as client:
                        headers = {}
                        if access_token: headers["Authorization"] = f"Bearer {access_token}"
                        elif api_key: headers["x-goog-api-key"] = api_key
                        
                        # Note: v1beta/models usually works public, but let's try
                        resp = await client.get("https://generativelanguage.googleapis.com/v1beta/models", headers=headers)
                        if resp.status_code == 200:
                            data = resp.json()
                            for m in data.get("models", []):
                                if "generateContent" in m.get("supportedGenerationMethods", []):
                                     name = m["name"].replace("models/", "")
                                     models.append({
                                         "id": name,
                                         "label": m.get("displayName", name),
                                         "provider": "google"
                                     })
             except Exception as e:
                 logger.error(f"Failed to fetch Google models: {e}")
                 # Fallback list
                 return [
                     {"id": "gemini-2.0-flash-exp", "label": "Gemini 2.0 Flash (Exp)", "provider": "google"},
                     {"id": "gemini-1.5-pro-latest", "label": "Gemini 1.5 Pro", "provider": "google"},
                     {"id": "gemini-1.5-flash-latest", "label": "Gemini 1.5 Flash", "provider": "google"},
                 ]

        # GitHub Copilot
        elif provider == "github_copilot":
             # Try to fetch dynamically
             copilot_token = credential_data.get("data", {}).get("copilot_token")
             if copilot_token:
                 try:
                     async with httpx.AsyncClient() as client:
                         resp = await client.get(
                             "https://api.githubcopilot.com/models",
                             headers={
                                 "Authorization": f"Bearer {copilot_token}",
                                 "Editor-Version": "vscode/1.85.0",
                                 "User-Agent": "GitHubCopilot/1.138.0"
                             },
                             timeout=5.0
                         )
                         if resp.status_code == 200:
                             data = resp.json()
                             # Expecting OpenAI-format: {"data": [{"id": "gpt-4", ...}]}
                             dynamic_models = []
                             for m in data.get("data", []):
                                 # specific filter? or just take all
                                 dynamic_models.append({
                                     "id": m["id"],
                                     "label": f"{m.get('id')} (Copilot)",
                                     "provider": "copilot"
                                 })
                             
                             if dynamic_models:
                                 return dynamic_models
                         else:
                             logger.warning(f"Copilot models fetch failed {resp.status_code}: {resp.text}")
                 except Exception as e:
                     logger.warning(f"Failed to fetch dynamic Copilot models: {e}")

             # Fallback
             return [
                 {"id": "gpt-4", "label": "GPT-4 (Copilot)", "provider": "copilot"},
                 {"id": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo (Copilot)", "provider": "copilot"},
             ]
             
        # OpenRouter / OpenAI
        elif provider == "openrouter":
             try:
                 async with httpx.AsyncClient() as client:
                     resp = await client.get("https://openrouter.ai/api/v1/models")
                     if resp.status_code == 200:
                         data = resp.json()
                         for m in data.get("data", []):
                             models.append({
                                 "id": m["id"],
                                 "label": m.get("name", m["id"]),
                                 "provider": "openrouter"
                             })
                         return models
             except Exception:
                 pass
        
        # Generic Fallback
        if not models:
             models = [
                 {"id": "gpt-4o", "label": "GPT-4o", "provider": "openai"},
                 {"id": "gpt-4o-mini", "label": "GPT-4o Mini", "provider": "openai"},
                 {"id": "claude-3-5-sonnet-20240620", "label": "Claude 3.5 Sonnet", "provider": "anthropic"},
             ]
        
        return models

    async def generate_workflow_from_prompt(
        self,
        prompt: str,
        model: str = "openrouter",
        current_nodes: Optional[List[dict]] = None,
        current_edges: Optional[List[dict]] = None,
        credential_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate workflow nodes and edges from natural language prompt"""
        system_prompt = self._get_system_prompt(current_nodes, current_edges)
        user_prompt = f"USER REQUEST: {prompt}\n\nPlease generate a workflow JSON based on this request."

        # Override model provider if credential specifies one
        provider = model
        if credential_data:
            provider = credential_data.get("provider")
            if not provider:
                provider = credential_data.get("type", model)

        try:
            if provider == "gemini" or provider == "google_ai":
                response_text = await self._generate_with_gemini(
                    f"{system_prompt}\n\n{user_prompt}", credential_data=credential_data
                )
            elif provider == "github_copilot":
                response_text = await self._generate_with_copilot(
                    f"{system_prompt}\n\n{user_prompt}", 
                    credential_data=credential_data,
                    model=model
                )
            elif provider == "openai":
                response_text = await self._generate_with_openai(
                    f"{system_prompt}\n\n{user_prompt}",
                    credential_data=credential_data,
                    model_name=model if model != "openai" else "gpt-4",
                )
            elif provider == "anthropic":
                response_text = await self._generate_with_anthropic(
                    f"{system_prompt}\n\n{user_prompt}", credential_data=credential_data
                )
            elif provider == "openrouter":
                response_text = await self._generate_with_openrouter(
                    f"{system_prompt}\n\n{user_prompt}",
                    model=model if model != "openrouter" else "deepseek/deepseek-r1",
                    credential_data=credential_data,
                )
            else:
                # Default to openrouter if model is unknown
                response_text = await self._generate_with_openrouter(
                    f"{system_prompt}\n\n{user_prompt}",
                    model=model,
                    credential_data=credential_data,
                )

            return self._parse_ai_response(response_text, current_nodes)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            # Fallback to dummy JSON if AI fails during testing
            dummy_file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "dummy_json",
                "work_flow_eg.json",
            )
            if os.path.exists(dummy_file_path):
                logger.warning("Falling back to dummy workflow example")
                with open(dummy_file_path, "r") as f:
                    response = f.read()
                return self._parse_ai_response(response, current_nodes)
            raise e

    def _get_system_prompt(
        self,
        current_nodes: Optional[List[dict]] = None,
        current_edges: Optional[List[dict]] = None,
    ) -> str:
        current_workflow_desc = ""
        if current_nodes:
            current_workflow_desc = (
                f"Current workflow has {len(current_nodes)} nodes. Extend it."
            )

        # Get available nodes from registry
        schemas = NodeRegistry.get_all_schemas()
        nodes_desc = (
            "AVAILABLE NODE TYPES (Use these EXACT names for 'spec.node_name'):\n"
        )

        for schema in schemas:
            inputs_desc = ", ".join([f"{i.name} ({i.type})" for i in schema.inputs])
            nodes_desc += f"- {schema.name} (Kind: {schema.type})\n  Description: {schema.description}\n"
            if inputs_desc:
                nodes_desc += f"  Config Inputs: {inputs_desc}\n"

        return f"""ROLE
You are a workflow architect AI that generates strictly valid JSON workflows for a low-code automation platform.

📐 CORE RULES (NON-NEGOTIABLE)
Output ONLY valid JSON
No explanations
No comments
No markdown
No trailing commas
No extra keys
JSON must strictly follow this top-level structure:
{{
  "meta": {{}},
  "graph": {{
    "nodes": [],
    "edges": []
  }},
  "execution": {{}},
  "observability": {{}},
  "ai": {{}}
}}

Every workflow MUST include: meta, graph.nodes, graph.edges, execution, observability, ai

🧠 META OBJECT RULES
meta MUST include:
id (string, unique, prefixed with "wf-")
name
description
version (semver)
status ("active" | "draft")
tags (array of strings)
owner.user_id
owner.team_id
created_at (ISO 8601 UTC)
updated_at (ISO 8601 UTC)

🧩 NODE RULES
Each node MUST follow this shape:
{{
  "id": "node-id",
  "kind": "trigger" | "action" | "logic",
  "ui": {{
    "label": "",
    "icon": "",
    "position": {{ "x": number, "y": number }}
  }},
  "spec": {{
    "node_name": "",
    "runtime": {{}},
    "config": {{}},
    OPTIONAL: "inputs": {{}},
    OPTIONAL: "outputs": {{}},
    OPTIONAL: "credentials_ref": "",
    OPTIONAL: "error_policy": {{}}
  }}
}}

Node Constraints:
id must be unique
kind must be correct for the node role
node_name must be one of the AVAILABLE NODE TYPES listed below
runtime.type must be one of: internal, code, http
Code runtimes must specify language
Inputs that reference other nodes MUST use mustache: {{{{node-id.outputs.key}}}}

🔗 EDGE RULES
Each edge MUST include: {{ "id": "edge-id", "source": "node-id", "target": "node-id" }}
Graph must be acyclic
All nodes must be connected
Trigger nodes have no incoming edges

⚙️ EXECUTION RULES
execution MUST include: mode ("sync" | "async"), timeout_seconds, retry.max_attempts, retry.strategy, concurrency

📊 OBSERVABILITY RULES
observability MUST include: logging, metrics, tracing

🤖 AI METADATA RULES
ai MUST include: generated_by, confidence, prompt_version

{nodes_desc}

{current_workflow_desc}

🎯 FUNCTIONAL REQUIREMENTS
When given a user intent, you must:
Choose correct trigger(s)
Choose correct action nodes
Include credentials via credentials_ref
Add error handling using error_policy
Keep UI positions logical (left → right)
Use realistic node names and configs
Make the workflow production-ready

❌ NEVER DO
Do NOT invent new top-level keys
Do NOT skip observability or execution
Do NOT mix schemas
Do NOT output partial workflows
Do NOT explain anything

✅ FINAL OUTPUT INSTRUCTION
Generate one complete workflow JSON that fully satisfies the user request and strictly follows this schema.
"""

    async def _generate_with_copilot(
        self, prompt: str, credential_data: Dict, model: str
    ) -> str:
        """Generate using GitHub Copilot"""
        copilot_token = credential_data.get("data", {}).get("copilot_token")
        if not copilot_token:
             raise ValueError("Copilot token missing.")
        
        # Use httpx
        headers = {
            "Authorization": f"Bearer {copilot_token}",
            "Editor-Version": "vscode/1.85.0",
            "User-Agent": "GitHubCopilot/1.138.0",
            "Content-Type": "application/json"
        }
        
        # Parse model or default
        copilot_model = model
        if not copilot_model or "/" in copilot_model: 
             # Strip provider prefix if present (e.g. "copilot/gpt-4o")
             if "/" in model: copilot_model = model.split("/")[-1]
             else: copilot_model = "gpt-4"

        payload = {
            "messages": [
                 {"role": "system", "content": "You are a workflow automation assistant. Return only valid JSON."},
                 {"role": "user", "content": prompt}
            ],
            "model": copilot_model,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.githubcopilot.com/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            ) 
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _generate_with_gemini(
        self, prompt: str, credential_data: Optional[Dict] = None
    ) -> str:
        """Generate using Google Gemini"""
        # Check for OAuth access token first
        access_token = credential_data.get("data", {}).get("access_token") if credential_data else None
        if access_token:
             async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent",
                     headers={
                        "Authorization": f"Bearer {access_token}", 
                        "Content-Type": "application/json"
                    },
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=60.0
                )
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

        client = self.gemini_client
        if credential_data:
            api_key = credential_data.get("data", {}).get("api_key")
            if api_key:
                client = genai.Client(api_key=api_key)

        if not client:
            raise ValueError(
                "Gemini API key not configured. Please set GOOGLE_AI_API_KEY environment variable or provide a credential."
            )
        async with CircuitBreakers.google():
            response = client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt
            )
            return response.text

    async def _generate_with_openai(
        self,
        prompt: str,
        credential_data: Optional[Dict] = None,
        model_name: str = "gpt-4",
    ) -> str:
        """Generate using OpenAI GPT"""
        client = self.openai_client
        if credential_data:
            api_key = credential_data.get("data", {}).get("api_key")
            base_url = credential_data.get("data", {}).get("base_url")
            if api_key:
                client = OpenAI(api_key=api_key, base_url=base_url)

        if not client:
            raise ValueError(
                "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable or provide a credential."
            )
        async with CircuitBreakers.openai():
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a workflow automation assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content

    async def _generate_with_anthropic(
        self, prompt: str, credential_data: Optional[Dict] = None
    ) -> str:
        """Generate using Anthropic Claude"""
        client = self.anthropic_client
        if credential_data:
            api_key = credential_data.get("data", {}).get("api_key")
            if api_key:
                client = Anthropic(api_key=api_key)

        if not client:
            raise ValueError(
                "Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable or provide a credential."
            )
        async with CircuitBreakers.anthropic():
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

    async def _generate_with_openrouter(
        self,
        prompt: str,
        model: str = "deepseek/deepseek-r1",
        credential_data: Optional[Dict] = None,
    ) -> str:
        """Generate using OpenRouter"""
        client = self.openrouter_client
        if credential_data:
            api_key = credential_data.get("data", {}).get("api_key")
            if api_key:
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )

        if not client:
            raise ValueError(
                "OpenRouter API key not configured. Please set OPENROUTER_API_KEY environment variable or provide a credential."
            )

        # Use a generic HTTP circuit breaker for OpenRouter
        async with CircuitBreakers.http("openrouter-api"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a workflow automation assistant. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4096,
                extra_body={"provider": {"allow_fallbacks": False}},
            )
            return response.choices[0].message.content

    def _parse_ai_response(
        self, response: str, current_nodes: Optional[List[dict]] = None
    ) -> Dict[str, Any]:
        """Parse AI response and extract JSON workflow. Returns V2 structure."""
        try:
            # Clean response more robustly
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[-1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[-1].split("```")[0].strip()

            json_start = json_str.find("{")
            json_end = json_str.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = json_str[json_start:json_end]
                workflow_data = json.loads(json_str)

                # Ensure it has the V2 top-level keys
                required_keys = ["meta", "graph", "execution", "observability", "ai"]
                for key in required_keys:
                    if key not in workflow_data:
                        # Add default if missing (graceful fallback)
                        if key == "meta":
                            workflow_data[key] = {"name": "AI Generated Workflow"}
                        elif key == "graph":
                            workflow_data[key] = {"nodes": [], "edges": []}
                        elif key == "execution":
                            workflow_data[key] = {"mode": "async"}
                        elif key == "observability":
                            workflow_data[key] = {"logging": True}
                        elif key == "ai":
                            workflow_data[key] = {"generated_by": "workflow-llm"}

                return {
                    "message": workflow_data["meta"].get(
                        "description", "Workflow generated by AI"
                    ),
                    "workflow": workflow_data,  # Return the full V2 object
                    "suggestions": [
                        "Configure credential fields",
                        "Test workflow execution",
                    ],
                }

            raise ValueError(
                f"No JSON object found in AI response. Raw string: {response[:200]}..."
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Extraction failed for: {json_str[:200]}...")
            raise ValueError(f"Invalid JSON in AI response: {e}")

    async def execute_node(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an AI node (Legacy/Simple). New nodes should use call_llm."""
        prompt_template = config.get("prompt", "")
        model = config.get("model", "gemini")
        system_instruction = config.get(
            "system_instruction", "You are a helpful assistant."
        )

        # Simple variable substitution
        prompt = prompt_template
        for key, value in input_data.items():
            if isinstance(value, (str, int, float, bool)):
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        full_prompt = f"{system_instruction}\n\n{prompt}"

        try:
            if model == "gemini":
                response = await self._generate_with_gemini(full_prompt)
            elif model == "openai":
                response = await self._generate_with_openai(full_prompt)
            elif model == "anthropic":
                response = await self._generate_with_anthropic(full_prompt)
            else:
                response = await self._generate_with_openrouter(
                    full_prompt, model=model
                )

            return {"response": response}
        except Exception as e:
            logger.error(f"AI execution error: {e}")
            raise e


    async def call_llm(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        credential: Dict[str, Any] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Unified method to call LLMs with dynamic credentials and structured parameters.
        Returns standardized dict with 'content' and 'usage'.
        """
        if not messages:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if user_prompt:
                messages.append({"role": "user", "content": user_prompt})

        # Determine provider
        provider = (credential.get("provider") or credential.get("type", "unknown")).lower()
        if provider == "ai_provider":
             provider = credential.get("data", {}).get("provider", "unknown").lower()
             
        cred_data = credential.get("data", {})
        api_key = cred_data.get("api_key")
        base_url = cred_data.get("base_url")

        # =========================================================================
        # Google AI (OAuth or API Key)
        # =========================================================================
        if provider == "gemini" or provider == "google_ai":
            access_token = cred_data.get("access_token")
            
            # Combine formatting for Gemini
            combined_prompt = ""
            for msg in messages:
                combined_prompt += f"{msg['role'].upper()}: {msg['content']}\n\n"

            # 1. OAuth Access Token (Google AI Login)
            if access_token:
                try:
                    target_model = model or "gemini-1.5-pro-latest"
                    if "/" in target_model: target_model = target_model.split("/")[-1]
                    
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent",
                            headers={
                                "Authorization": f"Bearer {access_token}", 
                                "Content-Type": "application/json"
                            },
                            json={
                                "contents": [{"parts": [{"text": combined_prompt}]}],
                                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
                            },
                            timeout=60.0
                        )
                        if resp.status_code != 200:
                             raise ValueError(f"Google AI OAuth Error: {resp.text}")
                        
                        resp_json = resp.json()
                        content = resp_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return {
                            "content": content,
                            "usage": {"total_tokens": 0} # Usage not always returned in simple format
                        }
                except Exception as e:
                    logger.error(f"Google AI OAuth Failed: {e}")
                    raise e
            
            # 2. Existing API Key Flow
            client = genai.Client(api_key=api_key) if api_key else self.gemini_client
            if not client:
                raise ValueError("Gemini API key not found and no OAuth token provided.")

            response = client.models.generate_content(
                model=model or "gemini-2.0-flash",
                contents=combined_prompt,
                config={"temperature": temperature, "max_output_tokens": max_tokens},
            )
            return {
                "content": response.text,
                "usage": {
                    "prompt_tokens": (
                        response.usage_metadata.prompt_token_count
                        if response.usage_metadata
                        else 0
                    ),
                    "completion_tokens": (
                        response.usage_metadata.candidates_token_count
                        if response.usage_metadata
                        else 0
                    ),
                    "total_tokens": (
                        response.usage_metadata.total_token_count
                        if response.usage_metadata
                        else 0
                    ),
                },
            }

        # =========================================================================
        # GitHub Copilot
        # =========================================================================
        elif provider == "github_copilot":
            copilot_token = cred_data.get("copilot_token")
            if not copilot_token:
                 raise ValueError("GitHub Copilot token missing. Please re-authenticate.")
            
            headers = {
                "Authorization": f"Bearer {copilot_token}",
                "Editor-Version": "vscode/1.85.0",
                "User-Agent": "GitHubCopilot/1.138.0",
                "Content-Type": "application/json"
            }
            
            # Map standard model names to Copilot internal names?
            # Copilot usually supports 'gpt-4', 'gpt-3.5-turbo'.
            # If user sends 'openai/gpt-4', split it.
            copilot_model = model
            if "/" in model:
                copilot_model = model.split("/")[-1]
            
            # Copilot often defaults to specific models if not specified or different names.
            # But the API is OpenAI compatible.
            
            payload = {
                "messages": messages,
                "model": copilot_model,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.githubcopilot.com/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                if resp.status_code != 200:
                    raise ValueError(f"GitHub Copilot API Error ({resp.status_code}): {resp.text}")
                
                resp_json = resp.json()
                return {
                    "content": resp_json["choices"][0]["message"]["content"],
                    "usage": resp_json.get("usage", {})
                }

        elif provider == "openai" or (provider == "openrouter" and not base_url):
            # ... (existing OpenAI logic) ...
            actual_base_url = base_url or (
                "https://openrouter.ai/api/v1" if provider == "openrouter" else None
            )
            client = (
                OpenAI(api_key=api_key, base_url=actual_base_url)
                if api_key
                else self.openai_client
            )
            if not client:
                raise ValueError(f"{provider.capitalize()} API key not found.")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        elif provider == "anthropic":
            # ... (existing Anthropic logic) ...
            client = Anthropic(api_key=api_key) if api_key else self.anthropic_client
            if not client:
                raise ValueError("Anthropic API key not found.")

            # Extract system message for Anthropic
            sys_msg = next(
                (m["content"] for m in messages if m["role"] == "system"), None
            )
            filtered_messages = [m for m in messages if m["role"] != "system"]

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=sys_msg,
                messages=filtered_messages,
                temperature=temperature,
            )
            return {
                "content": response.content[0].text,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
            }

        elif provider == "ai_provider" or base_url:
            # ... (Rest of existing logic) ...
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        else:
            raise ValueError(f"Unsupported AI provider: {provider}")


# Singleton instance
ai_service = AIWorkflowService()
