from pydantic import BaseModel


class ApiMessage(BaseModel):
    key: str
    message: str
