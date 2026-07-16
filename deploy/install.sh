#!/bin/bash
# Automated installer for the Telegram Gmail Backup Bot
# Run this on your Ubuntu/Debian VPS from inside the project directory:
#   bash deploy/install.sh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "📁 Project directory: $PROJECT_DIR"

# 1. System dependencies
echo "📦 Installing system dependencies..."
sudo apt update -qq
sudo apt install -y python3-pip python3-venv tmux curl tar xz-utils

# 2. Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q

# 3. Backup storage directory
echo "🗄️  Creating backup storage directory..."
mkdir -p "$HOME/gmail_backups"
chmod 700 "$HOME/gmail_backups"

# 4. .env setup
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
    echo "⚠️  Created .env from template. EDIT IT NOW with your token and chat ID:"
    echo "    nano $PROJECT_DIR/.env"
else
    chmod 600 "$PROJECT_DIR/.env"
    echo "✅ .env already exists (permissions set to 600)."
fi

# 5. GYB installation
if [ ! -f "/opt/gyb/gyb" ]; then
    echo "📥 Installing GYB (Got Your Back) to ~/bin/gyb..."
    echo "    NOTE: The official installer is interactive. Run it manually:"
    echo "    bash <(curl -s -S -L https://gyb-shortn.jaylee.us/gyb-install)"
    echo "    Then update GYB_PATH in your .env accordingly."
else
    echo "✅ GYB found at /opt/gyb/gyb"
fi

# 6. systemd service
echo "⚙️  Installing systemd service..."
# Patch the service file with the actual user and paths
sed "s|/home/ubuntu/gmail-backup-bot|$PROJECT_DIR|g; s|User=ubuntu|User=$USER|g; s|Group=ubuntu|Group=$USER|g; s|/home/ubuntu/gmail_backups|$HOME/gmail_backups|g" \
    "$PROJECT_DIR/deploy/telegram-gmail-bot.service" | sudo tee /etc/systemd/system/telegram-gmail-bot.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable telegram-gmail-bot.service

echo ""
echo "======================================================"
echo "✅ Installation complete!"
echo ""
echo "NEXT STEPS:"
echo "1. Edit your secrets:        nano $PROJECT_DIR/.env"
echo "2. Authenticate GYB:         see README (headless OAuth)"
echo "3. Run initial backup:       tmux new -s backup, then run GYB manually"
echo "4. Start the bot:            sudo systemctl start telegram-gmail-bot"
echo "5. Check bot status:         sudo systemctl status telegram-gmail-bot"
echo "6. (Optional) Nightly cron:  crontab -e  (see deploy/cron_snippet.txt)"
echo "======================================================"
