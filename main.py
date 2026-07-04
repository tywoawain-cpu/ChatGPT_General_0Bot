import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Conversation states
PROMPT, STYLE, TITLE = range(3)

# Store user data
user_data = {}

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    keyboard = [
        [InlineKeyboardButton("🎵 Generate Music", callback_data="generate")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎵 Welcome to ChatGPT_General_0Bot!\n\n"
        "I generate music using AI.\n"
        "Click the button below to start!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "generate":
        user_id = query.from_user.id
        user_data[user_id] = {}
        await query.edit_message_text(
            "🎵 Describe the music you want:\n\n"
            "Example: 'A happy pop song about summer'"
        )
        return PROMPT
    
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ **Commands:**\n"
            "/start - Start the bot\n"
            "/cancel - Cancel current operation\n\n"
            "Just describe what music you want!",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def receive_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive music prompt"""
    user_id = update.effective_user.id
    prompt = update.message.text
    
    user_data[user_id]["prompt"] = prompt
    
    # Style selection
    keyboard = [
        [InlineKeyboardButton("🎸 Rock", callback_data="style_rock")],
        [InlineKeyboardButton("🎹 Pop", callback_data="style_pop")],
        [InlineKeyboardButton("🎧 Electronic", callback_data="style_electronic")],
        [InlineKeyboardButton("🌅 Ambient", callback_data="style_ambient")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎨 Choose a style:",
        reply_markup=reply_markup
    )
    return STYLE

async def receive_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive style selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    style = query.data.replace("style_", "")
    
    user_data[user_id]["style"] = style
    
    await query.edit_message_text(
        "📝 Give your song a title:\n"
        "Type a name or send /skip for auto-title"
    )
    return TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive title and generate"""
    user_id = update.effective_user.id
    title = update.message.text
    
    data = user_data.get(user_id, {})
    prompt = data.get("prompt", "")
    style = data.get("style", "pop")
    
    await update.message.reply_text(
        f"🎧 Generating: {title}\n"
        f"Style: {style}\n"
        f"Prompt: {prompt}\n\n"
        "⏳ Please wait 30-60 seconds...\n\n"
        "⚠️ This is a demo. Full Suno AI integration coming soon!"
    )
    
    # Clean up
    if user_id in user_data:
        del user_data[user_id]
    
    return ConversationHandler.END

async def skip_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip title"""
    user_id = update.effective_user.id
    data = user_data.get(user_id, {})
    prompt = data.get("prompt", "")
    title = " ".join(prompt.split()[:3]).title()
    if not title:
        title = "My Song"
    
    update.message.text = title
    return await receive_title(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text("❌ Cancelled. Use /start to begin again.")
    return ConversationHandler.END

# --- Error Handler ---

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")

# --- Main ---

def main():
    """Start bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^generate$"),
            CommandHandler("start", start)
        ],
        states={
            PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prompt),
            ],
            STYLE: [
                CallbackQueryHandler(receive_style, pattern="^style_"),
            ],
            TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title),
                CommandHandler("skip", skip_title)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True
    )
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
