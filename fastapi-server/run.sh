#!/bin/zsh
export PYTHONPATH=$PYTHONPATH:/Users/yashdesai/work/agno/fastapi-server
uvicorn src.main:app --reload
