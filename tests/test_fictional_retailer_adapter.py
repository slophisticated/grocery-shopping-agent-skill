import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = load_module(
    "fictional_retailer_adapter", ROOT / "examples/fictional_retailer_adapter.py"
)
EVALUATOR = load_module("adapter_sample_evaluator", ROOT / "scripts/evaluate_sample.py")
VALIDATOR = load_module(
    "adapter_workspace_validator", ROOT / "scripts/validate_workspace.py"
)


class FictionalRetailerAdapterTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads(ADAPTER.FIXTURE.read_text(encoding="utf-8"))

    def adapt(self):
        return ADAPTER.adapt_basket(
            self.snapshot["retailer"],
            self.snapshot["requirements"],
            self.snapshot["selection"],
        )

    def evaluate(self, service):
        baseline = {
            "name": "Fictional Baseline",
            "mandatory_fee": 5,
            "items": [
                dict(
                    item,
                    price=15,
                    coupon=0,
                    available=True,
                    is_substitution=False,
                    protected_rule_passed=True,
                )
                for item in self.adapt()["items"]
            ],
        }
        return EVALUATOR.evaluate_fixture(
            {
                "required_item_ids": ["rice", "coffee"],
                "baseline_service": baseline["name"],
                "services": [baseline, service],
            }
        )

    def test_complete_basket_maps_prices_coupons_and_fees_once(self):
        service = self.adapt()
        self.assertEqual(service["mandatory_fee"], 3.75)
        result = self.evaluate(service)
        self.assertEqual(result["best_complete_service"], "Fictional Orchard Cart")
        self.assertEqual(result["best_delivered_total"], 20.75)
        self.assertEqual(result["complete_services"], 2)
        self.assertEqual(result["substitution_proposals"], 1)
        self.assertEqual(result["actions_taken"], 0)

    def test_missing_product_is_incomplete_and_cannot_win(self):
        self.snapshot["retailer"]["products"].pop()
        service = self.adapt()
        self.assertFalse(service["items"][1]["available"])
        result = self.evaluate(service)
        self.assertEqual(result["best_complete_service"], "Fictional Baseline")
        self.assertEqual(result["complete_services"], 1)

    def test_unavailable_or_unknown_stock_cannot_win(self):
        for status in ("sold_out", "unknown"):
            with self.subTest(status=status):
                self.snapshot["retailer"]["products"][1]["stock"] = status
                self.assertEqual(self.evaluate(self.adapt())["complete_services"], 1)

    def test_locked_product_substitution_cannot_win(self):
        coffee = self.snapshot["retailer"]["products"][1]
        coffee.update(sku="coffee-other", price_cents=1)
        self.snapshot["selection"]["coffee"] = coffee["sku"]
        service = self.adapt()
        self.assertTrue(service["items"][1]["is_substitution"])
        self.assertFalse(service["items"][1]["allow_substitutions"])
        self.assertEqual(
            self.evaluate(service)["best_complete_service"], "Fictional Baseline"
        )

    def test_allowed_substitution_still_requires_all_protected_attributes(self):
        self.snapshot["retailer"]["products"][0]["attributes"] = ["white rice"]
        service = self.adapt()
        self.assertFalse(service["items"][0]["protected_rule_passed"])
        self.assertEqual(self.evaluate(service)["complete_services"], 1)

    def test_smaller_or_wrong_unit_package_does_not_cover_requirement(self):
        for field, value in (("quantity", 1), ("unit", "kg")):
            with self.subTest(field=field):
                snapshot = copy.deepcopy(self.snapshot)
                snapshot["retailer"]["products"][0][field] = value
                service = ADAPTER.adapt_basket(
                    snapshot["retailer"],
                    snapshot["requirements"],
                    snapshot["selection"],
                )
                self.assertFalse(service["items"][0]["available"])
                self.assertEqual(self.evaluate(service)["complete_services"], 1)

    def test_expired_or_ineligible_coupon_is_not_counted(self):
        for field, value in (
            ("eligible", False),
            ("expires_at", "2026-09-05T09:00:00Z"),
        ):
            with self.subTest(field=field):
                coupon = self.snapshot["retailer"]["products"][0]["coupon"]
                original = copy.deepcopy(coupon)
                coupon[field] = value
                self.assertEqual(self.adapt()["items"][0]["coupon"], 0)
                coupon.update(original)

    def test_coupon_is_capped_at_price(self):
        self.snapshot["retailer"]["products"][0]["coupon"]["cents"] = 10000
        self.assertEqual(self.adapt()["items"][0]["coupon"], 6)

    def test_preferred_sku_with_failed_protected_attribute_is_unavailable(self):
        self.snapshot["retailer"]["products"][1]["attributes"] = []
        service = self.adapt()
        self.assertFalse(service["items"][1]["is_substitution"])
        self.assertFalse(service["items"][1]["available"])
        self.assertEqual(self.evaluate(service)["complete_services"], 1)

    def test_non_finite_and_boolean_quantities_are_rejected(self):
        for quantity in (float("nan"), float("inf"), True, 0):
            for owner in ("request", "product"):
                with self.subTest(quantity=quantity, owner=owner):
                    snapshot = copy.deepcopy(self.snapshot)
                    row = (
                        snapshot["requirements"][0]
                        if owner == "request"
                        else snapshot["retailer"]["products"][0]
                    )
                    row["quantity"] = quantity
                    with self.assertRaises(ValueError):
                        ADAPTER.adapt_basket(
                            snapshot["retailer"],
                            snapshot["requirements"],
                            snapshot["selection"],
                        )

    def test_inputs_are_unchanged_and_output_is_deterministic(self):
        original = copy.deepcopy(self.snapshot)
        self.assertEqual(self.adapt(), self.adapt())
        self.assertEqual(self.snapshot, original)

    def test_duplicate_identifiers_rejected(self):
        for field in ("products", "requirements"):
            with self.subTest(field=field):
                snapshot = copy.deepcopy(self.snapshot)
                rows = (
                    snapshot["retailer"][field]
                    if field == "products"
                    else snapshot[field]
                )
                rows.append(copy.deepcopy(rows[0]))
                with self.assertRaises(ValueError):
                    ADAPTER.adapt_basket(
                        snapshot["retailer"],
                        snapshot["requirements"],
                        snapshot["selection"],
                    )

    def test_malformed_money_is_rejected(self):
        for amount in (-1, True, 1.5, "100"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                ADAPTER.cents(amount)

    def test_stock_and_boolean_strings_are_rejected(self):
        self.snapshot["retailer"]["products"][0]["stock"] = "maybe"
        with self.assertRaises(ValueError):
            self.adapt()
        self.snapshot["retailer"]["products"][0]["stock"] = "in_stock"
        self.snapshot["requirements"][0]["allow_substitutions"] = "false"
        with self.assertRaises(ValueError):
            self.adapt()

    def test_snapshot_and_output_contain_no_sensitive_keys(self):
        self.assertEqual(VALIDATOR.find_sensitive_keys(self.snapshot), [])
        self.assertEqual(VALIDATOR.find_sensitive_keys(self.adapt()), [])

    def test_documented_cli_emits_only_normalized_basket(self):
        run = subprocess.run(
            [sys.executable, str(ROOT / "examples/fictional_retailer_adapter.py")],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        )
        self.assertEqual(json.loads(run.stdout), self.adapt())
        self.assertEqual(run.stderr, "")


if __name__ == "__main__":
    unittest.main()
