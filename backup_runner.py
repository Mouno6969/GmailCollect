import sys
import subprocess
import os
import requests
import logging
from dotenv import load_dotenv

# Determine the base directory of the script so it works regardless of where it's called from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("ALLOWED_CHAT_ID")
GYB_PATH = os.getenv("GYB_PATH", "/opt/gyb/gyb")
BACKUP_DIR = os.getenv("BACKUP_DIR", os.path.expanduser("~/gmail_backups"))

logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'backup.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_telegram_message(text):
    if not BOT_TOKEN or not ALLOWED_CHAT_ID:
        logging.warning("Telegram credentials not set, skipping notification.")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ALLOWED_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

def run_backup(account):
    logging.info(f"Starting backup for {account}")
    account_dir = os.path.join(BACKUP_DIR, account)
    
    # Ensure backup directory exists
    os.makedirs(account_dir, exist_ok=True)
    
    # Run GYB with fast-incremental mode
    cmd = [
        GYB_PATH,
        "--email", account,
        "--folder", account_dir,
        "--action", "backup",
        "--fast-incremental"
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"Backup successful for {account}")
        
        output_snippet = process.stdout[-200:] if process.stdout else "No output"
        send_telegram_message(f"✅ **Backup Complete**: `{account}`\n\nLog snippet:\n```\n{output_snippet}\n```")
    except subprocess.CalledProcessError as e:
        error_snippet = e.stderr[-200:] if e.stderr else "Unknown error"
        logging.error(f"Backup failed for {account}: {error_snippet}")
        send_telegram_message(f"❌ **Backup Failed**: `{account}`\n\nError:\n```\n{error_snippet}\n```")
    except FileNotFoundError:
        logging.error(f"GYB executable not found at {GYB_PATH}")
        send_telegram_message(f"❌ **Backup Failed**: GYB not found at `{GYB_PATH}`. Check your .env configuration.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 backup_runner.py <account>")
        sys.exit(1)
        
    run_backup(sys.argv[1])
