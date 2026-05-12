import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from ..core.config import AppEnvironment, settings
from ..core.logger import logger


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
            temperature=0,
        )
    logger.info("Using OpenRouter", model=settings.OPENROUTER_MODEL)
    http_client = httpx.AsyncClient(verify=False)
    return ChatOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        model=settings.OPENROUTER_MODEL,
        temperature=0,
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
        structured_llm = self.llm.with_structured_output(schema)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        self.logger.info("LLM structured call", schema=schema.__name__)
        result = await structured_llm.ainvoke(messages)
        self.logger.info("LLM structured response", result=str(result))
        return result  # type: ignore
