import random
from datetime import datetime, timedelta
from pathlib import Path

from app.models.database import (
    Customer,
    Inventory,
    Order,
    OrderItem,
    Payment,
    ReturnItem,
    ReturnRequest,
    SessionLocal,
    Shipment,
    SupportCase,
    init_db,
)


def seed_database() -> None:
    random.seed(41)
    init_db()
    now = datetime.utcnow()
    with SessionLocal() as db:
        if db.query(Customer).count() >= 100:
            print("Synthetic dataset already seeded.")
            return
        customers = [
            Customer(
                customer_id=f"CUS{1000 + index}",
                name=f"Customer {index:03}",
                email=f"customer{index:03}@example.test",
                tier="gold" if index % 9 == 0 else "standard",
                return_count=index % 7,
                risk_flag=index in {17, 58, 91},
                created_at=now - timedelta(days=900 - index),
            )
            for index in range(1, 101)
        ]
        db.add_all(customers)
        db.flush()

        special = {
            1001: (1, "damaged_item", "arrived damaged", 120.0, "delivered"),
            1002: (2, "late_return", "refund requested after return window", 85.0, "delivered"),
            1003: (3, "wrong_item", "wrong product delivered", 45.0, "delivered"),
            1004: (4, "refund_pending", "refund has not arrived", 210.0, "delivered"),
            1005: (5, "high_value", "high value item return", 899.0, "delivered"),
            1006: (6, "lost_shipment", "shipment marked lost", 67.0, "lost"),
            1007: (7, "missing_item", "item missing from package", 39.0, "delivered"),
            1008: (8, "duplicate_request", "duplicate return request", 120.0, "delivered"),
            1009: (17, "fraud_risk", "unusual repeated return activity", 499.0, "delivered"),
        }
        orders: list[Order] = []
        order_items: list[OrderItem] = []
        payments: list[Payment] = []
        shipments: list[Shipment] = []
        returns: list[ReturnRequest] = []
        return_items: list[ReturnItem] = []
        for number in range(1001, 1301):
            customer_number, issue, reason, price, shipping_status = special.get(
                number,
                (1 + (number - 1001) % 100, "standard", "changed mind", round(random.uniform(18, 260), 2), "delivered"),
            )
            delivery_days = 37 if number == 1002 else (42 if number == 1006 else random.randint(1, 25))
            delivered_at = None if shipping_status == "lost" else now - timedelta(days=delivery_days)
            order_id = f"ORD{number}"
            customer_id = f"CUS{1000 + customer_number}"
            product_id = f"PROD{2000 + ((number - 1001) % 120)}"
            orders.append(
                Order(
                    order_id=order_id,
                    customer_id=customer_id,
                    status=shipping_status,
                    order_date=(delivered_at or now - timedelta(days=50)) - timedelta(days=3),
                    delivered_at=delivered_at,
                    total=price,
                )
            )
            order_items.append(
                OrderItem(
                    item_id=f"ITEM{number}",
                    order_id=order_id,
                    product_id=product_id,
                    product_name="Premium Headphones" if price > 300 else "Everyday Home Product",
                    unit_price=price,
                )
            )
            payments.append(
                Payment(
                    payment_id=f"PAY{number}",
                    order_id=order_id,
                    status="captured",
                    amount=price,
                    refund_status="pending" if number == 1004 else "none",
                )
            )
            shipments.append(
                Shipment(
                    shipment_id=f"SHIP{number}",
                    order_id=order_id,
                    carrier="ParcelPost",
                    tracking_number=f"TRACK{number}",
                    status=shipping_status,
                    delivered_at=delivered_at,
                )
            )
            if number < 1101:
                return_id = f"RET{number}"
                returns.append(
                    ReturnRequest(
                        return_id=return_id,
                        order_id=order_id,
                        customer_id=customer_id,
                        reason=reason,
                        status="refund_pending" if number == 1004 else "requested",
                        requested_at=now - timedelta(days=1),
                        issue_type=issue,
                    )
                )
                return_items.append(
                    ReturnItem(
                        item_id=f"RITEM{number}",
                        return_id=return_id,
                        product_id=product_id,
                        condition="damaged" if number == 1001 else "unknown",
                    )
                )

        db.add_all(orders + order_items + payments + shipments + returns + return_items)
        db.add_all(
            Inventory(
                product_id=f"PROD{2000 + index}",
                warehouse_id=f"WH{1 + index % 4:02}",
                on_hand=random.randint(0, 80),
                disposition="quarantine" if index % 17 == 0 else "sellable",
            )
            for index in range(120)
        )
        db.add_all(
            SupportCase(
                case_id=f"CASE{index:04}",
                customer_id=f"CUS{1000 + 1 + index % 100}",
                order_id=f"ORD{1001 + index}",
                category="return inquiry" if index % 2 else "delivery issue",
                status="closed" if index % 3 else "open",
                summary=f"Synthetic prior case {index}: customer asked for a delivery or return status update.",
            )
            for index in range(1, 61)
        )
        db.commit()
    print("Seeded 100 customers, 300 orders, 100 returns, 300 payments/shipments, 120 inventory records, and 60 support cases.")


if __name__ == "__main__":
    seed_database()