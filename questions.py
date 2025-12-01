import os
import json
import random
from dotenv import load_dotenv
import uuid
import requests
from typing import List, Dict, Any

# -------------------------
# Model and API Info
# -------------------------
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using the stable, free Deepseek MoE model for strong JSON output
OPENROUTER_MODEL = "tngtech/deepseek-r1t2-chimera:free" 

# Global variable to cache the API key after loading
_OPENROUTER_API_KEY = None 

# -------------------------
# API Key Helper (Breaks Circular Import)
# -------------------------
def get_api_key():
    """Loads the API key and caches it."""
    global _OPENROUTER_API_KEY
    if _OPENROUTER_API_KEY is None:
        load_dotenv()
        _OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    return _OPENROUTER_API_KEY

# -------------------------
# Prompt for MCQs (UPDATED: Explanation length changed to 50-100 words)
# -------------------------
PROMPT = """
Generate exactly 4 multiple-choice questions for CSE technical interview level:

- 2 aptitude questions: Focused on **Quantitative Ability and Logical Reasoning** from the following topics: Sequences & Series, Permutations & Combinations, Probability, Geometry, Mensuration, Statistics, Blood Relations, Directions, Clocks & Calendars, Cubes, Coding & Decoding, Cryptarithmetic, and Non Verbal Reasoning.
- 2 technical questions: Focused on **Core Computer Science** concepts such as Data Structures, Algorithms, Operating Systems, and Database Management Systems.

Requirements:

1. Each question must have exactly 4 options (A, B, C, D).
2. The correct answer must be randomly placed among the options; do not always put it at A.
3. Provide one correct answer only.
4. Provide a detailed explanation for why the correct answer is correct, **between 50 and 100 words**.
5. **Include a 'sub_category' field** identifying the specific topic (e.g., 'Probability', 'Operating Systems').
6. Format the output strictly as a JSON list like this:

[
  {
    "type": "aptitude or technical",
    "sub_category": "Topic Name Here",
    "question": "question text",
    "options": {
      "A": "option text",
      "B": "option text",
      "C": "option text",
      "D": "option text"
    },
    "answer": "A/B/C/D",
    "explanation": "Detailed explanation (50-100 WORDS)"
  }
]

Do not include any text outside the JSON. Ensure that the options for each question are shuffled.
"""

# -------------------------
# Generate questions from OpenRouter
# -------------------------
def generate_questions() -> List[Dict[str, Any]] | None:
    OPENROUTER_API_KEY = get_api_key()
    if not OPENROUTER_API_KEY:
        print("InferenceClient not initialized. Check OPENROUTER_API_KEY.")
        return None
    
    unique_prompt = PROMPT + f"\n\n--- Request Seed: {uuid.uuid4()} ---"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost" # Placeholder for local development
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "response_format": {"type": "json_object"}, 
        "messages": [
            {"role": "system", "content": "You are an expert quiz generator. Your response must be a valid JSON array, strictly adhering to the user's required structure."},
            {"role": "user", "content": unique_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000 
    }
    
    text = ""
    try:
        # Increased timeout to 90 seconds to accommodate slow free-tier latency
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=90) 
        response.raise_for_status() 
        data = response.json()
        
        # OpenRouter/OpenAI parsing
        text = data['choices'][0]['message']['content']
        
        # Robust JSON cleanup
        if text.strip().startswith("```json"):
            text = text.strip().strip("```json").strip("```")
            
        json_start = text.find('[')
        json_end = text.rfind(']')
        if json_start == -1 or json_end == -1:
             raise ValueError(f"Could not find valid JSON array boundaries ([...]) in LLM output. Output length: {len(text)}")
        text = text[json_start : json_end + 1]
        
        questions = json.loads(text)
        
        # Shuffle options (Existing logic)
        for q in questions:
            opts = list(q['options'].items())
            random.shuffle(opts)
            shuffled = {k: v for k, v in opts}
            correct_value = q['options'].get(q['answer'], None)
            
            # Find the new key corresponding to the correct value after shuffle
            new_answer_key = next((key for key, val in shuffled.items() if val == correct_value), None)

            if new_answer_key:
                 q['answer'] = new_answer_key
            
            q['options'] = shuffled
            
        return questions
    
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', 'N/A')
        print(f"OpenRouter API Error: HTTP Status {status_code}. Reason: {e}")
        return None
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error parsing model output: {type(e).__name__}. RAW OUTPUT: {text}")
        return None
    except Exception as e:
        print(f"Unexpected generation error: {e}")
        return None

# -------------------------
# Fallback sample questions (UPDATED with new schema fields)
# -------------------------
def generate_sample_questions() -> List[Dict[str, Any]]:
    return [
        {
            "type": "aptitude",
            "sub_category": "Sequences & Series",
            "question": "What is the next number in the sequence: 2, 4, 8, 16, ...",
            "options": {"A": "20", "B": "24", "C": "32", "D": "48"},
            "answer": "C",
            "explanation": "This is a geometric progression where each term is twice the previous term. The rule is 2^n. Since the last term is 16 (2^4), the next term will be 2^5, which equals 32. This type of pattern recognition is fundamental to quantitative aptitude. (75 words)."
        },
        {
            "type": "aptitude",
            "sub_category": "Probability",
            "question": "What is the probability of rolling a 3 on a standard six-sided die?",
            "options": {"A": "1/2", "B": "1/6", "C": "1/3", "D": "1/12"},
            "answer": "B",
            "explanation": "Probability is calculated as (Number of favorable outcomes) / (Total number of possible outcomes). A standard six-sided die has six possible outcomes (1, 2, 3, 4, 5, 6). The favorable outcome is rolling a 3, which is 1 outcome. Therefore, the probability is 1/6. This is a basic example of discrete probability. (80 words)."
        },
        {
            "type": "technical",
            "sub_category": "Data Structures",
            "question": "Which data structure uses LIFO (Last-In, First-Out) ordering?",
            "options": {"A": "Queue", "B": "Stack", "C": "Linked List", "D": "Heap"},
            "answer": "B",
            "explanation": "A stack is an abstract data type that maintains elements in a LIFO order. Think of it like a stack of plates: you only add to the top, and you only remove from the top. Operations include push (add) and pop (remove). This is crucial for managing function calls and variable scoping in computer programs. (70 words)."
        },
        {
            "type": "technical",
            "sub_category": "Operating Systems",
            "question": "What is a deadlock?",
            "options": {"A": "A process waiting for I/O", "B": "Two processes waiting for each other indefinitely", "C": "A process that has finished execution", "D": "A system crash due to low memory"},
            "answer": "B",
            "explanation": "Deadlock is a state in concurrent computing where two or more processes are permanently unable to proceed because each is waiting for a resource that the other process is currently holding. The necessary conditions for deadlock are mutual exclusion, hold and wait, no preemption, and circular wait. This leads to system stagnation. (85 words)."
        }
    ]

# -------------------------
# Parse / normalize questions
# -------------------------
def parse_questions(raw_questions: List[Dict[str, Any]]):
    if not raw_questions:
        return []
    parsed = []
    for idx, q in enumerate(raw_questions):
        parsed.append({
            "id": idx + 1,
            "type": q.get("type", "unknown"),
            "sub_category": q.get("sub_category", "General"), 
            "question": q.get("question", ""),
            "options": q.get("options", {}),
            "answer": q.get("answer", ""),
            "explanation": q.get("explanation", "")
        })
    return parsed

# -------------------------
# Convenience function for app
# -------------------------
def get_questions():
    raw = generate_questions()
    if not raw:
        # If API fails, raw is None, so we get samples
        raw = generate_sample_questions()
    return parse_questions(raw)
