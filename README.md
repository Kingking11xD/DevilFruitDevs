# Cosc 310 DevilFruitDevs

Food Delivery Application\
Team Name: DevilFruitDevs\
Python Version Requirement: 3.14.7

**Set up from project root:**\
Virtual environment setup: python -m venv .venv \
.venv\Scripts\Activate.ps1\
**Once virtual environment is set up type in CLI:** \
pip install -r requirements.txt\
**If powershell won't run the scripts run:**\
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass # (current powershell session)\
Then retry the activation command above.

**Start application from project root:**\
python -m uvicorn main:app --reload

**API endpoints:**   
Health check: http://127.0.0.1:8000/health  
Restaurant list: http://127.0.0.1:8000/restaurants  
API documentation: http://127.0.0.1:8000/docs  

**Representative data:**\
data/restaurants.json contains the sample restaurant data

**Run tests from project root with the virtual environment active:**\
python -m pytest -v

**Project structure:**\
main.py - FastAPI application\
app/api/routes/ - API endpoints\
app/services/ - Application logic\
app/repositories/ - JSON file access\
app/schemas/ - Pydantic data models\
data/ - Representative restaurant data\
tests/ - Endpoint and repository tests\
scrum/ - Team agreement and signatures