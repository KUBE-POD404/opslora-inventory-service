from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.custom_exceptions import ConflictException, NotFoundException
from app.models.product import Product
from app.models.stock import StockBalance, StockMovement


def create_product(db: Session, payload, organization_id: int, created_by_user_id: int):
    product = Product(
        organization_id=organization_id,
        name=payload.name,
        sku=payload.sku,
        description=payload.description,
        hsn_sac_code=payload.hsn_sac_code,
        unit_of_measure=payload.unit_of_measure,
        sale_price=payload.sale_price,
        tax_rate=payload.tax_rate,
        created_by_user_id=created_by_user_id,
    )
    db.add(product)

    try:
        db.flush()
        db.add(
            StockBalance(
                organization_id=organization_id,
                product_id=product.id,
                quantity_on_hand=Decimal("0.00"),
                low_stock_threshold=payload.low_stock_threshold,
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise ConflictException("SKU already exists in this organization")


def list_products(db: Session, organization_id: int, offset: int = 0, limit: int = 15):
    return (
        db.query(Product)
        .filter(Product.organization_id == organization_id)
        .order_by(Product.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_product(db: Session, product_id: int, organization_id: int):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.organization_id == organization_id)
        .first()
    )
    if not product:
        raise NotFoundException("Product not found")
    return product


def update_product(db: Session, product_id: int, payload, organization_id: int):
    product = get_product(db, product_id, organization_id)
    product.name = payload.name
    product.description = payload.description
    product.hsn_sac_code = payload.hsn_sac_code
    product.unit_of_measure = payload.unit_of_measure
    product.sale_price = payload.sale_price
    product.tax_rate = payload.tax_rate
    product.is_active = payload.is_active
    db.commit()
    db.refresh(product)
    return product


def get_stock_balance(db: Session, product_id: int, organization_id: int):
    balance = (
        db.query(StockBalance)
        .filter(
            StockBalance.product_id == product_id,
            StockBalance.organization_id == organization_id,
        )
        .first()
    )
    if not balance:
        raise NotFoundException("Stock balance not found")
    return balance


def adjust_stock(db: Session, payload, organization_id: int, created_by_user_id: int):
    get_product(db, payload.product_id, organization_id)
    balance = get_stock_balance(db, payload.product_id, organization_id)

    quantity = Decimal(str(payload.quantity))
    if payload.movement_type == "OUT":
        if balance.quantity_on_hand < quantity:
            raise ConflictException("Insufficient stock")
        balance.quantity_on_hand -= quantity
    elif payload.movement_type == "IN":
        balance.quantity_on_hand += quantity
    else:
        balance.quantity_on_hand = quantity

    balance.updated_at = datetime.now(timezone.utc)
    movement = StockMovement(
        organization_id=organization_id,
        product_id=payload.product_id,
        movement_type=payload.movement_type,
        quantity=quantity,
        reason=payload.reason,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        created_by_user_id=created_by_user_id,
    )
    db.add(movement)
    db.commit()
    db.refresh(balance)
    return balance
