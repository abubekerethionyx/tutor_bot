import sys
import subprocess
import os
import multiprocessing
import time

def run_api():
    print("Starting FastAPI server...")
    # Render provides a PORT environment variable
    port = os.getenv("PORT", "8000")
    # In production, we don't want --reload. Use it only if local.
    is_prod = os.getenv("RENDER") is not None
    cmd = [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", port]
    if not is_prod:
        cmd.append("--reload")
    
    subprocess.run(cmd)

def run_bot():
    print("Starting Telegram Bot...")
    subprocess.run([sys.executable, "-m", "bot.handler"])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to running both if no argument provided
        cmd = "both"
    else:
        cmd = sys.argv[1]

    if cmd == "api":
        run_api()
    elif cmd == "bot":
        run_bot()
    elif cmd == "both":
        print("Starting both API and Bot...")
        api_process = multiprocessing.Process(target=run_api)
        bot_process = multiprocessing.Process(target=run_bot)

        api_process.start()
        time.sleep(2)
        bot_process.start()

        try:
            while True:
                time.sleep(1)
                if not api_process.is_alive():
                    print("API process died. Shutting down...")
                    bot_process.terminate()
                    sys.exit(1)
                if not bot_process.is_alive():
                    print("Bot process died. Shutting down...")
                    api_process.terminate()
                    sys.exit(1)
        except KeyboardInterrupt:
            print("Stopping services...")
            api_process.terminate()
            bot_process.terminate()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python run.py [api|bot|both]")
        sys.exit(1)
