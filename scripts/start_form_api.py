#!/usr/bin/env python3
import sys
import os
sys.path.append('/app/src')
sys.path.append('/app')
import uvicorn
from api.enhanced_smartsheet_form_api import app

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8003, log_level='info', timeout_keep_alive=30, limit_concurrency=50)
