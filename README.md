# Auto Newsletter Bot

This project fetches newsletters from Gmail from the previous day, summarizes them using AI models, and sends daily digests to your Telegram.

## Features
- Fetches newsletters from Gmail from the previous day
- Summarizes content using Cohere Command R+ (with HuggingFace fallback)
- Sends daily digest summaries to Telegram
- Includes date headers and newsletter counts
- Handles multiple newsletters per day

## Setup

### 1. Gmail API Setup
- Follow the [Gmail API setup guide](https://developers.google.com/gmail/api/quickstart/python)
- Download `credentials.json` and place it in the project root

### 2. Telegram Bot Setup
- Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
- Get your bot token and chat ID

### 3. Environment Variables
Create a `.env` file in the project root with the following:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
HUGGINGFACE_API_TOKEN=your_huggingface_api_token
COHERE_API_KEY=your_cohere_api_key
NEWSLETTER_LABEL=Newsletters
```

**Note:** 
- `COHERE_API_KEY` is optional but recommended for better summaries
- `HUGGINGFACE_API_TOKEN` is used as fallback if Cohere fails
- `NEWSLETTER_LABEL` should match your Gmail label/folder name

### 4. Install Dependencies
```
pip install -r requirements.txt
```

### 5. Run the Bot
```
python main.py
```

## How It Works
- The script runs daily and fetches all newsletters from the previous day
- It sends a date header message with the count of newsletters found
- Each newsletter is summarized and sent as a separate message
- If summarization fails (model limits reached), newsletters are sent without summaries
- A final statistics message shows how many were successfully summarized
- If no newsletters are found, it sends a "no newsletters" message
- The script uses Cohere Command R+ for high-quality summaries with HuggingFace models as fallback

## Notes
- The first time you run, you may need to authenticate with Google and save the token file
- The script will fetch ALL newsletters from your specified Gmail label from the previous day
- Summaries will be sent to your Telegram bot with links to the original emails
- No limit on the number of newsletters processed per day

## Scheduling (Optional)
To run daily at 12:01 AM, you can use:
- **Windows Task Scheduler**
- **Cron jobs** (Linux/Mac)
- **Any automation tool** of your choice 