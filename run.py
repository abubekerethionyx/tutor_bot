import sys
import subprocess

def run_api():
    print("Starting FastAPI server...")
    subprocess.run([sys.executable, "-m", "uvicorn", "api.main:app", "--reload"])

def run_bot():
    print("Starting Telegram Bot...")
    subprocess.run([sys.executable, "-m", "bot.handler"])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py [api|bot]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "api":
        run_api()
    elif cmd == "bot":
        run_bot()
    else:
        print(f"Unknown command: {cmd}")
