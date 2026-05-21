from ..core.logger import logger
from ..infrastructure.banking.banking_client import BankingClient
from ..infrastructure.llm_service import LLMService
from ..services.intent_service import IntentService
from ..services.pix_key_service import PixKeyService
from ..services.pix_withdraw_service import PixWithdrawService
from ..services.response_service import ResponseService
from . import nodes  # noqa: F401
from .graph import build_graph


class GraphProcessor:
    def __init__(self, log=None, cache_service=None, checkpointer=None):
        self.logger = log or logger
        self.banking_client = BankingClient(
            log=self.logger, cache_service=cache_service
        )
        self.llm_service = LLMService(log=self.logger)
        self.intent_service = IntentService(self.llm_service)
        self.pix_key_service = PixKeyService(self.banking_client)
        self.pix_withdraw_service = PixWithdrawService(self.banking_client)
        self.response_service = ResponseService(self.llm_service)
        self._graph = build_graph(
            self.intent_service,
            self.pix_key_service,
            self.pix_withdraw_service,
            self.response_service,
            self.logger,
            checkpointer=checkpointer,
        )

    def get_graph(self):
        return self._graph


graph = GraphProcessor().get_graph()
