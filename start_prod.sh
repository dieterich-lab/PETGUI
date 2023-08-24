#!/bin/bash

cd $(dirname $0)
venv="$(pwd)/venv"
. "$venv/bin/activate"
uvicorn app.petGui:app --port 8080 2>&1 | tee -a logs.txt
