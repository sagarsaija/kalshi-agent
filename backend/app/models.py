from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Index
from app.database import Base


class Fill(Base):
    """Represents a trade fill (executed order)."""
    __tablename__ = "fills"

    id = Column(String, primary_key=True)  # trade_id from Kalshi
    ticker = Column(String, nullable=False, index=True)
    market_title = Column(String, nullable=True)
    side = Column(String, nullable=False)  # 'yes' or 'no'
    action = Column(String, nullable=False)  # 'buy' or 'sell'
    count = Column(Integer, nullable=False)  # number of contracts
    price = Column(Integer, nullable=False)  # price in cents
    cost = Column(Integer, nullable=False)  # total cost in cents (can be negative for sells)
    created_at = Column(DateTime, nullable=False, index=True)
    is_taker = Column(Boolean, default=True)
    
    


class Settlement(Base):
    """Represents a settled position."""
    __tablename__ = "settlements"

    id = Column(String, primary_key=True)  # settlement_id
    ticker = Column(String, nullable=False, index=True)
    market_title = Column(String, nullable=True)
    market_result = Column(String, nullable=False)  # 'yes' or 'no'
    position_side = Column(String, nullable=False)  # 'yes' or 'no'
    position_count = Column(Integer, nullable=False)
    revenue = Column(Integer, nullable=False)  # payout in cents
    settled_at = Column(DateTime, nullable=False, index=True)


class Position(Base):
    """Represents a current open position."""
    __tablename__ = "positions"

    ticker = Column(String, primary_key=True)
    market_title = Column(String, nullable=True)
    position = Column(Integer, nullable=False)  # positive for yes, negative for no
    market_exposure = Column(Integer, nullable=False)  # exposure in cents
    resting_orders_count = Column(Integer, default=0)
    total_cost = Column(Integer, default=0)  # average cost basis
    realized_pnl = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


class PortfolioSnapshot(Base):
    """Historical portfolio value snapshots."""
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    balance = Column(Integer, nullable=False)  # cash balance in cents
    portfolio_value = Column(Integer, nullable=False)  # total value in cents
    pnl = Column(Integer, nullable=True)  # profit/loss in cents
    
    


class DailyPnL(Base):
    """Daily profit/loss summary."""
    __tablename__ = "daily_pnl"

    date = Column(String, primary_key=True)  # YYYY-MM-DD format
    realized_pnl = Column(Integer, default=0)  # from settlements
    trading_pnl = Column(Integer, default=0)  # from day trading (buy/sell spread)
    total_pnl = Column(Integer, default=0)
    trade_count = Column(Integer, default=0)
    volume = Column(Integer, default=0)  # total trading volume in cents


class Transaction(Base):
    """Manual deposit/withdrawal tracking."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)  # 'deposit' or 'withdrawal'
    amount = Column(Integer, nullable=False)  # in cents (positive for both types)
    note = Column(String, nullable=True)  # optional description
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
