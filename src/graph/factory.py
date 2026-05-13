from ..core.logger import logger
from ..infrastructure.banking.banking_client import BankingClient
from ..infrastructure.llm_service import LLMService
from . import nodes  # noqa: F401
from .graph import build_graph


class GraphProcessor:
    def __init__(self, llm_service=None, banking_client=None, log=None):
        self.logger = log or logger
        self.banking_client = banking_client or BankingClient()
        self.llm_service = llm_service or LLMService()
        self._graph = build_graph(self.llm_service, self.banking_client, self.logger)

    def get_graph(self):
        return self._graph


graph = GraphProcessor().get_graph()
