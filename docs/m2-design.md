# M2 Design

Version: V1  
Last updated: November 2, 2026

> **Working design for team review:** These are our proposed implementation choices. This document is separate from `docs/milestones/M2.md` and the required M2 team receipt. The lab schedule lists Receipt M2.2; the M2 assignment lists Team Receipt M2.3. Confirm whether these are separate submissions or a naming error, and confirm their templates and deadlines.

Connect **Customer -> Restaurant -> Menu -> Cart -> Checkout -> Order** through the frontend and API. Keep M1 features working. Leave the complete order lifecycle, deliveries and reporting for M3.

## Who does what

| Person | Work |
| --- | --- |
| Keenan | Customer accounts, authentication and reusable permission checks. |
| Ansella | Menus, carts and cart calculations. |
| Leyla | Checkout, orders and shopping-state persistence. |
| Leo | Frontend, API client and application wiring. |

Everyone writes tests, documents their interfaces, maintains issues/provenance and reviews PRs. Backend owners apply permission checks and resolve integration problems in their own features.

Account and restaurant/menu repositories use the existing `read_records()` and `update_records()` helpers in `app/repositories/json_store.py`. The checkout/orders owner extends this storage layer for shopping-state persistence and checkout, retaining the same shared lock. Existing repository interfaces remain compatible. All account, restaurant/menu, cart and order writes use this storage layer; do not introduce separate locks or direct file writes in feature code.

## Accounts and permissions

- Store all roles in `accounts.json`: `id`, `email`, `name`, `password_hash`, `role`, `active`, `delivery_address`, `managed_restaurant_ids`. Roles are `customer`, `restaurant_user`, `admin`.
- Registration accepts name, email and password; always creates an active customer. Normalize email with trimming/lowercasing and enforce uniqueness. Address starts unset and is required at checkout. Trim profile text, never passwords.
- Use Argon2 through `pwdlib` and signed bearer JWTs through `PyJWT`. Tokens contain the account ID as `sub` and expire after 30 minutes. Validate HS256 explicitly and use an environment-provided secret with no hard-coded fallback.
- Login accepts JSON email/password and returns `access_token`, `token_type: bearer`, `expires_in: 1800`. Invalid credentials get a generic 401. The frontend keeps the token in memory; reload requires sign-in. Discarding a token locally does not revoke it before expiry.
- Every protected request loads the current account and checks active status, role and ownership. Never expose password hashes. Profile updates change name only; address has its own operation. Email/role/ID changes and password reset are outside this slice.
- Deactivation sets `active=false`, preserves historical records and blocks further protected use, including with an existing token. Provision restaurant/admin accounts and restaurant assignments using an explicit local setup command; no privileged public registration or committed credentials.

| Operation | Access |
| --- | --- |
| Restaurant/menu browsing | Public. |
| Profile, address, deactivation, cart, checkout, order history | Active customer; own resources only. |
| Create a restaurant | Active administrator. |
| Update restaurant/menu data, including availability | Active administrator or restaurant user assigned to that restaurant. |

### Account field validation

These are application design choices.

- **Name:** trim surrounding whitespace; require 1–100 characters.
- **Email:** trim, lowercase, validate email format and require uniqueness. Email cannot be changed in M2.
- **Password:** require 12–128 characters; allow spaces and Unicode. Do not trim it or require particular character types. Store only its hash.
- **Delivery address:** use one text field, allowing multiple lines. Start with `null`; when supplied, trim surrounding whitespace and require 1–500 characters. A saved address is required for checkout. No address lookup or postal validation in M2.
- **Updates:** profile updates accept only `name`; address updates accept only `delivery_address`. Reject empty requests, blank values, explicit `null` and unexpected fields.
- **Server-controlled fields:** clients cannot set IDs, roles, active status or restaurant assignments through registration/profile updates. Deactivation uses its dedicated endpoint.

## Cart and order contract

- Keep stable server-assigned integer IDs and whole-number Berries. Use separate request/response models; reject extra fields and client-supplied IDs. PATCH changes only supplied fields and rejects empty updates or unsupported nulls. Quantities/prices are strict positive integers, not booleans.
- Cart fields: `id`, `customer_id`, `restaurant_id`, `status` (`active` or `closed`), and `items` containing `menu_item_id` and `quantity`. At most one active cart per customer; only one restaurant per cart.
- Creating/retrieving an active cart is an explicit POST. GET never creates it. Adding an existing item increases quantity; PATCH sets quantity; DELETE removes an item. Emptying the cart resets its restaurant to null.
- Reject additions of missing, unavailable or deactivated items. Keep items that later become unavailable visible with a problem indicator; block checkout. Use `available` for temporary availability and `active` for menu deactivation; preserve referenced records and initialize existing items as active.
- Cart responses include item names, current unit prices, quantities, line totals, subtotal, total and problems. Never accept client prices as authoritative. For M2, total equals subtotal; no additional fees.
- Accounts expose current identity/status/address; menus expose current item/restaurant/price/availability; carts expose owned contents and the checkout transition. Services use these agreed interfaces, never import routes. Construct dependencies in application wiring.
- Orders retain `id`, `source_cart_id`, customer/restaurant IDs, UTC creation time, initial status `placed`, customer name/address and restaurant-name snapshots, item ID/name/unit-price/quantity/line-total snapshots, subtotal and total. Later account/menu edits do not change saved orders.

## API

Keep existing restaurant/menu endpoints, `/health` and `/docs`; apply the permissions above.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/customers` | Register a customer. |
| POST | `/auth/login` | Sign in. |
| GET / PATCH | `/customers/me` | Read profile / update name. |
| PATCH | `/customers/me/address` | Update delivery address. |
| POST | `/customers/me/deactivate` | Deactivate own account. |
| POST / GET | `/customers/me/cart` | Create/retrieve active cart / read without creation. |
| POST | `/customers/me/cart/items` | Add item and quantity. |
| PATCH / DELETE | `/customers/me/cart/items/{item_id}` | Set quantity / remove item. |
| DELETE | `/customers/me/cart/items` | Clear cart contents. |
| POST | `/carts/{cart_id}/checkout` | Check out this cart; body contains `expected_total`. |
| GET | `/customers/me/orders` | List own orders. |
| GET | `/orders/{order_id}` | Retrieve own order. |

Return 201 for new resources, 200 for reads/updates and existing-cart/order retries, and 204 for successful DELETE operations. Deactivation returns 200 with the public account record. GET active cart returns 404 if absent. Use 401 for invalid/missing authentication; 403 for inactive accounts/disallowed roles; 404 for missing or another customer's private resources; 409 for duplicate email or state conflicts; 422 for invalid fields; 500 for storage failures. Errors follow M1's `detail` format and never expose credentials or file paths.

## Checkout and saving data

- Retain `restaurants.json` and `menu_items.json`; add `accounts.json` and `shopping.json`. The shopping file contains `{"carts": [], "orders": []}`. Cart/order repositories expose separate interfaces over this shared file.
- Checkout verifies ownership and current customer, address, restaurant, cart, quantities and menu state. Reject empty/invalid carts. Recalculate prices; if the result differs from `expected_total`, return 409 so the frontend refreshes and asks for confirmation.
- Build the order snapshot and closed-cart state in memory, then persist both in one atomic replacement of `shopping.json`. Never persist cart closure before the order. A failed save leaves the previous cart/order file intact.
- Allow only one order per `source_cart_id`. After authentication/ownership checks, a repeated checkout of a completed cart returns the existing order, preventing duplicates after a lost response.
- Extend the storage layer for the shopping object without changing existing list-file contracts. Use one shared lock across loading the relevant account/menu/restaurant/shopping state, validation and commit; all participating writes use that lock. Pass loaded state to service logic through repository interfaces. Do not recursively call existing lock-taking helpers while holding the lock.
- Keep configurable `DATA_DIR`, UTF-8, safe temporary-file replacement and one backend process. Missing/corrupt files are errors; setup does not overwrite existing data. External edits/cloud sync and power-loss recovery are outside this locking guarantee.

## Integration and testing

Deliver registration and authenticated identity first. Build against the contracts in this document, then connect sign-in -> menu -> one cart item -> checkout -> saved order early. Use one frontend API client with configurable base URL and consistent error handling.

Test services, repositories and APIs with isolated data: authentication/ownership, inactive accounts, cart rules/totals, changed price/availability, failed saves, repeated checkout, restart persistence and unchanged order snapshots. Each person adds a multi-subsystem test, a meaningful architectural improvement with receipt evidence, and a substantive PR improved through review. Include a regression test from a discovered defect; use small issues, tested PRs and CI.
