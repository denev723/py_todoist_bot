from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
import re
from datetime import datetime

# 환경 변수 로딩
load_dotenv()
app = Flask(__name__)

# Todoist API 설정
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
TODOIST_API_URL = "https://api.todoist.com/rest/v2/tasks"
HEADERS = {
    "Authorization": f"Bearer {TODOIST_API_TOKEN}",
    "Content-Type": "application/json"
}

# 임시로 메모리에 캐시할 할 일 목록
cached_tasks = []

# -------------------------
# 유틸 함수
# -------------------------

def extract_due_string(task_text):
    # ~2025.03.30
    match = re.search(r'~([0-9]{4}\.[0-9]{2}\.[0-9]{2})', task_text)
    if match:
        date_str = match.group(1)
        try:
            parsed_date = datetime.strptime(date_str, "%Y.%m.%d")
            return parsed_date.strftime("%Y-%m-%d")
        except:
            return None

    # ~15:00
    time_match = re.search(r'~([0-9]{1,2}:[0-9]{2})', task_text)
    if time_match:
        return f"today at {time_match.group(1)}"
    
    return None

def clean_task_content(task_text):
    # 앞 번호 제거 + 괄호 내 마감일 제거
    content = re.sub(r'^\d+\.\s*', '', task_text)                      # 앞 번호 제거
    content = re.sub(r'\s*\(.*?~.*?까지\)', '', content).strip()       # 괄호 내 마감일 제거
    return content

# -------------------------
# API 엔드포인트
# -------------------------

# ✅ 홈
@app.route('/')
def home():
    return "🔥 Todoist 연동 서버 작동 중!"

# ✅ 할 일 추가
@app.route('/add-task', methods=['POST'])
def add_task():
    data = request.get_json()
    raw_text = data.get("task")
    print(f"[받은 요청] {raw_text}")

    task_content = clean_task_content(raw_text)
    due_string = extract_due_string(raw_text)

    payload = {
        "content": task_content
    }

    if due_string:
        payload["due_string"] = due_string

    res = requests.post(TODOIST_API_URL, headers=HEADERS, json=payload)
    print(f"[보낼 payload] {payload}")
    print(f"[응답 코드] {res.status_code}")
    print(f"[응답 내용] {res.text}")

    if res.status_code in [200, 204]:
        return jsonify({"message": "할 일 추가 완료!"}), 200
    else:
        return jsonify({"message": "할 일 추가 실패", "error": res.text}), 400

# ✅ 할 일 목록 조회
@app.route("/tasks", methods=["GET"])
def get_tasks():
    global cached_tasks
    res = requests.get(TODOIST_API_URL, headers=HEADERS)
    if res.status_code != 200:
        return jsonify({"message": "할 일 목록 불러오기 실패"}), 500

    tasks = res.json()
    cached_tasks = tasks  # 캐싱

    visible_tasks = []
    for idx, task in enumerate(tasks, 1):
        visible_tasks.append({
            "번호": idx,
            "내용": task["content"],
            "마감": task.get("due", {}).get("string", "없음")
        })

    return jsonify(visible_tasks), 200

# ✅ 할 일 완료 처리
@app.route("/complete-task", methods=["POST"])
def complete_task():
    global cached_tasks
    data = request.get_json()
    index = data.get("index")

    if not index or index < 1 or index > len(cached_tasks):
        return jsonify({"message": "유효하지 않은 번호입니다!"}), 400

    task = cached_tasks[index - 1]
    task_id = task["id"]
    content = task["content"]

    res = requests.post(f"{TODOIST_API_URL}/{task_id}/close", headers=HEADERS)
    if res.status_code == 204:
        return jsonify({"message": f"'{content}' 완료 처리했어!"}), 200
    else:
        return jsonify({"message": "완료 처리 실패", "error": res.text}), 500

# ✅ 할 일 삭제
@app.route("/delete-task", methods=["POST"])
def delete_task():
    global cached_tasks
    data = request.get_json()
    index = data.get("index")

    if not index or index < 1 or index > len(cached_tasks):
        return jsonify({"message": "유효하지 않은 번호입니다!"}), 400

    task = cached_tasks[index - 1]
    task_id = task["id"]
    content = task["content"]

    res = requests.delete(f"{TODOIST_API_URL}/{task_id}", headers=HEADERS)
    if res.status_code == 204:
        return jsonify({"message": f"'{content}' 삭제 완료!"}), 200
    else:
        return jsonify({"message": "삭제 실패", "error": res.text}), 500

# -------------------------
# 실행
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
