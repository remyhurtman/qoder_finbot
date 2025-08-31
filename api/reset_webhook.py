from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', "8129552663:AAGgaGHk0rOJ2R6aJ1rEdgvsiZxMBP6--cs")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        self.wfile.write(json.dumps({
            'status': 'ready',
            'description': 'Используйте POST запрос для настройки webhook на простой обработчик',
            'instructions': 'Отправьте POST запрос для настройки'
        }).encode())
    
    def do_POST(self):
        try:
            # Определяем webhook URL для ПРОСТОГО обработчика
            host = self.headers.get('Host', '')
            webhook_url = f"https://{host}/api/webhook"
            
            # Удаляем существующий webhook
            delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
            delete_response = requests.post(delete_url)
            
            # Устанавливаем webhook с простым обработчиком
            telegram_api_url = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook'
            response = requests.post(
                telegram_api_url,
                json={'url': webhook_url},
                timeout=10
            )
            
            result = response.json()
            
            # Отправляем результат
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if result.get('ok'):
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': 'Webhook установлен на УПРОЩЕННЫЙ обработчик!',
                    'webhook_url': webhook_url,
                    'telegram_response': result
                }).encode())
            else:
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': result.get('description', 'Неизвестная ошибка'),
                    'telegram_response': result
                }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())