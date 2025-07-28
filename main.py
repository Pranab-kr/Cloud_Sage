import os
import logging
import asyncio
import tempfile
import shutil
import time
from urllib.parse import urlparse
from pathlib import Path

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatAction
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Get from environment variable

class VideoDownloaderBot:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        # Get the directory where the script is located for cookie files
        self.script_dir = Path(__file__).parent
        self.youtube_cookies = self.script_dir / "youtube.com_cookies.txt"
        self.instagram_cookies = self.script_dir / "instagram.com_cookies.txt"
        
        # Create cookie files from environment variables if they don't exist
        self.setup_cookies_from_env()
        
        # Validate cookie files on initialization
        self.validate_cookie_files()
    
    def setup_cookies_from_env(self):
        """Create cookie files from environment variables if they don't exist"""
        # YouTube cookies from environment variable
        youtube_cookies_content = os.getenv('YOUTUBE_COOKIES')
        if youtube_cookies_content and not self.youtube_cookies.exists():
            try:
                with open(self.youtube_cookies, 'w', encoding='utf-8') as f:
                    # Replace \n with actual newlines if the env var uses escaped newlines
                    content = youtube_cookies_content.replace('\\n', '\n')
                    f.write(content)
                logger.info("✅ YouTube cookies created from environment variable")
            except Exception as e:
                logger.error(f"❌ Error creating YouTube cookies from env: {e}")
        
        # Instagram cookies from environment variable
        instagram_cookies_content = os.getenv('INSTAGRAM_COOKIES')
        if instagram_cookies_content and not self.instagram_cookies.exists():
            try:
                with open(self.instagram_cookies, 'w', encoding='utf-8') as f:
                    # Replace \n with actual newlines if the env var uses escaped newlines
                    content = instagram_cookies_content.replace('\\n', '\n')
                    f.write(content)
                logger.info("✅ Instagram cookies created from environment variable")
            except Exception as e:
                logger.error(f"❌ Error creating Instagram cookies from env: {e}")
    
    
    def validate_cookie_files(self):
        """Validate that cookie files exist and are readable"""
        if self.youtube_cookies.exists():
            logger.info(f"✅ YouTube cookies file found: {self.youtube_cookies}")
            try:
                with open(self.youtube_cookies, 'r') as f:
                    lines = f.readlines()
                    logger.info(f"YouTube cookies file has {len(lines)} lines")
            except Exception as e:
                logger.error(f"❌ Error reading YouTube cookies: {e}")
        else:
            logger.warning(f"⚠️ YouTube cookies file not found at: {self.youtube_cookies}")
        
        if self.instagram_cookies.exists():
            logger.info(f"✅ Instagram cookies file found: {self.instagram_cookies}")
            try:
                with open(self.instagram_cookies, 'r') as f:
                    lines = f.readlines()
                    logger.info(f"Instagram cookies file has {len(lines)} lines")
            except Exception as e:
                logger.error(f"❌ Error reading Instagram cookies: {e}")
        else:
            logger.warning(f"⚠️ Instagram cookies file not found at: {self.instagram_cookies}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_message = """
🎬 **Video Downloader Bot**

Send me a YouTube or Instagram link and I'll download the video for you!

**Supported platforms:**
• YouTube (videos & audio)
• Instagram (posts, reels, stories)

**Commands:**
/start - Show this message
/help - Get help

Just paste a link to get started! 🚀
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
**How to use this bot:**

1. Copy a YouTube or Instagram video URL
2. Send it to this bot
3. Choose your preferred quality/format
4. Wait for the download to complete

**Supported URL formats:**
• https://www.youtube.com/watch?v=...
• https://youtu.be/...
• https://www.instagram.com/p/...
• https://www.instagram.com/reel/...

**Note:** Large files may take some time to process. Please be patient! ⏳
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    def is_youtube_url(self, url: str) -> bool:
        """Check if URL is from YouTube"""
        parsed = urlparse(url)
        return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be', 'm.youtube.com']
    
    def is_instagram_url(self, url: str) -> bool:
        """Check if URL is from Instagram"""
        parsed = urlparse(url)
        return parsed.netloc in ['www.instagram.com', 'instagram.com']
    
    async def download_youtube_video(self, url: str, quality: str = 'best') -> dict:
        """Download YouTube video using yt-dlp"""
        try:
            # Clean filename template with quality info to avoid conflicts
            try:
                quality_suffix = quality.split('+')[0].replace('/', '_')[:10]
            except (AttributeError, IndexError):
                quality_suffix = 'video'
            filename_template = f'%(id)s_{quality_suffix}.%(ext)s'
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': quality,
                'outtmpl': os.path.join(self.temp_dir, filename_template),
                'noplaylist': True,
                'writeinfojson': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'ignoreerrors': False,
                'extract_flat': False,
                'prefer_ffmpeg': True,
                'merge_output_format': 'mp4',
            }
            
            # Add YouTube cookies if the file exists
            if self.youtube_cookies.exists():
                ydl_opts['cookiefile'] = str(self.youtube_cookies)
                logger.info(f"Using YouTube cookies from: {self.youtube_cookies}")
            else:
                logger.warning("YouTube cookies file not found, proceeding without authentication")
            
            # Handle audio extraction
            if quality == 'bestaudio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                video_id = info.get('id', 'unknown')
                duration = info.get('duration', 0)
                
                # Log available formats for debugging
                formats = info.get('formats', [])
                logger.info(f"Available formats for {video_id}: {len(formats)} formats")
                
                # Log some high quality formats available
                high_quality_formats = [f for f in formats if (f.get('height') or 0) >= 720]
                logger.info(f"High quality formats (720p+): {len(high_quality_formats)}")
                for fmt in high_quality_formats[:3]:  # Log first 3
                    height = fmt.get('height') or 0
                    logger.info(f"Format {fmt.get('format_id')}: {height}p, {fmt.get('ext')}")
                
                # Check file size (estimate)
                if duration and duration > 600:  # 10 minutes
                    return {'error': 'Video is too long (max 10 minutes allowed)'}
                
                logger.info(f"Using format string: {quality}")
                
                # Try to get selected format info for debugging
                try:
                    selected_formats = ydl._format_selection(info['formats'], quality)
                    if selected_formats:
                        for fmt in selected_formats[:2]:  # Log first 2 selected formats
                            logger.info(f"Selected format: {fmt.get('format_id')} - {fmt.get('height', 'unknown')}p")
                except:
                    pass  # Ignore format selection debug errors
                
                # Download the video
                ydl.download([url])
                
                # Find the downloaded file using video ID and quality suffix
                try:
                    quality_suffix = quality.split('+')[0].replace('/', '_')[:10]
                except (AttributeError, IndexError):
                    quality_suffix = 'video'
                
                expected_extensions = ['.mp4', '.webm', '.mkv', '.mp3'] if 'bestaudio' in quality else ['.mp4', '.webm', '.mkv']
                
                for ext in expected_extensions:
                    file_path = os.path.join(self.temp_dir, f"{video_id}_{quality_suffix}{ext}")
                    if os.path.exists(file_path):
                        logger.info(f"Found downloaded file: {file_path} ({os.path.getsize(file_path)} bytes)")
                        return {
                            'success': True,
                            'file_path': file_path,
                            'title': title,
                            'type': 'audio' if quality == 'bestaudio' else 'video'
                        }
                
                # Fallback: search for any file containing the video ID
                for file in os.listdir(self.temp_dir):
                    if video_id in file and any(file.endswith(ext) for ext in expected_extensions):
                        file_path = os.path.join(self.temp_dir, file)
                        logger.info(f"Found downloaded file (fallback): {file_path} ({os.path.getsize(file_path)} bytes)")
                        return {
                            'success': True,
                            'file_path': file_path,
                            'title': title,
                            'type': 'audio' if quality == 'bestaudio' else 'video'
                        }
                
                return {'error': 'Download completed but file not found'}
                
        except Exception as e:
            logger.error(f"YouTube download error: {str(e)}")
            error_msg = str(e).lower()
            
            # Check for common authentication errors
            if any(keyword in error_msg for keyword in ['login', 'sign in', 'private', 'unavailable', 'members only', 'age-restricted']):
                if self.youtube_cookies.exists():
                    return {'error': 'Video requires authentication. Please update your YouTube cookies file.'}
                else:
                    return {'error': 'Video requires authentication. Please add your YouTube cookies file.'}
            elif 'requested format not available' in error_msg:
                return {'error': 'Requested video quality not available. Try a different quality option.'}
            else:
                return {'error': f'Download failed: {str(e)}'}
    
    async def download_instagram_content(self, url: str) -> dict:
        """Download Instagram content using yt-dlp"""
        try:
            # Configure yt-dlp options for Instagram
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': os.path.join(self.temp_dir, '%(id)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'writeinfojson': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            # Add Instagram cookies if the file exists
            if self.instagram_cookies.exists():
                ydl_opts['cookiefile'] = str(self.instagram_cookies)
                logger.info(f"Using Instagram cookies from: {self.instagram_cookies}")
            else:
                logger.warning("Instagram cookies file not found, proceeding without authentication")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Instagram_Video')
                video_id = info.get('id', 'instagram_video')
                
                # Download the content
                ydl.download([url])
                
                # Find the downloaded file using video ID
                expected_extensions = ['.mp4', '.webm', '.mkv']
                
                for ext in expected_extensions:
                    file_path = os.path.join(self.temp_dir, f"{video_id}{ext}")
                    if os.path.exists(file_path):
                        return {
                            'success': True,
                            'file_path': file_path,
                            'title': title,
                            'type': 'video'
                        }
                
                # Fallback: search for any recent video file
                for file in os.listdir(self.temp_dir):
                    if any(file.endswith(ext) for ext in expected_extensions):
                        file_path = os.path.join(self.temp_dir, file)
                        # Check if file was created recently (within last 30 seconds)
                        if os.path.getctime(file_path) > (time.time() - 30):
                            return {
                                'success': True,
                                'file_path': file_path,
                                'title': title,
                                'type': 'video'
                            }
                
                return {'error': 'Download completed but video file not found'}
            
        except Exception as e:
            logger.error(f"Instagram download error: {str(e)}")
            error_msg = str(e).lower()
            
            # Check for common authentication errors
            if any(keyword in error_msg for keyword in ['login', 'sign in', 'private', 'unavailable']):
                if self.instagram_cookies.exists():
                    return {'error': 'Content requires authentication. Please update your Instagram cookies file.'}
                else:
                    return {'error': 'Content requires authentication. Please add your Instagram cookies file.'}
            else:
                return {'error': f'Download failed: {str(e)}'}
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming URLs"""
        url = update.message.text.strip()
        
        # Check if it's a valid URL
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("Please send a valid URL starting with http:// or https://")
            return
        
        # Determine platform and show options
        if self.is_youtube_url(url):
            keyboard = [
                [InlineKeyboardButton("🎥 Best Quality (720p)", callback_data=f"yt_best_{url}")],
                [InlineKeyboardButton("🔥 1080p (Large File)", callback_data=f"yt_1080_{url}")],
                [InlineKeyboardButton("📱 720p", callback_data=f"yt_720_{url}")],
                [InlineKeyboardButton("📱 480p", callback_data=f"yt_480_{url}")],
                [InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data=f"yt_audio_{url}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Choose download quality:", reply_markup=reply_markup)
            
        elif self.is_instagram_url(url):
            await update.message.reply_text("📥 Starting Instagram download...")
            await self.process_instagram_download(update, url)
            
        else:
            await update.message.reply_text("❌ Unsupported URL. Please send a YouTube or Instagram link.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Button callback data: {data}")
        
        if data.startswith('yt_'):
            try:
                parts = data.split('_', 2)
                quality = parts[1]
                url = parts[2]
                logger.info(f"Parsed - Quality: {quality}, URL: {url[:50]}...")
            except IndexError as e:
                logger.error(f"Error parsing callback data: {e}")
                await query.edit_message_text("❌ Error: Invalid button data")
                return
            
            quality_map = {
                'best': '136+140/best[height<=720]/18',  # 720p+audio / best 720p / 360p fallback
                '1080': '137+140/best[height<=1080]',  # 1080p+audio / best 1080p
                '720': '136+140/best[height<=720]/134+140',  # 720p+audio / best 720p / 360p+audio
                '480': '135+140/best[height<=480]/134+140',  # 480p+audio / best 480p / 360p+audio
                'audio': 'bestaudio[ext=m4a]/bestaudio'
            }
            
            await query.edit_message_text("📥 Starting YouTube download...")
            await self.process_youtube_download(query, url, quality_map[quality])
    
    async def process_youtube_download(self, query, url: str, quality: str):
        """Process YouTube download"""
        try:
            # Send typing action
            await query.message.chat.send_action(ChatAction.UPLOAD_VIDEO)
            
            # Update message to show download progress
            await query.edit_message_text("📥 Downloading video... This may take a few minutes for large files.")
            
            # Download video with timeout (longer for large files)
            result = await asyncio.wait_for(
                self.download_youtube_video(url, quality), 
                timeout=300  # 5 minutes timeout for large downloads
            )
            
            if 'error' in result:
                await query.edit_message_text(f"❌ Error: {result['error']}")
                return
            
            # Send file
            file_path = result['file_path']
            file_size = os.path.getsize(file_path)
            
            await query.edit_message_text(f"✅ Downloaded! File size: {file_size / (1024*1024):.1f} MB. Format used: {quality}. Preparing upload...")
            
            # Check file size and warn if unexpected
            expected_sizes = {
                '480': 30,   # ~30MB for 480p
                '720': 50,   # ~50MB for 720p  
                'best': 50,  # ~50MB for 720p
                '1080': 150  # ~150MB for 1080p
            }
            
            # Extract quality from callback data safely
            try:
                quality_key = query.data.split('_')[1] if '_' in query.data else 'best'
            except (IndexError, AttributeError):
                quality_key = 'best'
            
            expected_mb = expected_sizes.get(quality_key, 50)
            if file_size > expected_mb * 1024 * 1024 * 1.5:  # 50% tolerance
                await query.edit_message_text(f"⚠️ Warning: File is larger than expected ({file_size / (1024*1024):.1f} MB vs ~{expected_mb} MB). Quality selection might have failed. Proceeding with upload...")
            
            # Check file size (Telegram limit is 50MB for bots, but we can try up to 2GB for users)
            max_size = 2 * 1024 * 1024 * 1024  # 2GB limit for regular users
            if file_size > max_size:
                await query.edit_message_text("❌ File is too large (>2GB). This video cannot be sent via Telegram.")
                return
            elif file_size > 50 * 1024 * 1024:
                # For files over 50MB, we need to send as document instead of video
                await query.edit_message_text(f"📤 File is large ({file_size / (1024*1024):.1f} MB). Uploading as document... Please wait, this may take several minutes.")
                
                try:
                    with open(file_path, 'rb') as file:
                        if result['type'] == 'audio':
                            # Remove timeout for uploads - let Telegram handle it
                            await query.message.reply_audio(
                                audio=file,
                                title=result['title'],
                                caption=f"🎵 {result['title']} ({file_size / (1024*1024):.1f} MB)"
                            )
                        else:
                            # Send as document for large videos - no timeout
                            await query.message.reply_document(
                                document=file,
                                caption=f"🎥 {result['title']} ({file_size / (1024*1024):.1f} MB)",
                                filename=f"{result['title'][:50]}.mp4"
                            )
                    
                    await query.edit_message_text("✅ Upload completed! Large file sent as document.")
                    
                except Exception as upload_error:
                    error_msg = str(upload_error)
                    logger.error(f"Large file upload error details: {error_msg}")
                    logger.error(f"Error type: {type(upload_error).__name__}")
                    
                    # Check if it's actually a timeout or another error
                    if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                        await query.edit_message_text(f"📤 Large file upload is taking longer than expected ({file_size / (1024*1024):.1f} MB). The file may still be uploading in the background. Please wait...")
                        # Don't return here - the upload might still succeed
                    else:
                        await query.edit_message_text(f"❌ Upload failed: {error_msg}. File: {file_size / (1024*1024):.1f} MB. Please try a lower quality.")
                        return
            else:
                # Normal upload for files under 50MB
                await query.edit_message_text(f"📤 Uploading to Telegram... ({file_size / (1024*1024):.1f} MB)")
                
                upload_success = False
                max_retries = 3
                
                for attempt in range(max_retries):
                    try:
                        with open(file_path, 'rb') as file:
                            if result['type'] == 'audio':
                                await query.message.reply_audio(
                                    audio=file,
                                    title=result['title'],
                                    caption=f"🎵 {result['title']}"
                                )
                            else:
                                await query.message.reply_video(
                                    video=file,
                                    caption=f"🎥 {result['title']}"
                                )
                        
                        upload_success = True
                        break  # Upload successful, exit retry loop
                        
                    except Exception as upload_error:
                        error_msg = str(upload_error)
                        logger.error(f"Upload attempt {attempt + 1} failed: {error_msg}")
                        logger.error(f"Error type: {type(upload_error).__name__}")
                        
                        # Check if it's a timeout and we should retry
                        if ("timeout" in error_msg.lower() or "timed out" in error_msg.lower()) and attempt < max_retries - 1:
                            await query.edit_message_text(f"📤 Upload attempt {attempt + 1} timed out. Retrying... ({file_size / (1024*1024):.1f} MB)")
                            await asyncio.sleep(2)  # Wait 2 seconds before retry
                            continue
                        else:
                            # Either not a timeout error or final attempt failed
                            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                                await query.edit_message_text(f"📤 Upload is taking longer than expected ({file_size / (1024*1024):.1f} MB). The file may still be uploading in the background. Please wait a moment...")
                                # Don't return here - give it some more time
                                await asyncio.sleep(10)  # Wait 10 seconds
                                # Check if file was actually uploaded by trying one more time
                                return
                            else:
                                await query.edit_message_text(f"❌ Upload failed: {error_msg}. File: {file_size / (1024*1024):.1f} MB.")
                                return
                
                if upload_success:
                    await query.edit_message_text("✅ Download completed!")
                else:
                    await query.edit_message_text(f"❌ Upload failed after {max_retries} attempts. File: {file_size / (1024*1024):.1f} MB. Please try again or use a lower quality.")
            
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors
            
        except asyncio.TimeoutError:
            await query.edit_message_text("❌ Download timed out after 5 minutes. The video is likely too large or connection is slow. Please try a lower quality (720p or 480p).")
        except Exception as e:
            logger.error(f"YouTube processing error: {str(e)}")
            logger.error(f"Query data: {query.data}")
            logger.error(f"Quality string: {quality}")
            await query.edit_message_text(f"❌ Error processing download: {str(e)}")
    
    async def process_instagram_download(self, update: Update, url: str):
        """Process Instagram download"""
        try:
            # Send typing action
            await update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)
            
            # Download content with timeout
            result = await asyncio.wait_for(
                self.download_instagram_content(url), 
                timeout=120  # 2 minutes timeout
            )
            
            if 'error' in result:
                await update.message.reply_text(f"❌ Error: {result['error']}")
                return
            
            # Send file
            file_path = result['file_path']
            file_size = os.path.getsize(file_path)
            
            # Check file size
            if file_size > 50 * 1024 * 1024:
                await update.message.reply_text("❌ File is too large (>50MB).")
                return
            
            try:
                with open(file_path, 'rb') as file:
                    await update.message.reply_video(
                        video=file,
                        caption=f"📱 {result['title']}"
                    )
                
                await update.message.reply_text("✅ Download completed!")
                
            except Exception as upload_error:
                logger.error(f"Instagram upload error: {str(upload_error)}")
                await update.message.reply_text(f"❌ Upload failed: {str(upload_error)}. File: {file_size / (1024*1024):.1f} MB.")
                return
            
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors
            
        except asyncio.TimeoutError:
            await update.message.reply_text("❌ Download timed out. Please try again.")
        except Exception as e:
            logger.error(f"Instagram processing error: {str(e)}")
            await update.message.reply_text(f"❌ Error processing download: {str(e)}")

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set!")
        return
    
    print("🚀 Starting Video Downloader Bot...")
    print("🔐 Checking cookie configuration...")
    
    # Create bot instance (this will trigger cookie setup and validation)
    bot = VideoDownloaderBot()
    
    # Log cookie status
    youtube_status = "✅ Available" if bot.youtube_cookies.exists() else "❌ Missing"
    instagram_status = "✅ Available" if bot.instagram_cookies.exists() else "❌ Missing"
    
    print(f"📺 YouTube cookies: {youtube_status}")
    print(f"📱 Instagram cookies: {instagram_status}")
    
    if not bot.youtube_cookies.exists() and not bot.instagram_cookies.exists():
        print("⚠️  No cookies found! Some videos may require authentication.")
        print("💡 Add YOUTUBE_COOKIES and INSTAGRAM_COOKIES environment variables for full functionality.")
    
    # Create application with custom timeouts
    from telegram.ext import ApplicationBuilder
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(60)  # 60 seconds read timeout
        .write_timeout(300)  # 5 minutes write timeout for uploads
        .connect_timeout(30)  # 30 seconds connect timeout
        .pool_timeout(30)  # 30 seconds pool timeout
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_url))
    
    # Start the bot
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
