from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    sku = Column(String(80), nullable=False)
    description = Column(String(500), nullable=True)
    hsn_sac_code = Column(String(20), nullable=True)
    unit_of_measure = Column(String(30), nullable=False, default="PCS")
    sale_price = Column(Numeric(12, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_products_org_sku"),
    )
