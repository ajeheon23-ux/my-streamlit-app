from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple

import requests
import streamlit as st


@dataclass(frozen=True)
class Option:
    label: str
    weights: Dict[str, int]
    tags: Tuple[str, ...]


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

GENRE_NAME_BY_ID = {value["id"]: key for key, value in GENRE_CONFIG.items()}

QUESTIONS = [
    Question(
        key="mood",
        prompt="오늘 원하는 무드는 어떤가요?",
        options=[
            Option("아드레날린 폭발!", {"액션": 3, "SF": 1}, ("속도감", "강렬함")),
            Option("가볍고 유쾌하게", {"코미디": 3, "로맨스": 1}, ("유쾌함", "기분전환")),
            Option("잔잔하고 진중하게", {"드라마": 3, "로맨스": 1}, ("몰입", "감성")),
            Option("새로운 세계를 탐험하고 싶어", {"SF": 2, "판타지": 3}, ("탐험", "상상력")),
        ],
    ),
    Question(
        key="setting",
        prompt="어떤 배경의 이야기가 끌리나요?",
        options=[
            Option("현실적이고 공감되는 이야기", {"드라마": 3, "로맨스": 2}, ("현실감", "공감")),
            Option("미래나 우주 등 미지의 공간", {"SF": 3, "액션": 1}, ("미지", "스케일")),
            Option("마법과 신화가 있는 세계", {"판타지": 3, "액션": 1}, ("마법", "신화")),
            Option("일상 속 소동과 웃음", {"코미디": 3, "로맨스": 1}, ("일상", "웃음")),
        ],
    ),
    Question(
        key="pace",
        prompt="스토리 전개 속도는 어떤 걸 선호하나요?",
        options=[
            Option("빠르고 박진감 있게", {"액션": 3, "SF": 1}, ("박진감", "스릴")),
            Option("서서히 몰입되는 서사", {"드라마": 3, "판타지": 1}, ("서사", "몰입")),
            Option("가볍게 흘러가는 리듬", {"코미디": 3}, ("가벼움", "리듬감")),
            Option("설레는 감정선이 중요한 속도", {"로맨스": 3}, ("설렘", "감정선")),
        ],
    ),
    Question(
        key="character",
        prompt="주인공의 모습은 어떨까요?",
        options=[
            Option("강인한 히어로", {"액션": 3, "SF": 1}, ("히어로", "강인함")),
            Option("평범하지만 특별한 인물", {"드라마": 3, "로맨스": 1}, ("공감", "성장")),
            Option("엉뚱하고 매력적인 캐릭터", {"코미디": 3}, ("개성", "유머")),
            Option("신비로운 존재", {"판타지": 3, "SF": 1}, ("신비", "비밀")),
        ],
    ),
    Question(
        key="ending",
        prompt="보고 난 뒤 어떤 여운이 남았으면 하나요?",
        options=[
            Option("짜릿하고 시원한 느낌", {"액션": 3, "SF": 1}, ("카타르시스", "전율")),
            Option("따뜻한 미소", {"로맨스": 3, "코미디": 1}, ("따뜻함", "힐링")),
            Option("생각할 거리를 주는 감동", {"드라마": 3}, ("감동", "여운")),
            Option("현실을 잊게 하는 몰입", {"판타지": 3, "SF": 1}, ("몰입", "판타지")),
        ],
    ),
]


st.set_page_config(page_title="심리테스트 영화 추천", page_icon="🎬", layout="wide")

st.title("🎬 심리테스트로 영화 추천")
st.caption("질문에 답하면 TMDB 인기 영화 중 나에게 맞는 5편을 추천합니다.")

tmdb_key = st.sidebar.text_input("TMDB API Key", type="password")
st.sidebar.info("TMDB API 키가 있어야 결과를 볼 수 있어요.")

with st.sidebar.expander("추천 필터 설정", expanded=False):
    sort_by = st.selectbox(
        "정렬 기준",
        ["popularity.desc", "vote_average.desc", "revenue.desc"],
        format_func=lambda value: {
            "popularity.desc": "인기순",
            "vote_average.desc": "평점순",
            "revenue.desc": "흥행순",
        }[value],
    )
    min_rating = st.slider("최소 평점", 0.0, 10.0, 6.5, 0.5)
    release_year = st.slider("개봉 연도 범위", 1980, date.today().year, (2000, date.today().year))
    include_adult = st.toggle("성인 콘텐츠 포함", value=False)


@st.cache_data(show_spinner=False)
def fetch_movies(
    api_key: str,
    genre_id: int,
    *,
    sort_by: str,
    min_rating: float,
    release_year: Tuple[int, int],
    include_adult: bool,
) -> List[dict]:
    response = requests.get(
        "https://api.themoviedb.org/3/discover/movie",
        params={
            "api_key": api_key,
            "with_genres": genre_id,
            "language": "ko-KR",
            "sort_by": sort_by,
            "vote_average.gte": min_rating,
            "primary_release_date.gte": f"{release_year[0]}-01-01",
            "primary_release_date.lte": f"{release_year[1]}-12-31",
            "include_adult": str(include_adult).lower(),
            "region": "KR",
        },
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[:5]


@st.cache_data(show_spinner=False)
def fetch_movie_detail(api_key: str, movie_id: int, language: str) -> dict:
    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={"api_key": api_key, "language": language},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def calculate_genre(selections: Dict[str, str]) -> tuple[str, Dict[str, int], List[str]]:
    scores = {genre: 0 for genre in GENRE_CONFIG}
    selected_tags: List[str] = []
    for question in QUESTIONS:
        selected_label = selections.get(question.key)
        if not selected_label:
            continue
        for option in question.options:
            if option.label == selected_label:
                selected_tags.extend(option.tags)
                for genre, weight in option.weights.items():
                    scores[genre] += weight
                break
    top_genre = max(scores, key=scores.get)
    return top_genre, scores, selected_tags


def build_recommend_reason(base_reason: str, tags: List[str]) -> str:
    unique_tags = list(dict.fromkeys(tags))
    if unique_tags:
        tag_text = ", ".join(unique_tags[:3])
        return f"{base_reason} 특히 **{tag_text}** 성향이 강해요."
    return base_reason


def render_movie_card(movie: dict, reason: str) -> None:
    poster_path = movie.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    title = movie.get("title") or movie.get("name") or "제목 미상"
    rating = movie.get("vote_average", 0.0)
    overview = movie.get("overview") or "줄거리 정보가 없습니다."
    genre_labels = [
        GENRE_NAME_BY_ID.get(genre_id, "기타") for genre_id in movie.get("genre_ids", [])
    ]
    release_date = movie.get("release_date") or "개봉일 미상"

    col_image, col_info = st.columns([1, 2.5], vertical_alignment="top")
    with col_image:
        if poster_url:
            st.image(poster_url, use_container_width=True)
        else:
            st.markdown("포스터 없음")
    with col_info:
        st.subheader(title)
        st.write(f"평점 ⭐ {rating:.1f}")
        st.caption(f"개봉일: {release_date}")
        if genre_labels:
            st.write("장르: " + " · ".join(genre_labels))
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

action_cols = st.columns([1, 1, 3])
with action_cols[0]:
    show_result = st.button("결과 보기", type="primary")
with action_cols[1]:
    if st.button("다시하기"):
        st.session_state.clear()
        st.experimental_rerun()

if show_result:
    if not tmdb_key:
        st.error("TMDB API Key를 입력해주세요.")
    else:
        selected_genre, score_board, selected_tags = calculate_genre(answers)
        genre_id = GENRE_CONFIG[selected_genre]["id"]
        reason_text = build_recommend_reason(GENRE_CONFIG[selected_genre]["reason"], selected_tags)

        st.session_state["selected_genre"] = selected_genre
        st.session_state["genre_reason"] = reason_text
        st.session_state["genre_id"] = genre_id
        st.session_state["score_board"] = score_board
        st.session_state["selected_tags"] = selected_tags

if "selected_genre" in st.session_state:
    st.subheader(f"당신에게 딱인 장르는: {st.session_state['selected_genre']}!")
    st.caption(st.session_state["genre_reason"])

    with st.expander("선택 성향 보기"):
        tags = st.session_state.get("selected_tags", [])
        if tags:
            st.write(", ".join(dict.fromkeys(tags)))
        else:
            st.caption("선택된 성향 태그가 없습니다.")
        st.bar_chart(st.session_state.get("score_board", {}), horizontal=True)

    with st.spinner("TMDB에서 영화를 가져오는 중..."):
        try:
            movies = fetch_movies(
                tmdb_key,
                st.session_state["genre_id"],
                sort_by=sort_by,
                min_rating=min_rating,
                release_year=release_year,
                include_adult=include_adult,
            )
        except requests.RequestException:
            st.error("TMDB 정보를 불러오지 못했습니다. API Key와 네트워크 상태를 확인해주세요.")
            movies = []

    if movies:
        if tmdb_key:
            for movie in movies:
                if not movie.get("overview"):
                    try:
                        detail = fetch_movie_detail(tmdb_key, movie["id"], "ko-KR")
                    except requests.RequestException:
                        detail = {}
                    movie["overview"] = detail.get("overview") or movie.get("overview")
                    movie["release_date"] = detail.get("release_date") or movie.get("release_date")
                    movie["genre_ids"] = detail.get("genres") or movie.get("genre_ids")

        columns = st.columns(3)
        for index, movie in enumerate(movies):
            poster_path = movie.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            title = movie.get("title") or movie.get("name") or "제목 미상"
            rating = movie.get("vote_average", 0.0)

            with columns[index % 3]:
                st.markdown(" ")
                if poster_url:
                    st.image(poster_url, use_container_width=True)
                else:
                    st.markdown("포스터 없음")
                st.markdown(f"**{title}**")
                st.caption(f"평점 ⭐ {rating:.1f}")

                with st.expander("상세 정보 보기"):
                    overview = movie.get("overview") or "줄거리 정보가 없습니다."
                    release_date = movie.get("release_date") or "개봉일 미상"
                    raw_genres = movie.get("genre_ids", [])
                    if raw_genres and isinstance(raw_genres[0], dict):
                        genre_labels = [genre.get("name", "기타") for genre in raw_genres]
                    else:
                        genre_labels = [
                            GENRE_NAME_BY_ID.get(genre_id, "기타") for genre_id in raw_genres
                        ]
                    st.write(f"개봉일: {release_date}")
                    if genre_labels:
                        st.write("장르: " + " · ".join(genre_labels))
                    st.write(overview)
                    st.info(f"이 영화를 추천하는 이유: {st.session_state['genre_reason']}")
    else:
        st.info("해당 장르의 영화를 찾지 못했습니다. 다른 답변을 시도해보세요.")
