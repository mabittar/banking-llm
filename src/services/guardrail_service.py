import hashlib
import re

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from ..core.config import AppEnvironment, settings
from ..core.logger import logger
from ..graph.prompts.guardrail import (
    GuardrailResult,
    get_guardrail_system_prompt,
    get_guardrail_user_prompt,
)

INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"(?i)(ignore|disregard|forget|bypass).{0,30}(instru[çc]|previous|anterior|system|prompt)"
    ),
    re.compile(
        r"(?i)(repita|repeat|show|mostre|print).{0,30}(system prompt|instruções de sistema|instructions)"
    ),
    re.compile(
        r"(?i)(you are now|act as|pretend|finja|assuma).{0,30}(admin|root|superuser|unrestricted|sem restrição)"
    ),
    re.compile(r"(?i)(privilege|acesso|access).{0,20}(escalat|admin|elevat|temporár)"),
    re.compile(r"(?i)(jailbreak|DAN|do anything now)"),
    re.compile(
        r"(?i)vamos jogar.{0,30}(jogo|game).{0,30}(sem restrição|without restriction|unrestricted)"
    ),
]


def _input_hash(user_input: str) -> str:
    return hashlib.sha256(user_input.encode()).hexdigest()[:12]


def _create_safeguard_llm():
    environment = getattr(settings, "ENVIRONMENT", AppEnvironment.LOCAL)
    if environment == AppEnvironment.LOCAL:
        return ChatOllama(
            model=settings.GUARDRAIL_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0,
        )
    http_client = httpx.AsyncClient(verify=False)
    return ChatOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        model=settings.GUARDRAIL_MODEL,
        temperature=0,
        http_async_client=http_client,
    )


class GuardrailService:
    def __init__(self):
        self._safeguard_llm = None

    @property
    def safeguard_llm(self):
        if self._safeguard_llm is None:
            self._safeguard_llm = _create_safeguard_llm()
        return self._safeguard_llm

    def _check_heuristics(self, user_input: str) -> str | None:
        for pattern in INJECTION_PATTERNS:
            if pattern.search(user_input):
                return pattern.pattern
        return None

    async def _check_safeguard_model(self, user_input: str) -> GuardrailResult:
        structured_llm = self.safeguard_llm.with_structured_output(GuardrailResult)
        messages = [
            SystemMessage(content=get_guardrail_system_prompt()),
            HumanMessage(content=get_guardrail_user_prompt(user_input)),
        ]
        result = await structured_llm.ainvoke(messages)
        return result  # type: ignore

    async def check(self, user_input: str) -> dict:
        if not settings.GUARDRAIL_ENABLED:
            return {"is_blocked": False}

        input_id = _input_hash(user_input)

        matched_pattern = self._check_heuristics(user_input)
        if matched_pattern:
            logger.warning(
                "guardrail.blocked",
                input_hash=input_id,
                detection_layer="heuristic",
                pattern_matched=matched_pattern,
            )
            return {"is_blocked": True}

        result = await self._check_safeguard_model(user_input)
        if result.score > settings.GUARDRAIL_THRESHOLD:
            logger.warning(
                "guardrail.blocked",
                input_hash=input_id,
                detection_layer="safeguard_model",
                score=result.score,
                category=result.category,
            )
            return {"is_blocked": True}

        logger.info(
            "guardrail.passed", input_hash=input_id, safeguard_score=result.score
        )
        return {"is_blocked": False}
