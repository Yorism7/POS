"""
GitHub Database Sync (NOT RECOMMENDED for Production)
This is for demonstration only - Use external database instead!

⚠️ WARNING: This approach has many limitations:
- Data is not real-time
- No concurrent access support
- Security issues
- Performance issues
- Not suitable for production

Use external database (PostgreSQL/MySQL) instead!
See STREAMLIT_CLOUD_DATABASE.md for proper setup.
"""

import os
import urllib.request
import json
from typing import Optional

def download_db_from_github(repo: str, branch: str = "main", db_path: str = "data/pos.db") -> Optional[str]:
    """
    Download database from GitHub repository
    
    ⚠️ NOT RECOMMENDED - Use external database instead!
    
    Args:
        repo: GitHub repository (format: "username/repo")
        branch: Branch name (default: "main")
        db_path: Path to database file in repo
    
    Returns:
        Local path to downloaded database or None if failed
    """
    # Construct GitHub raw URL
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{db_path}"
    
    # Download to /tmp (on Streamlit Cloud) or data/ (local)
    if os.path.exists("/tmp"):
        local_path = "/tmp/pos.db"
    else:
        local_path = "data/pos.db"
        os.makedirs("data", exist_ok=True)
    
    try:
        print(f"Downloading database from GitHub: {url}")
        urllib.request.urlretrieve(url, local_path)
        print(f"✅ Database downloaded to: {local_path}")
        return local_path
    except Exception as e:
        print(f"❌ Error downloading database: {e}")
        print("💡 Use external database (PostgreSQL/MySQL) instead!")
        return None

def upload_db_to_github(repo: str, token: str, db_path: str = "/tmp/pos.db") -> bool:
    """
    Upload database to GitHub using GitHub API
    
    ⚠️ NOT RECOMMENDED - Use external database instead!
    
    Args:
        repo: GitHub repository (format: "username/repo")
        token: GitHub personal access token
        db_path: Local path to database file
    
    Returns:
        True if successful, False otherwise
    """
    # This requires GitHub API and is complex
    # Not recommended - use external database instead!
    
    print("⚠️ Uploading database to GitHub is not recommended!")
    print("💡 Use external database (PostgreSQL/MySQL) instead!")
    return False

# Example usage (NOT RECOMMENDED):
# if __name__ == "__main__":
#     # Download database from GitHub
#     db_path = download_db_from_github("username/repo", "main", "data/pos.db")
#     if db_path:
#         print(f"Database available at: {db_path}")
#     else:
#         print("Failed to download database")

