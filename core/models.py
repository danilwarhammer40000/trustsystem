from dataclasses import dataclass
from datetime import datetime

@dataclass
class Credential:
    id: int
    user_id: int
    username: str
    password: str
    expires_at: datetime
    status: str
