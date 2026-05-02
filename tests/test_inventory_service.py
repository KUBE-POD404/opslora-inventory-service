from decimal import Decimal

import pytest

from app.exceptions.custom_exceptions import ConflictException, NotFoundException
from app.models.stock import StockMovement
from app.schemas import ProductCreate, StockAdjustment
from app.services.inventory_service import adjust_stock, create_product, get_product, get_stock_balance


def product_payload(sku="SKU-1"):
    return ProductCreate(
        name="Test Product",
        sku=sku,
        description="A product",
        hsn_sac_code="998311",
        unit_of_measure="PCS",
        sale_price=Decimal("1200.00"),
        tax_rate=Decimal("18.00"),
        low_stock_threshold=Decimal("5.00"),
    )


def test_create_product_creates_zero_stock_balance(db_session):
    product = create_product(db_session, product_payload(), organization_id=1, created_by_user_id=10)
    balance = get_stock_balance(db_session, product.id, organization_id=1)

    assert product.sku == "SKU-1"
    assert balance.quantity_on_hand == Decimal("0.00")
    assert balance.low_stock_threshold == Decimal("5.00")


def test_sku_is_unique_per_organization(db_session):
    create_product(db_session, product_payload("SKU-1"), organization_id=1, created_by_user_id=10)
    create_product(db_session, product_payload("SKU-1"), organization_id=2, created_by_user_id=20)

    with pytest.raises(ConflictException):
        create_product(db_session, product_payload("SKU-1"), organization_id=1, created_by_user_id=10)


def test_stock_in_out_and_adjustment_movements(db_session):
    product = create_product(db_session, product_payload(), organization_id=1, created_by_user_id=10)

    adjust_stock(
        db_session,
        StockAdjustment(product_id=product.id, quantity=Decimal("10"), movement_type="IN"),
        organization_id=1,
        created_by_user_id=10,
    )
    adjust_stock(
        db_session,
        StockAdjustment(product_id=product.id, quantity=Decimal("3"), movement_type="OUT"),
        organization_id=1,
        created_by_user_id=10,
    )
    balance = adjust_stock(
        db_session,
        StockAdjustment(product_id=product.id, quantity=Decimal("20"), movement_type="ADJUSTMENT"),
        organization_id=1,
        created_by_user_id=10,
    )

    assert balance.quantity_on_hand == Decimal("20.00")
    assert db_session.query(StockMovement).count() == 3


def test_stock_out_cannot_make_balance_negative(db_session):
    product = create_product(db_session, product_payload(), organization_id=1, created_by_user_id=10)

    with pytest.raises(ConflictException):
        adjust_stock(
            db_session,
            StockAdjustment(product_id=product.id, quantity=Decimal("1"), movement_type="OUT"),
            organization_id=1,
            created_by_user_id=10,
        )


def test_product_reads_are_tenant_scoped(db_session):
    product = create_product(db_session, product_payload(), organization_id=1, created_by_user_id=10)

    assert get_product(db_session, product.id, organization_id=1).id == product.id
    with pytest.raises(NotFoundException):
        get_product(db_session, product.id, organization_id=2)
