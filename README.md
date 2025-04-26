# Car Insurance Telegram Bot

A Telegram bot that guides users through the car insurance application process, from document verification to policy issuance. Built with Python best practices.

<div align="center">
  <video src="assets/demo/demo.mp4" controls></video>
</div>

## Features

- Interactive Telegram bot interface
- Document processing with Mindee AI for passport and vehicle ID extraction
- Multi-agent architecture for specialized handling of different stages
- Persistent conversation history with SQLite database
- Proper error handling and graceful shutdown
- Comprehensive logging with rotation
- Support for media uploads (documents)

## Requirements

- Python 3.8+
- Telegram Bot API token
- OpenAI API key
- Mindee API key and account with custom endpoints
- Custom Mindee endpoints for "passport" and "vehicle_id" document types

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd car-insurance-telegram-bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example.env file to create your .env file:

```bash
cp example.env .env
```

Then edit the .env file and fill in your API keys and configuration options:

```
# Bot configuration
BOT_TOKEN=your_telegram_bot_token_here

# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-4.1-nano-2025-04-14

# Mindee API configuration
MINDEE_API_KEY=your_mindee_api_key_here
MINDEE_ACCOUNT_NAME=your_mindee_account_name_here

# Data directory and database configuration
DATA_DIRECTORY_PATH=./data
DATABASE_FILENAME=db.sqlite

# Application settings
MAX_MESSAGES=64
MEDIA_GROUP_TIMEOUT=2.0

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/bot.log
```

### 5. Run the Bot

```bash
python main.py
```

## Project Structure

The project follows Python best practices with a clear structure:

```
car-insurance-telegram-bot/
├── main.py                # Entry point with signal handling
├── requirements.txt       # Dependencies
├── example.env            # Environment variable template
├── assets/                # Static assets directory
│   ├── demo/              # Demo videos
│   │   └── demo.mp4       # Application demo video
│   └── examples/          # Example documents
│       ├── passport.png   # Sample passport document
│       └── vehicle id.png # Sample vehicle ID document
├── src/
│   ├── __init__.py        # Package metadata
│   ├── bot/               # Telegram bot interface
│   │   ├── __init__.py
│   │   ├── bot.py         # Bot service initialization
│   │   └── handlers.py    # Message handling
│   ├── config/            # Configuration
│   │   ├── __init__.py
│   │   └── settings.py    # Environment variables and constants
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   └── conversation.py # Conversation state
│   ├── services/          # Business logic
│   │   ├── __init__.py
│   │   ├── ai_service.py  # AI agent management
│   │   └── database.py    # Database interactions
│   └── utils/             # Utilities
│       ├── __init__.py
│       └── logging.py     # Logging configuration
```

## Bot Workflow

The bot implements a multi-agent architecture with specialized agents for different stages of the insurance application process:

1. **Hub Agent** - The entry point for user interactions:
   - Greets users and introduces the car insurance service
   - Transfers users to Document Processor Agent when they express interest

2. **Document Processor Agent** - Handles document verification:
   - Requests and processes passport and vehicle identification documents
   - Uses Mindee AI to extract relevant information
   - Presents extracted data to user for verification
   - Transfers to Price Negotiator Agent after successful document verification

3. **Price Negotiator Agent** - Handles pricing and acceptance:
   - Presents fixed insurance price
   - Explains that the price is non-negotiable
   - Transfers to Insurance Policy Agent when user accepts the price

4. **Insurance Policy Agent** - Delivers final insurance policy:
   - Generates an insurance policy document with extracted user and vehicle details
   - Sends the formatted policy to the user via Telegram

The bot maintains conversation state using a SQLite database to ensure continuity across user sessions.

## Example Interaction Flows

### Successful Insurance Application Flow

1. **User Initiates Conversation**
   - User: "/start"
   - Bot: "Hello! I'm your car insurance assistant. Would you like to start the car insurance application process?"
   - User: "Yes, I'd like to get car insurance."

2. **Document Processing**
   - Bot: "Great! Please upload two documents: your passport and your vehicle identification document."
   - User: _uploads passport_
   - Bot: "Thank you for uploading your passport. Now please upload your vehicle identification document."
   - User: _uploads vehicle ID_
   - Bot: "I've processed your documents. Here's the information I extracted:
     - Name: John Smith
     - Date of Birth: 01/15/1985
     - Vehicle Manufacturer: Toyota
     - Vehicle Model: Camry
     - Vehicle Owner: John Smith
       Is this information correct?"
   - User: "Yes, that's correct."

3. **Price Negotiation**
   - Bot: "Based on the information provided, your insurance premium will be 100 USD. Would you like to proceed with this price?"
   - User: "Yes, I accept the price."

4. **Insurance Policy Issuance**
   - Bot: _sends formatted insurance policy document with all details_
   - Bot: "Your insurance policy has been issued. Thank you for choosing our service!"

### Error Handling Flow

1. **Invalid Document Upload**
   - User: _uploads blurry or incorrect document_
   - Bot: "I'm sorry, but I couldn't extract the required information from your document. Please ensure the document is clear and try uploading it again."

2. **Price Negotiation Rejection**
   - Bot: "Based on the information provided, your insurance premium will be 100 USD. Would you like to proceed with this price?"
   - User: "That's too expensive. Can you offer a lower price?"
   - Bot: "I apologize, but our prices are fixed and non-negotiable. The price for your insurance is 100 USD. Would you like to proceed?"

3. **Process Restart**
   - User: "I want to start over."
   - Bot: "I understand. Let's start the process again. Would you like to begin the car insurance application?"

## Technical Details

- **Framework**: Built with aiogram 3.x (Telegram Bot API framework for Python)
- **Document Processing**: Uses Mindee for document data extraction
- **AI Integration**: Leverages OpenAI GPT models
- **Database**: SQLite with WAL journaling mode for conversation persistence
- **Logging**: Rotating file logs with configurable levels
- **Error Handling**: Comprehensive error handling and graceful shutdown
- **Architecture**: Multi-agent system with specialized agents for different parts of the workflow

## Customization

- **Custom Document Types**: The system is currently configured for passport and vehicle ID documents. To add more document types, extend the `get_data` function in `ai_service.py`.
- **Pricing Logic**: The current pricing is fixed at 100 USD. For dynamic pricing, modify the `get_insurance_price` function in `ai_service.py`.
- **Policy Template**: The insurance policy template can be customized in the `send_insurance_policy` function in `ai_service.py`.
- **Agent Configuration**: The agent model and instructions can be modified in the `AIService` class.