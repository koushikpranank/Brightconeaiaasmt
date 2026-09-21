from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import InventoryItem, LogisticsUpdate, ProductionOrder, PurchaseOrder, Supplier

router = APIRouter(tags=["supply"])


@router.get("/suppliers", response_model=list[Supplier])
def list_suppliers(session: Session = Depends(get_session)):
    return session.exec(select(Supplier)).all()


@router.get("/inventory", response_model=list[InventoryItem])
def list_inventory(session: Session = Depends(get_session)):
    return session.exec(select(InventoryItem)).all()


@router.get("/purchase-orders", response_model=list[PurchaseOrder])
def list_purchase_orders(session: Session = Depends(get_session)):
    return session.exec(select(PurchaseOrder)).all()


@router.get("/production-orders", response_model=list[ProductionOrder])
def list_production_orders(session: Session = Depends(get_session)):
    return session.exec(select(ProductionOrder)).all()


@router.get("/shipments", response_model=list[LogisticsUpdate])
def list_shipments(session: Session = Depends(get_session)):
    return session.exec(select(LogisticsUpdate)).all()
