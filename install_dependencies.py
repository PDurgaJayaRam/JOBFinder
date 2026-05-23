"""
Install all required dependencies for enhanced job matching features
Run this script to set up the new features
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    print("=" * 60)
    print("Installing Enhanced Job Matching Dependencies")
    print("=" * 60)
    print()
    
    packages = [
        "mistralai",
        "google-generativeai",
        "sentence-transformers",
        "python-docx",
        "reportlab",
        "pyautogui",
        "pillow",
        "opencv-python",
    ]
    
    for package in packages:
        try:
            install_package(package)
            print(f"✅ {package} installed successfully")
        except Exception as e:
            print(f"❌ Failed to install {package}: {e}")
    
    print()
    print("=" * 60)
    print("Installation Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Set up your API keys in .env file:")
    print("   MISTRAL_API_KEY=your_key_here")
    print("   GEMINI_API_KEY=your_key_here")
    print()
    print("2. Create new database tables:")
    print("   python create_new_tables.py")
    print()
    print("3. Start the server:")
    print("   python -m uvicorn api.main:app --reload")

if __name__ == "__main__":
    main()
