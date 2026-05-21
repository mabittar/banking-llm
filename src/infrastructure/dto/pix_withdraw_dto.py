from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BeneficiaryRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    holder_name: str = Field(..., alias="holderName")
    government_id: str = Field(..., alias="governmentId")
    code: str = Field(..., alias="code")
    agency: str = Field(..., alias="agency")
    account: str = Field(..., alias="account")
    digit: str = Field(..., alias="digit")
    account_type: str = Field("checking", alias="accountType")
    pix_key: str | None = Field(None, alias="pixKey")
    financial_account: str | None = Field(None, alias="financialAccount")


class PixWithdrawRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    beneficiary: BeneficiaryRequestDTO
    amount: Decimal
    init_type: str = Field(..., alias="initType")
    end_to_end_id: str | None = Field(None, alias="endToEndId")
    additional_info: str | None = Field(None, alias="additionalInfo")
    qr_code: str | None = Field(None, alias="qrCode")
    reconciliation_id: str | None = Field(None, alias="reconciliationId")
    key_id: str | None = Field(None, alias="keyId")
    amount_type: str | None = Field(None, alias="amountType")
    nominal_amount: Decimal | None = Field(None, alias="nominalAmount")
    discount_amount: Decimal | None = Field(None, alias="discountAmount")
    fine_amount: Decimal | None = Field(None, alias="fineAmount")
    interest_amount: Decimal | None = Field(None, alias="interestAmount")
    reduction_amount: Decimal | None = Field(None, alias="reductionAmount")
    receiver_account: str | None = Field(None, alias="receiverAccount")
    receiver_account_type: str | None = Field(None, alias="receiverAccountType")
    receiver_branch: str | None = Field(None, alias="receiverBranch")
    receiver_name: str | None = Field(None, alias="receiverName")
    receiver_government_id: str | None = Field(None, alias="receiverGovernmentId")
    financial_account: str | None = Field(None, alias="financialAccount")
    status: str | None = Field(None, alias="status")


class PixWithdrawResponseDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid: str
    end_to_end_id: str = Field(..., alias="endToEndId")
    amount: Decimal
    status: str
    transaction_id: str | None = Field(None, alias="transactionId")
    sent_at: str | None = Field(None, alias="sentAt")
