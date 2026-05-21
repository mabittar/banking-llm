import json
from datetime import datetime

from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    intent: str = Field(
        description="The identified user intent: 'list_keys', 'read_key',"
        " 'pix_withdraw', 'brcode_preview', 'pix_payment', 'brcode_ambiguous', or 'unknown'"
    )
    pix_key: str | None = Field(
        None,
        description="The PIX key value extracted from the user message (e.g. CPF, email, phone, random key)",
    )
    amount: float | None = Field(
        None,
        description="The monetary amount extracted from the user message for transfer operations",
    )
    brcode: str | None = Field(
        None,
        description="The full EMV BRCode payload (TLV format, starts with '000201', ends with CRC '6304xxxx')",
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
                    "description": "User wants to send/transfer PIX money to someone",
                    "keywords": [
                        "enviar pix",
                        "transferir",
                        "pagar",
                        "mandar pix",
                        "enviar para",
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
                "brcode_preview": {
                    "description": "User wants to CONSULT/preview a QR Code (not pay it)",
                    "keywords": [
                        "consultar qr code",
                        "ver qr code",
                        "dados do qr code",
                        "preview qr code",
                        "ler qr code",
                        "qr code pix",
                        "consultar brcode",
                        "escanear qr code",
                        "ver dados",
                    ],
                    "required_fields": ["brcode"],
                },
                "pix_payment": {
                    "description": "User explicitly wants to PAY/execute a QR Code payment (not just consult)",
                    "keywords": [
                        "pague o pix",
                        "pagar qr code",
                        "pagar copia e cola",
                        "pagar pix copia e cola",
                        "pague o qr code",
                        "efetuar pagamento qr",
                        "pagar o brcode",
                        "pay qr code",
                        "pay pix",
                        "pague",
                    ],
                    "required_fields": ["brcode"],
                    "optional_fields": ["amount"],
                },
                "brcode_ambiguous": {
                    "description": "User provides a BRCode but does NOT clearly indicate if they want to consult or pay",  # noqa: E501
                    "keywords": [],
                    "required_fields": ["brcode"],
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
                "brcode": "Extract the full EMV QR Code payload (BRCode) from the message. It is a TLV-encoded string that always starts with '000201' (Payload Format Indicator), contains 'br.gov.bcb.pix' (GUI), and ends with a CRC checksum (tag '6304' + 4 hex chars). It may contain alphanumeric chars plus ./- @+ symbols. Do NOT confuse with a PIX key.",  # noqa: E501
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
                    "input": "Pague o pix copia e cola 00020126580014br.gov.bcb.pix0136a1b2c3d4-e5f6-7890-abcd-ef1234567890520400005303986540510.005802BR5913Test Merchant6008Brasilia62070503***6304A1B2",  # noqa: E501
                    "output": {
                        "intent": "pix_payment",
                        "pix_key": None,
                        "amount": None,
                        "brcode": "00020126580014br.gov.bcb.pix0136a1b2c3d4-e5f6-7890-abcd-ef1234567890520400005303986540510.005802BR5913Test Merchant6008Brasilia62070503***6304A1B2",  # noqa: E501
                    },
                },
                {
                    "input": "Pague R$50 no qr code 000201261800 14br.gov.bcb.pix5204000053039865802BR5925FULANO DE TAL6008Brasilia6304EEC0",  # noqa: E501
                    "output": {
                        "intent": "pix_payment",
                        "pix_key": None,
                        "amount": 50.0,
                        "brcode": "000201261800 14br.gov.bcb.pix5204000053039865802BR5925FULANO DE TAL6008Brasilia6304EEC0",  # noqa: E501
                    },
                },
                {
                    "input": "Segue o qr code 000201261800 14br.gov.bcb.pix5204000053039865802BR5925FULANO DE TAL6008Brasilia6304EEC0",  # noqa: E501
                    "output": {
                        "intent": "brcode_ambiguous",
                        "pix_key": None,
                        "amount": None,
                        "brcode": "000201261800 14br.gov.bcb.pix5204000053039865802BR5925FULANO DE TAL6008Brasilia6304EEC0",  # noqa: E501
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
                {
                    "input": "Consultar o QR Code 00020126580014br.gov.bcb.pix0136a1b2c3d4-e5f6-7890-abcd-ef1234567890520400005303986540510.005802BR5913Test Merchant6008Brasilia62070503***6304A1B2",  # noqa: E501
                    "output": {
                        "intent": "brcode_preview",
                        "pix_key": None,
                        "amount": None,
                        "brcode": "00020126580014br.gov.bcb.pix0136a1b2c3d4-e5f6-7890-abcd-ef1234567890520400005303986540510.005802BR5913Test Merchant6008Brasilia62070503***6304A1B2",  # noqa: E501
                    },
                },
                {
                    "input": "Quero ver os dados desse QR Code: 000201261800 14br.gov.bcb.pix5204000053039865802BR5925FULANO DE TAL6008Brasilia6304EEC0",  # noqa: E501
                    "output": {
                        "intent": "brcode_preview",
                        "pix_key": None,
                        "amount": None,
                        "brcode": "000201261800 14br.gov.bcb.pix5204000053039865802BR5925FULANO DE TAL6008Brasilia6304EEC0",  # noqa: E501
                    },
                },
            ],
            "important_rules": [
                "If the user asks to read a specific key but does NOT provide the pix_key value, set intent to 'unknown'.",  # noqa: E501
                "Always extract values exactly as the user provides them, without modification.",
                "For 'pix_withdraw', extract the amount if provided. If no amount is mentioned, set amount to null.",
                "For 'pix_withdraw', extract the pix_key if the user mentions a specific key to send to.",
                "If the user sends a BRCode (starts with '000201', contains 'br.gov.bcb.pix') WITH an explicit payment verb ('pague', 'pagar', 'pay'), classify as 'pix_payment'.",  # noqa: E501
                "If the user sends a BRCode WITH an explicit consult verb ('consultar', 'ver dados', 'preview'), classify as 'brcode_preview'.",  # noqa: E501
                "If the user sends a BRCode WITHOUT a clear action verb, classify as 'brcode_ambiguous'.",  # noqa: E501
                "For 'pix_payment' and 'brcode_preview' and 'brcode_ambiguous', the brcode field must contain the FULL EMV payload exactly as provided by the user.",  # noqa: E501
                "For 'pix_payment', also extract the amount if the user provides one.",  # noqa: E501
            ],
        },
        ensure_ascii=False,
    )


def get_user_prompt(user_message: str) -> str:
    return user_message
