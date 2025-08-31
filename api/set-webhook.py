from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Информация о сервисе установки webhook"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        self.wfile.write(json.dumps({
            'status': 'ready',
            'description': 'Используйте POST запрос для настройки webhook',
            'instructions': 'Отправьте POST запрос с webhook_url в теле запроса или оставьте пустым для автоматического определения URL'
        }).encode())
    
    def do_POST(self):
        """Установка webhook для Telegram бота"""
        try:
            # Получаем длину контента
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Пытаемся получить URL из запроса
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                webhook_url = request_data.get('webhook_url')
            except:
                webhook_url = None
            
            # Получаем токен бота
            bot_token = os.environ.get('BOT_TOKEN')
            if not bot_token:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'BOT_TOKEN не найден в переменных окружения'
                }).encode())
                return
            
            # Определяем webhook URL, если не предоставлен
            if not webhook_url:
                # Пытаемся использовать Vercel URL
                vercel_url = os.environ.get('VERCEL_URL')
                if vercel_url:
                    webhook_url = f"https://{vercel_url}/api/webhook"
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': 'Не указан webhook_url и не найден VERCEL_URL'
                    }).encode())
                    return
            
            # Устанавливаем webhook
            telegram_api_url = f'https://api.telegram.org/bot{bot_token}/setWebhook'
            response = requests.post(
                telegram_api_url,
                json={'url': webhook_url},
                timeout=10
            )
            
            result = response.json()
            
            if result.get('ok'):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': 'Webhook установлен успешно!',
                    'webhook_url': webhook_url,
                    'telegram_response': result
                }).encode())
            else:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
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