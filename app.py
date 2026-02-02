from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import requests
import streamlit as st


@dataclass(frozen=True)
class Option:
    label: str
    weights: Dict[str, int]


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str
    options: List[Option]


GENRE_CONFIG = {
    "액션": {"id": 28, "reason": "에너제틱한 선택이 많아 강렬한 액션이 잘 어울립니다."},
    "코미디": {"id": 35, "reason": "유쾌함을 중시하는 답변으로 웃음 가득한 영화를 추천해요."},
    "드라마": {"id": 18, "reason": "감정선과 몰입감을 중요하게 여겨 깊이 있는 이야기가 어울립니다."},
    "SF": {"id": 878, "reason": "새로운 세계에 대한 호기심이 높아 SF 장르가 잘 맞아요."},
    "로맨스": {"id": 10749, "reason": "따뜻한 관계와 설렘을 원해 로맨틱한 무드를 선택했습니다."},
    "판타지": {"id": 14, "reason": "상상력을 자극하는 답변이 많아 판타지 세계가 제격이에요."},
}

QUESTIONS = [
    Question(
        key="mood",
        prompt="오늘 원하는 무드는 어떤가요?",
        options=[
            Option("아드레날린 폭발!", {"액션": 3, "SF": 1}),
            Option("가볍고 유쾌하게", {"코미디": 3, "로맨스": 1}),
            Option("잔잔하고 진중하게", {"드라마": 3, "로맨스": 1}),
            Option("새로운 세계를 탐험하고 싶어", {"SF": 2, "판타지": 3}),
        ],
    ),
    Question(
        key="setting",
        prompt="어떤 배경의 이야기가 끌리나요?",
        options=[
            Option("현실적이고 공감되는 이야기", {"드라마": 3, "로맨스": 2}),
            Option("미래나 우주 등 미지의 공간", {"SF": 3, "액션": 1}),
            Option("마법과 신화가 있는 세계", {"판타지": 3, "액션": 1}),
            Option("일상 속 소동과 웃음", {"코미디": 3, "로맨스": 1}),
        ],
    ),
    Question(
        key="pace",
        prompt="스토리 전개 속도는 어떤 걸 선호하나요?",
        options=[
            Option("빠르고 박진감 있게", {"액션": 3, "SF": 1}),
            Option("서서히 몰입되는 서사", {"드라마": 3, "판타지": 1}),
            Option("가볍게 흘러가는 리듬", {"코미디": 3}),
            Option("설레는 감정선이 중요한 속도", {"로맨스": 3}),
        ],
    ),
    Question(
        key="character",
        prompt="주인공의 모습은 어떨까요?",
        options=[
            Option("강인한 히어로", {"액션": 3, "SF": 1}),
            Option("평범하지만 특별한 인물", {"드라마": 3, "로맨스": 1}),
            Option("엉뚱하고 매력적인 캐릭터", {"코미디": 3}),
            Option("신비로운 존재", {"판타지": 3, "SF": 1}),
        ],
    ),
    Question(
        key="ending",
        prompt="보고 난 뒤 어떤 여운이 남았으면 하나요?",
        options=[
            Option("짜릿하고 시원한 느낌", {"액션": 3, "SF": 1}),
            Option("따뜻한 미소", {"로맨스": 3, "코미디": 1}),
            Option("생각할 거리를 주는 감동", {"드라마": 3}),
            Option("현실을 잊게 하는 몰입", {"판타지": 3, "SF": 1}),
        ],
    ),
]


st.set_page_config(page_title="심리테스트 영화 추천", page_icon="🎬", layout="wide")

st.title("🎬 심리테스트로 영화 추천")
st.caption("질문에 답하고 나만의 취향에 맞는 영화를 추천받아 보세요.")

tmdb_key = st.sidebar.text_input("TMDB API Key", type="password")
st.sidebar.info("TMDB API 키가 있어야 결과를 볼 수 있어요.")


def fetch_movies(api_key: str, genre_id: int) -> List[dict]:
    response = requests.get(
        "https://api.themoviedb.org/3/discover/movie",
        params={
            "api_key": api_key,
            "with_genres": genre_id,
            "language": "ko-KR",
            "sort_by": "popularity.desc",
        },
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[:5]


def calculate_genre(selections: Dict[str, str]) -> str:
    scores = {genre: 0 for genre in GENRE_CONFIG}
    for question in QUESTIONS:
        selected_label = selections.get(question.key)
        if not selected_label:
            continue
        for option in question.options:
            if option.label == selected_label:
                for genre, weight in option.weights.items():
                    scores[genre] += weight
                break
    return max(scores, key=scores.get)


def render_movie_card(movie: dict, reason: str) -> None:
    poster_path = movie.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    title = movie.get("title") or movie.get("name") or "제목 미상"
    rating = movie.get("vote_average", 0)
    overview = movie.get("overview") or "줄거리 정보가 없습니다."

    col_image, col_info = st.columns([1, 2.5], vertical_alignment="top")
    with col_image:
        if poster_url:
            st.image(poster_url, use_container_width=True)
        else:
            st.markdown("포스터 없음")
    with col_info:
        st.subheader(title)
        st.write(f"평점 ⭐ {rating:.1f}")
        st.write(overview)
        st.info(f"이 영화를 추천하는 이유: {reason}")


st.subheader("📝 심리테스트")
answers: Dict[str, str] = {}
for question in QUESTIONS:
    answers[question.key] = st.radio(
        question.prompt,
        options=[option.label for option in question.options],
        horizontal=False,
        key=f"answer-{question.key}",
    )

if st.button("결과 보기", type="primary"):
    if not tmdb_key:
        st.error("TMDB API Key를 입력해주세요.")
    else:
        selected_genre = calculate_genre(answers)
        genre_id = GENRE_CONFIG[selected_genre]["id"]
        reason_text = GENRE_CONFIG[selected_genre]["reason"]

        st.session_state["selected_genre"] = selected_genre
        st.session_state["genre_reason"] = reason_text
        st.session_state["genre_id"] = genre_id

if "selected_genre" in st.session_state:
    st.subheader("📌 결과")
    st.markdown(
        f"당신에게 추천하는 장르는 **{st.session_state['selected_genre']}** 입니다. "
        f"{st.session_state['genre_reason']}"
    )

    try:
        movies = fetch_movies(tmdb_key, st.session_state["genre_id"])
    except requests.RequestException:
        st.error("TMDB 정보를 불러오지 못했습니다. API Key를 확인해주세요.")
        movies = []

    if movies:
        for movie in movies:
            render_movie_card(movie, st.session_state["genre_reason"])
            st.divider()
    else:
        st.info("해당 장르의 영화를 찾지 못했습니다. 다른 답변을 시도해보세요.")
