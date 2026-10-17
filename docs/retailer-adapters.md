# Fictional retailer adapter

The dependency-free [example adapter](../examples/fictional_retailer_adapter.py)
maps a fictional catalog snapshot into the **basket contract** used by
`scripts/evaluate_sample.py`. Run it from the repository root:

```bash
python3 examples/fictional_retailer_adapter.py
```

The default [fixture](../data/fictional-retailer.json) contains fictional products,
prices and a fixed evidence time. It is a historical demonstration, not a current
offer or a live integration. An optional positional argument reads another file
in that same example shape; use fictional data only.

## Mapping and ownership

`requirements` are caller-owned user intent: item IDs, preferred SKUs, required
quantity and unit, substitution permission, and protected attributes. `selection`
is a separate item-ID-to-SKU proposal. The retailer cannot overwrite those rules.
The adapter returns a new object and does not mutate either input.

| Retailer or caller field | Normalized basket field |
| --- | --- |
| `retailer.name` | `name` |
| Sum of `mandatory_fees_cents` | `mandatory_fee`, counted once for the basket |
| Selected product `price_cents` | Item `price` |
| Eligible, unexpired coupon `cents` | Item `coupon`, capped at the item price |
| `in_stock` or `limited`, enough quantity in the same unit, and matching protected attributes | Item `available: true` |
| Missing SKU, `sold_out`, `unknown`, insufficient quantity, unit mismatch or failed protected attributes | Item `available: false` |
| Selected SKU differs from caller's preferred SKU | Item `is_substitution` |
| Caller substitution permission | Item `allow_substitutions`, copied unchanged |
| All caller protected attributes appear in catalog attributes | Item `protected_rule_passed` |

Amounts use one fictional currency with integer cents at the retailer boundary.
The example models **one package per requested item** and does not convert units
or assemble multiple packages. Insufficient packages reduce coverage. Mandatory
fees include delivery and service fees; taxes, tips, and checkout-only estimates
are excluded and must be shown separately in a real review packet.

The sample's normalized total is `3.75 + (6.00 - 1.00) + 12.00 = 20.75`.
Both items are covered; rice is one substitution proposal. Coffee remains locked.

## Evaluation and authority

Pass the returned service as an entry in `services` for `evaluate_fixture`, with
the caller's item IDs in `required_item_ids` and a named `baseline_service`.
The evaluator excludes incomplete baskets and baskets with forbidden or
protected-rule-breaking substitutions. The tests exercise this integration,
including a cheaper locked-product replacement and a missing catalog item.

Stock, attribute labels, coupon eligibility and timestamps in this fixture are
asserted fictional evidence. A real adapter must verify their source and freshness;
this example performs no network access or retailer authentication. Coupon expiry
is checked against the snapshot time, not today's date. It does not validate
evidence freshness for a live purchase or emit the separate offer-evidence schema.

Output is a comparison input, never a cart update or approval. No order, payment,
login, coupon redemption or account change occurs. Substitutions remain proposals
requiring review. Keep exact addresses, credentials, cookies and payment data out
of fixtures and logs; this adapter needs none and emits only basket fields.
