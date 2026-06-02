from fastapi import FastAPI, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import date, datetime, timedelta
from typing import Optional
import uvicorn

# ── Database setup ──────────────────────────────────────────────────────────
DATABASE_URL = "sqlite:///./habits.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── Models ───────────────────────────────────────────────────────────────────
class Habit(Base):
    __tablename__ = "habits"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    habit_type = Column(String, nullable=False)   # "good" | "bad"
    icon       = Column(String, default="✨")
    created_at = Column(DateTime, default=datetime.utcnow)
    clean_since= Column(Date, nullable=True)       # for bad habits
    logs       = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")


class HabitLog(Base):
    __tablename__ = "habit_logs"
    id          = Column(Integer, primary_key=True, index=True)
    habit_id    = Column(Integer, ForeignKey("habits.id"), nullable=False)
    logged_date = Column(Date, nullable=False)
    done        = Column(Boolean, default=False)
    habit       = relationship("Habit", back_populates="logs")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id         = Column(Integer, primary_key=True, index=True)
    content    = Column(Text, nullable=False)
    mood       = Column(Integer, default=3)        # 1–5
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# ── App & templates ──────────────────────────────────────────────────────────
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ── Quotes ───────────────────────────────────────────────────────────────────
QUOTES = [
    "Har bir yangi kun – yangi imkoniyat. Undan to'g'ri foydalaning.",
    "Muvaffaqiyat – bu har kuni kichik qadamlar tashlash natijasidir.",
    "O'z oldingizga qo'ygan maqsadlaringizdan hech qachon voz kechmang.",
    "Kuchli odam – bu hech qachon qulamaydigan emas, balki har safar turadigan.",
    "Discipline is choosing between what you want now and what you want most.",
    "Small daily improvements are the key to staggering long-term results.",
    "Bugun qilmagan ishingizni ertaga amalga oshirish qiyinroq bo'ladi.",
    "Your habits will determine your future. Choose them wisely.",
    "Har bir daqiqa – bu imkoniyat. Uni behuda o'tkazmang.",
    "Success is the sum of small efforts repeated day in and day out.",
]

# ── DB dependency ─────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Seed defaults ─────────────────────────────────────────────────────────────
def seed_defaults(db: Session):
    if db.query(Habit).count() > 0:
        return
    good_defaults = [
        ("Morning Exercise",        "🏃"),
        ("Reading 20 min",          "📚"),
        ("Drink 8 glasses of water","💧"),
        ("Sleep Schedule",          "🌙"),
    ]
    bad_defaults = [
        ("Pornography-free", "🚫"),
    ]
    for name, icon in good_defaults:
        db.add(Habit(name=name, habit_type="good", icon=icon))
    for name, icon in bad_defaults:
        db.add(Habit(name=name, habit_type="bad", icon=icon, clean_since=date.today()))
    db.commit()

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_streak(habit: Habit, db: Session) -> int:
    """Count consecutive days a good habit was done going back from today."""
    streak = 0
    check_date = date.today()
    while True:
        log = db.query(HabitLog).filter(
            HabitLog.habit_id == habit.id,
            HabitLog.logged_date == check_date,
            HabitLog.done == True,
        ).first()
        if log:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


def get_or_create_log(habit_id: int, log_date: date, db: Session) -> HabitLog:
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.logged_date == log_date,
    ).first()
    if not log:
        log = HabitLog(habit_id=habit_id, logged_date=log_date, done=False)
        db.add(log)
        db.commit()
        db.refresh(log)
    return log


def weekly_data(db: Session):
    """Return list of (weekday_label, completion_pct) for last 7 days."""
    today = date.today()
    good_habits = db.query(Habit).filter(Habit.habit_type == "good").all()
    result = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        label = day.strftime("%a")
        if not good_habits:
            result.append({"label": label, "pct": 0})
            continue
        done_count = db.query(HabitLog).filter(
            HabitLog.habit_id.in_([h.id for h in good_habits]),
            HabitLog.logged_date == day,
            HabitLog.done == True,
        ).count()
        pct = round((done_count / len(good_habits)) * 100)
        result.append({"label": label, "pct": pct})
    return result

# ── Routes ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    quote = QUOTES[today.toordinal() % len(QUOTES)]

    good_habits = db.query(Habit).filter(Habit.habit_type == "good").all()
    bad_habits  = db.query(Habit).filter(Habit.habit_type == "bad").all()

    # Enrich good habits
    good_data = []
    for h in good_habits:
        log = get_or_create_log(h.id, today, db)
        streak = get_streak(h, db)
        good_data.append({"habit": h, "done": log.done, "streak": streak})

    # Enrich bad habits
    bad_data = []
    for h in bad_habits:
        clean_days = (today - h.clean_since).days if h.clean_since else 0
        bad_data.append({"habit": h, "clean_days": clean_days})

    # Daily completion %
    total = len(good_habits)
    done_today = sum(1 for g in good_data if g["done"])
    completion_pct = round((done_today / total) * 100) if total else 0

    # Weekly chart
    week = weekly_data(db)

    # Journal
    journal_entries = (
        db.query(JournalEntry)
        .order_by(JournalEntry.created_at.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "today":           today.strftime("%A, %B %d %Y"),
            "quote":           quote,
            "good_data":       good_data,
            "bad_data":        bad_data,
            "completion_pct":  completion_pct,
            "week":            week,
            "journal_entries": journal_entries,
        }
    )


@app.post("/toggle/{habit_id}")
def toggle_habit(habit_id: int, db: Session = Depends(get_db)):
    log = get_or_create_log(habit_id, date.today(), db)
    log.done = not log.done
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/reset_bad/{habit_id}")
def reset_bad(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if habit:
        habit.clean_since = date.today()
        db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/add_habit")
def add_habit(
    name:       str = Form(...),
    habit_type: str = Form(...),
    icon:       str = Form("✨"),
    db: Session = Depends(get_db),
):
    h = Habit(name=name, habit_type=habit_type, icon=icon)
    if habit_type == "bad":
        h.clean_since = date.today()
    db.add(h)
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/delete_habit/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if habit:
        db.delete(habit)
        db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/journal")
def save_journal(
    content: str = Form(...),
    mood:    int = Form(...),
    db: Session = Depends(get_db),
):
    db.add(JournalEntry(content=content, mood=mood))
    db.commit()
    return RedirectResponse("/", status_code=303)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
