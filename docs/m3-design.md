# M3 Design

Version: V1

Last updated: November 26, 2026

Extend **Checkout -> Order -> Delivery -> Completion -> Reports** through the frontend and API. Keep the M2 customer flow, FastAPI backend, React frontend and JSON storage.

## Who does what

| Person | Work |
| --- | --- |
| Unassigned | Orders and reliability |
| Unassigned | Deliveries |
| Unassigned | Reports, Docker and release |
| Unassigned | Frontend integration |

Aim for one PR per work area. Everyone tests their changes, documents their interfaces and updates provenance. Docker work can start alongside the backend.

## Accounts and permissions

Reuse the M2 permission helpers. Every protected request checks the active account and its access to the requested resource.

| Operation | Access |
| --- | --- |
| Order history and details | Customers see their own orders. |
| Management queue and order preparation | Staff manage orders for assigned restaurants. Admins manage all orders. |
| Cancel an order | Owning customer or admin. |
| Track a delivery | Owning customer, assigned restaurant staff or admin. |
| List drivers, manage deliveries and view reports | Admin only. |

## Order and delivery contract

- Orders move from `placed -> preparing -> ready -> out_for_delivery -> delivered`. Only a placed order can be cancelled. A later cancellation returns 409 and leaves the order unchanged. Delivered and cancelled orders are final. Use the same statuses in checkout, history and reports.
- A ready order can have one delivery. It starts as `pending` and becomes `assigned` when an active driver is selected. The order stays ready until dispatch.
- Dispatch moves both records to `out_for_delivery`. Completion moves both to `delivered`. Reject skipped and backward steps.

## API

Keep the existing customer order routes. Add these endpoints for management, delivery and reports.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/management/orders` | List accessible orders with their order ID, restaurant ID and status. |
| PATCH | `/orders/{order_id}/status` | Move an order to preparing or ready. |
| POST | `/orders/{order_id}/cancel` | Cancel a placed order. |
| POST / GET | `/orders/{order_id}/delivery` | Create or track the delivery. |
| GET | `/drivers` | List seeded drivers for assignment. |
| PATCH | `/deliveries/{delivery_id}/driver` | Assign an active driver. |
| PATCH | `/deliveries/{delivery_id}/status` | Dispatch or complete the delivery. |
| GET | `/reports/revenue` | Sum delivered order totals in whole Berries by restaurant. Sort by restaurant ID. |
| GET | `/reports/top-items` | Show “Top items from delivered orders.” Sum units by menu item ID. Sort by units descending, then ID ascending. |
| GET | `/reports/order-counts` | Count every order status, including cancelled. Show zero for unused statuses. |

Reports use saved order snapshots. If a name changed, use the name from the earliest order ID in the group. Revenue and top items return empty lists when there are no delivered orders.

Keep M2 response codes. Use 201 for creation, 200 for reads and updates, 401 for invalid authentication, 403 for blocked roles or inactive accounts, 404 for missing or inaccessible private records, 409 for conflicts, 422 for invalid fields and 500 for storage failures.

## Checkout and saving data

- Add `deliveries` to `shopping.json`. Read a valid M2 file with an empty delivery list and preserve its carts and orders. Reject malformed files. Keep seeded drivers in `drivers.json`.
- Use one backend worker and the existing shared lock. Read the latest state, check for duplicates, validate the transition, allocate any new ID and save all affected records in one atomic write.
- Keep checkout retries safe. Later edits to customer, address, restaurant, item or price data must leave saved orders intact.

## Integration and testing

Show customers their order status, delivery and cancellation option while eligible. Show staff and admins the actions their role allows. Send auth headers and refresh after an update or conflict. Use relative API URLs through Vite locally and the frontend proxy to `http://backend:8000` in Docker.

- Automate checkout through delivery and verify the reports. Cover permissions, skipped steps, late cancellation, empty reports and tied item totals.
- Send two simultaneous delivery requests for one ready order. Expect one 201 and one 409. A failed completion save must leave both records out for delivery.
- Retain M2 tests for changed prices, unavailable items, failed saves and safe retries. Check that M2 shopping files load and order snapshots survive later edits.

### Docker and release

Keep Dockerfiles, Compose config and demo setup in `docs/milestone3/`. Document startup commands, URLs and demo credentials for a customer, assigned staff and an admin. Start unattended and seed only an empty data volume.

Run pytest and the frontend build. On a clean Docker machine, load `frontend-m3.tar` and `backend-m3.tar` from the assessed commit. Start Compose with `--no-build --pull never`, complete an order in the browser and check that its status and revenue survive a restart using the same volume.
