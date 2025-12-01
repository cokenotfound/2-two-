import sqlite3
from sqlite3 import Error
import json
from typing import List, Dict, Any

DB_NAME = "2two.db"

# -------------------------
# Create DB connection
# -------------------------
def get_connection():
    """Establishes a connection to the SQLite database file."""
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        return conn
    except Error as e:
        print("Error connecting to DB:", e)
        return None

# -------------------------
# Create tables
# -------------------------
def create_tables():
    """Creates the necessary tables if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Questions table: Redesigned structure with JSON options and categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,        -- 'aptitude' or 'technical'
        sub_category TEXT,    -- e.g., 'Probability', 'Algorithms'
        question TEXT,
        options TEXT,         -- JSON string: {"A": "Option A text", "B": "Option B text"}
        correct_option TEXT,  -- e.g., 'A', 'B', 'C', 'D'
        explanation TEXT
    )
    """)
    
    # User answers table: Stores user's history and results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        choice TEXT,
        correct INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(question_id) REFERENCES questions(id)
    )
    """)
    
    conn.commit()
    conn.close()

# -------------------------
# Save questions
# -------------------------
def save_questions(date: str, questions: List[Dict[str, Any]], overwrite: bool = False):
    """Saves a list of questions to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    if overwrite:
        # Delete old questions for the current date to ensure fresh content
        cursor.execute("DELETE FROM questions WHERE date=?", (date,))
    
    for q in questions:
        # Serialize the options dictionary into a JSON string before saving
        options_json = json.dumps(q["options"])
        
        cursor.execute("""
        INSERT INTO questions 
        (date, category, sub_category, question, options, correct_option, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            date,
            q["type"],             # Mapped from 'type' in LLM output
            q["sub_category"],
            q["question"],
            options_json,
            q["answer"],           # Mapped from 'answer' in LLM output
            q["explanation"]
        ))
    conn.commit()
    conn.close()


# -------------------------
# Fetch questions by date
# -------------------------
def get_questions_by_date(date: str) -> List[tuple]:
    """Fetches all question data for a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    # Select all columns in the new schema order
    cursor.execute("SELECT id, category, sub_category, question, options, correct_option, explanation FROM questions WHERE date=?", (date,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# -------------------------
# Save user answer
# -------------------------
def save_user_answer(question_id: int, choice: str, correct: bool):
    """Saves the user's choice and correctness status for a question."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_answers (question_id, choice, correct)
    VALUES (?, ?, ?)
    """, (question_id, choice, int(correct)))
    conn.commit()
    conn.close()
