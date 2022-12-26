cd ..
if exist venv rd /s/q venv
set PYTHON=c:\python\python38\python
%PYTHON% -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt