from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BuildingCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class BuildingResponse(BaseModel):
    id: str
    name: str
