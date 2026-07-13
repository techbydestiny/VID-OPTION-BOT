import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from utils import download_video, download_audio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_USERNAME = os.getenv("VIDPTION_BOT_USERNAME")
TOKEN = os.getenv("VIDPTION_BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

# Validate required environment variables
if not TOKEN:
    raise ValueError("VIDPTION_BOT_TOKEN environment variable is required")
if not BOT_USERNAME:
    raise ValueError("VIDPTION_BOT_USERNAME environment variable is required")

# Create downloads directory
os.makedirs("downloads", exist_ok=True)
os.makedirs("downloads/audios", exist_ok=True)

# Your existing message constants...
TERMS_MESSAGE = """
*📜 Terms & Conditions*
[Your terms text here...]
"""

PRIVACY_POLICY = """
🔒 *Privacy Policy*
[Your privacy policy text here...]
"""

WELCOME_MESSAGE = """
🎥 *Welcome to Vidption!*

Your all-in-one media downloader for Telegram.

✨ *What I can do:*
• 📹 Download videos from multiple platforms
• 🎵 Extract audio from videos
• ⚡ Fast and reliable downloads
• 🔒 Private and secure

*Supported Platforms:*
YouTube • Instagram • TikTok • Twitter/X • Facebook • and more!

💡 *Quick Start:*
Just send me any video URL to download!
Add `@toaudio` to get audio only.

📚 Use /help for detailed instructions
"""

HELP_MESSAGE = f"""
*📚 How to use Vidption:*

🎬 *Download Videos:*
• Simply send any video URL
• Works in private chat automatically
• In groups, mention @{BOT_USERNAME} followed by URL

🎵 *Download Audio:*
• Add `@toaudio` before or after any URL
• Example: `@toaudio https://youtube.com/watch?v=...`
• Get MP3 audio extracted from videos

📱 *Supported Platforms:*
• YouTube, Instagram, TikTok
• Twitter/X, Facebook, Vimeo
• And many more!

🛠 *Available Commands:*
• /start - Start the bot
• /help - Show this help message
• /terms - Terms & Conditions
• /privacy - Privacy Policy

⚠️ *Limitations:*
• Maximum file size: 50MB
• Videos up to 720p quality
• Public content only

*Need support?* Contact @VidptionSupportBot
"""

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Render health checks"""
    
    def do_GET(self):
        """Respond to health check requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Vidption Bot is running!')
    
    def do_HEAD(self):
        """Respond to HEAD requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

def run_health_server(port):
    """Run a simple HTTP server for Render health checks"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")

# Your existing handler functions...
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode=ParseMode.MARKDOWN
    )

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /terms command"""
    await update.message.reply_text(TERMS_MESSAGE, parse_mode=ParseMode.MARKDOWN)

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /privacy command"""
    await update.message.reply_text(PRIVACY_POLICY, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.MARKDOWN)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages with URLs"""
    message_type: str = update.message.chat.type
    link: str = update.message.text.strip()

    logger.info(f"User {update.message.chat.id} in {message_type}: {link}")

    # Handle group messages with bot mention
    if message_type == 'group':
        if BOT_USERNAME in link:
            link = link.replace(BOT_USERNAME, '').strip()
        else:
            return  # Ignore messages without bot mention in groups

    # Check if audio download is requested
    if '@toaudio' in link:
        link = link.replace('@toaudio', '').strip()
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🎵 *Vidption is processing your audio...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            file_path = download_audio(link)
            
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 50 * 1024 * 1024:  # 50MB
                    await processing_msg.delete()
                    await update.message.reply_text(
                        "❌ Audio file is too large (>50MB).",
                        reply_to_message_id=update.message.message_id
                    )
                else:
                    try:
                        with open(file_path, 'rb') as audio:
                            await context.bot.send_audio(
                                chat_id=update.message.chat_id,
                                audio=audio,
                                reply_to_message_id=update.message.message_id,
                                caption="🎵 Downloaded with Vidption Bot",
                                read_timeout=60,
                                write_timeout=60
                            )
                        await processing_msg.delete()
                        logger.info(f"Audio sent successfully: {file_path}")
                    except Exception as e:
                        logger.error(f"Error sending audio: {e}")
                        await update.message.reply_text(
                            f"❌ Couldn't send the audio. Please try again.",
                            reply_to_message_id=update.message.message_id
                        )
            else:
                await processing_msg.delete()
                await update.message.reply_text(
                    "❌ Failed to download audio. Please check the URL.",
                    reply_to_message_id=update.message.message_id
                )
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await update.message.reply_text(
                "❌ An error occurred while processing your audio request.",
                reply_to_message_id=update.message.message_id
            )
        finally:
            if 'file_path' in locals() and file_path and os.path.exists(file_path):
                os.remove(file_path)
    else:
        # Video download
        processing_msg = await update.message.reply_text(
            "🎥 *Vidption is downloading your video...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            file_path = download_video(link)
            
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 50 * 1024 * 1024:  # 50MB
                    await processing_msg.delete()
                    await update.message.reply_text(
                        "❌ Video is too large (>50MB).",
                        reply_to_message_id=update.message.message_id
                    )
                else:
                    try:
                        with open(file_path, 'rb') as video:
                            await context.bot.send_video(
                                chat_id=update.message.chat_id,
                                video=video,
                                reply_to_message_id=update.message.message_id,
                                supports_streaming=True,
                                caption="📹 Downloaded with Vidption Bot",
                                read_timeout=60,
                                write_timeout=60
                            )
                        await processing_msg.delete()
                        logger.info(f"Video sent successfully: {file_path}")
                    except Exception as e:
                        logger.error(f"Error sending video: {e}")
                        await update.message.reply_text(
                            f"❌ Couldn't send the video. Please try again.",
                            reply_to_message_id=update.message.message_id
                        )
            else:
                await processing_msg.delete()
                await update.message.reply_text(
                    "❌ Failed to download video. Please check the URL.",
                    reply_to_message_id=update.message.message_id
                )
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            await update.message.reply_text(
                "❌ An error occurred while processing your video request.",
                reply_to_message_id=update.message.message_id
            )
        finally:
            if 'file_path' in locals() and file_path and os.path.exists(file_path):
                os.remove(file_path)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Main function to run the bot"""
    logger.info("Starting Vidption Bot...")
    print("Starting Vidption Bot...")
    
    # Start health check server in a separate thread
    health_port = PORT
    health_thread = threading.Thread(
        target=run_health_server, 
        args=(health_port,), 
        daemon=True
    )
    health_thread.start()
    logger.info(f"Health server started on port {health_port}")
    
    # Create application
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('terms', terms_command))
    app.add_handler(CommandHandler('privacy', privacy_command))
    app.add_handler(CommandHandler('help', help_command))

    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    # Add error handler
    app.add_error_handler(error_handler)

    # Run polling
    logger.info("Starting polling mode...")
    print("Bot is now listening for messages...")
    app.run_polling(
        poll_interval=1.0,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()