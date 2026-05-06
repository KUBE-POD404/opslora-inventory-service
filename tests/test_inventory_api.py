from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.product import Product  # noqa: F401
from app.models.stock import StockBalance, StockMovement  # noqa: F401
from app.security.jwt import TokenPayload


def test_inventory_api_product_and_stock_workflow():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_current_user():
        return TokenPayload(
            user_id=10,
            org_id=20,
            permissions=[
                "inventory.create",
                "inventory.read",
                "inventory.update",
                "inventory.adjust",
            ],
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        client = TestClient(app)

        create_response = client.post(
            "/api/v1/inventory/products",
            json={
                "name": "Steel Bolt",
                "sku": "BOLT-001",
                "description": "M8 bolt",
                "hsn_sac_code": "7318",
                "unit_of_measure": "PCS",
                "sale_price": "12.50",
                "tax_rate": "18",
                "low_stock_threshold": "5",
            },
        )

        assert create_response.status_code == 201
        product = create_response.json()
        assert product["sku"] == "BOLT-001"
        assert product["hsn_sac_code"] == "7318"

        stock_response = client.get(f"/api/v1/inventory/stock/{product['id']}")
        assert stock_response.status_code == 200
        assert stock_response.json()["quantity_on_hand"] == "0.00"

        snapshot_response = client.get(f"/api/v1/inventory/products/{product['id']}/order-snapshot")
        assert snapshot_response.status_code == 200
        assert snapshot_response.json()["sku"] == "BOLT-001"

        adjust_response = client.post(
            "/api/v1/inventory/stock/adjust",
            json={
                "product_id": product["id"],
                "quantity": "25",
                "movement_type": "IN",
                "reason": "Opening stock",
            },
        )
        assert adjust_response.status_code == 200
        assert adjust_response.json()["quantity_on_hand"] == "25.00"

        check_response = client.post(
            "/api/v1/inventory/stock/check",
            json={"items": [{"product_id": product["id"], "quantity": "3"}]},
        )
        assert check_response.status_code == 200
        assert check_response.json()["all_available"] is True

        deduct_response = client.post(
            "/api/v1/inventory/stock/deduct",
            json={
                "reference_type": "ORDER",
                "reference_id": 1001,
                "items": [{"product_id": product["id"], "quantity": "3"}],
            },
        )
        assert deduct_response.status_code == 200
        assert deduct_response.json()[0]["quantity_on_hand"] == "22.00"

        list_response = client.get("/api/v1/inventory/products")
        assert list_response.status_code == 200
        assert [item["id"] for item in list_response.json()] == [product["id"]]
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
