cd ..
if exist venv rd /s/q venv
set PYTHON=python
%PYTHON% -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r scripts\requirements_for_py_36_37.txt
pause