from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BeneficiaryDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    holder_name: str
    government_id: str
    code: str
    agency: str
    account: str
    digit: str
    pix_key: str
    account_type: str


class ReadKeysResponseDTO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    beneficiary: BeneficiaryDTO
    end_to_end_id: str
