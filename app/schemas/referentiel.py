from pydantic import BaseModel, ConfigDict


class NiveauRead(BaseModel):
    id: int
    designation: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class SerieRead(BaseModel):
    id: int
    designation: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class InteretRead(BaseModel):
    id: int
    designation: str
    description: str

    model_config = ConfigDict(from_attributes=True)
