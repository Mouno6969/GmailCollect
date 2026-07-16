# Telegram Gmail Backup Bot

A secure, production-ready Telegram bot for a Linux VPS (Ubuntu/Debian) that triggers and monitors Gmail backups using **GYB (Got Your Back)** over the Gmail API with OAuth.

## Architecture

```text
[ Telegram App ]
      │  (Commands: /backup, /status)
      ▼
[ VPS: systemd Service ]
      │
      ├─► [ aiogram Bot (main.py) ] ─(Validates Chat ID)─┐
      │                                           (Subprocess)
      │                                                  ▼
      │                                   [ backup_runner.py ]
[ VPS: cron ] ─(Nightly Incremental)─────────────────────┤
                                                         ▼
                                          [ GYB → Gmail API (OAuth) ]
                                                         │
                                                         ▼
                              [ /home/<user>/gmail_backups/<email>/ ]
```

## Features

- `/backup <email>` — trigger an incremental backup for any configured account
- `/status` — check the bot's systemd service status
- Telegram notifications on backup success/failure
- Chat-ID restriction: only YOUR chat can control the bot
- Non-blocking: backups run as background subprocesses
- Nightly incremental backups via cron (optional)
- OAuth-only authentication (no passwords stored)

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Mouno6969/GmailCollect.git gmail-backup-bot
cd gmail-backup-bot
bash deploy/install.sh
```

### 2. Configure secrets

```bash
nano .env
```

Set your **new** bot token (revoke any token that was ever shared in plain text via @BotFather → `/revoke`) and your chat ID (from @userinfobot). Then verify permissions:

```bash
chmod 600 .env
```

### 3. Install and authenticate GYB

```bash
bash <(curl -s -S -L https://gyb-shortn.jaylee.us/gyb-install)
```

The installer walks you through creating a Google Cloud project. On a **headless VPS**, authenticate with one of these methods:

**Method A — Local Auth & Copy (recommended):**
1. Install GYB on your local machine and run `gyb --email you@gmail.com --action estimate`.
2. Complete the OAuth flow in your local browser.
3. Copy the generated credentials to the VPS: `scp ~/bin/gyb/*.json ~/bin/gyb/*.cfg user@vps:/path/to/gyb/`
4. `chmod 600` all copied files.

**Method B — No-browser flow:**
1. On the VPS run `gyb --email you@gmail.com --action estimate --no-browser`.
2. Open the printed URL in your local browser, authenticate, and paste the code back.

Update `GYB_PATH` in `.env` to match your GYB install location.

### 4. Initial full backup (do this manually first!)

> ⚠️ **Warning:** The initial backup of a large mailbox can take hours or days and consume many GB of disk. Check free space with `df -h` first.

```bash
tmux new -s initial_backup
/opt/gyb/gyb --email you@gmail.com --action backup --folder ~/gmail_backups/you@gmail.com
# Detach with Ctrl+B, then D
```

### 5. Start the bot

```bash
sudo systemctl start telegram-gmail-bot
sudo systemctl status telegram-gmail-bot
```

Send `/start` to your bot on Telegram. You should get the command menu.

### 6. Optional: nightly incremental backups

```bash
crontab -e
# Paste the line from deploy/cron_snippet.txt, adjusting the email address
```

## Adding More Gmail Accounts

1. Run the GYB OAuth flow for the new address (Method A or B above).
2. That's it — use `/backup new@email.com` or add a new cron line.

## Selective Backups (Gmail Search Syntax)

Edit the `cmd` list in `backup_runner.py` to add `--search`:

| Goal | Flag |
|------|------|
| Only last 7 days (fast daily runs) | `--search "newer_than:7d"` |
| Only important mail | `--search "is:important"` |
| Skip huge attachments | `--search "smaller:10M"` |
| Specific label | `--search "label:invoices"` |

## Security Checklist

- [ ] `.env` and all GYB `*.json` / `*.cfg` files are `chmod 600`
- [ ] `ALLOWED_CHAT_ID` is set (bot ignores everyone else)
- [ ] Bot runs as a normal user, never root
- [ ] Backup directory is `chmod 700` and outside any web root
- [ ] Old/leaked bot tokens have been revoked via @BotFather

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Backup fails with auth error | OAuth token expired/revoked — redo the auth flow |
| GYB not found | Check `GYB_PATH` in `.env` matches actual install location |
| Bot doesn't respond | `sudo journalctl -u telegram-gmail-bot -f` to see logs |
| Disk full | `df -h`; prune old backups or use `--search` filters |
| Rate limits on huge mailboxes | GYB auto-pauses and resumes; just let it run in tmux |
| Backup very slow daily | Ensure `--fast-incremental` is used (it is, by default here) |

## Project Layout

```
gmail-backup-bot/
├── main.py                 # aiogram Telegram bot
├── backup_runner.py        # GYB wrapper + Telegram notifications
├── requirements.txt
├── .env.example            # copy to .env and fill in
├── .gitignore              # keeps secrets out of git
└── deploy/
    ├── install.sh          # one-shot automated installer
    ├── telegram-gmail-bot.service   # systemd unit
    └── cron_snippet.txt    # nightly backup cron line
```
