from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cargar_csv import load_fixture
from app.domain import InvalidOrderTransition, InvalidOrderData

app = FastAPI(title="TechStore U4")
orders = load_fixture()


class ShipData(BaseModel):
    tracking_number: str


class CancelData(BaseModel):
    reason: str


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    return {
        "id": order.id,
        "status": order.status.value,
        "units": order.units,
        "total": str(order.total.amount),
        "events": [e.name for e in order.events],
    }


@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    try:
        order.confirm()
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidOrderData as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": order.id, "status": order.status.value}


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, data: ShipData):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    try:
        order.ship(data.tracking_number)
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidOrderData as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": order.id, "status": order.status.value}


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, data: CancelData):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    try:
        order.cancel(data.reason)
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidOrderData as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": order.id, "status": order.status.value}