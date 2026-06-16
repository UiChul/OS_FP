from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import operator
import json
import os

app = FastAPI()

# 1. JSON 파일에서 룰셋 데이터 불러오기
def load_rules():
    # rules.json 파일이 현재 파일(main.py)과 같은 폴더에 있다고 가정
    file_path = os.path.join(os.path.dirname(__file__), "rules.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 앱 실행 시 미리 데이터를 메모리에 올려둡니다.
rules_data = load_rules()
pokemon_map = rules_data["pokemon_map"]
scoring_rules = rules_data["scoring_rules"]

# 2. Pydantic 데이터 모델 (프론트엔드 요청 구조와 매핑)
class Answer(BaseModel):
    question_id: str
    choice: str

class UserInput(BaseModel):
    gender: str
    answers: List[Answer]

# 3. 추천 계산 API 엔드포인트
@app.post("/recommend")
def get_pokemon_recommendation(user_input: UserInput):
    # 1. 초기 점수판 세팅 (모든 성격을 0점으로 초기화)
    scores = {key: 0 for key in pokemon_map.keys()}
    
    # 2. 프론트엔드에서 넘어온 답변 리스트를 순회하며 점수 합산
    for ans in user_input.answers:
        q_id = ans.question_id
        choice = ans.choice
        
        # 룰셋(scoring_rules)에 해당 질문과 선택지가 존재하는지 확인
        if q_id in scoring_rules and choice in scoring_rules[q_id]:
            # 부여할 점수 항목들을 가져와서 합산
            points_to_add = scoring_rules[q_id][choice]
            for personality, point in points_to_add.items():
                if personality in scores:
                    scores[personality] += point
                    
    # 3. 최고 점수를 받은 성격 도출
    best_personality = max(scores.items(), key=operator.itemgetter(1))[0]
    
    # 4. 성별에 따른 최종 포켓몬 도출 (매핑 실패 시 기본값으로 '001_이상해씨' 반환)
    recommended_pokemon = pokemon_map[best_personality].get(user_input.gender, "001_이상해씨")
    
    # 5. 최종 결과 반환
    return {
        "personality": best_personality,
        "pokemon": recommended_pokemon,
        "scores_detail": scores
    }