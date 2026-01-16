from typing import Any, Dict, List, Optional
import time
import json
import logging
from jinja2 import Template
import jsonschema
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry
from fuse.credentials.service import get_credential_by_id, get_full_credential_by_id

logger = logging.getLogger(__name__)

@NodeRegistry.register
class LLMNode(BaseNode):
    """
    Deterministic AI LLM Node with Schema Enforcement and Variable Injection.
    Rule 1: Deterministic, not autonomous.
    Rule 2: Output always valid JSON.
    Rule 3: Schema validation mandatory if provided.
    """
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="ai.llm",
            label="AI LLM",
            type="action",
            description="Generate text or JSON using AI models with variable injection and schema validation.",
            category="AI",
            inputs=[
                NodeInput(name="credential", type="credential", label="AI Provider", credential_type="ai_provider", required=True),
                NodeInput(name="model", type="select", label="Intelligence", options=[
                    {"label": "Gemini 2.0 Flash (Free)", "value": "google/gemini-2.0-flash-exp:free"},
                    {"label": "Llama 3.3 70B (Free)", "value": "meta-llama/llama-3.3-70b-instruct:free"},
                    {"label": "Llama 3.1 8B (Free)", "value": "meta-llama/llama-3.1-8b-instruct:free"},
                    {"label": "Mistral 7B (Free)", "value": "mistralai/mistral-7b-instruct:free"}
                ], default="google/gemini-2.0-flash-exp:free"),
                NodeInput(name="prompt", type="string", label="Prompt", default="Summarize this", description="Main instruction or question for the AI."),
                NodeInput(name="messages", type="messages", label="Advanced: Prompts / Messages", required=False, default=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Summarize the input data."}
                ]),
                NodeInput(name="output_schema", type="json", label="Expected JSON Structure (Optional)", required=False, description="Tell the AI exactly what format you want the data in.")
            ],
            outputs=[
                NodeOutput(name="result", type="json", label="JSON Result"),
                NodeOutput(name="content", type="string", label="Response Text"),
                NodeOutput(name="usage", type="json", label="Usage Info")
            ]
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        from fuse.ai.service import ai_service
        
        config = context.get("node_config", {})
        start_time = time.time()
        
        # 1. Resolve Credentials
        cred_id = config.get("credential")
        if not cred_id:
            raise ValueError("Credential ID ('credential') is required for AI LLM node.")
        
        cred_data = get_full_credential_by_id(cred_id)
        if not cred_data:
            raise ValueError(f"Credential '{cred_id}' not found.")
        
        logger.info(f"DEBUG LLM: Credential ID: {cred_id}")
        logger.info(f"DEBUG LLM: Credential data: {cred_data}")
            
        # 2. Variable Injection (Structured Input)
        try:
            template_context = {
                "input": input_data,
                "workflow_id": context.get("workflow_id"),
                "execution_id": context.get("execution_id"),
                **context.get("results", {}),
                **(input_data if isinstance(input_data, dict) else {})
            }
            
            # Prioritize 'prompt' field if it has content, otherwise use 'messages'
            prompt_content = config.get("prompt")
            messages_raw = []
            
            if prompt_content and str(prompt_content).strip():
                # Use simple prompt
                messages_raw = [{"role": "user", "content": prompt_content}]
            else:
                # Fallback to messages
                messages_raw = config.get("messages")
                if not messages_raw:
                    # Deep fallback for old or double-nested structures
                    inner_config = config.get("config", {})
                    messages_raw = inner_config.get("messages") or [{"role": "user", "content": inner_config.get("prompt", "Summarize this")}]
            
            rendered_messages = []
            for msg in messages_raw:
                if not isinstance(msg, dict): continue
                role = msg.get("role", "user")
                content_tpl = msg.get("content", "")
                if content_tpl:
                    rendered_content = Template(content_tpl).render(template_context)
                    rendered_messages.append({"role": role, "content": rendered_content})
            
            if not rendered_messages:
                 rendered_messages = [{"role": "user", "content": "Hello!"}]
                 
        except Exception as e:
            raise ValueError(f"Prompt variable injection failed: {str(e)}")

        # 3. Prepare AI Request Configuration
        model = config.get("model", "google/gemini-2.0-flash-exp:free")
        
        # Backward compatibility for simple model names
        model_mapping = {
            "gemini": "google/gemini-2.0-flash-exp:free",
            "openai": "openai/gpt-4o-mini",
            "anthropic": "anthropic/claude-3-haiku",
            "llama": "meta-llama/llama-3.3-70b-instruct:free",
            "microsoft/phi-3-medium-128k-instruct:free": "google/gemini-2.0-flash-exp:free",
            "huggingfaceh4/zephyr-orpo-141b-a35b-v0.1:free": "google/gemini-2.0-flash-exp:free"
        }
        if model in model_mapping:
            model = model_mapping[model]

        temperature = 0.7
        max_tokens = 4096
        output_schema = config.get("output_schema")
        
        # Enforce JSON if schema is provided
        if output_schema:
            has_json_instr = any("JSON" in m["content"].upper() for m in rendered_messages)
            if not has_json_instr:
                # Add instruction to the first system message or add a new one
                system_indices = [i for i, m in enumerate(rendered_messages) if m["role"] == "system"]
                if system_indices:
                    rendered_messages[system_indices[0]]["content"] += "\nReturn only valid JSON matching the requested structure."
                else:
                    rendered_messages.insert(0, {"role": "system", "content": "Return only valid JSON matching the requested structure."})

        # 4. Call AI Service with dynamic credentials
        try:
            resp_data = await ai_service.call_llm(
                messages=rendered_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                credential=cred_data,
                response_format={"type": "json_object"} if output_schema else None
            )
            
            content = resp_data.get("content", "")
            usage = resp_data.get("usage", {})
            
            # 5. Parse and Validate
            result_json = None
            cleaned_content = content
            
            # Clean Markdown formatting if present
            if "```json" in content:
                cleaned_content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content:
                cleaned_content = content.split("```")[-1].split("```")[0].strip()
            
            try:
                result_json = json.loads(cleaned_content)
                
                # Schema Validation
                if output_schema:
                    jsonschema.validate(instance=result_json, schema=output_schema)
            except json.JSONDecodeError:
                if output_schema:
                    raise ValueError(f"LLM failed to produce valid JSON: {content}")
                result_json = {"text": cleaned_content}
            except jsonschema.ValidationError as e:
                raise ValueError(f"LLM output failed schema validation: {e.message}")

            # 6. Final Observability Data
            latency_ms = int((time.time() - start_time) * 1000)
            usage["latency_ms"] = latency_ms
            usage["model"] = model
            
            return {
                "result": result_json,
                "content": content,
                "usage": usage
            }
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                logger.error(f"Rate limit hit for AI model {model}: {error_msg}")
                raise RuntimeError(f"AI Rate Limit: The free tier of {model} is currently busy. Please try another model (like Mistral or Llama 8B) or wait a few seconds.")
            elif "404" in error_msg:
                logger.error(f"AI Model Not Found: {model}. Error: {error_msg}")
                raise RuntimeError(f"AI Model Error (model_not_found): The model {model} is currently unavailable on OpenRouter.")
            
            logger.error(f"AI LLM Node execution failed: {error_msg}")
            raise e
