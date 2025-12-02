import streamlit as st
import datetime
import json
from db import create_tables, get_questions_by_date, save_questions, save_user_answer
# REMOVED: from questions import get_questions (Imported locally below to break the circular dependency)

# -------------------------
# Initialize DB
# -------------------------
create_tables()

st.markdown("<h1>2<sup>Two</sup></h1>", unsafe_allow_html=True)
st.write("Solve 2 Aptitude + 2 Technical Questions Daily!")

# -------------------------
# Today's date
# -------------------------
today = datetime.date.today().isoformat()

# -------------------------
# Utility function to convert DB row to app dictionary format
# -------------------------
def format_db_row(row):
    """Converts a SQLite row tuple into the app's dictionary format."""
    # Columns: id, category, sub_category, question, options (JSON), correct_option, explanation
    return {
        "id": row[0],
        "type": row[1],
        "sub_category": row[2],
        "question": row[3],
        "options": json.loads(row[4]),  # Deserialize the JSON string back to a dict
        "answer": row[5],              # Mapped from correct_option
        "explanation": row[6]
    }

# -------------------------
# Data Validation Utility
# -------------------------
def validate_questions_for_save(questions_list):
    """Checks if mandatory fields required by the new DB schema are present."""
    valid_questions = []
    required_keys = ["type", "sub_category", "question", "options", "answer", "explanation"]
    
    for q in questions_list:
        if all(key in q for key in required_keys):
            valid_questions.append(q)
        else:
            print(f"Skipping malformed question due to missing keys: {q.keys()}")
            
    return valid_questions

# -------------------------
# Regenerate Questions Button (Forces new API call)
# -------------------------
if st.button("Regenerate Questions"):
    from questions import get_questions # <-- Local import breaks the loop
    new_questions = get_questions() 
    
    # Validation before saving
    validated_questions = validate_questions_for_save(new_questions)
    
    if not validated_questions or len(validated_questions) == 0:
        st.error("Failed to generate or validate new questions. Check console/fallback structure.")
    else:
        save_questions(today, validated_questions, overwrite=True) 
        st.session_state.questions_cached = validated_questions
        st.success("Questions regenerated and saved!")

    st.session_state.q_index = 0
    st.session_state.answers = []
    st.session_state.submitted = False
    st.session_state.user_choice = None
    st.rerun() 


# -------------------------
# Load questions 
# -------------------------
questions = []

if 'questions_cached' not in st.session_state:
    questions_db = get_questions_by_date(today)
    if not questions_db:
        with st.spinner("Generating Fresh Questions via OpenRouter API..."):
            from questions import get_questions # <-- Local import breaks the loop
            questions = get_questions()
            
            # Validation before saving 
            validated_questions = validate_questions_for_save(questions)
            
            if not validated_questions or len(validated_questions) == 0:
                st.warning("Failed to generate and validate questions. Check console for structure errors. Cannot start quiz.")
                st.stop()
            
            questions = validated_questions
            save_questions(today, questions, overwrite=True)
            st.session_state.questions_cached = questions
            st.success("Fresh Questions are Ready!")
    else:
        # Load and deserialize questions from DB
        questions = [format_db_row(row) for row in questions_db]
        st.session_state.questions_cached = questions

else:
    questions = st.session_state.questions_cached

total_questions = len(questions)

# -------------------------
# Session State (Unchanged)
# -------------------------
if 'q_index' not in st.session_state:
    st.session_state.q_index = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'user_choice' not in st.session_state:
    st.session_state.user_choice = None

# -------------------------
# Quiz Complete (Unchanged)
# -------------------------
if st.session_state.q_index >= total_questions:
    st.balloons()
    st.success("🎉 Quiz Completed! 🎉")
    st.write(f"Your Score: {sum(ans['correct'] for ans in st.session_state.answers)}/{total_questions}")
    st.write("Summary:")
    for ans in st.session_state.answers:
        q = next(q for q in questions if q["id"] == ans["id"])
        st.write(f"**Q{q['id']}: {q['question']}**")
        st.write(f"Your answer: {ans['choice']} | Correct: {q['answer']}")
        st.write(f"Explanation: {q['explanation']}")
    st.stop()

# -------------------------
# Current Question (Displaying Category)
# -------------------------
current_q = questions[st.session_state.q_index]

# Displaying the category and sub-category
st.markdown(f"**Category:** *{current_q['type'].title()}* | **Topic:** *{current_q['sub_category'].title()}*")
st.write(f"**Q{st.session_state.q_index + 1}: {current_q['question']}**")

# -------------------------
# Single Progress Bar (Unchanged)
# -------------------------
answered_questions = st.session_state.q_index
if st.session_state.submitted:
    answered_questions += 1
st.progress(answered_questions / total_questions)

# -------------------------
# Display Options or Explanation (FIXED FOR FEEDBACK)
# -------------------------
if not st.session_state.submitted:
    # Show options
    user_choice_local = st.radio(
        "Choose an option:",
        [f"{key}: {val}" for key, val in current_q["options"].items()],
        key=f"radio_{st.session_state.q_index}"
    )

    if st.button("Submit Answer"):
        if not user_choice_local:
            st.warning("Please select an option before submitting!")
        else:
            choice_key = user_choice_local.split(":")[0]
            correct = current_q["answer"]
            is_correct = choice_key == correct

            # Save answer
            save_user_answer(current_q["id"], choice_key, is_correct)
            st.session_state.answers.append({
                "id": current_q["id"],
                "choice": choice_key,
                "correct": is_correct
            })

            st.session_state.user_choice = choice_key
            st.session_state.submitted = True
            st.rerun() 

else:
    # --- START: FEEDBACK LOGIC ---
    last_answer_correct = st.session_state.answers[-1]['correct']
    correct_option_text = f"{current_q['answer']}: {current_q['options'][current_q['answer']]}"

    if last_answer_correct:
        st.success("✅ Correct! Well done.")
    else:
        st.error(f"❌ Incorrect. The correct answer is {current_q['answer']}.")
    
    st.write(f"**Correct Option:** {correct_option_text}")
    # --- END: FEEDBACK LOGIC ---
    
    # Show explanation and Next button
    st.write("Explanation:", current_q["explanation"])

    if st.button("Next Question"):
        st.session_state.q_index += 1
        st.session_state.submitted = False
        st.session_state.user_choice = None
        st.rerun()
