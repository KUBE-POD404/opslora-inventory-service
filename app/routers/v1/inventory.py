from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.permissions import require_permission
from app.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StockAdjustment,
    StockBalanceResponse,
)
from app.services.inventory_service import (
    adjust_stock,
    create_product,
    get_product,
    get_stock_balance,
    list_products,
    update_product,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentReadUser = Annotated[object, Depends(require_permission("inventory.read"))]
CurrentCreateUser = Annotated[object, Depends(require_permission("inventory.create"))]
CurrentUpdateUser = Annotated[object, Depends(require_permission("inventory.update"))]
CurrentAdjustUser = Annotated[object, Depends(require_permission("inventory.adjust"))]


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_api(data: ProductCreate, db: DbSession, current_user: CurrentCreateUser):
    return create_product(db, data, current_user.org_id, current_user.user_id)


@router.get("/products", response_model=list[ProductResponse])
def list_products_api(
    db: DbSession,
    current_user: CurrentReadUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 15,
):
    return list_products(db, current_user.org_id, (page - 1) * limit, limit)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product_api(product_id: int, db: DbSession, current_user: CurrentReadUser):
    return get_product(db, product_id, current_user.org_id)


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product_api(
    product_id: int,
    data: ProductUpdate,
    db: DbSession,
    current_user: CurrentUpdateUser,
):
    return update_product(db, product_id, data, current_user.org_id)


@router.get("/stock/{product_id}", response_model=StockBalanceResponse)
def get_stock_api(product_id: int, db: DbSession, current_user: CurrentReadUser):
    return get_stock_balance(db, product_id, current_user.org_id)


@router.post("/stock/adjust", response_model=StockBalanceResponse)
def adjust_stock_api(data: StockAdjustment, db: DbSession, current_user: CurrentAdjustUser):
    return adjust_stock(db, data, current_user.org_id, current_user.user_id)
