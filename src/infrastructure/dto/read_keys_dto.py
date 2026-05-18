from pydantic import BaseModel, Field


class BeneficiaryDTO(BaseModel):
    holderName: str = Field(..., alias="holderName")
    government_id: str = Field(..., alias="governmentId")
    code: str = Field(..., alias="code")
    agency: str = Field(..., alias="agency")
    account: str = Field(..., alias="account")
    digit: str = Field(..., alias="digit")
    pix_key: str = Field(..., alias="pixKey")
    account_type: str = Field(..., alias="accountType")

    class Config:
        populate_by_name = True


class ReadKeysResponseDTO(BaseModel):
    beneficiary: BeneficiaryDTO = Field(..., alias="beneficiary")
    end_to_end_id: str = Field(..., alias="endToEndId")

    class Config:
        populate_by_name = True
