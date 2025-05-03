from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
    # password: str
    
    class Config:
        from_attributes = True


class TokenCreate(BaseModel):
    access_token: str
    refresh_token: str
    access_token_expiry: str
    refresh_token_expiry: str
    # token_type: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    access_token_expiry: str
    refresh_token_expiry: str
    token_type: str

    class Config:
        from_attributes = True
