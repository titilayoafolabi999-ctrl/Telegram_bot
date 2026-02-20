# Gemini Telegram Bot

This is a Python Telegram bot that uses the Google Gemini API as its AI backend.

## Setup

1.  **Clone the repository (or create the files manually):**

    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**

    Replace the placeholder values for `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY` in `bot.py` with your actual credentials:

    ```python
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
    ```

    *   **Telegram Bot Token:** Obtain this from BotFather on Telegram.
    *   **Gemini API Key:** Obtain this from the Google AI Studio.

## Running the Bot

To start the bot, run the `bot.py` file:

```bash
python bot.py
```

The bot will start polling for updates. You can then interact with it on Telegram.

## Usage

-   Send `/start` to the bot to receive a welcome message.
-   Send `/help` to get information on how to use the bot.
-   Send any other text message, and the bot will use the Gemini API to generate a response.
