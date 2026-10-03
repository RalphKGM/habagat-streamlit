#!/bin/zsh
# Double-click to start Habagat. First run creates .venv and installs packages (needs internet).
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv || { echo "Python 3 is required: https://www.python.org/downloads/"; read; exit 1; }
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
fi
.venv/bin/python -m streamlit run streamlit_app.py
