#!/usr/bin/env python3
"""
Run script for Project Aegis backend
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    # Use standardized port 8000 for backend
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)