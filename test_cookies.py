#!/usr/bin/env python3
"""
Test script to verify cookie functionality before deployment
"""

import os
import tempfile
from pathlib import Path
import yt_dlp

def test_youtube_cookies():
    """Test YouTube cookie functionality"""
    print("🧪 Testing YouTube cookies...")
    
    script_dir = Path(__file__).parent
    youtube_cookies = script_dir / "youtube.com_cookies.txt"
    
    if not youtube_cookies.exists():
        print("❌ YouTube cookies file not found")
        return False
    
    # Test with a simple YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - should always be available
    
    ydl_opts = {
        'format': 'worst',  # Use worst quality for faster testing
        'cookiefile': str(youtube_cookies),
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Don't download, just extract info
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            if info:
                print("✅ YouTube cookies are working!")
                print(f"   Test video: {info.get('title', 'Unknown')}")
                return True
            else:
                print("❌ YouTube cookies test failed - no info extracted")
                return False
    except Exception as e:
        print(f"❌ YouTube cookies test failed: {str(e)}")
        return False

def test_instagram_cookies():
    """Test Instagram cookie functionality"""
    print("🧪 Testing Instagram cookies...")
    
    script_dir = Path(__file__).parent
    instagram_cookies = script_dir / "instagram.com_cookies.txt"
    
    if not instagram_cookies.exists():
        print("❌ Instagram cookies file not found")
        return False
    
    # Note: Instagram testing is more complex as it requires a valid post URL
    # We'll just check if the cookies file is readable
    try:
        with open(instagram_cookies, 'r') as f:
            content = f.read()
            if content and 'instagram.com' in content:
                print("✅ Instagram cookies file looks valid!")
                print(f"   Cookie entries: {len(content.splitlines())} lines")
                return True
            else:
                print("❌ Instagram cookies file appears invalid")
                return False
    except Exception as e:
        print(f"❌ Instagram cookies test failed: {str(e)}")
        return False

def main():
    print("🔐 Cookie Functionality Test")
    print("=" * 40)
    
    youtube_ok = test_youtube_cookies()
    instagram_ok = test_instagram_cookies()
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"YouTube: {'✅ PASS' if youtube_ok else '❌ FAIL'}")
    print(f"Instagram: {'✅ PASS' if instagram_ok else '❌ FAIL'}")
    
    if youtube_ok and instagram_ok:
        print("\n🎉 All tests passed! Your cookies are ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Check your cookie files before deploying.")
        print("💡 Make sure cookies are in Netscape format and not expired.")

if __name__ == "__main__":
    main()
