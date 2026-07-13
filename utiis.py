import os
import logging
import yt_dlp
from yt_dlp import YoutubeDL
import re

# Setup logging
logger = logging.getLogger(__name__)

def sanitize_filename(name):
    """Remove special characters from filename"""
    return re.sub(r'[^\w\-_.]', '', name).replace(" ", "")

def download_video(link):
    """Download video from URL"""
    if 'https://' in link:
        try:
            # Ensure download directory exists
            os.makedirs("downloads", exist_ok=True)
            
            # Setup output template
            output_path = os.path.join("downloads", "%(title)s.%(ext)s")
            ydl_opts = {
                'outtmpl': output_path.strip(),
                'quiet': True,
                'noplaylist': True,
                'format': 'best[ext=mp4]/best',  # force mp4
                'max_filesize': 50 * 1024 * 1024,  # 50MB limit for Telegram
            }

            with YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading video: {link}")
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)

                # Remove spaces from filename
                new_filename = filename.replace(" ", "")
                if new_filename != filename and os.path.exists(filename):
                    os.rename(filename, new_filename)
                else:
                    new_filename = filename
                
                # Verify file exists
                if os.path.exists(new_filename):
                    file_size = os.path.getsize(new_filename)
                    logger.info(f"Video downloaded: {new_filename} ({file_size/1024/1024:.2f} MB)")
                    return new_filename
                else:
                    logger.error(f"File not found after download: {new_filename}")
                    return None

        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    else:
        logger.error("Invalid URL - missing https://")
        return None


def download_audio(link):
    """Download audio from URL"""
    if 'https://' in link:
        try:
            output_dir = "downloads/audios"
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path.strip(),
                'quiet': True,
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading audio: {link}")
                info = ydl.extract_info(link, download=True)

                title = info.get("title", "audio")
                filename = f"{title}.mp3"
                full_path = os.path.join(output_dir, filename)

                # Sanitize filename to avoid emoji/special character errors
                clean_filename = sanitize_filename(title) + ".mp3"
                clean_path = os.path.join(output_dir, clean_filename)

                # Rename if needed
                if full_path != clean_path and os.path.exists(full_path):
                    os.rename(full_path, clean_path)
                    logger.info(f"Audio downloaded: {clean_path}")
                    return clean_path
                elif os.path.exists(clean_path):
                    logger.info(f"Audio downloaded: {clean_path}")
                    return clean_path
                elif os.path.exists(full_path):
                    logger.info(f"Audio downloaded: {full_path}")
                    return full_path
                else:
                    logger.error("MP3 file not found after download")
                    return None

        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None
                
    else:
        logger.error("Invalid URL - missing https://")
        return None