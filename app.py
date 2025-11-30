import streamlit as st
import datetime
import time
from db import create_tables, get_questions_by_date, save_questions, save_user_answer
from questions import generate_questions, parse_questions

# Initialize DB tables
create_tables()

# App title
st.title("2^two")
st.write("Solve 2 Aptitude + 2 Verbal Questions Daily!")

# Today's date
today = datetime.date.today().isoformat()

# Fetch today's questions from DB
questions_db = get_questions_by_date(today)

# If no questions, generate them
if not questions_db:
    with st.spinner("Generating Today's Questions..."):
        raw = generate_questions()
        questions = parse_questions(raw)
        save_questions(today, questions)
        st.success("Ready to Fire!")
else:
    # Convert DB rows into dicts
    questions = []
    for row in questions_db:
        questions.append({
            "id": row[0],
            "question": row[2],
            "options": {
                "A": row[3],
                "B": row[4],
                "C": row[5],
                "D": row[6]
            },
            "answer": row[7],
            "explanation": row[8]
        })

# Initialize session state
if 'q_index' not in st.session_state:
    st.session_state.q_index = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'time_left' not in st.session_state:
    st.session_state.time_left = 5 * 60  # 5 minutes per question
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = True

q_index = st.session_state.q_index
total_questions = len(questions)
current_q = questions[q_index]

# Display current question
st.subheader(f"Question {q_index + 1} of {total_questions}")
st.write(current_q["question"])

# Options
user_choice = st.radio("Choose:", ["A", "B", "C", "D"])

# Progress bar
progress = st.progress(q_index / total_questions)

# Timer display
timer_placeholder = st.empty()

# Function to count down
def countdown():
    if st.session_state.timer_running and st.session_state.time_left > 0:
        mins, secs = divmod(st.session_state.time_left, 60)
        timer_placeholder.info(f"Time left: {mins:02d}:{secs:02d}")
        st.session_state.time_left -= 1
        time.sleep(1)
        st.experimental_rerun()
    elif st.session_state.time_left <= 0:
        timer_placeholder.warning("Time's up!")
        st.session_state.timer_running = False

countdown()

# Submit button
if st.button("Submit Answer"):
    st.session_state.timer_running = False
    correct = current_q["answer"]
    
    if user_choice == correct:
        st.success("Correct! ")
    else:
        st.error(f"Wrong! Correct answer: {correct}")
    
    st.write("💡 Explanation:")
    st.write(current_q["explanation"])

    # Save user answer to DB
    save_user_answer(current_q["id"], user_choice, user_choice == correct)

    # Save in session
    st.session_state.answers.append({
        "id": current_q["id"],
        "choice": user_choice,
        "correct": user_choice == correct
    })

    # Reset timer for next question
    st.session_state.time_left = 5 * 60
    st.session_state.timer_running = True

    # Move to next question
    if q_index + 1 < total_questions:
        st.session_state.q_index += 1
        st.experimental_rerun()
    else:
        progress.progress(1.0)
        st.balloons()
        st.success("Today's Batch Completed, See You Tomorrow! ✅")
        st.write("Your Score:")
        for ans in st.session_state.answers:
            q = next(q for q in questions if q["id"] == ans["id"])
            st.write(f"- **{q['question']}** | Your answer: {ans['choice']} | Correct: {q['answer']}")
