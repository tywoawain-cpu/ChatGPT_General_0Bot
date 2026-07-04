import os
import sys
import logging
import asyncio
import json
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram.error import TelegramError, Conflict

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUNO_COOKIE = os.environ.get("SUNO_COOKIE")

# Logging setup with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Conversation states
GENERATE_PROMPT, GENERATE_STYLE, GENERATE_TITLE = range(3)

# Store user sessions
user_sessions = {}

# --- Helper Functions ---

def generate_music(prompt, style="pop", title="My Song"):
    """Generate music using Suno AI API (placeholder)"""
    try:
        # Mock response for testing
        return {
            "success": True,
            "song_url": "https://example.com/generated_song.mp3",
            "title": title,
            "duration": 30
        }
    except Exception as e:
        logger.error(f"Music generation error: {e}")
        return {"success": False, "error": str(e)}

async def generate_music_async(prompt, style, title):
    """Async wrapper for music generation"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, generate_music, prompt, style, title)
    return result

# --- Command Handlers ---

async def start(update: Update, context: CallbackContext):
    """Welcome message and main menu"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        
        keyboard = [
            [InlineKeyboardButton("🎵 Generate Music", callback_data="generate")],
            [InlineKeyboardButton("🎶 Generate Instrumental", callback_data="instrumental")],
            [InlineKeyboardButton("💳 Check Credits", callback_data="credits")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            f"🎵 Welcome {username}!\n\n"
            "I'm your AI music generator powered by Suno AI.\n"
            "Create unique songs from text descriptions instantly.\n\n"
            "Try it now by clicking the buttons below!"
        )
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong. Please try /help")

async def button_handler(update: Update, context: CallbackContext):
    """Handle inline keyboard button clicks"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data in ["generate", "instrumental"]:
            music_type = "song" if data == "generate" else "instrumental"
            await query.edit_message_text(
                f"🎵 Let's create a {music_type}!\n\n"
                "Please send me a description of what you want to create.\n"
                "Example: 'A calm lo-fi beat with piano and soft drums'"
            )
            user_sessions[user_id] = {"step": GENERATE_PROMPT, "type": music_type}
            return GENERATE_PROMPT
        
        elif data == "credits":
            await query.edit_message_text(
                "💳 Credit System\n\n"
                "You have 10 free generations remaining today.\n"
                "Reset at midnight UTC.\n\n"
                "✨ Premium Plan: $9.99/month\n"
                "• Unlimited generations\n"
                "• Commercial license"
            )
            return
        
        elif data == "help":
            help_text = (
                "ℹ️ **How to Use This Bot**\n\n"
                "**Commands:**\n"
                "/start - Show main menu\n"
                "/generate - Create a song\n"
                "/instrumental - Create an instrumental\n"
                "/credits - Check your usage\n"
                "/help - Show this help\n"
                "/cancel - Cancel current operation"
            )
            await query.edit_message_text(help_text, parse_mode='Markdown')
            return
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        return ConversationHandler.END

async def generate_start(update: Update, context: CallbackContext):
    """Start song generation flow"""
    try:
        user_id = update.effective_user.id
        user_sessions[user_id] = {"step": GENERATE_PROMPT, "type": "song"}
        
        await update.message.reply_text(
            "🎵 Let's create a song!\n\n"
            "1️⃣ First, tell me the theme or lyrics of your song.\n"
            "Describe what you want the song to be about.\n\n"
            "Example: 'A love song about summer romance'"
        )
        return GENERATE_PROMPT
    except Exception as e:
        logger.error(f"Error in generate_start: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")
        return ConversationHandler.END

async def generate_receive_prompt(update: Update, context: CallbackContext):
    """Receive prompt and ask for style"""
    try:
        user_id = update.effective_user.id
        prompt = update.message.text
        
        # Store prompt
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        user_sessions[user_id]["prompt"] = prompt
        
        # Create style selection keyboard
        styles = [
            ["🎸 Rock", "🎹 Pop"],
            ["🎵 Hip Hop", "🎻 Classical"],
            ["🎷 Jazz", "🎧 Electronic"],
            ["🌅 Ambient", "🎶 Lo-fi"]
        ]
        
        keyboard = []
        for row in styles:
            buttons = []
            for style in row:
                buttons.append(InlineKeyboardButton(style, callback_data=f"style_{style}"))
            keyboard.append(buttons)
        
        keyboard.append([InlineKeyboardButton("📝 Custom Style", callback_data="style_custom")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎨 Great! Now choose a music style or genre:",
            reply_markup=reply_markup
        )
        
        user_sessions[user_id]["step"] = GENERATE_STYLE
        return GENERATE_STYLE
    except Exception as e:
        logger.error(f"Error in generate_receive_prompt: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")
        return ConversationHandler.END

async def generate_receive_style(update: Update, context: CallbackContext):
    """Receive style and generate music"""
    try:
        user_id = update.effective_user.id
        query = update.callback_query
        await query.answer()
        
        style = query.data.replace("style_", "")
        user_sessions[user_id]["style"] = style
        user_sessions[user_id]["step"] = GENERATE_TITLE
        
        await query.edit_message_text(
            "📝 Almost done! Give your song a title:\n\n"
            "Type a name for your song or send /skip to auto-generate."
        )
        return GENERATE_TITLE
    except Exception as e:
        logger.error(f"Error in generate_receive_style: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")
        return ConversationHandler.END

async def generate_receive_title(update: Update, context: CallbackContext):
    """Receive title and generate the music"""
    try:
        user_id = update.effective_user.id
        title = update.message.text
        
        # Get saved data
        session = user_sessions.get(user_id, {})
        prompt = session.get("prompt", "")
        style = session.get("style", "pop")
        music_type = session.get("type", "song")
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🎧 Generating your {music_type}...\n\n"
            f"Title: {title}\n"
            f"Style: {style}\n\n"
            "⏳ This may take 30-60 seconds..."
        )
        
        # Generate music
        result = await generate_music_async(prompt, style, title)
        
        if result.get("success"):
            audio_url = result.get("song_url")
            await processing_msg.edit_text(
                f"✅ **{title}** generated successfully!\n\n"
                f"🎵 Style: {style}\n"
                f"⏱️ Duration: {result.get('duration', 30)} seconds\n\n"
                f"🎧 **Listen here:** [Audio Link]({audio_url})\n\n"
                "💾 Want to create another? Use /start",
                parse_mode='Markdown'
            )
        else:
            error_msg = result.get("error", "Unknown error occurred")
            await processing_msg.edit_text(
                f"❌ Failed to generate music.\n\n"
                f"Error: {error_msg}\n\n"
                "Please try again later."
            )
        
        # Clean up session
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in generate_receive_title: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")
        return ConversationHandler.END

async def skip_title(update: Update, context: CallbackContext):
    """Skip title generation and auto-generate a title"""
    try:
        user_id = update.effective_user.id
        session = user_sessions.get(user_id, {})
        prompt = session.get("prompt", "")
        words = prompt.split()[:3]
        title = " ".join(words).title()
        if not title:
            title = "My Song"
        
        await update.message.reply_text(f"Auto-generating title: {title}")
        update.message.text = title
        return await generate_receive_title(update, context)
    except Exception as e:
        logger.error(f"Error in skip_title: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")
        return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    """Cancel current operation"""
    try:
        user_id = update.effective_user.id
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        await update.message.reply_text(
            "❌ Operation cancelled.\n\n"
            "Use /start to begin again!"
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in cancel: {e}")
        return ConversationHandler.END

async def credits(update: Update, context: CallbackContext):
    """Check credit balance"""
    try:
        await update.message.reply_text(
            "💳 **Your Credits**\n\n"
            "• Free generations remaining: 10\n"
            "• Reset time: 00:00 UTC\n"
            "• Current plan: Free\n\n"
            "Upgrade to Premium for unlimited access!",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in credits: {e}")

async def help_command(update: Update, context: CallbackContext):
    """Show help message"""
    try:
        help_text = (
            "ℹ️ **Bot Commands**\n\n"
            "/start - Show main menu\n"
            "/generate - Create a song\n"
            "/instrumental - Create an instrumental\n"
            "/credits - Check your usage\n"
            "/help - Show this help\n"
            "/cancel - Cancel current operation\n\n"
            "**Need Support?**\n"
            "Join our community for updates and help!"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in help_command: {e}")

# --- Error Handler ---

async def error_handler(update: Update, context: CallbackContext):
    """Handle errors gracefully"""
    try:
        logger.error(f"Error: {context.error}")
        
        # Handle specific errors
        if isinstance(context.error, Conflict):
            logger.error("Conflict error - another instance is running")
            await update.message.reply_text(
                "⚠️ Bot is already running in another instance. Please wait..."
            )
        elif isinstance(context.error, TelegramError):
            logger.error(f"Telegram API error: {context.error}")
        else:
            logger.error(f"Unexpected error: {context.error}")
    except Exception as e:
        logger.error(f"Error in error_handler: {e}")

# --- Main Bot ---

def main():
    """Start the bot with robust error handling"""
    # Validate environment variables
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        logger.info("Please add TELEGRAM_BOT_TOKEN to Railway environment variables.")
        return
    
    if not SUNO_COOKIE:
        logger.warning("⚠️ SUNO_COOKIE not set. Music generation will not work.")
        logger.info("Add SUNO_COOKIE to Railway environment variables to enable music generation.")
    
    try:
        # Create application with timeout settings
        application = Application.builder()\
            .token(TELEGRAM_BOT_TOKEN)\
            .connect_timeout(30.0)\
            .read_timeout(30.0)\
            .build()
        
        # --- Conversation Handlers ---
        
        # Song generation conversation
        song_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('generate', generate_start),
                CallbackQueryHandler(button_handler, pattern="^generate$"),
                CallbackQueryHandler(button_handler, pattern="^instrumental$")
            ],
            states={
                GENERATE_PROMPT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, generate_receive_prompt),
                    CallbackQueryHandler(button_handler)
                ],
                GENERATE_STYLE: [
                    CallbackQueryHandler(generate_receive_style, pattern="^style_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, generate_receive_style)
                ],
                GENERATE_TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, generate_receive_title),
                    CommandHandler('skip', skip_title)
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('start', start)
            ],
            allow_reentry=True
        )
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("credits", credits))
        application.add_handler(song_conv_handler)
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_error_handler(error_handler)
        
        # Start bot with error handling
        logger.info("🚀 Bot starting successfully!")
        logger.info("🤖 Bot username: @ChatGPT_General_0Bot")
        logger.info("📡 Running in polling mode...")
        
        # This is the key fix - start polling with proper error handling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Conflict as e:
        logger.error(f"Conflict error: {e}")
        logger.info("Another instance is running. Waiting 5 seconds and retrying...")
        time.sleep(5)
        main()  # Retry
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
