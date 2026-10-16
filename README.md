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
python -m uvicorn main:app --reload

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
| GET | `/docs` | View the FastAPI API documentation |

**Data storage:**  
Data defaults to `data/restaurants.json`. To change the folder before starting the app:  
$env:DATA_DIR = "C:\path\to\data"

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
├── data/ (Representative restaurant data)
│   └── restaurants.json
├── docs/
│   └── m1-design.md
│   └── PROVENANCE.md
├── frontend/
│   └── frontend.py
├── tests/ (Automated tests) 
├── scrum/ (Team coordination)
│   └── team-agreement.md
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```
