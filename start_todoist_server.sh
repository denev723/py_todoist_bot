#!/bin/zsh

cd /Users/byeongjookim/Documents/todoist-sync-bot  # ⚠️ 여기를 데네브 실제 경로로 바꿔줘!
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
