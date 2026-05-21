from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BRCodePreviewBeneficiaryDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    holder_name: str
    government_id: str
    code: str
    agency: str
    account: str
    digit: str
    account_type: str = "checking"
    pix_key: str | None = None
    financial_account: str | None = None


class BRCodePreviewResponseDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    end_to_end_id: str
    qr_code: str
    beneficiary: BRCodePreviewBeneficiaryDTO
    amount: Decimal | None = None
    amount_type: str
    nominal_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    fine_amount: Decimal | None = None
    interest_amount: Decimal | None = None
    reduction_amount: Decimal | None = None
    reconciliation_id: str | None = None
    status: str = "UNKNOWN"
    init_type: str
    key_id: str | None = None
    schedule_at: str | None = None
    cash_amount: Decimal | None = None
    cashier_type: str | None = None
    cashier_bank_code: str | None = None
    pix_pull_subscription_id: str | None = None
