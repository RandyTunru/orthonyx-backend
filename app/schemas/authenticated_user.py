from pydantic import BaseModel

class AuthenticatedUser(BaseModel):
    id: str
    api_key: str

    class Config:
        orm_mode = True

