from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import operator
import json
import os

app = FastAPI()

# JSON 파일에서 룰셋 데이터 불러오기
def load_rules():

    file_path = os.path.join(os.path.dirname(__file__), "rules.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


rules_data = load_rules()
pokemon_map = rules_data["pokemon_map"]
scoring_rules = rules_data["scoring_rules"]

class Answer(BaseModel):
    question_id: str
    choice: str

class UserInput(BaseModel):
    gender: str
    answers: List[Answer]

@app.post("/recommend")
def get_pokemon_recommendation(user_input: UserInput):
    scores = {key: 0 for key in pokemon_map.keys()}
    
    for ans in user_input.answers:
        q_id = ans.question_id
        choice = ans.choice
        

        if q_id in scoring_rules and choice in scoring_rules[q_id]:
   
            points_to_add = scoring_rules[q_id][choice]
            for personality, point in points_to_add.items():
                if personality in scores:
                    scores[personality] += point

    best_personality = max(scores.items(), key=operator.itemgetter(1))[0]
    
   
    recommended_pokemon = pokemon_map[best_personality].get(user_input.gender, "001_이상해씨")
   
    return {
        "personality": best_personality,
        "pokemon": recommended_pokemon,
        "scores_detail": scores
    }