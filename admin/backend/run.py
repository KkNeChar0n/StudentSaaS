#!/usr/bin/env python
"""
Flask应用启动脚本
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    app.run(host=host, port=port, debug=debug)
