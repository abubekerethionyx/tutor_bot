# Tutormula 🎓

Tutormula is a modern Telegram-based tutoring management platform designed to connect students, tutors, and parents seamlessly. It simplifies lesson scheduling, progress reporting, and tutor discovery through an intuitive bot interface.

## 🚀 Features

- **Tutor Discovery**: Students can search for tutors by subject and enroll directly.
- **Session Management**: Both tutors and students can create and manage study sessions.
- **Progress Reporting**: Tutors can file detailed performance reports for sessions.
- **Role-Based Access**: Specialized interfaces for Students, Tutors, and Parents.
- **API Access**: A complete FastAPI backend for data management and external integration.

## 🛠️ Tech Stack

- **Bot**: [Aiogram 3.x](https://docs.aiogram.dev/) (Asynchronous Telegram Bot API)
- **API**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) with SQLite
- **Environment**: Python 3.11+

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/tutormula.git
   cd tutormula
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/scripts/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   - Copy `.env.example` to `.env`
   - Fill in your `TELEGRAM_BOT_TOKEN` from [@BotFather](https://t.me/BotFather)

5. **Initialize Database**:
   ```bash
   python init_db.py
   ```

## 🏃 Running the Project

You can run the bot and the API separately using the provided runner:

- **Run Bot**:
  ```bash
  python run.py bot
  ```

- **Run API**:
  ```bash
  python run.py api
  ```

## 📁 Project Structure

- `bot/`: Telegram bot logic, handlers, and keyboards.
- `api/`: FastAPI routes and schemas.
- `services/`: Business logic and database interactions.
- `database/`: Models and database configuration.
- `run.py`: Entry point for running different components.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
