from __future__ import annotations

from datetime import date, datetime, time, timedelta

import streamlit as st

st.set_page_config(page_title="나의 일정 관리자", page_icon="🗓️", layout="wide")

st.title("🗓️ 나의 일정 관리자")
st.caption("오늘과 다음 일정을 한눈에 확인하고, 빠르게 추가하세요.")

if "schedules" not in st.session_state:
    st.session_state.schedules = []
if "schedule_counter" not in st.session_state:
    st.session_state.schedule_counter = 1


def format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


def add_schedule(
    title: str,
    schedule_date: date,
    schedule_time: time,
    duration_minutes: int,
    priority: str,
    notes: str,
    category: str,
) -> None:
    schedule_datetime = datetime.combine(schedule_date, schedule_time)
    st.session_state.schedules.append(
        {
            "id": st.session_state.schedule_counter,
            "title": title,
            "datetime": schedule_datetime,
            "duration": duration_minutes,
            "priority": priority,
            "notes": notes,
            "category": category,
            "done": False,
        }
    )
    st.session_state.schedule_counter += 1


st.sidebar.header("일정 빠르게 추가")
with st.sidebar.form("schedule_form", clear_on_submit=True):
    title = st.text_input("일정 제목", placeholder="예: 팀 미팅 준비")
    schedule_date = st.date_input("날짜", value=date.today())
    schedule_time = st.time_input("시간", value=time(9, 0))
    duration_minutes = st.number_input("소요 시간 (분)", min_value=15, max_value=480, value=60, step=15)
    priority = st.selectbox("우선순위", ["높음", "보통", "낮음"], index=1)
    category = st.selectbox("카테고리", ["업무", "개인", "학습", "건강", "기타"], index=0)
    notes = st.text_area("메모", placeholder="준비물, 링크, 체크리스트 등을 입력하세요.")
    submitted = st.form_submit_button("일정 추가")

if submitted:
    if not title.strip():
        st.sidebar.error("일정 제목을 입력해주세요.")
    else:
        add_schedule(title.strip(), schedule_date, schedule_time, duration_minutes, priority, notes, category)
        st.sidebar.success("일정이 추가되었습니다!")


def sorted_schedules() -> list[dict]:
    return sorted(st.session_state.schedules, key=lambda item: item["datetime"])


all_schedules = sorted_schedules()
pending_schedules = [item for item in all_schedules if not item["done"]]
completed_schedules = [item for item in all_schedules if item["done"]]

today = date.today()
tomorrow = today + timedelta(days=1)

st.subheader("✨ 다음 처리할 일정")
next_up = pending_schedules[:3]
if next_up:
    columns = st.columns(3)
    for column, item in zip(columns, next_up):
        with column:
            st.markdown(
                f"""
                <div style="padding:16px;border-radius:12px;background:linear-gradient(135deg,#F8FAFF,#EEF2FF);border:1px solid #E0E7FF;">
                    <div style="font-size:18px;font-weight:600;">{item['title']}</div>
                    <div style="margin-top:6px;color:#4B5563;">{format_datetime(item['datetime'])}</div>
                    <div style="margin-top:6px;font-size:14px;color:#6B7280;">{item['category']} · {item['priority']} · {item['duration']}분</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("등록된 일정이 없습니다. 왼쪽에서 새 일정을 추가해보세요.")

st.subheader("📌 오늘 & 내일 일정")
today_items = [item for item in pending_schedules if item["datetime"].date() == today]
tomorrow_items = [item for item in pending_schedules if item["datetime"].date() == tomorrow]

col_today, col_tomorrow = st.columns(2)
with col_today:
    st.markdown("#### 오늘")
    if today_items:
        for item in today_items:
            st.markdown(
                f"**{format_datetime(item['datetime'])}** · {item['title']}  ",
                help=f"{item['category']} · {item['priority']} · {item['duration']}분",
            )
            if item["notes"]:
                st.caption(item["notes"])
    else:
        st.caption("오늘 예정된 일정이 없습니다.")

with col_tomorrow:
    st.markdown("#### 내일")
    if tomorrow_items:
        for item in tomorrow_items:
            st.markdown(
                f"**{format_datetime(item['datetime'])}** · {item['title']}  ",
                help=f"{item['category']} · {item['priority']} · {item['duration']}분",
            )
            if item["notes"]:
                st.caption(item["notes"])
    else:
        st.caption("내일 예정된 일정이 없습니다.")

st.subheader("📝 전체 일정 관리")
if not all_schedules:
    st.write("일정을 추가하면 이곳에서 상태를 관리할 수 있어요.")
else:
    for item in all_schedules:
        columns = st.columns([0.08, 0.7, 0.12, 0.1])
        with columns[0]:
            item["done"] = st.checkbox("완료", value=item["done"], key=f"done-{item['id']}")
        with columns[1]:
            status = "✅ 완료" if item["done"] else "⏳ 진행 중"
            st.markdown(
                f"**{item['title']}**  \n"
                f"{format_datetime(item['datetime'])} · {item['category']} · {item['priority']} · {item['duration']}분  \n"
                f"{status}"
            )
            if item["notes"]:
                st.caption(item["notes"])
        with columns[2]:
            st.metric("D-day", (item["datetime"].date() - today).days)
        with columns[3]:
            if st.button("삭제", key=f"delete-{item['id']}"):
                st.session_state.schedules = [
                    schedule for schedule in st.session_state.schedules if schedule["id"] != item["id"]
                ]
                st.experimental_rerun()

if completed_schedules:
    with st.expander("완료된 일정 보기"):
        for item in completed_schedules:
            st.markdown(f"- ~~{item['title']}~~ ({format_datetime(item['datetime'])})")
            
