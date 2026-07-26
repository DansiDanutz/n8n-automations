#!/bin/bash
set -e
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade "pip>=26.1.2"
python -m pip install -r backend/requirements.txt -q
python -m backend.main
