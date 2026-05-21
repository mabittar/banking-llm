import json
from datetime import datetime

from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    intent: str = Field(
        description="The identified user intent: 'list_keys', 'read_key', 'pix_withdraw', or 'unknown'"
    )
    pix_key: str | None = Field(
        None,
        description="The PIX key value extracted from the user message (e.g. CPF, email, phone, random key)",
    )
    amount: float | None = Field(
        None,
        description="The monetary amount extracted from the user message for transfer operations",
    )


def get_system_prompt() -> str:
    return json.dumps(
        {
            "role": "Intent Classifier for PIX Key Operations",
            "task": "Identify user intent and extract PIX key details from the user message",
            "current_date": datetime.now().isoformat(),
            "intents": {
                "list_keys": {
                    "description": "User wants to list/view/consult all active PIX keys",
                    "keywords": [
                        "listar chaves",
                        "chaves ativas",
                        "chaves pix",
                        "quais chaves",
                        "consultar chaves",
                        "ver chaves",
                        "mostrar chaves",
                        "minhas chaves",
                        "list keys",
                        "active keys",
                    ],
                    "required_fields": [],
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
                    "required_fields": ["pix_key"],
                },
                "pix_withdraw": {
                    "description": "User wants to send/transfer PIX money to someone or pay a QR Code",
                    "keywords": [
                        "enviar pix",
                        "transferir",
                        "pagar",
                        "mandar pix",
                        "enviar para",
                        "pagar qrcode",
                        "pagar qr code",
                        "fazer pix",
                        "pix para",
                        "enviar dinheiro",
                        "transferir pix",
                        "send pix",
                        "transfer",
                        "pay",
                    ],
                    "required_fields": ["amount"],
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
                "pix_key": "Extract the PIX key value. It can be a CPF (11 digits), CNPJ (14 digits), email address, phone number (+55...), or a random UUID key.",  # noqa: E501
                "amount": "Extract the monetary amount from the message. Formats: R$100, 100.00, 100,50. Convert to float.",  # noqa: E501
            },
            "examples": [
                {
                    "input": "Quais são as chaves pix ativas?",
                    "output": {
                        "intent": "list_keys",
                        "pix_key": None,
                        "amount": None,
                    },
                },
                {
                    "input": "Quais chaves Pix tenho ativas na minha conta?",
                    "output": {
                        "intent": "list_keys",
                        "pix_key": None,
                        "amount": None,
                    },
                },
                {
                    "input": "Quero ver os detalhes da chave pix email@test.com",
                    "output": {
                        "intent": "read_key",
                        "pix_key": "email@test.com",
                        "amount": None,
                    },
                },
                {
                    "input": "Consultar a chave 12345678901",
                    "output": {
                        "intent": "read_key",
                        "pix_key": "12345678901",
                        "amount": None,
                    },
                },
                {
                    "input": "Qual a previsão do tempo?",
                    "output": {
                        "intent": "unknown",
                        "pix_key": None,
                        "amount": None,
                    },
                },
                {
                    "input": "Quero enviar R$200 para a chave email@test.com",
                    "output": {
                        "intent": "pix_withdraw",
                        "pix_key": "email@test.com",
                        "amount": 200.0,
                    },
                },
                {
                    "input": "Transferir 1500 reais para o CPF 12345678901",
                    "output": {
                        "intent": "pix_withdraw",
                        "pix_key": "12345678901",
                        "amount": 1500.0,
                    },
                },
                {
                    "input": "Pagar o QR Code",
                    "output": {
                        "intent": "pix_withdraw",
                        "pix_key": None,
                        "amount": None,
                    },
                },
                {
                    "input": "Fazer um pix de R$50,00",
                    "output": {
                        "intent": "pix_withdraw",
                        "pix_key": None,
                        "amount": 50.0,
                    },
                },
            ],
            "important_rules": [
                "If the user asks to read a specific key but does NOT provide the pix_key value, set intent to 'unknown'.",  # noqa: E501
                "Always extract values exactly as the user provides them, without modification.",
                "For 'pix_withdraw', extract the amount if provided. If no amount is mentioned, set amount to null.",
                "For 'pix_withdraw', extract the pix_key if the user mentions a specific key to send to.",
            ],
        },
        ensure_ascii=False,
    )


def get_user_prompt(user_message: str) -> str:
    return user_message
