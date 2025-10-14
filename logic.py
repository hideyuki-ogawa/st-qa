"""Core calculation helpers for the AI Ready Streamlit app."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

READY_PHASES: Tuple[Tuple[int, int, str, str], ...] = (
    (0, 39, "🌱", "準備"),
    (40, 69, "🔧", "試行"),
    (70, 100, "🚀", "拡張"),
)

ADOPTION_PHASES: Tuple[Tuple[int, int, str], ...] = (
    (0, 39, "未導入"),
    (40, 69, "一部導入"),
    (70, 100, "定着"),
)

MATRIX_HINTS: Dict[Tuple[str, str], str] = {
    ("準備", "未導入"): "基盤整備を進めつつ、小規模な試行から取り組みましょう。",
    ("準備", "一部導入"): "成功事例を共有し、本格導入へ向けた体制を整えましょう。",
    ("準備", "定着"): "ガバナンス（セキュリティやルール）整備で安心して活用できる環境を整えましょう。",
    ("試行", "未導入"): "日報・報告など取り組みやすい業務からAI導入を始めましょう。",
    ("試行", "一部導入"): "テンプレート整備と効果測定で導入範囲を広げましょう。",
    ("試行", "定着"): "運用の標準化と定期研修で活用レベルを底上げしましょう。",
    ("拡張", "未導入"): "高効果が期待できる部門に一気に導入を進めましょう。",
    ("拡張", "一部導入"): "全社最適化とROI管理で成果の最大化を図りましょう。",
    ("拡張", "定着"): "自動化や高度応用に踏み出し、新たな価値創出につなげましょう。",
}


def _ensure_ten_answers(answers: Iterable[int]) -> Tuple[int, ...]:
    values = tuple(answers)
    if len(values) != 10:
        raise ValueError("10 件の回答が必要です。")
    if any(value is None for value in values):
        raise ValueError("すべての設問に回答してください。")
    return values


def calc_ready(answers: Dict[str, int]) -> int:
    """Average the 10 slider answers and round to the nearest integer."""
    ordered_keys = sorted(
        answers.keys(),
        key=lambda name: int("".join(ch for ch in name if ch.isdigit()) or 0),
    )
    values = _ensure_ten_answers(answers[key] for key in ordered_keys)
    return round(sum(values) / len(values))


def calc_reduction(ready: int, adoption: int) -> float:
    """Apply the MVP reduction formula (Section 5 of the spec)."""
    readiness = ready / 100
    adoption_ratio = adoption / 100
    return ((1 - adoption_ratio) * readiness * 0.9 + adoption_ratio * readiness * 0.3) * 100


def phase_label(ready: int) -> str:
    """Return 🌱 / 🔧 / 🚀 based on the ready score."""
    for min_val, max_val, emoji, _ in READY_PHASES:
        if min_val <= ready <= max_val:
            return emoji
    return "❓"


def phase_name(ready: int) -> str:
    """Return the textual phase name (準備 / 試行 / 拡張)."""
    for min_val, max_val, _, name in READY_PHASES:
        if min_val <= ready <= max_val:
            return name
    return "未分類"


def adoption_stage(adoption: int) -> str:
    """Return 未導入 / 一部導入 / 定着 based on adoption score."""
    for min_val, max_val, label in ADOPTION_PHASES:
        if min_val <= adoption <= max_val:
            return label
    return "未分類"


def matrix_hint(ready: int, adoption: int) -> str:
    """Return the 9-matrix recommendation string."""
    phase = phase_name(ready)
    stage = adoption_stage(adoption)
    return MATRIX_HINTS.get((phase, stage), "現在の状況に合わせた取り組みを検討しましょう。")
