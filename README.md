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
Health check: http://127.0.0.1:8000/health  
Restaurant list: http://127.0.0.1:8000/restaurants  
API documentation: http://127.0.0.1:8000/docs  

**Run tests from project root with the virtual environment active:**\
python -m pytest -v

**Project structure:**
```text
root/
├── app/
│   ├── api/
│   │   └── routes/ (API endpoints)
│   ├── services/ (Business rules & application logic)
│   ├── repositories/ (JSON file access)
│   ├── schemas/ (Pydantic data models)
│   └── core/
├── main.py (FastAPI application)
├── data/ (Representative restaurant data)
│   └── restaurants.json
├── tests/ (Automated tests) 
├── scrum/ (Team coordination)
│   └── team-agreement.md
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```
