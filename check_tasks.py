import os
import requests
from dotenv import load_dotenv

# .env 불러오기
load_dotenv()

TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TODOIST_API_TOKEN}"
}

def get_incomplete_tasks():
    try:
        res = requests.get("https://api.todoist.com/rest/v2/tasks", headers=HEADERS)
        res.raise_for_status()
        tasks = res.json()
        return [task["content"] for task in tasks]
    except Exception as e:
        print(f"[에러] 할 일 가져오기 실패: {e}")
        return []

def notify(task):
    try:
        os.system(f'''osascript -e 'display notification "{task}" with title "할 일 완료했어??"' ''')
    except Exception as e:
        print(f"[에러] 알림 실패: {e}")

if __name__ == "__main__":
    tasks = get_incomplete_tasks()
    for task in tasks:
        notify(task)
