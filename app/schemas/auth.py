from pydantic import BaseModel, EmailStr

class SignupIn(BaseModel):
    email: EmailStr
    username: str
    password: str

class SigninIn(BaseModel):
    username: str   
    password: str

class SigninOut(BaseModel):
    username: str
    api_key: str
