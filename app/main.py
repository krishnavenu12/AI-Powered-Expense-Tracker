from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, database
from datetime import datetime
import pandas as pd

app = FastAPI()
models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/expenses/", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = models.Expense(**expense.dict())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/expenses/", response_model=list[schemas.Expense])
def read_expenses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Expense).offset(skip).limit(limit).all()

@app.put("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense(expense_id: int, updated: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    exp = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, value in updated.dict().items():
        setattr(exp, key, value)
    db.commit()
    db.refresh(exp)
    return exp

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    exp = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(exp)
    db.commit()
    return {"detail": "Deleted"}

@app.get("/expenses/forecast")
def forecast_expense(db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    if not expenses:
        return {"month": None, "forecast": 0.0}

    data = [{
        "amount": e.amount,
        "date": e.date
    } for e in expenses]

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')

    monthly_sums = df.groupby('month')['amount'].sum().reset_index()
    monthly_sums['month'] = monthly_sums['month'].dt.to_timestamp()

    if len(monthly_sums) >= 3:
        forecast_value = monthly_sums['amount'].tail(3).mean()
    else:
        forecast_value = monthly_sums['amount'].iloc[-1]

    last_month = monthly_sums['month'].max()
    next_month = (last_month + pd.offsets.MonthBegin(1)).strftime('%Y-%m')

    return {"month": next_month, "forecast": round(float(forecast_value), 2)}
