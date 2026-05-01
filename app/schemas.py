from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    sku: str = Field(..., min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    hsn_sac_code: str | None = Field(default=None, max_length=20)
    unit_of_measure: str = Field(default="PCS", max_length=30)
    sale_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=0, ge=0, le=100)
    low_stock_threshold: Decimal = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    hsn_sac_code: str | None = Field(default=None, max_length=20)
    unit_of_measure: str = Field(default="PCS", max_length=30)
    sale_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=0, ge=0, le=100)
    is_active: bool = True


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    description: str | None
    hsn_sac_code: str | None
    unit_of_measure: str
    sale_price: Decimal
    tax_rate: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockAdjustment(BaseModel):
    product_id: int
    quantity: Decimal
    movement_type: str = Field(..., pattern="^(IN|OUT|ADJUSTMENT)$")
    reason: str | None = Field(default=None, max_length=255)
    reference_type: str | None = Field(default=None, max_length=50)
    reference_id: int | None = None


class StockBalanceResponse(BaseModel):
    product_id: int
    quantity_on_hand: Decimal
    low_stock_threshold: Decimal
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
