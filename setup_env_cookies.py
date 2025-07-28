#!/usr/bin/env python3
"""
Cookie File to Environment Variable Converter
This script helps you convert your cookie files to environment variables for secure deployment.
"""

import os
from pathlib import Path

def read_cookie_file(file_path):
    """Read and return the content of a cookie file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None

def escape_for_env(content):
    """Escape content for environment variable usage"""
    # Replace newlines with \n for single-line env var
    return content.replace('\n', '\\n').replace('"', '\\"')

def main():
    script_dir = Path(__file__).parent
    youtube_cookies = script_dir / "youtube.com_cookies.txt"
    instagram_cookies = script_dir / "instagram.com_cookies.txt"
    
    print("🔐 Cookie File to Environment Variable Converter")
    print("=" * 50)
    
    # Process YouTube cookies
    if youtube_cookies.exists():
        youtube_content = read_cookie_file(youtube_cookies)
        if youtube_content:
            escaped_youtube = escape_for_env(youtube_content)
            print("\n📺 YouTube Cookies Environment Variable:")
            print("Add this to your Render environment variables:")
            print(f"YOUTUBE_COOKIES={escaped_youtube}")
            print(f"(Length: {len(escaped_youtube)} characters)")
    else:
        print("⚠️ YouTube cookies file not found")
    
    # Process Instagram cookies
    if instagram_cookies.exists():
        instagram_content = read_cookie_file(instagram_cookies)
        if instagram_content:
            escaped_instagram = escape_for_env(instagram_content)
            print("\n📱 Instagram Cookies Environment Variable:")
            print("Add this to your Render environment variables:")
            print(f"INSTAGRAM_COOKIES={escaped_instagram}")
            print(f"(Length: {len(escaped_instagram)} characters)")
    else:
        print("⚠️ Instagram cookies file not found")
    
    print("\n" + "=" * 50)
    print("🚀 Deployment Instructions:")
    print("1. Copy the environment variables above")
    print("2. Go to your Render dashboard")
    print("3. Navigate to your service settings")
    print("4. Add the environment variables in the 'Environment' section")
    print("5. Deploy your application")
    print("\n⚠️ IMPORTANT: Never commit cookie files to Git!")
    print("   The .gitignore file has been updated to prevent this.")

if __name__ == "__main__":
    main()
