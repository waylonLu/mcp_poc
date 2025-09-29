from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FinancialProduct(BaseModel):
    """理财产品模型"""
    id: str
    name: str
    description: str
    min_investment: float
    expected_return_rate: float
    risk_level: str  # 低风险、中风险、高风险
    duration_days: int  # 投资期限（天）
    status: str  # 可购买、已售罄、下架


class UserInvestment(BaseModel):
    """用户投资记录模型"""
    id: str
    account_id: str
    product_id: str
    investment_amount: float
    investment_date: datetime
    expected_maturity_date: datetime
    status: str  # 持有中、已到期、已赎回
