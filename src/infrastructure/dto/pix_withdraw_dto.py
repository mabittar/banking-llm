from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BeneficiaryRequestDTO(BaseModel):
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


class PixWithdrawRequestDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    beneficiary: BeneficiaryRequestDTO
    amount: Decimal
    init_type: str
    end_to_end_id: str | None = None
    additional_info: str | None = None
    qr_code: str | None = None
    reconciliation_id: str | None = None
    key_id: str | None = None
    amount_type: str | None = None
    nominal_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    fine_amount: Decimal | None = None
    interest_amount: Decimal | None = None
    reduction_amount: Decimal | None = None
    receiver_account: str | None = None
    receiver_account_type: str | None = None
    receiver_branch: str | None = None
    receiver_name: str | None = None
    receiver_government_id: str | None = None
    financial_account: str | None = None
    status: str | None = None


class PixWithdrawResponseDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    uuid: str
    end_to_end_id: str
    amount: Decimal
    status: str
    transaction_id: str | None = None
    sent_at: str | None = None
