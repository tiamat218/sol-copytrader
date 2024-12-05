from pydantic import BaseModel


class Wallet(BaseModel):
    wallet_address: str


class PrivateKey(BaseModel):
    key: str


class Allocation(BaseModel):
    percentage: float
