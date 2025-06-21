import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from telegram import Bot
from googleapiclient.errors import HttpError
import base64
from email import message_from_bytes
from google.auth.transport.requests import Request
import asyncio
import re
import unicodedata
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
NEWSLETTER_LABEL = os.getenv('NEWSLETTER_LABEL', 'Newsletters')

# If modifying these SCOPES, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Step 1: Authenticate and build Gmail API service
def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

# Step 2: Fetch emails
def fetch_newsletters(service):
    """
    Fetch ALL emails from Gmail from the previous day that are in the user-specified label (folder/tag).
    Returns a list of dicts: {subject, body, sender, message_id}
    """
    newsletters = []
    try:
        from datetime import datetime, timedelta
        
        # Calculate yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y/%m/%d')
        
        # Search for emails from yesterday with the specified label
        query = f'label:{NEWSLETTER_LABEL} after:{yesterday_str}'
        print(f"DEBUG: Searching for emails with query: {query}")
        
        # Use pagination to get ALL emails
        page_token = None
        total_fetched = 0
        
        while True:
            # Get a page of results
            if page_token:
                results = service.users().messages().list(
                    userId='me', 
                    q=query, 
                    pageToken=page_token,
                    maxResults=100  # Gmail API max per request
                ).execute()
            else:
                results = service.users().messages().list(
                    userId='me', 
                    q=query, 
                    maxResults=100  # Gmail API max per request
                ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                if total_fetched == 0:
                    print(f"DEBUG: No emails found for {yesterday_str}")
                else:
                    print(f"DEBUG: Finished fetching emails. Total: {total_fetched}")
                break
                
            print(f"DEBUG: Fetched {len(messages)} emails (page)")
            total_fetched += len(messages)
            
            # Process each message in this page
            for msg in messages:
                msg_id = msg['id']
                msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                payload = msg_data.get('payload', {})
                headers = payload.get('headers', [])
                
                # Extract subject
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
                
                # Extract sender
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
                
                # Extract date
                date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                
                # Try to get the plain text body
                body = ''
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part.get('mimeType') == 'text/plain':
                            data = part['body'].get('data')
                            if data:
                                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                                break
                else:
                    # Single part message
                    data = payload.get('body', {}).get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                
                # Fallback: if no plain text, try to extract from html
                if not body and 'parts' in payload:
                    for part in payload['parts']:
                        if part.get('mimeType') == 'text/html':
                            data = part['body'].get('data')
                            if data:
                                html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                                # Strip HTML tags (very basic)
                                import re
                                body = re.sub('<[^<]+?>', '', html)
                                break
                
                newsletters.append({
                    'subject': subject, 
                    'body': body, 
                    'sender': sender,
                    'message_id': msg_id,
                    'date': date_header
                })
            
            # Check if there are more pages
            page_token = results.get('nextPageToken')
            if not page_token:
                print(f"DEBUG: No more pages. Total newsletters fetched: {total_fetched}")
                break
                
    except HttpError as error:
        print(f'An error occurred: {error}')
    return newsletters

# Step 3: Summarize content using Cohere API (with HuggingFace fallback)
def summarize_text(text):
    # Preprocess text: clean and limit length
    import re
    import unicodedata
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Remove email headers and common artifacts
    text = re.sub(r'From:.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'To:.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Subject:.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Date:.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Reply-To:.*?\n', '', text, flags=re.IGNORECASE)
    
    # Remove URLs and emails
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
    
    # Remove common newsletter artifacts
    text = re.sub(r'Unsubscribe.*?$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'Click here.*?$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'View in browser.*?$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean special characters more aggressively
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)\'\"]', ' ', text)
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()
    
    # Remove very short sentences (likely artifacts)
    sentences = text.split('.')
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # Only keep sentences longer than 10 characters
            cleaned_sentences.append(sentence)
    text = '. '.join(cleaned_sentences)
    
    # Limit text length
    max_length = 4000  # Cohere can handle longer text
    if len(text) > max_length:
        # Try to cut at a sentence boundary
        sentences = text.split('.')
        truncated_text = ""
        for sentence in sentences:
            if len(truncated_text + sentence) < max_length:
                truncated_text += sentence + "."
            else:
                break
        text = truncated_text.strip()
    
    print(f"DEBUG: Original text length: {len(text)} characters")
    print(f"DEBUG: Cleaned text length: {len(text)} characters")
    
    # Try Cohere first (if API key is available)
    if COHERE_API_KEY:
        try:
            print("DEBUG: Trying Cohere Command R+...")
            cohere_url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {COHERE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""Please provide a concise summary of the following newsletter content. Focus on the key points and main takeaways:

{text}

Summary:"""
            
            payload = {
                "model": "command-r-plus",
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.3,
                "k": 0,
                "stop_sequences": [],
                "return_likelihoods": "NONE"
            }
            
            response = requests.post(cohere_url, headers=headers, json=payload, timeout=30)
            print(f"DEBUG: Cohere - Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'generations' in result and len(result['generations']) > 0:
                    summary = result['generations'][0]['text'].strip()
                    print("DEBUG: Success with Cohere Command R+")
                    return summary
                else:
                    print("DEBUG: Cohere - Unexpected response format")
            else:
                print(f"DEBUG: Cohere - Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"DEBUG: Cohere - Exception: {e}")
    
    # Fallback to HuggingFace models
    print("DEBUG: Falling back to HuggingFace models...")
    models_to_try = [
        ('sshleifer/distilbart-cnn-6-6', text),
        ('t5-small', f"summarize: {text[:1000]}"),
        ('facebook/bart-large-cnn', text[:1000])
    ]
    
    for model_name, model_input in models_to_try:
        try:
            print(f"DEBUG: Trying model: {model_name}")
            api_url = f'https://api-inference.huggingface.co/models/{model_name}'
            headers = {'Authorization': f'Bearer {HUGGINGFACE_API_TOKEN}'} if HUGGINGFACE_API_TOKEN else {}
            payload = {"inputs": model_input}
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            print(f"DEBUG: {model_name} - Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    summary = result[0]['summary_text']
                    print(f"DEBUG: Success with {model_name}")
                    return summary
                else:
                    print(f"DEBUG: {model_name} - Unexpected response format")
            else:
                print(f"DEBUG: {model_name} - Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"DEBUG: {model_name} - Exception: {e}")
            continue
    
    # If all models fail, return None (no summary)
    print("DEBUG: All models failed, returning None")
    return None

# Step 4: Send summary to Telegram
async def send_to_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('Telegram credentials not set.')
        return
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        result = await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Message sent successfully! Message ID: {result.message_id}")
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

if __name__ == '__main__':
    print("Starting newsletter automation...")
    # Authenticate Gmail
    print("Authenticating with Gmail...")
    gmail_service = get_gmail_service()
    print("Gmail authentication successful!")
    
    # Fetch newsletters from yesterday
    print(f"Searching for emails with label: {NEWSLETTER_LABEL}")
    newsletters = fetch_newsletters(gmail_service)
    print(f"Found {len(newsletters)} newsletters from yesterday.")
    
    # Process each newsletter
    async def process_newsletters():
        # Send date header message
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%A, %B %d, %Y')
        day_name = yesterday.strftime('%A')
        
        header_message = f"📅 Daily Newsletter Digest\n📆 {date_str}\n📊 {len(newsletters)} newsletters found"
        
        if len(newsletters) == 0:
            header_message += "\n\nNo newsletters received yesterday."
            await send_to_telegram(header_message)
            print("Sent 'no newsletters' message to Telegram")
            return
        
        await send_to_telegram(header_message)
        print(f"Sent date header to Telegram")
        
        # Track summary success/failure
        successful_summaries = 0
        failed_summaries = 0
        
        for i, newsletter in enumerate(newsletters, 1):
            print(f"\nProcessing newsletter {i}/{len(newsletters)}: {newsletter['subject']}")
            
            # Clean sender name
            sender = newsletter['sender']
            if '<' in sender and '>' in sender:
                # Extract name from "Name <email@domain.com>" format
                sender = sender.split('<')[0].strip()
            
            # Try to get summary
            summary = summarize_text(newsletter['body'])
            
            # Create email link
            email_link = f"https://mail.google.com/mail/u/0/#inbox/{newsletter['message_id']}"
            
            if summary:
                # Send with summary
                message = f"📧 Newsletter {i}/{len(newsletters)}\n\n👤 From: {sender}\n📋 Subject: {newsletter['subject']}\n🔗 [View Email]({email_link})\n\n📝 Summary:\n{summary}"
                successful_summaries += 1
            else:
                # Send without summary (models reached limits or failed)
                message = f"📧 Newsletter {i}/{len(newsletters)}\n\n👤 From: {sender}\n📋 Subject: {newsletter['subject']}\n🔗 [View Email]({email_link})\n\n⚠️ Summary unavailable (model limit reached)"
                failed_summaries += 1
            
            await send_to_telegram(message)
            print(f"Sent newsletter {i}/{len(newsletters)} to Telegram")
        
        # Send summary statistics
        if len(newsletters) > 0:
            stats_message = f"📊 Summary Statistics:\n✅ {successful_summaries} newsletters summarized\n⚠️ {failed_summaries} newsletters without summary\n📧 Total processed: {len(newsletters)}"
            await send_to_telegram(stats_message)
            print(f"Sent summary statistics to Telegram")
    
    # Run the async function
    asyncio.run(process_newsletters()) 