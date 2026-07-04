import os
import logging
import asyncio
import json
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUNO_COOKIE = os.environ.get("SUNO_COOKIE")
SUNO_API_URL = os.environ.get("SUNO_API_URL", "https://suno-api.com/api/generate")  # Placeholder URL

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Conversation states
GENERATE_PROMPT = 0
GENERATE_STYLE = 1
GENERATE_TITLE = 2

# Store user sessions (in production, use a database)
user_sessions = {}

# --- Helper Functions ---

def generate_music(prompt, style="pop", title="My Song"):
    """
    Generate music using Suno AI API.
    This is a placeholder - you'll need to implement the actual API call.
    """
    try:
        # Example API call structure (adjust based on actual Suno API)
        headers = {
            "Content-Type": "application/json",
            "Cookie": SUNO_COOKIE
        }
        
        payload = {
            "prompt": prompt,
            "style": style,
            "title": title,
            "duration": 30  # seconds
        }
        
        # Uncomment and adjust when you have the actual API endpoint
        # response = requests.post(SUNO_API_URL, json=payload, headers=headers)
        # response.raise_for_status()
        # return response.json()
        
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
        f"🎵 Welcome {username} to ChatGPT_General_0Bot!\n\n"
        "I'm your AI music generator powered by Suno AI. "
        "Create unique songs from text descriptions instantly.\n\n"
        "✨ Features:\n"
        "• Generate full songs with vocals\n"
        "• Create instrumental tracks\n"
        "• Customize style and genre\n"
        "• High-quality audio output\n\n"
        "🎯 Try it now by clicking the buttons below!"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext):
    """Handle inline keyboard button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "generate":
        await query.edit_message_text(
            "🎵 Let's create a song!\n\n"
            "1️⃣ First, tell me the theme or lyrics of your song.\n"
            "Describe what you want the song to be about.\n\n"
            "Example: 'A love song about summer romance'"
        )
        user_sessions[user_id] = {"step": GENERATE_PROMPT, "type": "song"}
        return GENERATE_PROMPT
    
    elif data == "instrumental":
        await query.edit_message_text(
            "🎶 Let's create an instrumental track!\n\n"
            "1️⃣ Describe the vibe or mood you want.\n"
            "Example: 'Upbeat electronic dance music'"
        )
        user_sessions[user_id] = {"step": GENERATE_PROMPT, "type": "instrumental"}
        return GENERATE_PROMPT
    
    elif data == "credits":
        await query.edit_message_text(
            "💳 Credit System\n\n"
            "You have 10 free generations remaining today.\n"
            "Reset at midnight UTC.\n\n"
            "✨ Premium Plan: $9.99/month\n"
            "• Unlimited generations\n"
            "• Commercial license\n"
            "• Priority processing"
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
            "/cancel - Cancel current operation\n\n"
            "**Tips:**\n"
            "• Be specific in your descriptions\n"
            "• Mention genre for better results\n"
            "• Use /cancel if you get stuck"
        )
        await query.edit_message_text(help_text, parse_mode='Markdown')
        return
    
    return ConversationHandler.END

async def generate_start(update: Update, context: CallbackContext):
    """Start song generation flow"""
    user_id = update.effective_user.id
    user_sessions[user_id] = {"step": GENERATE_PROMPT, "type": "song"}
    
    await update.message.reply_text(
        "🎵 Let's create a song!\n\n"
        "1️⃣ First, tell me the theme or lyrics of your song.\n"
        "Describe what you want the song to be about.\n\n"
        "Example: 'A love song about summer romance'"
    )
    return GENERATE_PROMPT

async def generate_receive_prompt(update: Update, context: CallbackContext):
    """Receive prompt and ask for style"""
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
        ["🌅 Ambient", "🎸 Metal"],
        ["🌍 World", "🎵 Lo-fi"],
        ["🎶 Custom"]
    ]
    
    keyboard = []
    for row in styles:
        keyboard.append([InlineKeyboardButton(style, callback_data=f"style_{style.split()[1] if ' ' in style else style}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎨 Great! Now choose a music style or genre:\n\n"
        "You can also type your own style description.",
        reply_markup=reply_markup
    )
    
    user_sessions[user_id]["step"] = GENERATE_STYLE
    return GENERATE_STYLE

async def generate_receive_style(update: Update, context: CallbackContext):
    """Receive style and generate music"""
    user_id = update.effective_user.id
    style = update.message.text
    
    user_sessions[user_id]["style"] = style
    user_sessions[user_id]["step"] = GENERATE_TITLE
    
    await update.message.reply_text(
        "📝 Almost done! Give your song a title:\n\n"
        "Type a name for your song or send /skip to use auto-generate."
    )
    return GENERATE_TITLE

async def generate_receive_title(update: Update, context: CallbackContext):
    """Receive title and generate the music"""
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
        f"Style: {style}\n"
        f"Prompt: {prompt}\n\n"
        "⏳ This may take 30-60 seconds..."
    )
    
    # Generate music
    result = await generate_music_async(prompt, style, title)
    
    if result.get("success"):
        # In a real implementation, you would send the audio file
        audio_url = result.get("song_url")
        await processing_msg.edit_text(
            f"✅ **{title}** generated successfully!\n\n"
            f"🎵 Style: {style}\n"
            f"⏱️ Duration: {result.get('duration', 30)} seconds\n\n"
            "🎧 **Listen here:** [Audio Link]({audio_url})\n\n"
            "💾 Want to create another? Use /start",
            parse_mode='Markdown'
        )
    else:
        error_msg = result.get("error", "Unknown error occurred")
        await processing_msg.edit_text(
            f"❌ Failed to generate music.\n\n"
            f"Error: {error_msg}\n\n"
            "Please try again later or use a different prompt."
        )
    
    # Clean up session
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    return ConversationHandler.END

async def skip_title(update: Update, context: CallbackContext):
    """Skip title generation and auto-generate a title"""
    user_id = update.effective_user.id
    
    # Auto-generate title from prompt
    session = user_sessions.get(user_id, {})
    prompt = session.get("prompt", "")
    words = prompt.split()[:3]
    title = " ".join(words).title()
    if not title:
        title = "My Song"
    
    # Reuse the title handler
    update.message.text = title
    return await generate_receive_title(update, context)

async def cancel(update: Update, context: CallbackContext):
    """Cancel current operation"""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Use /start to begin again!"
    )
    return ConversationHandler.END

async def credits(update: Update, context: CallbackContext):
    """Check credit balance"""
    # Implement actual credit checking
    await update.message.reply_text(
        "💳 **Your Credits**\n\n"
        "• Free generations remaining: 10\n"
        "• Reset time: 00:00 UTC\n"
        "• Current plan: Free\n\n"
        "Upgrade to Premium for unlimited access!",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: CallbackContext):
    """Show help message"""
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

# --- Error Handler ---

async def error_handler(update: Update, context: CallbackContext):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "⚠️ Sorry, something went wrong. Please try again later."
        )

# --- Main Bot ---

def main():
    """Start the bot"""
    # Validate environment variables
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        logger.info("Please add TELEGRAM_BOT_TOKEN to Railway environment variables.")
        return
    
    if not SUNO_COOKIE:
        logger.warning("⚠️ SUNO_COOKIE not set. Music generation will not work.")
        logger.info("Add SUNO_COOKIE to Railway environment variables to enable music generation.")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
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
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_receive_style),
                CallbackQueryHandler(button_handler, pattern="^style_")
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
    
    # Start bot
    logger.info("🚀 Bot started successfully!")
    logger.info("🤖 Bot username: @ChatGPT_General_0Bot")
    logger.info("📡 Running in polling mode...")
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
