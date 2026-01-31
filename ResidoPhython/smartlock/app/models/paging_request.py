from dataclasses import dataclass
from typing import Optional


@dataclass
class PagingRequest:
    page: Optional[int] = 1
    page_size: Optional[int] = 10
    order_by: Optional[str] = None
    direction: Optional[str] = "desc"

    def normalize(self):
        self.page = int(self.page or 1)
        self.page_size = int(self.page_size or 10)
        self.direction = (self.direction or "desc").lower()
        return self
