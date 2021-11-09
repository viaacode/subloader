mkdir -p python_env
python3 -m venv python_env
source python_env/bin/activate
python3 -m pip install -r requirements.txt
# python3 -m pip install -r requirements-test.txt

export PYTHONPATH=$PYTHONPATH:$(pwd)

brew install libxmlsec1
pip install xmlsec -vvv --force-reinstall --no-cache-dir
pip install dm.xmlsec.binding
pip install onelogin


