"""AI package — provider-aware factory for building the LLM runtime."""
from src.ai.models.registry import ModelRegistry
from src.ai.prompts.loader import PromptLoader
from src.ai.providers.base import LLMProvider
from src.ai.runtimes.llm_runtime import LLMRuntime
from src.core.config import settings


def _build_provider() -> LLMProvider:
    """Instantiate the correct provider based on AI_PROVIDER setting."""
    provider = settings.ai_provider.lower()

    if provider == "gemini":
        from src.ai.providers.gemini import GeminiProvider

        api_keys = settings.parsed_gemini_api_keys()
        sa_path = settings.gemini_service_account_path or None
        project = settings.gemini_project_id or None

        if not api_keys and not sa_path:
            raise ValueError(
                "AI_PROVIDER=gemini but neither GEMINI_API_KEYS nor "
                "GEMINI_SERVICE_ACCOUNT_PATH is configured. "
                "Set at least one in apps/api/.env."
            )
        return GeminiProvider(
            api_keys=api_keys,
            service_account_path=sa_path,
            project_id=project,
            location=settings.gemini_location,
            chat_model=settings.gemini_chat_model,
            embedding_model=settings.gemini_embedding_model,
        )

    if provider == "lmstudio":
        from src.ai.providers.lmstudio import LMStudioProvider

        return LMStudioProvider(
            base_url=settings.lmstudio_base_url,
            api_key=settings.lmstudio_api_key,
            chat_model=settings.lmstudio_chat_model,
            embedding_model=settings.lmstudio_embedding_model,
        )

    # Default: Ollama
    from src.ai.providers.ollama import OllamaProvider

    return OllamaProvider(base_url=settings.ollama_base_url)


def get_llm_runtime() -> LLMRuntime:
    """Build a fully-wired LLMRuntime from application settings.

    Provider is selected by the ``AI_PROVIDER`` environment variable:

    - ``gemini`` (default) — Google Gemini, API key rotation or service account
    - ``ollama`` — local Ollama service
    - ``lmstudio`` — local LM Studio service

    Returns:
        Ready-to-use LLMRuntime. Skills always use logical names
        ``"chat_model"`` / ``"embedding_model"`` — the registry resolves
        the physical model for the active provider.
    """
    provider = _build_provider()
    registry = ModelRegistry()
    loader = PromptLoader()
    return LLMRuntime(provider=provider, registry=registry, prompt_loader=loader)
