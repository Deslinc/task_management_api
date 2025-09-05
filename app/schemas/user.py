from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    firebase_uid: str
    email: str
    display_name: str | None = None
    created_at: datetime
