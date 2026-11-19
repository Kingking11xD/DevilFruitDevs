# Frontend

React and TypeScript frontend for the M2 customer-to-order workflow.

## Setup

Install Node.js and npm (CI uses Node.js 24), then follow the [root README](../README.md) to set up Python and the backend dependencies.

From the project root with the Python environment active, start the backend:

```powershell
python -m uvicorn main:app --reload
```

For demo admin/staff accounts, use this command instead. Stop any running backend first:

```powershell
python setup_demo_account.py --demo
```

Demo mode starts the backend and keeps its data in `.devilfruitdevs-demo` inside your user folder. It creates missing files and preserves existing accounts, passwords, carts and orders.

In a second terminal, starting from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. Keep that port free: the backend currently allows this frontend origin. The backend runs at **http://127.0.0.1:8000**, with API documentation at **http://127.0.0.1:8000/docs**. Keep both terminals running; use Ctrl+C to stop them.

## Customer flow

- Open Captain's Log (Auth), register a customer and sign in.
- Add a delivery address in your profile before checkout.
- Use Find Grub to search/filter restaurants and browse a menu.
- Add items, then open Ship's Cargo to change quantities, remove items or clear the cart.
- Check out and view the saved order in Log Book (Orders). Prices and totals use Berries.
- If checkout reports a changed total, review the refreshed total before trying again.

## Restaurant management

Public registration creates customers only. Demo mode creates `bulma@email.com` (admin) and `vegeta@email.com` (restaurant staff). Use the password chosen during setup; later runs keep the existing password. Vegeta is assigned to the first demo restaurant.

Sign in through Captain's Log, then open Find Grub and enable Fleet Admiral Mode. This toggle is a management view, not a way to change your role.

- Admins can create restaurants and manage all restaurants and menus.
- Staff can update their assigned restaurants and add/edit menu items, including availability and active status.
- Customers and signed-out visitors do not see the management toggle. The backend still checks permissions on every protected request.

Tokens stay in memory. Refreshing the page signs you out; tokens also expire after 30 minutes or when the backend restarts. Sign in again to continue. Staff/admin accounts do not have customer profile editing, carts or order history.

## Build check

Run from `frontend`:

```powershell
npm run build
```

This checks TypeScript and creates the production files in `dist`. Use `npm run dev` for the documented local API workflow. Run backend tests from the project root as described in the root README.

GitHub Actions runs `npm ci` and `npm run build` on pull requests to `main` and pushes to `main`. The committed `package-lock.json` keeps dependency versions consistent. This build check does not replace browser testing.
