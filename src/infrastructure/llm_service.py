import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from ..core.config import AppEnvironment, settings
from ..core.logger import logger
from ..core.observability.domain_metrics import record_llm_tokens


def _create_llm(log) -> BaseChatModel:
    environment = getattr(settings, "ENVIRONMENT", AppEnvironment.LOCAL)
    if environment == AppEnvironment.LOCAL:
        log.info(
            "Using Ollama",
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            top_k=settings.LLM_TOP_K,
            top_p=settings.LLM_TOP_P,
        )
    logger.info("Using OpenRouter", model=settings.OPENROUTER_MODEL)
    http_client = httpx.AsyncClient(verify=False)
    return ChatOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        model=settings.OPENROUTER_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        model_kwargs={
            "extra_body": {
                "top_k": settings.LLM_TOP_K,
                "top_p": settings.LLM_TOP_P,
            }
        },
        http_async_client=http_client,
    )


class LLMService:
    def __init__(self, log=None):
        self.logger = log or logger
        self.llm = _create_llm(self.logger)

    async def generate_structured[T: BaseModel](
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
    ) -> T:
        structured_llm = self.llm.with_structured_output(schema, include_raw=True)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        self.logger.info("LLM structured call", schema=schema.__name__)
        result = await structured_llm.ainvoke(messages)
        
        if isinstance(result, dict) and "raw" in result:
            token_usage = result["raw"].response_metadata.get("token_usage", {})
            self.logger.info("LLM token usage", token_usage=token_usage)
            total_tokens = token_usage.get("total_tokens")
            if total_tokens:
                model_name = getattr(self.llm, "model_name", getattr(self.llm, "model", "unknown"))
                record_llm_tokens(model_name, total_tokens)
            parsed_result = result["parsed"]
        else:
            parsed_result = result
            
        self.logger.info("LLM structured response", result=str(parsed_result))
        return parsed_result  # type: ignore
