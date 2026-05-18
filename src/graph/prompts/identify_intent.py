import json
from datetime import datetime

from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    intent: str = Field(description="The identified user intent: 'list_keys', 'read_key', or 'unknown'")
    fin_account_id: str | None = Field(None, description="The financial account ID extracted from the user message")
    pix_key: str | None = Field(
        None,
        description="The PIX key value extracted from the user message (e.g. CPF, email, phone, random key)",
    )


def get_system_prompt() -> str:
    return json.dumps(
        {
            "role": "Intent Classifier for PIX Key Operations",
            "task": "Identify user intent and extract all PIX-related details from the user message",
            "current_date": datetime.now().isoformat(),
            "intents": {
                "list_keys": {
                    "description": "User wants to list/view/consult all active PIX keys for a financial account",
                    "keywords": [
                        "listar chaves",
                        "chaves ativas",
                        "chaves pix",
                        "quais chaves",
                        "consultar chaves",
                        "ver chaves",
                        "mostrar chaves",
                        "list keys",
                        "active keys",
                    ],
                    "required_fields": ["fin_account_id"],
                },
                "read_key": {
                    "description": "User wants to read/view/consult the details of a specific PIX key",
                    "keywords": [
                        "detalhes da chave",
                        "consultar chave",
                        "ver chave",
                        "informações da chave",
                        "dados da chave",
                        "detalhe",
                        "key details",
                        "read key",
                    ],
                    "required_fields": ["fin_account_id", "pix_key"],
                },
                "unknown": {
                    "description": "Anything not related to PIX key operations",
                    "examples": [
                        "weather questions",
                        "general info",
                        "unrelated queries",
                        "greetings without a request",
                    ],
                },
            },
            "extraction_instructions": {
                "fin_account_id": "Extract the financial account ID (UUID or numeric ID) from the user message. Look for patterns like account ID, conta, account number.",  # noqa: E501
                "pix_key": "Extract the PIX key value. It can be a CPF (11 digits), CNPJ (14 digits), email address, phone number (+55...), or a random UUID key.",  # noqa: E501
            },
            "examples": [
                {
                    "input": "Quais são as chaves pix ativas da conta 550e8400-e29b-41d4-a716-446655440000?",
                    "output": {
                        "intent": "list_keys",
                        "fin_account_id": "550e8400-e29b-41d4-a716-446655440000",
                        "pix_key": None,
                    },
                },
                {
                    "input": "Quero ver os detalhes da chave pix email@test.com na conta 550e8400-e29b-41d4-a716-446655440000",  # noqa: E501
                    "output": {
                        "intent": "read_key",
                        "fin_account_id": "550e8400-e29b-41d4-a716-446655440000",
                        "pix_key": "email@test.com",
                    },
                },
                {
                    "input": "Consultar a chave 12345678901 da conta abc-123",
                    "output": {
                        "intent": "read_key",
                        "fin_account_id": "abc-123",
                        "pix_key": "12345678901",
                    },
                },
                {
                    "input": "Qual a previsão do tempo?",
                    "output": {
                        "intent": "unknown",
                        "fin_account_id": None,
                        "pix_key": None,
                    },
                },
                {
                    "input": "Quero listar minhas chaves pix",
                    "output": {
                        "intent": "unknown",
                        "fin_account_id": None,
                        "pix_key": None,
                    },
                },
            ],
            "important_rules": [
                "If the user asks about PIX keys but does NOT provide a fin_account_id, set intent to 'unknown'.",
                "If the user asks to read a specific key but does NOT provide the pix_key value, set intent to 'unknown'.",  # noqa: E501
                "Always extract values exactly as the user provides them, without modification.",
            ],
        },
        ensure_ascii=False,
    )


def get_user_prompt(user_message: str) -> str:
    return user_message
