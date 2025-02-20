import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests


app = Flask(__name__)
CORS(app)  # 모든 도메인 허용

# Slack Webhook URL 설정
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"  # Replace with your Webhook URL


def send_slack_alert():
    payload = {
        "text": "⚠️ ストレス警告:ストレス因子が高いです!",
        "username": "StressAlertBot",
        "icon_emoji": ":warning:"
    }
    
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    
    if response.status_code == 200:
        print("슬랙 경고 메시지가 전송되었습니다.")
    else:
        print(f"슬랙 메시지 전송 실패: {response.status_code}, {response.text}")

# 미답변 질문 리스트
questions_db = [
    {"id": 1, "question": "最近趣味はなんですか?", "answered": False},
    {"id": 2, "question": "最近一番仲のいい友達は誰ですか?", "answered": False},
    {"id": 3, "question": "今一番楽しめるのはなんですか?", "answered": False},
]

# 동적으로 설문 데이터 생성
def generate_survey_data(sections, questions_per_section):
    survey_sections = []
    for section_id, section_name in enumerate(sections, start=1):
        section_questions = [
            {
                "QuestionId": f"{section_id}-{question_id}",
                "QuestionText": f"{section_name} 質問 {question_id}"
            }
            for question_id in range(1, questions_per_section + 1)
        ]
        survey_sections.append(section_questions)
    return survey_sections

# 설문 데이터 생성
SECTIONS = ["A因子", "B因子", "C因子", "D因子", "E因子", "ストレス因子"]
QUESTIONS_PER_SECTION = 10
SURVEY_SECTIONS = generate_survey_data(SECTIONS, QUESTIONS_PER_SECTION)

@app.route("/")
def home():
    return "서버가 정상적으로 실행 중입니다!"

@app.route("/survey", methods=["GET"])
def get_survey():
    # 설문 데이터를 반환
    return jsonify({"sections": SURVEY_SECTIONS}), 200

@app.route("/submit-survey", methods=["POST"])
def submit_survey():
    data = request.json
    scores = data.get("scores", {})

    if len(scores) != len(SECTIONS):
        return jsonify({"success": False, "message": "잘못된 데이터입니다."}), 400

    # 기본 타입 산출
    a, b, c, d, e, stress = scores.get("A因子", 0), scores.get("B因子", 0), scores.get("C因子", 0), scores.get("D因子", 0), scores.get("E因子", 0), scores.get("ストレス因子", 0)

    basic_type = None
    if a < 5 and b >= 5 and c >= 5 and d >= 5 and e < 5:
        basic_type = "さくら"
    elif a >= 5 and b < 5 and c >= 5 and d >= 5 and e < 5:
        basic_type = "うめ"
    elif a < 5 and b < 5 and c >= 5 and d < 5 and e >= 5:
        basic_type = "もも"
    elif a >= 5 and b < 5 and c >= 5 and d < 5 and e >= 5:
        basic_type = "すもも"

    # 추가 타입 산출
    additional_type = None
    if c > (QUESTIONS_PER_SECTION // 2):
        additional_type = "デジタル"
    elif c <= 10:
        additional_type = "アナログ"

    # 타입 결과 출력
    print(f"基本 タイプ: {basic_type}")
    print(f"追加 タイプ: {additional_type}")

    # ストレス 경고 메일 전송
    if stress >= 5:
        send_slack_alert()

    return jsonify({"success": True, "basicType": basic_type, "additionalType": additional_type}), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        # 클라이언트에서 질문 가져오기
        data = request.json
        user_question = data.get("question", "")

        if not user_question:
            return jsonify({"answer": "質問を入力してください."}), 400


        # ChatGPT 응답 가져오기
        chatgpt_answer = "LLMからの回答がここに戻って来ます"

        return jsonify({"answer": chatgpt_answer}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"answer": "⚠️ 서버에서 문제가 발생했습니다."}), 500

@app.route("/questions", methods=["GET"])
def get_questions():
    # 미답변 질문만 반환
    unanswered_questions = [q["question"] for q in questions_db if not q["answered"]]
    return jsonify({"questions": unanswered_questions}), 200

@app.route("/answer", methods=["POST"])
def save_answer():
    data = request.json
    question_text = data.get("question")
    answer_text = data.get("answer")

    if not question_text or not answer_text:
        return jsonify({"success": False, "message": "질문과 답변이 필요합니다."}), 400

    # 질문을 DB에서 찾고 답변 처리
    for question in questions_db:
        if question["question"] == question_text:
            question["answered"] = True
            # 답변 저장 로직 추가 가능 (DB 저장 등)
            print(f"질문: {question_text} | 답변: {answer_text}")
            return jsonify({"success": True}), 200

    return jsonify({"success": False, "message": "질문을 찾을 수 없습니다."}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render 환경에서 제공되는 PORT 환경 변수 사용
    app.run(host="0.0.0.0", port=port)


