from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone


@dataclass
class BaseRequest:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    date: Optional[str] = None