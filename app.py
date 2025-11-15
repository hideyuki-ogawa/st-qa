import json
import time
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List
from uuid import uuid4

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dateutil import tz

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    gspread = None  # type: ignore
    ServiceAccountCredentials = None  # type: ignore


PAGE_TITLE = "AI Ready チェック"
QUESTIONS_PATH = Path(__file__).parent / "data" / "quiz.md"
SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CATEGORY_ALIASES = {
    "データ活用志向": "データ活用",
    "データ応用意": "データ活用",
}
INDUSTRY_OPTIONS = [
    "製造業",
    "情報通信業",
    "流通・小売",
    "専門サービス・士業",
    "医療・福祉",
    "教育・学習支援",
    "建設・不動産",
    "飲食・宿泊",
    "行政・公共",
    "その他（自由入力）",
]
PREFECTURE_OPTIONS = [
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
]
DEFAULT_PREFECTURE = "京都府"


@st.cache_data(show_spinner=False)
def load_questions() -> List[Dict[str, str]]:
    """Parse the quiz markdown into a list of question dicts."""
    if not QUESTIONS_PATH.exists():
        st.error("質問ファイルが見つかりませんでした。`data/quiz.md` を確認してください。")
        st.stop()

    lines = QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
    questions: List[Dict[str, str]] = []
    table_started = False

    for line in lines:
        if not line.strip():
            continue
        if line.startswith("No"):
            table_started = True
            continue
        if not table_started:
            continue

        parts = [part.strip() for part in line.split("\t") if part.strip()]
        if len(parts) < 2:
            continue

        no, prompt = parts[:2]
        category = parts[3] if len(parts) > 3 else ""
        try:
            idx = int(no)
        except ValueError:
            continue

        questions.append(
            {
                "id": f"q{idx}",
                "order": idx,
                "prompt": prompt,
                "category": category,
            }
        )

    if len(questions) != 10:
        st.warning("質問数が10件ではありません。`data/quiz.md` の内容をご確認ください。")

    questions.sort(key=lambda item: item["order"])
    return questions


@st.cache_resource(show_spinner=False)
def get_gspread_client(creds_json: str):
    """Create a cached gspread client from JSON credentials."""
    if not gspread or not ServiceAccountCredentials:
        raise RuntimeError("gspread または oauth2client がインポートできません。")

    try:
        creds_dict = json.loads(creds_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Streamlit Secrets の GOOGLE_SHEETS_CREDS が JSON 形式ではありません。") from exc

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes=SHEETS_SCOPE)
    return gspread.authorize(credentials)


def ensure_session_defaults(questions: List[Dict[str, str]]) -> None:
    """Initialize session state keys used by the wizard."""
    if "client_id" not in st.session_state:
        st.session_state.client_id = str(uuid4())

    if "prefecture" not in st.session_state:
        st.session_state.prefecture = DEFAULT_PREFECTURE

    if "industry_choice" not in st.session_state:
        st.session_state.industry_choice = INDUSTRY_OPTIONS[0]

    if "industry_custom" not in st.session_state:
        st.session_state.industry_custom = ""

    if "industry" not in st.session_state:
        st.session_state.industry = None

    if "answers" not in st.session_state:
        st.session_state.answers = {q["id"]: None for q in questions}

    if "current_question" not in st.session_state:
        st.session_state.current_question = 0

    if "step" not in st.session_state:
        st.session_state.step = "industry"

    if "submission_status" not in st.session_state:
        st.session_state.submission_status = None


def compute_results(answers: Dict[str, int]) -> Dict[str, float]:
    """Calculate aggregate metrics from the answer set."""
    numeric_answers = [value for value in answers.values() if value is not None]
    if len(numeric_answers) != len(answers):
        raise ValueError("Missing answers; cannot compute final results.")

    numeric_answers = [int(value) for value in numeric_answers]
    ai_ready = round(mean(numeric_answers))
    ai_adoption = int(answers.get("q4", 0))

    ready_ratio = ai_ready / 100
    adoption_ratio = ai_adoption / 100
    reduction_pct = ((1 - adoption_ratio) * ready_ratio * 0.9 + adoption_ratio * ready_ratio * 0.3) * 100

    category = "🌱 スタート"
    if ai_ready >= 70:
        category = "🚀 拡張期"
    elif ai_ready >= 40:
        category = "🔧 試行期"

    return {
        "ai_ready": ai_ready,
        "ai_adoption": ai_adoption,
        "reduction_pct": round(reduction_pct, 1),
        "category_label": category,
    }


def suggestion_from_matrix(ai_ready: int, ai_adoption: int) -> str:
    """Return a short suggestion based on the 3x3 matrix."""
    ready_band = "準備"
    if ai_ready >= 70:
        ready_band = "拡張"
    elif ai_ready >= 40:
        ready_band = "試行"

    adoption_band = "未導入"
    if ai_adoption >= 70:
        adoption_band = "定着"
    elif ai_adoption >= 40:
        adoption_band = "一部"

    matrix = {
        ("準備", "未導入"): "基盤整備→小規模試行",
        ("準備", "一部"): "成功事例の共有→法人プランへ",
        ("準備", "定着"): "ガバナンス整備（セキュリティ/ルール）",
        ("試行", "未導入"): "日報/報告から導入",
        ("試行", "一部"): "テンプレ整備と効果測定",
        ("試行", "定着"): "標準化と定期研修",
        ("拡張", "未導入"): "高効果部門に一気に導入",
        ("拡張", "一部"): "全社最適化とROI管理",
        ("拡張", "定着"): "自動化/高度応用へ",
    }

    return matrix.get((ready_band, adoption_band), "次の一歩を検討しましょう。")


def build_category_scores(questions: List[Dict[str, str]], answers: Dict[str, int]) -> pd.DataFrame:
    """Aggregate slider answers into category averages."""
    buckets: Dict[str, List[int]] = {}
    order: List[str] = []

    for question in questions:
        raw_category = question.get("category") or "その他"
        category = CATEGORY_ALIASES.get(raw_category, raw_category)
        value = answers.get(question["id"])
        if value is None:
            continue
        if category not in buckets:
            buckets[category] = []
            order.append(category)
        buckets[category].append(int(value))

    data = []
    for category in order:
        values = buckets.get(category)
        if not values:
            continue
        data.append({"カテゴリ": category, "スコア": round(mean(values))})

    return pd.DataFrame(data)


def render_category_radar(category_df: pd.DataFrame):
    """Render a polar radar chart from the category averages using Plotly."""
    if category_df.empty:
        return

    categories = list(category_df["カテゴリ"])
    scores = list(category_df["スコア"])

    categories.append(categories[0])
    scores.append(scores[0])

    fig = go.Figure(
        data=go.Scatterpolar(
            r=scores,
            theta=categories,
            fill="toself",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=8),
            name="カテゴリ平均",
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 100],
                showticklabels=True,
                tickfont=dict(size=18),  # 1.5倍に拡大 (12 * 1.5 = 18)
            ),
            angularaxis=dict(
                tickfont=dict(size=18),  # カテゴリ名のフォントサイズも1.5倍に
            ),
        ),
        showlegend=False,
        margin=dict(t=40, b=40, l=60, r=60),  # 余白を広めに
        width=500,  # チャート幅を制限 (元の2/3程度)
        height=500,  # 高さも同様に調整
    )

    # チャートを中央寄せで表示
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, use_container_width=False)


def format_timestamp() -> str:
    """Return the current timestamp string using TZ secret or JST."""
    tz_name = st.secrets.get("TZ", "Asia/Tokyo")
    target_tz = tz.gettz(tz_name)
    now = datetime.now(tz=tz.UTC).astimezone(target_tz)
    return now.isoformat()


def append_response_to_sheet(row_values: List):
    """Append a response row to the configured Google Sheet with retries."""
    if "GOOGLE_SHEETS_CREDS" not in st.secrets:
        raise RuntimeError("Streamlit Secrets に GOOGLE_SHEETS_CREDS が設定されていません。")

    client = get_gspread_client(st.secrets["GOOGLE_SHEETS_CREDS"])
    sheet_name = st.secrets.get("SHEET_NAME", "AI_Ready_Responses")
    worksheet_name = st.secrets.get("WORKSHEET_NAME", "responses")

    spreadsheet = client.open(sheet_name)
    worksheet = spreadsheet.worksheet(worksheet_name)

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            worksheet.append_row(row_values, value_input_option="USER_ENTERED")
            return
        except Exception as exc:  # pylint: disable=broad-except
            wait_sec = 2 ** (attempt - 1)
            if attempt == max_attempts:
                raise RuntimeError("Google Sheets への書き込みに失敗しました。") from exc
            time.sleep(wait_sec)


def ensure_answer_value(question_id: str, value: int) -> None:
    """Persist the latest slider value into session state."""
    st.session_state.answers[question_id] = int(value)


def render_question_step(questions: List[Dict[str, str]]):
    """Render the wizard UI for the current question."""
    idx = st.session_state.current_question
    total = len(questions)
    question = questions[idx]

    st.progress(idx / total)
    st.caption(f"質問 {idx + 1} / {total}")
    st.subheader(question["prompt"])

    prev_value = st.session_state.answers.get(question["id"])
    default_value = prev_value if prev_value is not None else 50

    slider_key = f"slider_{question['id']}"
    if slider_key not in st.session_state:
        st.session_state[slider_key] = default_value

    slider_value = st.slider(
        "スライダーで回答してください（0 = ほぼ無、100 = 十分）",
        min_value=0,
        max_value=100,
        step=1,
        key=slider_key,
    )

    col_prev, col_next = st.columns(2)

    if col_prev.button("◀ 戻る", disabled=idx == 0):
        ensure_answer_value(question["id"], slider_value)
        st.session_state.current_question = max(0, idx - 1)
        st.rerun()

    if col_next.button("次へ ▶"):
        ensure_answer_value(question["id"], slider_value)
        if idx + 1 < total:
            st.session_state.current_question = idx + 1
        else:
            if None in st.session_state.answers.values():
                st.warning("未回答の質問があります。戻ってすべて回答してください。")
                return
            st.session_state.step = "ready"
        st.rerun()


def render_industry_step():
    """Collect industry information before starting the questionnaire."""
    st.header("地域と業種について教えてください")
    st.caption("結果の分析に活用します。該当する地域と業種をお選びください。")

    current_prefecture = st.session_state.prefecture
    if current_prefecture not in PREFECTURE_OPTIONS:
        current_prefecture = DEFAULT_PREFECTURE
        st.session_state.prefecture = current_prefecture

    prefecture = st.selectbox(
        "都道府県を選択",
        options=PREFECTURE_OPTIONS,
        index=PREFECTURE_OPTIONS.index(current_prefecture),
        key="prefecture_select",
    )
    st.session_state.prefecture = prefecture

    selected = st.selectbox(
        "業種を選択",
        options=INDUSTRY_OPTIONS,
        index=INDUSTRY_OPTIONS.index(st.session_state.industry_choice),
        key="industry_choice_select",
    )
    st.session_state.industry_choice = selected

    custom_value = st.text_input(
        "その他の業種（任意）",
        value=st.session_state.industry_custom,
        placeholder="例: エネルギー、エンタメ など",
        disabled=selected != "その他（自由入力）",
    )

    if selected == "その他（自由入力）":
        st.session_state.industry_custom = custom_value
    else:
        st.session_state.industry_custom = ""

    cols = st.columns([1, 1, 1])
    if cols[1].button("次へ進む", use_container_width=True):
        if selected == "その他（自由入力）":
            if not custom_value.strip():
                st.warning("その他の業種を入力してください。")
                st.stop()
            st.session_state.industry = custom_value.strip()
        else:
            st.session_state.industry = selected
        st.session_state.step = "questions"
        st.rerun()


def render_results_step(questions: List[Dict[str, str]]):
    """Show the calculated results and submission controls."""
    answers = st.session_state.answers

    incomplete = [item for item in questions if answers.get(item["id"]) is None]
    if incomplete:
        st.warning("未回答の質問があります。回答画面に戻ります。")
        next_question = incomplete[0]
        st.session_state.current_question = questions.index(next_question)
        st.session_state.step = "questions"
        st.rerun()

    with st.spinner("スコアを解析中..."):
        time.sleep(0.6)
        results = compute_results(answers)
    st.progress(1.0)
    st.header("AI Ready 結果")

    info_bits = []
    prefecture_value = st.session_state.get("prefecture")
    if prefecture_value:
        info_bits.append(f"回答都道府県: {prefecture_value}")
    if st.session_state.industry:
        info_bits.append(f"回答業種: {st.session_state.industry}")
    if info_bits:
        st.caption(" / ".join(info_bits))

    col_ready, col_cat = st.columns([2, 1])
    col_ready.metric("AI Ready 指数", f"{results['ai_ready']}")
    col_ready.caption(results["category_label"])
    col_cat.metric("導入度", f"{results['ai_adoption']} %")

    st.metric("想定作業時間削減率", f"{results['reduction_pct']} %")
    st.write("次の一歩:")
    st.info(suggestion_from_matrix(results["ai_ready"], results["ai_adoption"]))

    category_df = build_category_scores(questions, answers)
    if not category_df.empty:
        st.subheader("カテゴリ別スコア")
        st.caption("各カテゴリの平均スコアをもとにレーダーチャートを表示しています。")
        render_category_radar(category_df)

    # 記録操作は事前の完了画面で実施済み。ここでは結果表示のみ。

    
def render_ready_step(questions: List[Dict[str, str]]):
    """Show finalization screen with a single CTA to record and view results."""
    answers = st.session_state.answers
    incomplete = [item for item in questions if answers.get(item["id"]) is None]
    if incomplete:
        st.warning("未回答の質問があります。回答画面に戻ります。")
        next_question = incomplete[0]
        st.session_state.current_question = questions.index(next_question)
        st.session_state.step = "questions"
        st.rerun()

    st.header("終了しました。お疲れ様です")
    st.caption("下のボタンで結果を記録し、集計に協力いただけます。そのまま結果も確認できます。")

    can_submit = "GOOGLE_SHEETS_CREDS" in st.secrets
    col = st.columns([1])[0]

    if can_submit:
        if col.button("結果を記録して・確認する", use_container_width=True):
            try:
                # 先に計算し、その行をシートへ追加
                results = compute_results(answers)
                append_response_to_sheet(build_row_payload(results, answers))
            except Exception as exc:  # pylint: disable=broad-except
                st.warning(f"記録に失敗しましたが、結果は表示します: {exc}")
            finally:
                st.session_state.step = "results"
                st.rerun()
    else:
        st.info("記録設定が未構成のため、結果のみ表示します。")
        if col.button("結果を確認する", use_container_width=True):
            st.session_state.step = "results"
            st.rerun()

    # 編集して戻る導線
    if st.button("回答を編集する"):
        st.session_state.step = "questions"
        st.rerun()


def build_row_payload(results: Dict[str, float], answers: Dict[str, int]) -> List:
    """Construct the row payload for Google Sheets."""
    timestamp = format_timestamp()
    ordered_answers = [answers[f"q{idx}"] for idx in range(1, 11)]

    user_agent = st.session_state.get("user_agent", "streamlit-client")
    referrer = st.experimental_get_query_params().get("ref", ["direct"])[0]

    return [
        timestamp,
        *ordered_answers,
        results["ai_ready"],
        results["ai_adoption"],
        results["reduction_pct"],
        st.session_state.prefecture or "",
        st.session_state.industry or "",
        st.session_state.client_id,
        user_agent,
        referrer,
        "",
    ]


def render_completion_step():
    """Display the final thank-you screen."""
    st.progress(1.0)
    st.header("ご協力ありがとうございました")
    st.write("ご回答を送信しました。今後のサービス向上に活用させていただきます。")
    st.write("データは匿名で集計し、業種別の傾向分析にのみ利用します。")
    st.link_button("長目サイトを見る", "https://www.chomoku.info", use_container_width=False)
    st.button("新しく回答する", on_click=reset_session)


def reset_session():
    """Reset session state to allow a fresh start."""
    keys_to_clear = (
        "answers",
        "current_question",
        "step",
        "submission_status",
        "client_id",
        "prefecture",
        "industry",
        "industry_choice",
        "industry_custom",
        "prefecture_select",
    )
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    slider_keys = [key for key in st.session_state.keys() if key.startswith("slider_")]
    for slider_key in slider_keys:
        del st.session_state[slider_key]

    st.rerun()


def inject_print_styles():
    """Inject CSS for print-friendly results page."""
    st.markdown(
        """
        <style>
        /* 印刷時にStreamlitのヘッダー・フッター・ナビゲーションを非表示 */
        @media print {
            header, footer, .stApp > header, [data-testid="stHeader"],
            [data-testid="stToolbar"], [data-testid="stDecoration"],
            [data-testid="stStatusWidget"], .stDeployButton {
                display: none !important;
            }

            /* 印刷時に余白を最適化 */
            .main .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
                max-width: 100% !important;
            }

            /* ページ余白の調整 */
            @page {
                margin: 1cm;
            }
        }

        /* 結果ページの余白を整理 */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    inject_print_styles()

    st.title(PAGE_TITLE)
    st.caption("AI Ready 度合いを10問のスライダーで診断し、導入度と想定削減率を把握できます。")

    questions = load_questions()
    ensure_session_defaults(questions)

    step = st.session_state.step
    if step == "industry":
        render_industry_step()
    elif step == "questions":
        render_question_step(questions)
    elif step == "ready":
        render_ready_step(questions)
    elif step == "results":
        render_results_step(questions)
    elif step == "completed":
        render_completion_step()
    else:
        st.session_state.step = "questions"
        st.rerun()


if __name__ == "__main__":
    main()
