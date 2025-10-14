# Agents.md — 「AI Ready チェック（Streamlit Cloud + Google Sheets）」仕様書

## 0. ミッション / コンセプト

* **目的**：ニュースレター2号（3ページQR）から遷移し、**会社全体の雰囲気**として回答する10本スライダーで「AI Ready指数（0–100）」を算出。Q4（導入度）と組み合わせて**想定作業時間削減率**を即時提示し、**回答データをGoogleスプレッドシートに記録**する。
* **ゴール**：

  1. 3分で自己理解（指数・フェーズ）
  2. 1クリックで効果推定（%）
  3. データ蓄積による「地域AI導入マップ」基盤づくり
* **非ゴール**：個社コンサル機能、PDF自動生成、メール送信、ログイン。MVPではやらない。

---

## 1. 成果物 / KPI

* **成果物**：Streamlit アプリ（1リポジトリ / `app.py`）＋ Google Sheets 接続。
* **KPI（MVP）**

  * 回答完了率 ≥ 70%
  * 所要時間中央値 ≤ 3分
  * データ欠損率（各設問） ≤ 5%
  * スプレッドシート書き込み失敗率 ≤ 1%

---

## 2. ユーザーストーリー

* 事業者A：QRからアクセス→**一問ずつ**スライダーで回答→指数と効果%を即確認→送信→完了。
* 長目チーム：スプレッドシートで集計→業種別傾向をニュースレター・講座に反映。

---

## 3. UX要件（重要）

* **一問ずつ出るUI**（ウィザード型）：

  * 進行：`次へ / 戻る`、プログレスバー（10/10）。
  * スライダー：0–100（0=ほぼ無/未、100=十分）。
  * 質問文は**「あなたの会社では…」**で統一（会社全体の雰囲気）。
  * Q4の回答を**導入度**として結果に反映。
* **結果画面**（即時）：

  * AI Ready指数（0–100）＋区分（🌱0–39 / 🔧40–69 / 🚀70–100）
  * 導入度（Q4%）
  * **想定作業時間削減率**（式は§5）
  * 9マトリクスに基づく**短文提案**（1〜2行）
  * 「回答を送信」ボタン（送信前に編集可能）
* **完了画面**：

  * 「ご協力ありがとうございました」＋データ活用ポリシーの短文
  * （任意）長目サイト/セミナーへの静的リンク

---

## 4. 質問仕様（10スライダー, 全て重み=1）

> すべて 0〜100（0=全く/ほぼ無い、100=十分/常に）
> ※「あなたの会社**では**（会社全体の雰囲気として）」に統一

1. 📄 **業務文書の電子化割合**
2. 💻 **IT環境（社内の情報共有・検索・アクセス）整備度**
3. 🤖 **生成AIアプリ（ChatGPT/Gemini/Copilot等）を使ったことがある人の割合**
4. 💼 **生成AIを実務に取り入れている部署・チームの割合（＝導入度）** ← *Q4*
5. 🧑‍💼 **経営層のAI/IT導入への支援の強さ**
6. ⚡ **“やってみよう”で試行が進む雰囲気（意思決定の速さ）**
7. 📚 **AI/ITの勉強会・共有会の実施頻度**
8. 💬 **社員同士でAIの使い方を共有・相談できる雰囲気**
9. 📊 **意思決定にデータを使う頻度**
10. 🚀 **業務改善・商品開発でAIを使おうとする動きの活発さ**

**スコア計算**

* `AI_READY = round(平均(10問))`（0〜100）
* 区分：🌱0–39 / 🔧40–69 / 🚀70–100
* `AI_ADOPTION = Q4`（0〜100）

---

## 5. 効果シミュレーション（MVPモデル）

**想定作業時間削減率（%）**

```
R = AI_READY / 100
A = AI_ADOPTION / 100
想定削減率 = ((1 - A) * R * 0.9 + A * R * 0.3) * 100
```

* 直感：未導入分は大きく（0.9）、導入済み分も最適化余地（0.3）を残す。
* 例：Ready=0.68, Adoption=0.45 → 0.55*0.68*0.9 + 0.45*0.68*0.3 ≒ **36%**
* （任意）「月間削減時間」= 削減率 × 想定対象時間（例：月200h）

**9マトリクスの短文提案**（Ready×Adoption：3×3）

* 準備×未導入：**基盤整備→小規模試行**
* 準備×一部：**成功事例の共有→法人プランへ**
* 準備×定着：**ガバナンス整備（セキュリティ/ルール）**
* 試行×未導入：**日報/報告から導入**
* 試行×一部：**テンプレ整備と効果測定**
* 試行×定着：**標準化と定期研修**
* 拡張×未導入：**高効果部門に一気に導入**
* 拡張×一部：**全社最適化とROI管理**
* 拡張×定着：**自動化/高度応用へ**

---

## 6. データモデル（Google Sheets）

**スプレッドシート**：`AI_Ready_Responses`
**シート**：`responses`（1行=1回答）

| 列名            | 型       | 説明                       |
| ------------- | ------- | ------------------------ |
| timestamp     | ISO8601 | 送信時刻（アプリ側でUTC or JST統一）  |
| q1..q10       | int     | 0–100                    |
| ready_score   | int     | 0–100（平均）                |
| adoption_q4   | int     | 0–100                    |
| reduction_pct | float   | 想定削減率（%）小数1桁             |
| client_id     | str     | UUID（Cookie無しでセッション起点生成） |
| user_agent    | str     | 任意（簡易UA）                 |
| referrer      | str     | 任意（QR/直/サイト）             |
| notes         | str     | 予備                       |

> 将来：別シートに業種・従業員規模などの任意入力を追加可能。

---

## 7. アーキテクチャ / 実装指針

* **フロント**：Streamlit（1ファイル or 小分割）。
* **状態管理**：`st.session_state`（`step`, `answers{q1..q10}`）。
* **ウィザード**：1問/画面、`次へ/戻る`、`st.progress`。
* **計算**：ローカルで即時計算→結果表示。
* **送信**：押下時にGoogle Sheets `append_row`。
* **リトライ**：Sheets書き込み失敗時は3回指数バックオフ。
* **ログ**：失敗時のみ簡易ログ（コンソール）。PIIは記録しない。
* **アクセシビリティ**：ラベル明確化、キーボード操作、最小フォント14px相当。

---

## 8. セキュリティ / Secrets / 権限

* **Google Service Account**（Sheets API）を使用。

  * JSON鍵を**Streamlit Cloud の Secrets**に保存（例：`GOOGLE_SHEETS_CREDS`）。
  * 対象スプレッドシートに**サービスアカウントのメール**を編集者共有。
* **PII最小化**：会社名やメールは**MVPでは収集しない**。匿名データのみ。
* **依存**：`gspread`, `oauth2client`（または`google-auth`系）。

---

## 9. 環境 / デプロイ

**リポジトリ構成**

```
.
├─ app.py
├─ requirements.txt
└─ README.md
```

**requirements.txt（MVP）**

```
streamlit==1.38.*
gspread==6.*
oauth2client==4.1.3
pandas>=2.2
python-dateutil>=2.9
```

**Secrets（Streamlit Cloud 側）**

* `GOOGLE_SHEETS_CREDS`：サービスアカウントJSON文字列
* `SHEET_NAME`：`AI_Ready_Responses`
* `WORKSHEET_NAME`：`responses`
* `TZ`：`Asia/Tokyo`（任意）

**デプロイ手順**

1. GitHubにPush
2. Streamlit Cloudでリポジトリを選択→デプロイ
3. Secrets投入＆再デプロイ
4. アプリURLをQR化→ニュースレター2号3ページに差し込み

---

## 10. TDD / 受け入れ基準

**ユニット観点（関数化してテスト）**

* `calc_ready(answers: dict) -> int`

  * 10個の0–100を受け、平均を四捨五入して0–100を返す
* `calc_reduction(ready:int, adoption:int) -> float`

  * §5の式通り、0–100を返す
* `phase_label(ready:int) -> str`

  * 🌱/🔧/🚀 を返す
* `matrix_hint(ready:int, adoption:int) -> str`

  * 9パターンの1行提案

**E2E観点**

* 10問回答→結果→送信→**Sheetsに1行追加**される
* 書き込み失敗時にユーザーへ**再試行メッセージ**が出る
* ブラウザリロードでも**回答が消えない**（`session_state`保持/直前保存）

**受け入れ基準**

* 全設問が未回答のまま送信不能
* 10問回答後、指数と削減率が**即表示**
* 送信後の完了画面に**データ活用ポリシー**短文が出る
* Sheetsに**必須列**（timestamp, q1..q10, ready_score, adoption_q4, reduction_pct, client_id）が欠損なく入る

---

## 11. コピー（そのまま使える文言）

* **冒頭**：「あなたの会社のAI Ready指数を3分でチェック。会社全体の雰囲気をイメージしてお答えください。」
* **注記**：「個人情報は収集しません。回答は匿名で統計的に利用します。」
* **結果見出し**：「AI Ready指数：{score}点（{phase}）／現在のAI導入度：{q4}%」
* **効果**：「想定作業時間削減率：{pct}%」
* **送信ボタン**：「この結果を送信・集計に協力する」
* **完了**：「ご協力ありがとうございました。結果は統計的に集計し、長目通信などでご報告します。」

---

## 12. 開発メモ（実装ヒント）

* **一問ずつUI**：

  * `st.session_state.step` を0..9で管理
  * `st.slider(key=f"q{n}")`で永続
  * `st.progress((step+1)/10)`
  * 次へ→`step+=1`、戻る→`step-=1`
* **Sheets接続**：

  * `gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(...))`
  * `sheet.append_row([...], value_input_option="USER_ENTERED")`
* **耐障害**：

  * 書き込み関数に`for i in range(3)`＋`time.sleep(1*i)`
  * 失敗詳細は`st.error("送信に失敗しました。しばらくして再度お試しください。")`

---

## 13. 将来拡張（ロードマップ）

* **v1.1**：会社名・業種・規模（任意）フォーム、Supabase併用
* **v1.2**：結果PDF/メール送付、イベント申込フォーム連携
* **v1.3**：業種別ベンチマークの自動提示、ダッシュボード公開（Looker Studio）
* **v2.0**：Next.js + Cloud Run + Supabase へ移行、常時起動/権限管理

---

## 14. ライセンス / データ方針（短文）

* 回答データは匿名で収集し、**統計的に集計・公表**します。
* 個別回答の内容を外部に公開・特定することはありません。
* 利用規約・プライバシーポリシーは長目サイトの規約に準じます。

---

### 付録：最小骨格コード（抜粋・擬似）

```python
# app.py（骨格のみ）
import streamlit as st, json, gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone, timedelta
import uuid

st.set_page_config(page_title="AI Ready チェック", page_icon="🤖", layout="centered")

# --- state ---
if "step" not in st.session_state: st.session_state.step = 0
for i in range(1,11):
    st.session_state.setdefault(f"q{i}", None)
st.session_state.setdefault("client_id", str(uuid.uuid4()))

# --- UI: question wizard ---
QUESTIONS = [
 "業務文書の電子化割合は？",
 "IT環境（共有・検索・アクセス）の整備度は？",
 "生成AIアプリを使ったことがある人の割合は？",
 "生成AIを実務に取り入れている部署の割合は？",  # Q4=導入度
 "経営層の支援の強さは？",
 "“やってみよう”で試行が進む雰囲気は？",
 "AI/ITの勉強会・共有会の頻度は？",
 "AIの使い方を共有・相談できる雰囲気は？",
 "意思決定にデータを使う頻度は？",
 "改善・開発でAIを使おうとする動きは？"
]

def q_slider(i):
    return st.slider(QUESTIONS[i], 0, 100, 50, key=f"q{i+1}")

step = st.session_state.step
st.progress((step+1)/10)
q_slider(step)

cols = st.columns(2)
if cols[0].button("戻る", disabled=step==0): st.session_state.step -= 1
if cols[1].button("次へ", disabled=step==9): st.session_state.step += 1

# --- results ---
if all(st.session_state[f"q{i}"] is not None for i in range(1,11)):
    vals = [st.session_state[f"q{i}"] for i in range(1,11)]
    ready = round(sum(vals)/len(vals))
    q4 = st.session_state["q4"] if "q4" in st.session_state else st.session_state["q4"]  # alias
    q4 = st.session_state["q4"] if "q4" in st.session_state else vals[3]
    R, A = ready/100, q4/100
    reduction = ((1-A)*R*0.9 + A*R*0.3)*100
    st.subheader(f"AI Ready指数：{ready} 点")
    st.write(f"現在のAI導入度：{q4} %")
    st.metric("想定作業時間削減率", f"{reduction:.0f}%")

    # --- send ---
    if st.button("この結果を送信・集計に協力する"):
        # Sheets write
        creds = json.loads(st.secrets["GOOGLE_SHEETS_CREDS"])
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds, scope))
        sh = gc.open(st.secrets["SHEET_NAME"]).worksheet(st.secrets["WORKSHEET_NAME"])
        ts = datetime.now(timezone(timedelta(hours=9))).isoformat()
        row = [ts, *vals, ready, q4, round(reduction,1), st.session_state["client_id"], st.experimental_user["user_agent"] if "experimental_user" in dir(st) else "", st.experimental_get_query_params().get("ref", [""])[0], ""]
        sh.append_row(row, value_input_option="USER_ENTERED")
        st.success("送信しました。ご協力ありがとうございます。")
```

## 問題

/data/quiz.md を参照

---

この仕様のまま実装すれば、**今日から動く“一問ずつUIの診断＋効果推定＋Sheets保存”**が完成します。次はリポジトリを切って、Secrets（サービスアカウント）を発行して投入すれば即デプロイ可能です。

