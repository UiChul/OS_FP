import streamlit as st
import requests
import json
import random
import os

# 페이지 기본 설정
st.set_page_config(page_title="포켓몬 페르소나 진단", page_icon="🔍")

# 1. JSON 파일에서 질문 데이터 불러오기
@st.cache_data
def load_questions():
    # questions.json 파일이 front 폴더 안에 있다고 가정
    file_path = os.path.join(os.path.dirname(__file__), "questions.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

QUESTIONS = load_questions()

@st.cache_data
def load_pokemon_image(image_path):
    if os.path.exists(image_path):
        # 이미지를 바이너리(bytes) 형태로 읽어서 메모리에 저장합니다.
        with open(image_path, "rb") as f:
            return f.read()
    return None

# 2. 세션 상태 초기화 및 30문항 세팅 로직
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'gender' not in st.session_state:
    st.session_state.gender = None

if 'questions_to_ask' not in st.session_state:
    # 필수 문항 15개 ID (q37_b는 분기 질문이므로 여기서 제외)
    core_ids = [
        "q1", "q2", "q6", "q8", "q10", 
        "q21", "q29", "q30", "q35", "q36", 
        "q37", "q44", "q47", "q54", "q55"
    ]
    
    # 문항 분류
    core_questions = [q for q in QUESTIONS if q['id'] in core_ids]
    random_candidates = [q for q in QUESTIONS if q['id'] not in core_ids and q['id'] != "q37_b"]
    q37_b_data = next(q for q in QUESTIONS if q['id'] == "q37_b")
    
    # 남은 문항 중 15개 랜덤 추출
    sampled_random_questions = random.sample(random_candidates, 15)
    
    # 필수 문항 + 랜덤 문항 합치고 순서 섞기
    final_questions = core_questions + sampled_random_questions
    random.shuffle(final_questions)
    
    # 우주인 분기 질문(q37_b)을 원래 질문(q37) 바로 다음 순서에 삽입
    q37_index = next(i for i, q in enumerate(final_questions) if q['id'] == 'q37')
    final_questions.insert(q37_index + 1, q37_b_data)
    
    st.session_state.questions_to_ask = final_questions

# 3. 화면 렌더링
def render_ui():
    st.title("🔍 나는 어떤 포켓몬일까?")
    
    current_step = st.session_state.step
    target_questions = st.session_state.questions_to_ask
    total_steps = len(target_questions) + 1 # 질문 수 + 성별 질문

    # --- [상태 A] 질문 진행 중 ---
    if current_step < len(target_questions):
        progress = int((current_step / total_steps) * 100)
        st.progress(progress, text=f"진행도: {progress}%")
        
        q = target_questions[current_step]
        
        # 분기 로직 처리: q37에서 '싸운다'를 안 골랐다면 q37_b 건너뛰기
        if q["id"] == "q37_b":
            alien_answer = next((ans["choice"] for ans in st.session_state.answers if ans["question_id"] == "q37"), None)
            if alien_answer != "싸운다":
                st.session_state.step += 1
                st.rerun()

        st.markdown(f"### Q. {q['text']}")
        st.write("")
        
        # 블록 형태의 버튼 렌더링
        for option in q['options']:
            if st.button(option, use_container_width=True):
                st.session_state.answers.append({
                    "question_id": q["id"],
                    "choice": option
                })
                st.session_state.step += 1
                st.rerun()

    # --- [상태 B] 모든 질문 완료 후 성별 질문 ---
    elif current_step == len(target_questions):
        st.progress(95, text="거의 다 왔습니다! (95%)")
        st.markdown("### 마지막으로, 당신의 성별을 알려주세요.")
        st.caption("포켓몬 페르소나 매핑을 위해 필요합니다.")
        
        if st.button("남자", use_container_width=True):
            st.session_state.gender = "남자"
            st.session_state.step += 1
            st.rerun()
        if st.button("여자", use_container_width=True):
            st.session_state.gender = "여자"
            st.session_state.step += 1
            st.rerun()

    # --- [상태 C] 결과 화면 ---
    else:
        st.progress(100, text="분석 완료!")
        
        with st.spinner("포켓몬 세계와 연결하는 중..."):
            # Docker Compose 환경에서는 "http://backend:8000/recommend" 를 사용합니다.
            # 로컬 테스트 시에는 "http://localhost:8000/recommend" 로 변경하세요.
            api_url = "http://localhost:8000/recommend"
            payload = {
                "gender": st.session_state.gender,
                "answers": st.session_state.answers
            }
            
            try:
                response = requests.post(api_url, json=payload)
                response.raise_for_status()
                result_data = response.json()
                pokemon_name = result_data['pokemon'] # 예: "001_이상해씨"
                print(pokemon_name)
                
                
                st.balloons()
                
                # 결과 텍스트 출력
                st.markdown(f"<h3 style='text-align: center; color: gray;'>당신의 성격은 [{result_data['personality']}]!</h3>", unsafe_allow_html=True)
                # "001_이상해씨" 에서 번호를 떼고 이름만 예쁘게 보여주기 위한 전처리
                display_name = pokemon_name.split('_')[-1] 
                st.markdown(f"<h1 style='text-align: center;'>어울리는 포켓몬은 [{display_name}] 입니다!</h1>", unsafe_allow_html=True)
                
                # 로컬 폴더(front/images)에서 포켓몬 이미지 불러오기
                image_path = os.path.join(os.path.dirname(__file__), "images", f"{pokemon_name}.png")
                print(image_path)
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    cached_image = load_pokemon_image(image_path)
                    
                    if cached_image:
                        st.image(cached_image, use_container_width=True)
                    else:
                        st.warning("이미지 파일을 찾을 수 없습니다.")
                
                st.write("")
                if st.button("다시 테스트하기", use_container_width=True):
                    # 다시 시작할 때 질문도 새로 셔플되도록 전체 세션 초기화
                    st.session_state.clear()
                    st.rerun()
                    
            except Exception as e:
                st.error(f"서버와 통신 실패: {e}")

if __name__ == "__main__":
    render_ui()