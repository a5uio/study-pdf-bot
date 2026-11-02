# 📚 Study PDF Bot | مساعد المذاكرة

An AI study assistant: upload a university course PDF, get a structured summary, and take an auto-graded multiple-choice quiz with as many questions as you want.

مساعد مذاكرة بالذكاء الاصطناعي: ترفع ملف PDF لمادة جامعية، يطلع لك ملخص مرتب، ويسوي لك اختبار اختيار من متعدد بعدد الأسئلة اللي تحدده ويصححه ويعطيك درجتك.

---

## ✨ Features | المميزات

| English | العربية |
|---|---|
| Summary of the whole PDF with key ideas, definitions and formulas | ملخص للملف كامل فيه الأفكار الرئيسية والتعاريف والقوانين |
| Quiz generator: choose the number of questions (1–50) and difficulty | مولّد اختبارات: تختار عدد الأسئلة (1–50) ومستوى الصعوبة |
| Automatic grading with score, percentage and explanation for each answer | تصحيح تلقائي مع الدرجة والنسبة وتوضيح لكل سؤال |
| Arabic and English interface | واجهة بالعربي والإنجليزي |
| Download the summary as Markdown | تحميل الملخص كملف Markdown |

## 🧠 How it works | طريقة العمل

1. The PDF is sent directly to **Claude** (`claude-opus-5-5`) as a document block, so text, tables and diagrams are all read.
2. **Summary**: streamed response, shown live as it is written.
3. **Quiz**: generated with **structured outputs** (JSON Schema), so every question always has choices, a correct answer index and an explanation.
4. **Prompt caching** on the PDF block makes the second request (quiz after summary) faster and cheaper.

## 🚀 Run it | التشغيل

```bash
git clone https://github.com/a5uio/study-pdf-bot.git
cd study-pdf-bot
pip install -r requirements.txt
streamlit run app.py
```

Then put your Anthropic API key in the sidebar (or set the `ANTHROPIC_API_KEY` environment variable). Get a key from [console.anthropic.com](https://console.anthropic.com).

بعدها حط مفتاح Anthropic API في الشريط الجانبي (أو في متغير البيئة `ANTHROPIC_API_KEY`).

## 🗂️ Project structure | هيكل المشروع

```
study-pdf-bot/
├── app.py            # Streamlit app: summary + quiz + grading
├── requirements.txt
└── README.md
```

## 🛠️ Tech stack

Python · Streamlit · Anthropic Claude API (PDF input, streaming, structured outputs, prompt caching)

## 📌 Ideas for next versions | أفكار للتطوير

- Save quiz history and track progress over time | حفظ نتائج الاختبارات ومتابعة التقدم
- Flashcards mode | وضع البطاقات التعليمية
- Multiple PDFs per course | أكثر من ملف للمادة الواحدة
