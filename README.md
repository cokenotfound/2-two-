# 2^two: Daily CSE Aptitude & Technical Quizzer

**2^two** is a daily quiz application built with Streamlit that provides **4 fresh, structured questions**—2 Aptitude and 2 Core Technical—tailored for CSE interview preparation. Questions and concise explanations are generated reliably using the **OpenRouter API** with the **Deepseek MoE** model.

## Application:
[**2^two Live Quiz**](https://2powtwo.streamlit.app/) 

---

## Key Technologies:

| Technology | Role |
| :--- | :--- |
| **Streamlit** | Frontend, User Interface, and Session Management. |
| **OpenRouter API** | Reliable content generation engine using the free **`tngtech/deepseek-r1t2-chimera:free`** model. |
| **SQLite DB** | Local persistence for saving daily questions and tracking user answers. |

## What's Next?

Our current question pool relies on direct, live API generation, which can suffer from latency. To ensure faster load times and 100% data reliability, our next goal is to implement a hybrid data sourcing strategy:

### 1. **Transition to Curated Local Sources**

We will stop generating the base questions live and shift to reliable, structured local files:

* **Aptitude Questions:** Sourced from specific, trusted textbooks and saved in a file (`aptitude_textbook_questions.csv`) to guarantee consistency and topic coverage (Sequences & Series, Probability, etc.).
* **Technical Questions:** Sourced from Previous Year Questions (PYQs) and stored in a separate file (`technical_pyq_questions.csv`) to maximize interview relevance.

### 2. **Maintain LLM for High-Value Tasks**

The Language Model will remain a core intelligence component, focusing on the task it excels at:

* **Custom Explanations:** The OpenRouter API will be used exclusively to generate the detailed, **50-100 word explanations** for the questions loaded from the CSV files, providing unique, high-quality learning content without compromising app reliability.
* **Dynamic Quiz Pool:** The app will randomly select 2 Aptitude and 2 Technical questions daily from the local CSV pools, ensuring a varied and challenging experience.




