# Auto-Newsletter Summarizer

An automated system that fetches newsletters from Gmail, summarizes them using AI (Cohere Command R+ with HuggingFace fallback), and sends daily digests to Telegram.

## Features

- 📧 **Gmail Integration**: Fetches newsletters from a specific Gmail label
- 🤖 **AI Summarization**: Uses Cohere Command R+ with HuggingFace model fallback
- 📱 **Telegram Delivery**: Sends formatted summaries to your Telegram
- ⏰ **Daily Automation**: Runs automatically every day at 12:01 AM UTC
- 🔄 **Robust Error Handling**: Multiple fallback options for reliability
- 📊 **Statistics**: Provides summary success/failure statistics

## Setup Instructions

### Prerequisites

1. **Gmail API Access**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download `credentials.json`

2. **Telegram Bot**
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Get your bot token
   - Start a chat with your bot and get your chat ID

3. **AI API Keys**
   - **Cohere**: Sign up at [cohere.ai](https://cohere.ai) (free tier available)
   - **HuggingFace**: Sign up at [huggingface.co](https://huggingface.co) (free)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Auto-Newsletter.git
   cd Auto-Newsletter
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   HUGGINGFACE_API_TOKEN=your_huggingface_token
   COHERE_API_KEY=your_cohere_api_key
   NEWSLETTER_LABEL=Newsletters
   ```

4. **Add Gmail credentials**
   - Place your `credentials.json` file in the project root
   - Run the script once to authenticate: `python main.py`
   - This will create `token.json` for future use

5. **Test locally**
   ```bash
   python main.py
   ```

### GitHub Actions Setup (Recommended)

1. **Fork or clone this repository**

2. **Set up GitHub Secrets**
   Go to your repository → Settings → Secrets and variables → Actions
   Add these secrets:
   - `GMAIL_CREDENTIALS`: Content of your `credentials.json` file
   - `GMAIL_TOKEN`: Content of your `token.json` file (after first local run)
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID
   - `HUGGINGFACE_API_TOKEN`: Your HuggingFace API token
   - `COHERE_API_KEY`: Your Cohere API key
   - `NEWSLETTER_LABEL`: Your Gmail label name (default: "Newsletters")

3. **Enable GitHub Actions**
   - Go to Actions tab in your repository
   - The workflow will run automatically daily at 12:01 AM UTC
   - You can also trigger it manually from the Actions tab

## Configuration

### Gmail Label Setup
1. In Gmail, create a label (e.g., "Newsletters")
2. Set up filters to automatically apply this label to newsletter emails
3. Update `NEWSLETTER_LABEL` in your environment variables

### Customization
- **Schedule**: Modify the cron expression in `.github/workflows/daily-newsletter.yml`
- **Models**: Adjust the AI models in `main.py` (summarize_text function)
- **Message Format**: Customize the Telegram message format in `main.py`

## How It Works

1. **Authentication**: Uses Gmail API OAuth 2.0 for secure access
2. **Email Fetching**: Searches for emails from yesterday with the specified label
3. **Content Extraction**: Extracts plain text content from emails
4. **AI Summarization**: 
   - Tries Cohere Command R+ first (better quality)
   - Falls back to HuggingFace models if Cohere fails
   - Handles text preprocessing and length limits
5. **Telegram Delivery**: Sends formatted messages with summaries and links
6. **Error Handling**: Continues processing even if some summaries fail

## Troubleshooting

### Common Issues

1. **Gmail Authentication**
   - Delete `token.json` and run again to re-authenticate
   - Ensure `credentials.json` is in the project root

2. **No Newsletters Found**
   - Check your Gmail label name matches `NEWSLETTER_LABEL`
   - Verify emails are actually in that label
   - Check the date range (yesterday's emails only)

3. **API Rate Limits**
   - The script handles rate limits gracefully
   - Some newsletters may be sent without summaries if limits are reached

4. **GitHub Actions Failures**
   - Check the Actions tab for detailed error logs
   - Verify all secrets are set correctly
   - Ensure the workflow file is in `.github/workflows/`

### Debug Mode
The script includes extensive debug logging. Check the console output for detailed information about each step.

## Security Notes

- API keys are stored as GitHub Secrets (encrypted)
- Gmail credentials are handled securely via OAuth 2.0
- Sensitive files are cleaned up after GitHub Actions runs
- Local `.env` file should never be committed to Git

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE). 