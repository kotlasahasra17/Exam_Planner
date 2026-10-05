import streamlit as st
import ollama
from datetime import date

st.set_page_config(page_title="AI Exam Planner", page_icon="📚", layout="wide")

st.title("📚 AI Exam Planner")
st.write("Your personal AI assistant for smart exam preparation.")

# Session state
if "subjects" not in st.session_state:
    st.session_state.subjects = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "schedule" not in st.session_state:
    st.session_state.schedule = ""

# Sidebar
with st.sidebar:
    st.header("⚙️ Planner Settings")

    st.subheader("Add Your Subjects")

    with st.form("subject_form", clear_on_submit=True):
        subject = st.text_input("Subject Name")
        exam_date = st.date_input("Exam Date", min_value=date.today())
        topics = st.text_area("Topics (one per line)")
        priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"]
        )
        submitted = st.form_submit_button("Add Subject")

        if submitted:
            if subject.strip():
                st.session_state.subjects.append({
                    "subject": subject.strip(),
                    "date": exam_date,
                    "topics": topics.strip(),
                    "priority": priority
                })
                st.success(f"{subject} added successfully!")
            else:
                st.warning("Please enter a subject name.")

    st.divider()

    study_hours = st.slider(
        "Daily Study Hours",
        min_value=1,
        max_value=12,
        value=4
    )

    personality = st.selectbox(
        "AI Assistant Style",
        ["Friendly", "Professor", "Motivational"]
    )

    if st.button("Clear All Subjects"):
        st.session_state.subjects = []
        st.session_state.schedule = ""
        st.session_state.messages = []
        st.rerun()

# Display subjects
st.header("📖 My Exams")

if st.session_state.subjects:
    for i, item in enumerate(st.session_state.subjects):
        with st.expander(
            f"{item['subject']} - {item['date'].strftime('%d %b %Y')}"
        ):
            st.write("**Topics:**")
            st.write(item["topics"] if item["topics"] else "Not specified")
            st.write(f"**Priority:** {item['priority']}")

            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.subjects.pop(i)
                st.rerun()
else:
    st.info("Add your subjects and exam dates using the sidebar.")

# Generate study plan
st.divider()
st.header("🗓️ Generate Study Timetable")

if st.button("✨ Create My Study Plan", disabled=not st.session_state.subjects):
    today = date.today()

    exam_details = ""
    for item in st.session_state.subjects:
        days_left = (item["date"] - today).days
        exam_details += f"""
        Subject: {item['subject']}
        Exam Date: {item['date']}
        Days Remaining: {days_left}
        Topics: {item['topics'] or 'Not specified'}
        Priority: {item['priority']}
        """

    prompt = f"""
    You are an intelligent AI exam planner.

    Create a day-wise study timetable from today until the last exam.

    Today's date: {today}
    Daily study hours: {study_hours}

    Exam details:
    {exam_details}

    Rules:
    1. Include multiple upcoming subjects on regular
    preparation days, based on priority and exam dates.
    2. Give more time to high-priority and nearer exams.
    3. Focus only on the next day's exam on the day
    before the exam.
    4. On exam days, exclude the completed exam subject
    and prepare only for the next upcoming exam.
    5. Never include subjects whose exams are over.
    6. Divide study hours into topic-wise sessions,
    revision, practice, and short breaks.
    7. Present a clear table with date, subject,
    topics, and study duration.

    Output only the timetable. No extra advice or tips.
    """

    with st.spinner("Creating your personalized study plan..."):
        try:
            response = ollama.chat(
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI exam planner."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            st.session_state.schedule = response["message"]["content"]

        except Exception as e:
            st.error(f"Error connecting to Ollama: {e}")

if st.session_state.schedule:
    st.subheader("📅 Your Personalized Timetable")
    st.markdown(st.session_state.schedule)

# AI Chatbot
st.divider()
st.header("🤖 AI Study Assistant")
st.write("Ask questions about your exams, subjects, or study schedule.")

personalities = {
    "Friendly": "Explain things in a simple, friendly way.",
    "Professor": "Explain topics like a knowledgeable college professor.",
    "Motivational": "Be a supportive and motivating study coach."
}

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Ask your AI study assistant...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    subject_context = "\n".join(
        [
            f"{item['subject']}: Exam on {item['date']}, "
            f"Topics: {item['topics']}"
            for item in st.session_state.subjects
        ]
    )

    system_prompt = f"""
    You are an AI exam planning assistant.
    {personalities[personality]}

    Student's subjects and exam dates:
    {subject_context or 'No subjects added yet.'}

    Current study plan:
    {st.session_state.schedule or 'No study plan generated yet.'}

    Help the student with exam preparation, time management,
    revision strategies, and study-related questions.
    Keep answers clear and useful.
    """

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = ollama.chat(
                    model="llama3.2:3b",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        }
                    ] + st.session_state.messages
                )

                answer = response["message"]["content"]
                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                st.error(f"Error: {e}")
