from pydantic import BaseModel, EmailStr


class SubscriptionCreate(BaseModel):
    email: EmailStr


class SubscriptionOut(BaseModel):
    email: str
    confirmed: bool

    @classmethod
    def from_subscriber(cls, s) -> "SubscriptionOut":
        return cls(email=s.email, confirmed=s.confirmed)
