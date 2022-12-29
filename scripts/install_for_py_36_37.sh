cd ..
rm -rf venv
python3 -m venv venv
./venv/bin/python3 -m pip install --upgrade pip
./venv/bin/python3 -m pip install -r scripts/requirements_for_py_36_37.txt