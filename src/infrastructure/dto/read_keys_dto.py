from pydantic import BaseModel, Field


class BeneficiaryDTO(BaseModel):
    holderName: str = Field(..., alias="holderName")
    governmentId: str = Field(..., alias="governmentId")
    code: str = Field(..., alias="code")
    agency: str = Field(..., alias="agency")
    account: str = Field(..., alias="account")
    digit: str = Field(..., alias="digit")
    pixKey: str = Field(..., alias="pixKey")
    accountType: str = Field(..., alias="accountType")

    class Config:
        populate_by_name = True


class ReadKeysResponseDTO(BaseModel):
    beneficiary: BeneficiaryDTO = Field(..., alias="beneficiary")
    endToEndId: str = Field(..., alias="endToEndId")

    class Config:
        populate_by_name = True
