import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
try:
    ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))
except ValueError:
    ALLOWED_CHAT_ID = 0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or "YOUR_" in BOT_TOKEN or ALLOWED_CHAT_ID == 0:
    logger.error("BOT_TOKEN or ALLOWED_CHAT_ID is missing or still a placeholder in your .env file! Edit .env and restart.")
    sys.exit(1)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Security middleware / filter
def is_authorized(message: types.Message) -> bool:
    if message.chat.id != ALLOWED_CHAT_ID:
        logger.warning(f"Unauthorized access attempt from chat_id: {message.chat.id}")
        return False
    return True

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_authorized(message):
        return
    await message.answer(
        "🛡️ **Gmail Backup Bot Online**\n\n"
        "Commands:\n"
        "/backup <account> - Run incremental backup\n"
        "/status - Check backup service status\n\n"
        "⚠️ Ensure GYB is properly authenticated before running backups."
    )

@dp.message(Command("backup"))
async def cmd_backup(message: types.Message):
    if not is_authorized(message):
        return
    # Extract account from command args
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /backup user@example.com")
        return
    
    account = args[1]
    await message.answer(f"⏳ Starting background backup for `{account}`...")
    
    # Run the backup runner script in the background
    try:
        # Get the directory of the current script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        runner_path = os.path.join(base_dir, "backup_runner.py")
        
        # We use the same python executable that is running the bot (from venv)
        process = await asyncio.create_subprocess_shell(
            f"{sys.executable} {runner_path} {account}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # We don't wait for it to finish here to avoid blocking the bot.
        # The runner script will notify the bot upon completion.
    except Exception as e:
        logger.error(f"Failed to start backup: {e}")
        await message.answer(f"❌ Error starting backup: {str(e)}")

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if not is_authorized(message):
        return
    # Check systemd service status
    try:
        process = await asyncio.create_subprocess_shell(
            "systemctl status telegram-gmail-bot.service --no-pager | head -n 10",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if stdout:
            await message.answer(f"📊 **Service Status:**\n```\n{stdout.decode()}\n```", parse_mode="Markdown")
        else:
            await message.answer("⚠️ Could not retrieve systemd status. Are you running via systemd?")
    except Exception as e:
        await message.answer(f"❌ Error retrieving status: {e}")

async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
