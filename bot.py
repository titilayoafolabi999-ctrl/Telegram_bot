
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- Configuration --- #
TELEGRAM_BOT_TOKEN = ""
GEMINI_API_KEY = ""

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot powered by Google Gemini. Send me a message and I'll try to respond."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the command /help is issued."""
    await update.message.reply_text("Send me any message, and I will use the Gemini API to generate a response!")

async def gemini_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echoes the user message using the Gemini API."""
    user_message = update.message.text
    logger.info(f"User {update.effective_user.first_name} ({update.effective_user.id}) said: {user_message}")

    try:
        # Generate content using Gemini API
        response = model.generate_content(user_message)
        gemini_text = response.text
        await update.message.reply_text(gemini_text)
        logger.info(f"Gemini responded: {gemini_text}")
    except Exception as e:
        logger.error(f"Error generating response from Gemini: {e}")
        await update.message.reply_text("Sorry, I couldn't get a response from Gemini. Please try again later.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # On different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # On non-command messages - echo the message using Gemini
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gemini_response))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started. Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
