from dataclasses import dataclass
from typing import Optional
from app.models.paging_request import PagingRequest


@dataclass
class ListEKeysRequest(PagingRequest):
    smart_lock_id: Optional[str] = None
    ekey_id: Optional[str] = None
    key_name: Optional[str] = None
