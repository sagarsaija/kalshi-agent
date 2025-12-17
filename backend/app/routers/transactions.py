from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    type: str  # 'deposit' or 'withdrawal'
    amount: int  # in cents
    note: Optional[str] = None
    created_at: Optional[str] = None  # ISO format, defaults to now


class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: int
    note: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("")
async def get_transactions(db: AsyncSession = Depends(get_db)):
    """Get all deposits and withdrawals."""
    result = await db.execute(
        select(Transaction).order_by(Transaction.created_at.desc())
    )
    transactions = result.scalars().all()

    return {
        "transactions": [
            {
                "id": t.id,
                "type": t.type,
                "amount": t.amount,
                "note": t.note,
                "created_at": t.created_at.isoformat(),
            }
            for t in transactions
        ]
    }


@router.get("/summary")
async def get_transactions_summary(db: AsyncSession = Depends(get_db)):
    """Get summary of deposits and withdrawals."""
    # Get total deposits
    deposits_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.type == "deposit"
        )
    )
    total_deposits = deposits_result.scalar() or 0

    # Get total withdrawals
    withdrawals_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.type == "withdrawal"
        )
    )
    total_withdrawals = withdrawals_result.scalar() or 0

    # Net deposited = deposits - withdrawals
    net_deposited = total_deposits - total_withdrawals

    return {
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "net_deposited": net_deposited,
    }


@router.post("")
async def create_transaction(
    transaction: TransactionCreate, db: AsyncSession = Depends(get_db)
):
    """Add a new deposit or withdrawal."""
    if transaction.type not in ["deposit", "withdrawal"]:
        raise HTTPException(
            status_code=400, detail="Type must be 'deposit' or 'withdrawal'"
        )

    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Parse created_at if provided
    created_at = datetime.utcnow()
    if transaction.created_at:
        try:
            created_at = datetime.fromisoformat(
                transaction.created_at.replace("Z", "+00:00")
            )
        except ValueError:
            pass

    db_transaction = Transaction(
        type=transaction.type,
        amount=transaction.amount,
        note=transaction.note,
        created_at=created_at,
    )

    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)

    return {
        "id": db_transaction.id,
        "type": db_transaction.type,
        "amount": db_transaction.amount,
        "note": db_transaction.note,
        "created_at": db_transaction.created_at.isoformat(),
    }


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int, db: AsyncSession = Depends(get_db)
):
    """Delete a transaction."""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await db.delete(transaction)
    await db.commit()

    return {"deleted": True}
