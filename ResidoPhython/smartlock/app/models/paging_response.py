from dataclasses import dataclass
from typing import Any, List


@dataclass
class PagingResponse:
    page: int
    page_size: int
    total: int
    order_by: str
    direction: str
    data: List[Any]

    def to_dict(self):
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "order_by": self.order_by,
            "direction": self.direction,
            "data": self.data,
        }
