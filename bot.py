import os
import logging
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
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Your Render app URL

# Validate required environment variables
if not TOKEN:
    raise ValueError("VIDPTION_BOT_TOKEN environment variable is required")
if not BOT_USERNAME:
    raise ValueError("VIDPTION_BOT_USERNAME environment variable is required")

# Create downloads directory
os.makedirs("downloads", exist_ok=True)
os.makedirs("downloads/audios", exist_ok=True)

# Constants
TERMS_MESSAGE = """
*📜 Terms & Conditions*

*1. Introduction*
These Terms & Conditions govern your use of Vidption Bot. By using our bot, you agree to these terms. If you do not agree, please discontinue use immediately.

*2. Use of Media and Copyright Notice*
We do not claim ownership of any media content downloaded or shared using Vidption. All copyrights belong to their respective owners. We are not responsible for any unauthorized use of copyrighted material.

*3. Third-Party Associations*
Vidption is not officially connected with any social media platform. Use at your own discretion.

*4. Downloading Social Media Data*
We can only download publicly available data. Third-party services may be used to process links.

*5. Service Disclaimer*
We aim for stability, but service may be interrupted or ended at any time. We're not liable for damages resulting from service issues.

*6. Indemnity*
You agree to hold Vidption harmless from any claims related to your use of the bot.

*7. Changes to Terms*
We may update these at any time. Continued use means acceptance.

*8. Contact*
For questions, contact: @VidptionSupportBot
"""

PRIVACY_POLICY = """
🔒 *Privacy Policy*

*1. Introduction*
This Privacy Policy explains how Vidption collects, uses, and protects your information. By using the bot, you agree to this policy.

*2. Information We Collect*
• *Telegram User ID:* Collected to identify you as a user.
• *General Data:* We may use data like your language to generate bot usage statistics.

*3. Cookies and Tracking*
We do not use cookies or tracking technologies.

*4. Downloading Social Media Data*
• *Public Data Only:* We only download publicly available content.
• *Third-Party Services:* Media downloads are handled by external tools that do not receive your personal info—only media links.

*5. Data Storage & Security*
• We do *not* store chat history.
• Media may link to external sites. Review their privacy policies.
• Ads may be shown occasionally. Clicking them leads outside the bot; we advise checking external policies.
• We use modern encryption and best practices to protect your data.

*6. Payment Processing*
Some features may require payment. We do not process payments ourselves—please review the privacy policy of the payment provider.

*7. Age Restriction*
Vidption is intended for users aged *18 and above*. If you are under 18, please stop using the bot.

*8. Policy Changes*
We may update this Privacy Policy. Please check periodically for changes.

*9. Contact Us*
For any questions, contact: @VidptionSupportBot

*10. Use of Media*
Vidption serves as a media downloading tool. We do not claim ownership of content downloaded via this bot.

*11. Copyright Notice*
All rights belong to original creators. Always seek permission before sharing content.
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

HELP_MESSAGE = """
*📚 How to use Vidption:*

🎬 *Download Videos:*
• Simply send any video URL
• Works in private chat automatically
• In groups, mention @{bot_username} followed by URL

🎵 *Download Audio:*
• Add `@toaudio` before or after any URL
• Example: `@toaudio https://youtube.com/watch?v=...`
• Get MP3 audio extracted from videos

📱 *Supported Platforms:*
• YouTube (videos, shorts)
• Instagram (posts, reels, stories)
• TikTok (videos)
• Twitter/X (videos)
• Facebook (videos)
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

🔧 *Tips:*
• Make sure the URL is complete and accessible
• For best results, use links from supported platforms
• The bot works in groups when mentioned

*Need support?* Contact @VidptionSupportBot
""".format(bot_username="{bot_username}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode=ParseMode.MARKDOWN
    )
    await send_pinned_ad(update, context)

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /terms command"""
    await update.message.reply_text(TERMS_MESSAGE, parse_mode=ParseMode.MARKDOWN)

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /privacy command"""
    await update.message.reply_text(PRIVACY_POLICY, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = HELP_MESSAGE.format(bot_username=BOT_USERNAME)
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def send_pinned_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send and pin advertisement message"""
    chat_id = update.effective_chat.id

    ad_text = "🔥 Want to make money online? Click the link below 👇\n[Ad] Earn from home 💸"
    ad_url = "https://www.profitableratecpm.com/q3kdk49ih?key=06f9eb9a496c602b5b0e39cba2d700cd"

    # Inline button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Check it out", url=ad_url)]
    ])

    try:
        # Send the ad message
        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text=ad_text,
            reply_markup=keyboard
        )

        # Pin it
        await context.bot.pin_chat_message(
            chat_id=chat_id,
            message_id=sent_message.message_id,
            disable_notification=True
        )
    except Exception as e:
        logger.error(f"Failed to pin message: {e}")

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
                try:
                    with open(file_path, 'rb') as audio:
                        await context.bot.send_audio(
                            chat_id=update.message.chat_id,
                            audio=audio,
                            reply_to_message_id=update.message.message_id,
                            caption="🎵 Downloaded with Vidption Bot"
                        )
                    await processing_msg.delete()
                    logger.info(f"Audio sent successfully: {file_path}")
                except Exception as e:
                    logger.error(f"Error sending audio: {e}")
                    await update.message.reply_text(
                        f"❌ Couldn't send the audio: {str(e)}",
                        reply_to_message_id=update.message.message_id
                    )
                finally:
                    # Clean up file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Cleaned up: {file_path}")
            else:
                await processing_msg.delete()
                await update.message.reply_text(
                    "❌ Failed to download audio. Please check the URL and try again.",
                    reply_to_message_id=update.message.message_id
                )
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ An error occurred while processing your audio request.",
                reply_to_message_id=update.message.message_id
            )
    else:
        # Video download
        processing_msg = await update.message.reply_text(
            "🎥 *Vidption is downloading your video...*\n⏳ This might take a moment",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            file_path = download_video(link)
            
            if file_path and os.path.exists(file_path):
                try:
                    # Check file size (Telegram limit is 50MB for bots)
                    file_size = os.path.getsize(file_path)
                    if file_size > 50 * 1024 * 1024:  # 50MB
                        await processing_msg.delete()
                        await update.message.reply_text(
                            "❌ Video is too large (>50MB). Please try a shorter video or lower quality.",
                            reply_to_message_id=update.message.message_id
                        )
                    else:
                        with open(file_path, 'rb') as video:
                            await context.bot.send_video(
                                chat_id=update.message.chat_id,
                                video=video,
                                reply_to_message_id=update.message.message_id,
                                supports_streaming=True,
                                caption="📹 Downloaded with Vidption Bot"
                            )
                        await processing_msg.delete()
                        logger.info(f"Video sent successfully: {file_path}")
                except Exception as e:
                    logger.error(f"Error sending video: {e}")
                    await processing_msg.delete()
                    await update.message.reply_text(
                        f"❌ Couldn't send the video: {str(e)}",
                        reply_to_message_id=update.message.message_id
                    )
                finally:
                    # Clean up file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Cleaned up: {file_path}")
            else:
                await processing_msg.delete()
                await update.message.reply_text(
                    "❌ Failed to download video. Please check:\n"
                    "• The URL is correct\n"
                    "• The video is publicly accessible\n"
                    "• The platform is supported\n\n"
                    "Use /help to see supported platforms.",
                    reply_to_message_id=update.message.message_id
                )
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ An error occurred while processing your video request.",
                reply_to_message_id=update.message.message_id
            )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Notify user if possible
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
        except:
            pass

def main():
    """Main function to run the bot"""
    logger.info("Starting Vidption Bot...")
    
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

    # Start webhook
    logger.info(f"Starting webhook on port {PORT}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",  # This MUST match the path in WEBHOOK_URL
        webhook_url=f"{WEBHOOK_URL}/webhook",
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()

