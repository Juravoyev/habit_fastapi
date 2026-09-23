# ⚡ Habit Tracker & Personal Growth Web App (FastAPI)

![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-Templates-B41717?style=for-the-badge)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-SQLite-D71F00?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

A full-featured habit tracking web application built with **FastAPI**, **SQLAlchemy**, and **Jinja2 Templates** to track good and bad habits, monitor streaks, log daily moods, and keep a personal journal.

---

## 🌟 Key Features

- **✨ Dual Habit Tracking**: Monitor positive habits (daily check-ins) and quit negative habits (clean streak counter).
- **📖 Daily Mood Journal (`JournalEntry`)**: Log thoughts and track mood scores (1–5 scale).
- **🔥 Streak Analytics**: Automated daily streak calculations and motivational quotes.
- **🎨 Interactive Web Dashboard**: Built-in HTML templates powered by Jinja2 rendering.

---

## ⚙️ How to Run

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/Juravoyev/habit_fastapi.git
   cd habit_fastapi
   
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Launch Server:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Open Dashboard:**
   Visit `http://127.0.0.1:8000/` in your web browser.

---

## 👨‍💻 Author

**Shams Juravoyev**  
- Telegram: [@Juravoyev](https://t.me/Juravoyev)  
- LinkedIn: [Shams Juravoyev](https://www.linkedin.com/in/shams-juravoyev-3017473ab/)  
- GitHub: [@Juravoyev](https://github.com/Juravoyev)  
