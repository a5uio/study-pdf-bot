"""
Study PDF Bot — مساعد المذاكرة
Upload a university course PDF, get a summary, and take an auto-graded quiz.
"""

import base64
import json
import os

import anthropic
import streamlit as st

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "choices": {"type": "array", "items": {"type": "string"}},
                    "answer_index": {"type": "integer"},
                    "explanation": {"type": "string"},
                },
                "required": ["question", "choices", "answer_index", "explanation"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

TEXT = {
    "العربية": {
        "title": "📚 مساعد المذاكرة",
        "subtitle": "ارفع ملف PDF لمادتك، وخذ ملخص واختبار يتصحح تلقائياً.",
        "key": "مفتاح Anthropic API",
        "upload": "ارفع ملف المادة (PDF)",
        "tab_sum": "📝 الملخص",
        "tab_quiz": "✅ الاختبار",
        "sum_btn": "لخّص المادة",
        "sum_wait": "جاري التلخيص...",
        "n_q": "عدد الأسئلة",
        "level": "مستوى الصعوبة",
        "levels": ["سهل", "متوسط", "صعب"],
        "quiz_btn": "سوّ الاختبار",
        "quiz_wait": "جاري تجهيز الأسئلة...",
        "submit": "سلّم الإجابات",
        "score": "درجتك",
        "correct": "✔️ صح",
        "wrong": "❌ غلط — الإجابة الصحيحة:",
        "why": "التوضيح",
        "need_key": "حط مفتاح API في الشريط الجانبي أول.",
        "need_pdf": "ارفع ملف PDF أول.",
        "refused": "النموذج رفض هذا الطلب. جرّب ملف ثاني.",
        "lang_name": "Arabic",
    },
    "English": {
        "title": "📚 Study PDF Bot",
        "subtitle": "Upload your course PDF, get a summary and an auto-graded quiz.",
        "key": "Anthropic API key",
        "upload": "Upload course file (PDF)",
        "tab_sum": "📝 Summary",
        "tab_quiz": "✅ Quiz",
        "sum_btn": "Summarize",
        "sum_wait": "Summarizing...",
        "n_q": "Number of questions",
        "level": "Difficulty",
        "levels": ["Easy", "Medium", "Hard"],
        "quiz_btn": "Generate quiz",
        "quiz_wait": "Preparing questions...",
        "submit": "Submit answers",
        "score": "Your score",
        "correct": "✔️ Correct",
        "wrong": "❌ Wrong — correct answer:",
        "why": "Explanation",
        "need_key": "Enter your API key in the sidebar first.",
        "need_pdf": "Upload a PDF first.",
        "refused": "The model declined this request. Try another file.",
        "lang_name": "English",
    },
}


def pdf_block(pdf_bytes: bytes) -> dict:
    # cache_control lets the summary and quiz calls reuse the same uploaded PDF
    return {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": base64.standard_b64encode(pdf_bytes).decode(),
        },
        "cache_control": {"type": "ephemeral"},
    }


def stream_summary(client: anthropic.Anthropic, pdf_bytes: bytes, lang: str):
    prompt = (
        f"You are a study assistant for a university student. Write the summary in {lang}. "
        "Summarize this course material so the student can review it before an exam: "
        "start with a short overview, then one section per main topic with the key ideas, "
        "definitions and formulas, and end with a list of the most important points to remember. "
        "Use Markdown headings and bullet points."
    )
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        messages=[{"role": "user", "content": [pdf_block(pdf_bytes), {"type": "text", "text": prompt}]}],
    ) as stream:
        for text in stream.text_stream:
            yield text
        final = stream.get_final_message()
    if final.stop_reason == "refusal":
        raise RuntimeError("refusal")


def make_quiz(client: anthropic.Anthropic, pdf_bytes: bytes, n: int, level: str, lang: str) -> list[dict]:
    prompt = (
        f"Write exactly {n} multiple-choice questions in {lang} about this course material, "
        f"difficulty: {level}. Each question has exactly 4 choices and one correct answer "
        "(answer_index is 0-3). Cover different topics across the material, and give a short "
        "explanation of the correct answer."
    )
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        output_config={"format": {"type": "json_schema", "schema": QUIZ_SCHEMA}},
        messages=[{"role": "user", "content": [pdf_block(pdf_bytes), {"type": "text", "text": prompt}]}],
    ) as stream:
        final = stream.get_final_message()
    if final.stop_reason == "refusal":
        raise RuntimeError("refusal")
    text = next(b.text for b in final.content if b.type == "text")
    questions = json.loads(text)["questions"]
    return [q for q in questions if len(q["choices"]) >= 2 and 0 <= q["answer_index"] < len(q["choices"])]


def main():
    st.set_page_config(page_title="Study PDF Bot", page_icon="📚", layout="centered")

    lang_choice = st.sidebar.radio("اللغة / Language", list(TEXT), horizontal=True)
    t = TEXT[lang_choice]
    if lang_choice == "العربية":
        st.markdown("<style>.stApp, .stMarkdown {direction: rtl; text-align: right;}</style>", unsafe_allow_html=True)

    api_key = st.sidebar.text_input(t["key"], value=os.environ.get("ANTHROPIC_API_KEY", ""), type="password")

    st.title(t["title"])
    st.caption(t["subtitle"])

    uploaded = st.file_uploader(t["upload"], type=["pdf"])
    if uploaded is None:
        st.info(t["need_pdf"])
        return
    if not api_key:
        st.warning(t["need_key"])
        return

    pdf_bytes = uploaded.getvalue()
    # Reset saved results when a different file is uploaded
    if st.session_state.get("file_id") != uploaded.file_id:
        st.session_state.update(file_id=uploaded.file_id, summary=None, quiz=None, graded=False)

    client = anthropic.Anthropic(api_key=api_key)
    tab_sum, tab_quiz = st.tabs([t["tab_sum"], t["tab_quiz"]])

    with tab_sum:
        if st.button(t["sum_btn"], type="primary"):
            try:
                with st.spinner(t["sum_wait"]):
                    st.session_state.summary = st.write_stream(stream_summary(client, pdf_bytes, t["lang_name"]))
            except RuntimeError:
                st.error(t["refused"])
            except anthropic.APIError as e:
                st.error(str(e))
        elif st.session_state.summary:
            st.markdown(st.session_state.summary)
        if st.session_state.summary:
            st.download_button("⬇️ summary.md", st.session_state.summary, file_name="summary.md")

    with tab_quiz:
        col1, col2 = st.columns(2)
        n = col1.number_input(t["n_q"], min_value=1, max_value=50, value=10)
        level = col2.selectbox(t["level"], t["levels"], index=1)
        if st.button(t["quiz_btn"], type="primary"):
            try:
                with st.spinner(t["quiz_wait"]):
                    st.session_state.quiz = make_quiz(client, pdf_bytes, int(n), level, t["lang_name"])
                    st.session_state.graded = False
            except RuntimeError:
                st.error(t["refused"])
            except anthropic.APIError as e:
                st.error(str(e))

        quiz = st.session_state.quiz
        if quiz:
            with st.form("quiz_form"):
                answers = []
                for i, q in enumerate(quiz):
                    st.markdown(f"**{i + 1}. {q['question']}**")
                    answers.append(
                        st.radio(
                            f"q{i}", range(len(q["choices"])), index=None,
                            format_func=lambda c, q=q: q["choices"][c],
                            key=f"ans_{i}", label_visibility="collapsed",
                        )
                    )
                if st.form_submit_button(t["submit"], type="primary"):
                    st.session_state.graded = True

            if st.session_state.graded:
                right = sum(a == q["answer_index"] for a, q in zip(answers, quiz))
                pct = round(100 * right / len(quiz))
                st.metric(t["score"], f"{right} / {len(quiz)}", f"{pct}%")
                st.progress(pct / 100)
                if pct >= 90:
                    st.balloons()
                for i, (a, q) in enumerate(zip(answers, quiz)):
                    if a == q["answer_index"]:
                        st.success(f"{i + 1}. {t['correct']}")
                    else:
                        st.error(f"{i + 1}. {t['wrong']} {q['choices'][q['answer_index']]}")
                    st.caption(f"{t['why']}: {q['explanation']}")


if __name__ == "__main__":
    main()
