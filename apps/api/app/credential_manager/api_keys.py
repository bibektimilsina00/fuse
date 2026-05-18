from pydantic import BaseModel


class CredentialField(BaseModel):
    id: str
    label: str
    type: str
    placeholder: str


class APIKeyProvider:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        icon_url: str,
        hint: str,
        fields: list[CredentialField],
        ai_provider_id: str | None = None,
        default_model: str | None = None,
        supports_tools: bool = False,
        supports_response_format: bool = False,
    ):
        self.id = id
        self.name = name
        self.type = "api_key"
        self.description = description
        self.icon_url = icon_url
        self.hint = hint
        self.fields = fields
        self.ai_provider_id = ai_provider_id
        self.default_model = default_model
        self.supports_tools = supports_tools
        self.supports_response_format = supports_response_format


PROVIDERS = {
    "openai": APIKeyProvider(
        id="openai_api_key",
        name="OpenAI",
        description="Use your OpenAI API key for AI nodes",
        icon_url="https://cdn.brandfetch.io/openai.com/icon",
        hint="sk-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-...")
        ],
        ai_provider_id="openai",
        default_model="gpt-4o-mini",
        supports_tools=True,
        supports_response_format=True,
    ),
    "anthropic": APIKeyProvider(
        id="anthropic_api_key",
        name="Anthropic",
        description="Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku",
        icon_url="https://cdn.brandfetch.io/anthropic.com/icon",
        hint="sk-ant-...",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="sk-ant-..."
            )
        ],
        ai_provider_id="anthropic",
        default_model="claude-3-5-sonnet-latest",
        supports_tools=True,
        supports_response_format=False,
    ),
    "google": APIKeyProvider(
        id="google_api_key",
        name="Google Gemini",
        description="Gemini 1.5 Pro, Gemini 1.5 Flash",
        icon_url="https://cdn.brandfetch.io/google.com/icon",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
        ai_provider_id="google",
        default_model="gemini-1.5-flash",
        supports_tools=True,
        supports_response_format=True,
    ),
    "groq": APIKeyProvider(
        id="groq_api_key",
        name="Groq",
        description="Llama 3, Mixtral, Gemma (Ultra-fast inference)",
        icon_url="https://cdn.brandfetch.io/groq.com/icon",
        hint="gsk-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="gsk-...")
        ],
        ai_provider_id="groq",
        default_model="llama-3.1-8b-instant",
        supports_tools=True,
        supports_response_format=True,
    ),
}


def get_ai_providers() -> list[APIKeyProvider]:
    return [provider for provider in PROVIDERS.values() if provider.ai_provider_id]


def get_ai_provider(provider_id: str) -> APIKeyProvider | None:
    return next(
        (provider for provider in get_ai_providers() if provider.ai_provider_id == provider_id),
        None,
    )


def get_ai_provider_ids() -> set[str]:
    return {provider.ai_provider_id for provider in get_ai_providers() if provider.ai_provider_id}
