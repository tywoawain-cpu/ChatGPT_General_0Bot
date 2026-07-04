import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Conversation states
SELECTING_ACTION, TYPING_PROMPT, TYPING_STYLE = range(3)

# Store user data
user_data = {}

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when /start is issued."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🎵 Generate Song", callback_data="generate_song")],
        [InlineKeyboardButton("🎶 Generate Instrumental", callback_data="generate_instrumental")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm a music generator bot.\n\n"
        f"Select an option below to get started:",
        reply_markup=reply_markup
    )
    return SELECTING_ACTION

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "generate_song":
        user_data[user_id] = {"type": "song"}
        await query.edit_message_text(
            "🎵 Great! Describe the song you want to create.\n\n"
            "Example: 'A happy pop song about summer vacations'\n\n"
            "Send your description:"
        )
        return TYPING_PROMPT
    
    elif data == "generate_instrumental":
        user_data[user_id] = {"type": "instrumental"}
        await query.edit_message_text(
            "🎶 Great! Describe the instrumental you want to create.\n\n"
            "Example: 'A calm piano instrumental for studying'\n\n"
            "Send your description:"
        )
        return TYPING_PROMPT
    
    elif data == "help":
        await query.edit_message_text(
            "ℹ️ **How to use this bot:**\n\n"
            "1. Click 'Generate Song' or 'Generate Instrumental'\n"
            "2. Describe what you want to create\n"
            "3. Choose a music style\n"
            "4. Wait for your music to generate!\n\n"
            "Commands:\n"
            "/start - Restart the bot\n"
            "/cancel - Cancel current operation",
            parse_mode='Markdown'
        )
        return SELECTING_ACTION
    
    return SELECTING_ACTION

async def receive_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the music description."""
    user_id = update.effective_user.id
    prompt = update.message.text
    
    # Store the prompt
    if user_id in user_data:
        user_data[user_id]["prompt"] = prompt
    else:
        user_data[user_id] = {"prompt": prompt}
    
    # Ask for style
    keyboard = [
        [InlineKeyboardButton("🎸 Rock", callback_data="style_rock")],
        [InlineKeyboardButton("🎹 Pop", callback_data="style_pop")],
        [InlineKeyboardButton("🎧 Electronic", callback_data="style_electronic")],
        [InlineKeyboardButton("🌅 Ambient", callback_data="style_ambient")],
        [InlineKeyboardButton("🎵 Hip Hop", callback_data="style_hiphop")],
        [InlineKeyboardButton("🎻 Classical", callback_data="style_classical")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📝 Got it! Now choose a style:",
        reply_markup=reply_markup
    )
    return TYPING_STYLE

async def receive_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the style selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    style = query.data.replace("style_", "")
    
    # Get user data
    data = user_data.get(user_id, {})
    prompt = data.get("prompt", "No description provided")
    music_type = data.get("type", "song")
    
    # Generate the music (placeholder)
    await query.edit_message_text(
        f"🎵 **Generating your {music_type}...**\n\n"
        f"📝 Description: {prompt}\n"
        f"🎨 Style: {style}\n\n"
        "⏳ Processing... (this is a demo)\n\n"
        "⚠️ **Note:** Full Suno AI integration is coming soon!\n"
        "For now, this is a demo to show the flow works."
    )
    
    # Clean up user data
    if user_id in user_data:
        del user_data[user_id]
    
    # Send completion message
    await query.message.reply_text(
        "✅ **Done!** Your music has been generated (demo).\n\n"
        "To generate real music, Suno AI integration is needed.\n\n"
        "Use /start to generate another song!",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Use /start to begin again!"
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await update.message.reply_text(
        "ℹ️ **Available Commands:**\n\n"
        "/start - Start the bot\n"
        "/cancel - Cancel current operation\n\n"
        "Just click the buttons to generate music!"
    )

# --- Error Handler ---

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.warning(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "⚠️ Sorry, something went wrong. Please try /start again."
        )

# --- Main Function ---

def main():
    """Start the bot."""
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment variables!")
        return
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(button_callback, pattern="^(generate_song|generate_instrumental|help)$"),
            ],
            TYPING_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prompt),
            ],
            TYPING_STYLE: [
                CallbackQueryHandler(receive_style, pattern="^style_"),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("🚀 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
