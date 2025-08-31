from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# Правильный токен бота
BOT_TOKEN = "8129552663:AAGgaGHk0rOJ2R6aJ1rEdgvsiZxMBP6--cs"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Получаем информацию о боте для проверки валидности токена
        try:
            response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
            bot_info = response.json()
            
            self.wfile.write(json.dumps({
                'status': 'Testing token',
                'token_status': 'valid' if bot_info.get('ok') else 'invalid',
                'bot_info': bot_info
            }).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': str(e)
            }).encode())