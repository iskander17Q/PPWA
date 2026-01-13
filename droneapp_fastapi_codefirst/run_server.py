#!/usr/bin/env python3
import os
import sys

# Ensure the app package in this directory is preferred on import
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn

if __name__ == "__main__":
    # Read PORT and RELOAD from environment if present
    port = int(os.environ.get("PORT", "8000"))
    reload_flag = os.environ.get("RELOAD", "false").lower() in ("1", "true", "yes")
    
    # For reload to work, we need to pass app as import string
    if reload_flag:
        uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
    else:
        from app.main import app
        uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
