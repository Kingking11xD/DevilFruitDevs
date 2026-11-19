# Cosc 310 DevilFruitDevs

Food Delivery Application\
Team Name: DevilFruitDevs\
Python Version Requirement: 3.10 or above

**Set up from project root:**\
Virtual environment setup: python -m venv .venv \
.venv\Scripts\Activate.ps1\
**Once virtual environment is set up type in CLI:** \
pip install -r requirements.txt\
**If powershell won't run the scripts, run:**\
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass # (current powershell session)\
Then retry the activation command above.

**Start application from project root:**\
python -m uvicorn main:app --reload\
After running the application open another terminal\
cd frontend \
npm ci \
npm run dev

The frontend requires Node.js and npm. Open `http://localhost:5173`, the frontend origin allowed by the backend. See [frontend setup and current features](frontend/README.md).

**API endpoints:**   
Health check: `http://127.0.0.1:8000/health`  
Restaurant list: `http://127.0.0.1:8000/restaurants`  
API documentation: `http://127.0.0.1:8000/docs`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Check that the API is running |
| GET | `/restaurants` | View all restaurants with optional name search and cuisine filtering |
| GET | `/restaurants/{restaurant_id}` | View the details of a restaurant by ID |
| POST | `/restaurants` | Create a new restaurant as an admin |
| PATCH | `/restaurants/{restaurant_id}` | Update a restaurant as an admin or assigned restaurant staff |
| GET | `/restaurants/{restaurant_id}/menu-items` | Browse a restaurant's menu |
| GET | `/restaurants/{restaurant_id}/menu-items/{item_id}` | View one menu item |
| POST | `/restaurants/{restaurant_id}/menu-items` | Add a menu item as an admin or assigned restaurant staff |
| PATCH | `/restaurants/{restaurant_id}/menu-items/{item_id}` | Update a menu item, including availability and active status |
| POST | `/customers` | Register a customer account |
| POST | `/auth/login` | Sign in and receive a session token |
| GET | `/auth/me` | View your signed-in account, role and restaurant assignments |
| GET | `/customers/me` | View your profile |
| PATCH | `/customers/me` | Update your name |
| PATCH | `/customers/me/address` | Update your delivery address |
| POST | `/customers/me/deactivate` | Deactivate your account |
| POST | `/customers/me/cart` | Create a cart or return your active cart |
| GET | `/customers/me/cart` | View your active cart and backend-calculated totals |
| POST | `/customers/me/cart/items` | Add a menu item and quantity |
| PATCH | `/customers/me/cart/items/{item_id}` | Set an item's quantity |
| DELETE | `/customers/me/cart/items/{item_id}` | Remove an item |
| DELETE | `/customers/me/cart/items` | Clear the cart |
| POST | `/carts/{cart_id}/checkout` | Place an order using the displayed total as `expected_total` |
| GET | `/orders` | View your order history |
| GET | `/orders/{order_id}` | View one of your saved orders |
| GET | `/docs` | View the FastAPI API documentation |

**Registration and sign-in:**

Try both endpoints at `http://127.0.0.1:8000/docs`.

- `POST /customers` takes a name, email and password. Passwords must be 12 to 128 characters and are saved as hashes.
- `POST /auth/login` takes an email and password and returns a session token.

Send the token with protected requests:

    Authorization: Bearer <token>

Tokens expire after 30 minutes. Restarting the backend clears them, so users must sign in again. Saved accounts remain. Run one backend process.

Cart, checkout and order endpoints require an active customer and only access that customer's data. Set a delivery address before checkout. Missing or invalid authentication returns 401; inactive accounts or disallowed roles return 403. Another customer's cart or order returns 404.

Checkout rechecks current prices and availability. A changed total returns 409 so the customer can review it; retrying a completed checkout returns the existing order with 200 instead of creating a duplicate.

Restaurant and menu browsing is public. Restaurant creation requires an active admin. Restaurant updates and menu changes require an active admin or assigned restaurant staff. `GET /auth/me` accepts any active account role and returns the signed-in account and its restaurant assignments without password hashes.

For a local demo, activate your Python environment, stop any running backend, and run from the project root:

```powershell
python setup_demo_account.py --demo
```

Use this instead of the normal backend startup command. It prepares data in `.devilfruitdevs-demo` inside your user folder and starts the backend automatically. Missing shopping storage starts with empty carts and orders; existing data is preserved. No `DATA_DIR` setup is needed. Start the frontend in a second terminal using the commands above.

On the first run, choose a 12-128 character password and enter it twice. Password typing shows stars on Python 3.14+ and stays hidden on older versions. Open `http://127.0.0.1:8000/docs` and use `POST /auth/login` with `bulma@email.com` (admin) or `vegeta@email.com` (restaurant user) and that password. Vegeta is assigned to the first restaurant in the demo data.

Later runs keep existing data and passwords. Press Ctrl+C to stop. For custom account options, run `python setup_demo_account.py --help`. Public registration still creates customers only.

You can also sign in through the frontend's Captain's Log. Admins and staff can enable Fleet Admiral Mode under Find Grub; available controls follow their role and restaurant assignments. See the [frontend guide](frontend/README.md) for the customer and management flows. Refreshing the frontend requires signing in again.

For permissions routes can use `Depends(get_current_admin)` or `Depends(get_restaurant_manager)` from `app/api/dependencies.py`. Services can use `require_owner(account, customer_id)` from `app/services/permissions.py`. Map ownership failures to 404. Invalid tokens return 401 and blocked access returns 403.

**Data storage:**  
Restaurants are saved in `data/restaurants.json`, menus in `data/menu_items.json`, accounts in `data/accounts.json`, and carts and orders together in `data/shopping.json`. The included accounts file starts as an empty JSON list. To change the folder before starting the app:

```powershell
$env:DATA_DIR = "C:\path\to\data"
```

The selected folder must already contain the required JSON files. For a new accounts file, use `[]`; an empty shopping file uses `{"carts": [], "orders": []}`. Do not replace existing data. Missing or invalid files cause an error instead of resetting saved data.

**Run tests from project root with the virtual environment active:**\
python -m pytest -v

**Project structure:**
```text
root/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
├── app/
│   ├── api/
│   │   └── routes/ (API endpoints)
│   ├── services/ (Business rules & application logic)
│   ├── repositories/ (JSON file access)
│   │   └── json_store.py (Shared JSON storage)
│   ├── schemas/ (Pydantic data models)
├── main.py (FastAPI application)
├── data/ (Saved application data)
│   ├── accounts.json
│   ├── restaurants.json
│   ├── menu_items.json
│   └── shopping.json
├── docs/
│   ├── m1-design.md
│   ├── m2-design.md
│   └── PROVENANCE.md
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   └── restaurants.ts
│   │   ├── assets/
│   │   │   └── react.svg
│   │   ├── types/
│   │   │   └── restaurant.ts
│   │   ├── App.css
│   │   ├── App.tsx
│   │   ├── CustomerApp.tsx
│   │   ├── CartApp.tsx
│   │   ├── MenuApp.tsx
│   │   ├── OrdersApp.tsx
│   │   ├── index.css
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── .gitignore
│   ├── README.md
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── tests/ (Automated tests) 
├── scrum/ (Team coordination)
│   └── team-agreement.md
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```
