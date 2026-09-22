# Cosc310DevilFruitDevs

Fast Food delivery Project\
Python Version Requirement: 3.10.3 or above\
Set up:\
Virtual environment setup: python -m venv .venv\
then run this
.venv\Scripts\Activate.ps1\
if powershell won't run the scripts run:\
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass (Note this only works in this directory)\
Once virtual envinrontment is set up type in CLI: \
pip install -r requirements.txt\
\
API endpoints path: app/api/routes\
Starting the application:\
pip install uv\
uv add "fastapi[standard]"\
uv run fastapi dev\
go to this link http://127.0.0.1:8000 \
for docs: http://127.0.0.1:8000/docs \
location of representative Data: data/..jsonfiles\
\
Testing: in CLI type pytest -v or just pytest -q for quick results\
\
Project Structure\
project-root/\
├── app/\
│   ├── api/\
│   │   └── routes/\
│   ├── services/\
│   ├── repositories/\
│   ├── schemas/\
│   ├── core/\
│── main.py\
├── data/\
│   └── restaurants.json\
├── tests/\
├── scrum/\
│   └── team-agreement.md\
├── .gitignore\
├── requirements.txt \
| -pyproject.toml\
└── README.md
