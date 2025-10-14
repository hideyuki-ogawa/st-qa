import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

from logic import (
    adoption_stage,
    calc_ready,
    calc_reduction,
    matrix_hint,
    phase_label,
    phase_name,
)

st.set_page_config(
    page_title="AI Ready チェック",
    page_icon="🤖",
    layout="centered",
)

# --- Constants -----------------------------------------------------------------

QUESTIONS: List[str] = [
    "あなたの会社では、業務文書の電子化はどの程度進んでいますか？",
    "あなたの会社では、IT環境（情報共有・検索・アクセス）はどの程度整っていますか？",
    "あなたの会社では、生成AIアプリ（ChatGPT/Gemini/Copilot等）を使ったことがある人はどの程度いますか？",
    "あなたの会社では、生成AIを実務に取り入れている部署・チームはどの程度ありますか？",
    "あなたの会社では、経営層のAI/IT導入への支援はどの程度ありますか？",
    "あなたの会社では、“やってみよう”で試行が進む雰囲気はどの程度ありますか？",
    "あなたの会社では、AI/ITの勉強会・共有会はどの程度行われていますか？",
    "あなたの会社では、社員同士でAIの使い方を共有・相談できる雰囲気はどの程度ありますか？",
    "あなたの会社では、意思決定にデータを使うことはどの程度ありますか？",
    "あなたの会社では、業務改善や商品開発でAIを使おうとする動きはどの程度ありますか？",
]

GOOGLE_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


# --- Session State -------------------------------------------------------------

if "step" not in st.session_state:
    st.session_state.step = 0

for idx in range(1, len(QUESTIONS) + 1):
    st.session_state.setdefault(f"q{idx}", 50)

st.session_state.setdefault("client_id", str(uuid.uuid4()))
st.session_state.setdefault("submission_in_progress", False)
st.session_state.setdefault("submission_success", False)
st.session_state.setdefault("submission_error", "")


def post_to_sheets(row: List):
    creds_raw = st.secrets.get("GOOGLE_SHEETS_CREDS")
    sheet_name = st.secrets.get("SHEET_NAME")
    worksheet_name = st.secrets.get("WORKSHEET_NAME")

    if not creds_raw or not sheet_name or not worksheet_name:
        raise RuntimeError("Google Sheets の接続情報が設定されていません。")

    credentials_dict = json.loads(creds_raw)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        credentials_dict, GOOGLE_SCOPE
    )

    client = gspread.authorize(credentials)
    worksheet = client.open(sheet_name).worksheet(worksheet_name)
    worksheet.append_row(row, value_input_option="USER_ENTERED")


def submit_answers(vals: List[int], ready: int, adoption: int, reduction: float) -> bool:
    timestamp = datetime.now(timezone(timedelta(hours=9))).isoformat()
    query_params = st.experimental_get_query_params()
    referrer = query_params.get("ref", [""])[0]

    st.session_state.submission_error = ""

    metadata = {
        "timestamp": timestamp,
        "values": vals,
        "ready": ready,
        "adoption": adoption,
        "reduction": reduction,
        "client_id": st.session_state["client_id"],
        "referrer": referrer,
        "notes": "",
    }

    row = [
        metadata["timestamp"],
        *metadata["values"],
        metadata["ready"],
        metadata["adoption"],
        round(metadata["reduction"], 1),
        metadata["client_id"],
        "",
        metadata["referrer"],
        metadata["notes"],
    ]

    for attempt in range(3):
        try:
            post_to_sheets(row)
            return True
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                st.session_state.submission_error = str(exc)
                return False
            time.sleep(1 * (attempt + 1))
    return False


# --- UI Rendering --------------------------------------------------------------

st.title("AI Ready チェック")
st.caption("会社全体の雰囲気として、今のAI活用度を簡単診断します。")

total_steps = len(QUESTIONS)
current_step = st.session_state.step

if current_step < total_steps:
    st.progress((current_step + 1) / total_steps)
    st.subheader(f"Q{current_step + 1}")
    question_key = f"q{current_step + 1}"
    st.slider(
        QUESTIONS[current_step],
        min_value=0,
        max_value=100,
        value=st.session_state.get(question_key, 50),
        key=question_key,
    )

    button_cols = st.columns(2)
    with button_cols[0]:
        if st.button("戻る", disabled=current_step == 0):
            st.session_state.step = max(0, current_step - 1)
            st.rerun()
    with button_cols[1]:
        if st.button("次へ"):
            if st.session_state.get(f"q{current_step + 1}") is None:
                st.warning("スライダーで値を選択してください。")
            else:
                st.session_state.step = current_step + 1
                st.rerun()

else:
    answers = {f"q{idx}": st.session_state.get(f"q{idx}") for idx in range(1, total_steps + 1)}
    vals = [answers[f"q{idx}"] for idx in range(1, total_steps + 1)]
    ready_score = calc_ready(answers)
    adoption_score = answers["q4"]
    reduction_pct = calc_reduction(ready_score, adoption_score)

    phase_icon = phase_label(ready_score)
    phase_text = phase_name(ready_score)
    adoption_label = adoption_stage(adoption_score)
    recommendation = matrix_hint(ready_score, adoption_score)

    st.success("結果がまとまりました。内容をご確認ください。")
    st.metric("AI Ready 指数", f"{ready_score} 点", delta=None)
    st.write(f"フェーズ：{phase_icon} {phase_text}フェーズ")
    st.write(f"現在のAI導入度（Q4）：{adoption_score} %（{adoption_label}）")
    st.metric("想定作業時間削減率", f"{reduction_pct:.0f} %")
    st.info(recommendation)

    st.divider()
    st.write("9マトリクス提案に基づく次の一歩のヒントです。")

    cols = st.columns(2)
    with cols[0]:
        if st.button("回答を編集する"):
            st.session_state.step = total_steps - 1
            st.rerun()

    with cols[1]:
        disabled = st.session_state.submission_in_progress or st.session_state.submission_success
        if st.button("この結果を送信・集計に協力する", disabled=disabled):
            st.session_state.submission_in_progress = True
            if submit_answers(vals, ready_score, adoption_score, reduction_pct):
                st.session_state.submission_success = True
                st.session_state.submission_error = ""
            st.session_state.submission_in_progress = False
            st.rerun()

    if st.session_state.submission_in_progress:
        st.info("送信処理中です。少々お待ちください。")

    if st.session_state.submission_success:
        st.balloons()
        st.success(
            "ご協力ありがとうございました。結果は統計的に集計し、長目通信などで活用します。"
        )
        st.markdown("[長目の公式サイトを見る](https://www.nagame.jp)")

    if st.session_state.submission_error:
        st.error(
            "送信に失敗しました。時間をおいて再度お試しください。\n\n"
            f"詳細: {st.session_state.submission_error}"
        )
