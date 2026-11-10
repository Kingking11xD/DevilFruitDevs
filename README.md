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
npm run dev

**API endpoints:**   
Health check: `http://127.0.0.1:8000/health`  
Restaurant list: `http://127.0.0.1:8000/restaurants`  
API documentation: `http://127.0.0.1:8000/docs`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Check that the API is running |
| GET | `/restaurants` | View all restaurants with optional name search and cuisine filtering |
| GET | `/restaurants/{restaurant_id}` | View the details of a restaurant by ID |
| POST | `/restaurants` | Create a new restaurant |
| PATCH | `/restaurants/{restaurant_id}` | Update an existing restaurant |
| POST | `/customers` | Register a customer account |
| POST | `/auth/login` | Sign in and receive a session token |
| GET | `/customers/me` | View your profile |
| PATCH | `/customers/me` | Update your name |
| PATCH | `/customers/me/address` | Update your delivery address |
| POST | `/customers/me/deactivate` | Deactivate your account |
| GET | `/docs` | View the FastAPI API documentation |

**Registration and sign-in:**

Try both endpoints at `http://127.0.0.1:8000/docs`.

- `POST /customers` takes a name, email and password. Passwords must be 12 to 128 characters and are saved as hashes.
- `POST /auth/login` takes an email and password and returns a session token.

Send the token with protected requests:

    Authorization: Bearer <token>

Tokens expire after 30 minutes. Restarting the backend clears them, so users must sign in again. Saved accounts remain. Run one backend process.

For a local demo, activate your Python environment, stop any running backend, and run from the project root:

```powershell
python setup_demo_account.py --demo
```

The command prepares data in `.devilfruitdevs-demo` inside your user folder and starts the backend automatically. No `DATA_DIR` setup is needed.

On the first run, choose a 12-128 character password and enter it twice. Password typing shows stars on Python 3.14+ and stays hidden on older versions. Open `http://127.0.0.1:8000/docs` and use `POST /auth/login` with `bulma@email.com` (admin) or `vegeta@email.com` (restaurant user) and that password. Vegeta is assigned to the first restaurant in the demo data.

Later runs keep existing data and passwords. Press Ctrl+C to stop. For custom account options, run `python setup_demo_account.py --help`. Public registration still creates customers only.

For permissions routes can use `Depends(get_current_admin)` or `Depends(get_restaurant_manager)` from `app/api/dependencies.py`. Services can use `require_owner(account, customer_id)` from `app/services/permissions.py`. Map ownership failures to 404. Invalid tokens return 401 and blocked access returns 403. Feature owners still need to connect and test these helpers on their endpoints.

**Data storage:**  
Restaurants are saved in `data/restaurants.json` and accounts in `data/accounts.json`. The included accounts file starts as an empty JSON list. To change the folder before starting the app:

```powershell
$env:DATA_DIR = "C:\path\to\data"
```

The selected folder must already contain the required JSON files. For a new accounts file, use `[]`. Do not replace an existing accounts file. Missing or invalid files cause an error instead of resetting saved data.

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
│   └── restaurants.json
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
