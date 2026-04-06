from pydantic import BaseModel, EmailStr, Field


class RoleBrief(BaseModel):
    code: str
    name: str

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[RoleBrief] = Field(default_factory=list)

    model_config = {"from_attributes": True}
