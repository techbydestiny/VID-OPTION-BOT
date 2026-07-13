import os
import logging
import yt_dlp
from yt_dlp import YoutubeDL
import re

# Setup logging
logger = logging.getLogger(__name__)

def sanitize_filename(name):
    """Remove special characters from filename"""
    # Keep letters, numbers, hyphens, underscores, and dots only
    sanitized = re.sub(r'[^\w\-_.]', '', name)
    # Remove spaces
    sanitized = sanitized.replace(" ", "")
    # Limit filename length (Telegram has limits)
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized

def download_video(link):
    """Download video from URL"""
    if 'https://' not in link:
        logger.error("Invalid URL - missing https://")
        return None
    
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
            'retries': 3,  # Retry on failure
            'fragment_retries': 3,  # Retry fragments
            'socket_timeout': 30,  # Network timeout
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
                
                # Double check file size
                if file_size > 50 * 1024 * 1024:
                    logger.error(f"File too large: {file_size/1024/1024:.2f} MB")
                    os.remove(new_filename)
                    return None
                    
                return new_filename
            else:
                logger.error(f"File not found after download: {new_filename}")
                return None

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return None


def download_audio(link):
    """Download audio from URL"""
    if 'https://' not in link:
        logger.error("Invalid URL - missing https://")
        return None
    
    try:
        output_dir = "downloads/audios"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path.strip(),
            'quiet': True,
            'noplaylist': True,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
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
                logger.info(f"Audio downloaded and renamed: {clean_path}")
                
                # Check file size
                file_size = os.path.getsize(clean_path)
                if file_size > 50 * 1024 * 1024:
                    logger.error(f"Audio too large: {file_size/1024/1024:.2f} MB")
                    os.remove(clean_path)
                    return None
                    
                return clean_path
            elif os.path.exists(clean_path):
                logger.info(f"Audio downloaded: {clean_path}")
                
                # Check file size
                file_size = os.path.getsize(clean_path)
                if file_size > 50 * 1024 * 1024:
                    logger.error(f"Audio too large: {file_size/1024/1024:.2f} MB")
                    os.remove(clean_path)
                    return None
                    
                return clean_path
            elif os.path.exists(full_path):
                logger.info(f"Audio downloaded: {full_path}")
                
                # Check file size
                file_size = os.path.getsize(full_path)
                if file_size > 50 * 1024 * 1024:
                    logger.error(f"Audio too large: {file_size/1024/1024:.2f} MB")
                    os.remove(full_path)
                    return None
                    
                return full_path
            else:
                logger.error("MP3 file not found after download")
                return None

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        return None