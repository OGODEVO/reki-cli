"""
MT5 FastAPI Service - Minimal Trade Execution API
Runs on Windows VPS alongside MT5 Terminal
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import MetaTrader5 as mt5
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MT5 Trading API", version="1.0.0")

# IP Whitelist - Only allow this IP
ALLOWED_IPS = ["194.113.64.216", "127.0.0.1", "::1"]

@app.middleware("http")
async def ip_whitelist_middleware(request: Request, call_next):
    """Check if client IP is whitelisted"""
    client_ip = request.client.host
    
    if client_ip not in ALLOWED_IPS:
        return JSONResponse(
            status_code=403,
            content={"detail": f"Access denied. IP {client_ip} is not whitelisted."}
        )
    
    response = await call_next(request)
    return response

# MT5 Credentials from environment
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
MT5_PATH = os.getenv("MT5_PATH", "")


# Request/Response Models
class OrderRequest(BaseModel):
    symbol: str
    lot_size: float
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    comment: Optional[str] = "Reki Auto Trade"


class PositionResponse(BaseModel):
    ticket: int
    symbol: str
    type: str  # "BUY" or "SELL"
    volume: float
    price_open: float
    price_current: float
    profit: float
    swap: float
    comment: str


class AccountInfo(BaseModel):
    balance: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    currency: str
    profit: float = 0.0
    server: str = ""
    login: int = 0


class HistoryDeal(BaseModel):
    ticket: int
    order: int
    time: int
    time_msc: int
    type: str
    entry: str
    magic: int
    position_id: int
    reason: str
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    symbol: str
    comment: str


class HistoryOrder(BaseModel):
    ticket: int
    time_setup: int
    time_setup_msc: int
    time_done: int
    time_done_msc: int
    type: str
    type_time: str
    type_filling: str
    state: str
    magic: int
    position_id: int
    reason: str
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str


# Startup/Shutdown
@app.on_event("startup")
async def startup():
    """Initialize MT5 connection on startup"""
    init_params = {}
    if MT5_PATH:
        init_params["path"] = MT5_PATH
        print(f"Using custom MT5 path: {MT5_PATH}")
    
    if not mt5.initialize(**init_params):
        raise RuntimeError(f"MT5 initialize() failed, error code: {mt5.last_error()}")
    
    # Login to account
    if MT5_LOGIN and MT5_PASSWORD and MT5_SERVER:
        authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
        if not authorized:
            mt5.shutdown()
            raise RuntimeError(f"MT5 login failed, error code: {mt5.last_error()}")
        print(f"✓ Connected to MT5 account {MT5_LOGIN} on {MT5_SERVER}")
    else:
        print("⚠ MT5 credentials not set, using terminal default account")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown MT5 connection"""
    mt5.shutdown()
    print("MT5 connection closed")


# Health Check
@app.get("/health")
async def health():
    """Check if MT5 is connected"""
    terminal_info = mt5.terminal_info()
    account_info = mt5.account_info()
    
    if terminal_info is None or account_info is None:
        return {
            "status": "error",
            "connected": False,
            "error": str(mt5.last_error())
        }
    
    return {
        "status": "ok",
        "connected": True,
        "terminal": terminal_info.company,
        "account": account_info.login,
        "server": account_info.server,
        "balance": account_info.balance,
        "equity": account_info.equity
    }


# Account Info
@app.get("/account/info", response_model=AccountInfo)
async def get_account_info():
    """Get account information"""
    account = mt5.account_info()
    if account is None:
        raise HTTPException(status_code=500, detail=f"Failed to get account info: {mt5.last_error()}")
    
    return AccountInfo(
        balance=account.balance,
        equity=account.equity,
        margin=account.margin,
        margin_free=account.margin_free,
        margin_level=account.margin_level if account.margin > 0 else 0,
        currency=account.currency,
        profit=account.profit,
        server=account.server,
        login=account.login
    )


@app.get("/account/comprehensive")
async def get_comprehensive_account_info(history_days: int = 3, max_trades: int = 10):
    """
    Get comprehensive account information in one call:
    - Account info (balance, equity, margin, etc.)
    - Open positions
    - Closed trades (deals) from last N days (limited to max_trades)
    - Order history from last N days (limited to max_trades)
    """
    # Get account info
    account = mt5.account_info()
    if account is None:
        raise HTTPException(status_code=500, detail=f"Failed to get account info: {mt5.last_error()}")
    
    # Get open positions
    positions = mt5.positions_get()
    if positions is None:
        error = mt5.last_error()
        if error != (1, 'Success') and error != 1:
            raise HTTPException(status_code=500, detail=f"Failed to get positions: {error}")
        positions = []
    
    # Get closed trades (deals)
    date_from = datetime.now() - timedelta(days=history_days)
    date_to = datetime.now()
    deals = mt5.history_deals_get(date_from, date_to)
    if deals is None:
        error = mt5.last_error()
        if error != (1, 'Success') and error != 1:
            raise HTTPException(status_code=500, detail=f"Failed to get history deals: {error}")
        deals = []
    
    # Get order history
    orders = mt5.history_orders_get(date_from, date_to)
    if orders is None:
        error = mt5.last_error()
        if error != (1, 'Success') and error != 1:
            raise HTTPException(status_code=500, detail=f"Failed to get history orders: {error}")
        orders = []
    
    # Limit to most recent trades (sorted by time descending, take last N)
    deals_list = list(deals)[-max_trades:] if deals else []
    orders_list = list(orders)[-max_trades:] if orders else []
    
    return {
        "account": {
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "margin_free": account.margin_free,
            "margin_level": account.margin_level if account.margin > 0 else 0,
            "profit": account.profit,
            "currency": account.currency
        },
        "positions": [
            {
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "profit": pos.profit
            }
            for pos in positions
        ],
        "closed_trades": [
            {
                "ticket": deal.ticket,
                "time": deal.time,
                "type": "BUY" if deal.type == mt5.ORDER_TYPE_BUY else "SELL",
                "entry": "IN" if deal.entry == mt5.DEAL_ENTRY_IN else "OUT" if deal.entry == mt5.DEAL_ENTRY_OUT else "INOUT",
                "volume": deal.volume,
                "price": deal.price,
                "profit": deal.profit,
                "symbol": deal.symbol
            }
            for deal in deals_list
        ],
        "order_history": [
            {
                "ticket": order.ticket,
                "time_done": order.time_done,
                "type": "BUY" if order.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume_initial": order.volume_initial,
                "price_open": order.price_open,
                "symbol": order.symbol
            }
            for order in orders_list
        ],
        "history_days": history_days,
        "max_trades": max_trades
    }


# History
@app.get("/history/deals", response_model=List[HistoryDeal])
async def get_history_deals(days: int = 30):
    """Get history deals (closed trades) for the last N days"""
    date_from = datetime.now() - timedelta(days=days)
    date_to = datetime.now()
    deals = mt5.history_deals_get(date_from, date_to)
    
    if deals is None:
        error = mt5.last_error()
        if error == (1, 'Success') or error == 1:
            return []
        raise HTTPException(status_code=500, detail=f"Failed to get history deals: {error}")
    
    return [
        HistoryDeal(
            ticket=deal.ticket,
            order=deal.order,
            time=deal.time,
            time_msc=deal.time_msc,
            type="BUY" if deal.type == mt5.ORDER_TYPE_BUY else "SELL",
            entry="IN" if deal.entry == mt5.DEAL_ENTRY_IN else "OUT" if deal.entry == mt5.DEAL_ENTRY_OUT else "INOUT",
            magic=deal.magic,
            position_id=deal.position_id,
            reason=str(deal.reason),
            volume=deal.volume,
            price=deal.price,
            commission=deal.commission,
            swap=deal.swap,
            profit=deal.profit,
            fee=deal.fee,
            symbol=deal.symbol,
            comment=deal.comment
        )
        for deal in deals
    ]


@app.get("/history/orders", response_model=List[HistoryOrder])
async def get_history_orders(days: int = 30):
    """Get history orders for the last N days"""
    date_from = datetime.now() - timedelta(days=days)
    date_to = datetime.now()
    orders = mt5.history_orders_get(date_from, date_to)
    
    if orders is None:
        error = mt5.last_error()
        if error == (1, 'Success') or error == 1:
            return []
        raise HTTPException(status_code=500, detail=f"Failed to get history orders: {error}")
    
    return [
        HistoryOrder(
            ticket=order.ticket,
            time_setup=order.time_setup,
            time_setup_msc=order.time_setup_msc,
            time_done=order.time_done,
            time_done_msc=order.time_done_msc,
            type="BUY" if order.type == mt5.ORDER_TYPE_BUY else "SELL",
            type_time=str(order.type_time),
            type_filling=str(order.type_filling),
            state=str(order.state),
            magic=order.magic,
            position_id=order.position_id,
            reason=str(order.reason),
            volume_initial=order.volume_initial,
            volume_current=order.volume_current,
            price_open=order.price_open,
            sl=order.sl,
            tp=order.tp,
            price_current=order.price_current,
            price_stoplimit=order.price_stoplimit,
            symbol=order.symbol,
            comment=order.comment
        )
        for order in orders
    ]


# Helper Functions
def _get_filling_mode(symbol: str):
    """
    Get the appropriate filling mode for a symbol.
    Different brokers support different filling modes.
    Try RETURN first (most flexible), then IOC, then FOK.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Appropriate ORDER_FILLING mode constant
    """
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        # Default to IOC if we can't get symbol info
        return mt5.ORDER_FILLING_IOC
    
    # Get filling mode flags from symbol
    filling_modes = symbol_info.filling_mode
    
    # Priority order: RETURN > IOC > FOK
    # RETURN is most flexible (allows partial fills and returns remainder)
    if filling_modes & 4:  # ORDER_FILLING_RETURN flag
        return mt5.ORDER_FILLING_RETURN
    elif filling_modes & 1:  # ORDER_FILLING_IOC flag  
        return mt5.ORDER_FILLING_IOC
    elif filling_modes & 2:  # ORDER_FILLING_FOK flag
        return mt5.ORDER_FILLING_FOK
    
    # Fallback to IOC
    return mt5.ORDER_FILLING_IOC


# Positions
@app.get("/positions", response_model=List[PositionResponse])
async def get_positions(symbol: Optional[str] = None):
    """Get all open positions, optionally filtered by symbol"""
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()
    
    # positions_get returns None if no positions found OR if there's an error
    # We need to check last_error to distinguish between them
    if positions is None:
        error = mt5.last_error()
        # Error code 1 or (1, 'Success') means no positions, not an actual error
        if error == (1, 'Success') or error == 1:
            return []  # No positions found, return empty list
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get positions: {error}")
    
    return [
        PositionResponse(
            ticket=pos.ticket,
            symbol=pos.symbol,
            type="BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
            volume=pos.volume,
            price_open=pos.price_open,
            price_current=pos.price_current,
            profit=pos.profit,
            swap=pos.swap,
            comment=pos.comment
        )
        for pos in positions
    ]


@app.post("/positions/close/{ticket}")
async def close_position(ticket: int):
    """Close a specific position by ticket"""
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        raise HTTPException(status_code=404, detail=f"Position {ticket} not found")
    
    position = positions[0]
    
    # Create close request
    close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask
    
    # Get the appropriate filling mode for this symbol
    filling_mode = _get_filling_mode(position.symbol)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": close_type,
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": 0,
        "comment": "Reki Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise HTTPException(status_code=400, detail=f"Order failed: {result.comment}")
    
    return {
        "success": True,
        "ticket": ticket,
        "closed_at": price,
        "profit": position.profit
    }


@app.post("/positions/close_all")
async def close_all_positions():
    """Close all open positions"""
    positions = mt5.positions_get()
    if not positions:
        return {"message": "No open positions", "closed": 0}
    
    closed_count = 0
    errors = []
    
    for position in positions:
        try:
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask
            
            # Get the appropriate filling mode for this symbol
            filling_mode = _get_filling_mode(position.symbol)
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": position.ticket,
                "price": price,
                "deviation": 20,
                "magic": 0,
                "comment": "Reki Close All",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
            else:
                errors.append(f"Ticket {position.ticket}: {result.comment}")
        except Exception as e:
            errors.append(f"Ticket {position.ticket}: {str(e)}")
    
    return {
        "closed": closed_count,
        "total": len(positions),
        "errors": errors if errors else None
    }


# Trading - Buy
@app.post("/order/buy")
async def place_buy_order(order: OrderRequest):
    """Place a BUY order"""
    symbol_info = mt5.symbol_info(order.symbol)
    if symbol_info is None:
        raise HTTPException(status_code=404, detail=f"Symbol {order.symbol} not found")
    
    if not symbol_info.visible:
        if not mt5.symbol_select(order.symbol, True):
            raise HTTPException(status_code=400, detail=f"Failed to select {order.symbol}")
    
    price = mt5.symbol_info_tick(order.symbol).ask
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": order.symbol,
        "volume": order.lot_size,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": order.stop_loss if order.stop_loss else 0,
        "tp": order.take_profit if order.take_profit else 0,
        "deviation": 20,
        "magic": 0,
        "comment": order.comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise HTTPException(status_code=400, detail=f"Order failed: {result.comment} (code: {result.retcode})")
    
    return {
        "success": True,
        "ticket": result.order,
        "symbol": order.symbol,
        "type": "BUY",
        "volume": order.lot_size,
        "price": result.price,
        "take_profit": order.take_profit,
        "stop_loss": order.stop_loss
    }


# Trading - Sell
@app.post("/order/sell")
async def place_sell_order(order: OrderRequest):
    """Place a SELL order"""
    symbol_info = mt5.symbol_info(order.symbol)
    if symbol_info is None:
        raise HTTPException(status_code=404, detail=f"Symbol {order.symbol} not found")
    
    if not symbol_info.visible:
        if not mt5.symbol_select(order.symbol, True):
            raise HTTPException(status_code=400, detail=f"Failed to select {order.symbol}")
    
    price = mt5.symbol_info_tick(order.symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": order.symbol,
        "volume": order.lot_size,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": order.stop_loss if order.stop_loss else 0,
        "tp": order.take_profit if order.take_profit else 0,
        "deviation": 20,
        "magic": 0,
        "comment": order.comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise HTTPException(status_code=400, detail=f"Order failed: {result.comment} (code: {result.retcode})")
    
    return {
        "success": True,
        "ticket": result.order,
        "symbol": order.symbol,
        "type": "SELL",
        "volume": order.lot_size,
        "price": result.price,
        "take_profit": order.take_profit,
        "stop_loss": order.stop_loss
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
