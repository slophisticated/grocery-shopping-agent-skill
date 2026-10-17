#!/usr/bin/env python3
"""Map a fictional retailer snapshot to the sample evaluator's basket contract."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


FIXTURE = Path(__file__).resolve().parents[1] / "data" / "fictional-retailer.json"


def cents(value: int) -> float:
    if type(value) is not int or value < 0:
        raise ValueError("Money must be non-negative integer cents.")
    return value / 100


def adapt_basket(
    retailer: dict[str, Any],
    requirements: list[dict[str, Any]],
    selection: dict[str, str],
) -> dict[str, Any]:
    """Normalize one selected package per item without changing user policy."""
    products = {product["sku"]: product for product in retailer["products"]}
    if len(products) != len(retailer["products"]):
        raise ValueError("Duplicate retailer SKU.")
    if len({item["id"] for item in requirements}) != len(requirements):
        raise ValueError("Duplicate required item ID.")
    checked_at = datetime.fromisoformat(retailer["checked_at"].replace("Z", "+00:00"))
    if checked_at.tzinfo is None:
        raise ValueError("checked_at must include a timezone.")
    items = []
    for request in requirements:
        allowed = request["allow_substitutions"]
        if type(allowed) is not bool:
            raise ValueError("allow_substitutions must be boolean.")
        product = products.get(selection.get(request["id"]))
        item = {
            "item_id": request["id"],
            "price": 0.0,
            "coupon": 0.0,
            "available": False,
            "is_substitution": False,
            "allow_substitutions": allowed,
            "protected_rule_passed": False,
        }
        if product is not None:
            status = product["stock"]
            if status not in {"in_stock", "limited", "sold_out", "unknown"}:
                raise ValueError("Unknown stock status.")
            if (
                type(product["quantity"]) not in (int, float)
                or not math.isfinite(product["quantity"])
                or product["quantity"] <= 0
            ):
                raise ValueError("Package quantity must be positive.")
            if (
                type(request["quantity"]) not in (int, float)
                or not math.isfinite(request["quantity"])
                or request["quantity"] <= 0
            ):
                raise ValueError("Required quantity must be positive.")
            sufficient = (
                product["unit"] == request["unit"]
                and product["quantity"] >= request["quantity"]
            )
            protected = set(request["protected_attributes"]).issubset(
                product["attributes"]
            )
            coupon = product.get("coupon")
            discount = 0.0
            if coupon is not None:
                if type(coupon["eligible"]) is not bool:
                    raise ValueError("Coupon eligibility must be boolean.")
                expiry = datetime.fromisoformat(
                    coupon["expires_at"].replace("Z", "+00:00")
                )
                if expiry.tzinfo is None:
                    raise ValueError("Coupon expiry must include a timezone.")
                amount = cents(coupon["cents"])
                if coupon["eligible"] and checked_at < expiry:
                    discount = amount
            price = cents(product["price_cents"])
            item.update(
                price=price,
                coupon=min(price, discount),
                available=status in {"in_stock", "limited"}
                and sufficient
                and protected,
                is_substitution=product["sku"] != request["preferred_sku"],
                protected_rule_passed=protected,
            )
        items.append(item)
    fee = sum(cents(value) for value in retailer["mandatory_fees_cents"].values())
    return {"name": retailer["name"], "mandatory_fee": round(fee, 2), "items": items}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", nargs="?", type=Path, default=FIXTURE)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    basket = adapt_basket(
        snapshot["retailer"], snapshot["requirements"], snapshot["selection"]
    )
    print(json.dumps(basket, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
