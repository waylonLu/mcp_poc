from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# 定义数据模型
class Account(BaseModel):
    id: str
    name: str
    balance: float
    card_number: str

class Transaction(BaseModel):
    id: str
    from_account: str
    to_account: str
    amount: float
    timestamp: datetime
    description: Optional[str] = None