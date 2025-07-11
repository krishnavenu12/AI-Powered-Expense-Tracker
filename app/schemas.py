from pydantic import BaseModel
from datetime import date

class ExpenseBase(BaseModel):
    title: str
    amount: float
    category: str
    date: date

class ExpenseCreate(ExpenseBase):
    pass

class Expense(ExpenseBase):
    id: int

    class Config:
        orm_mode = True
