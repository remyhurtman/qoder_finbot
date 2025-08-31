from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import traceback

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', "8129552663:AAGgaGHk0rOJ2R6aJ1rEdgvsiZxMBP6--cs")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Получаем длину контента
            content_length = int(self.headers['Content-Length'])
            # Чтение данных запроса
            post_data = self.rfile.read(content_length)
            
            # Обработка данных от Telegram
            update_dict = json.loads(post_data.decode('utf-8'))
            
            # Проверка наличия сообщения
            if 'message' in update_dict and 'text' in update_dict['message']:
                chat_id = update_dict['message']['chat']['id']
                text = update_dict['message']['text']
                
                # Прямой ответ через Telegram API
                if text == '/start':
                    response_text = """🚀 Бот успешно запущен!
                    
👋 Привет! Я финансовый бот.

💸 Введите расход в формате: "500 кофе"
📊 Или просто сумму: "500" для выбора категории

📈 /stats - посмотреть статистику расходов

🎉 Бот работает на Vercel!
✨ Полная 4-уровневая система парсинга"""
                    
                    # Отправляем сообщение напрямую через API
                    send_message_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": response_text
                    }
                    requests.post(send_message_url, json=payload)
                    
                elif text.isdigit():
                    # Если введено только число
                    amount = float(text)
                    response_text = f"💰 Сумма: {amount} ₽\n\n🔍 Выберите категорию или добавьте описание"
                    
                    # Отправляем сообщение напрямую через API
                    send_message_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": response_text
                    }
                    requests.post(send_message_url, json=payload)
                
                else:
                    # Простой парсинг "сумма описание"
                    parts = text.split()
                    if len(parts) >= 2 and parts[0].replace('.', '', 1).isdigit():
                        amount = float(parts[0])
                        description = ' '.join(parts[1:])
                        
                        response_text = f"✅ Расход добавлен!\n\n💰 Сумма: {amount} ₽\n📝 Описание: {description}\n🏷️ Категория: Прочее"
                    else:
                        response_text = "❓ Не понял. Попробуйте: '500 кофе' или просто '500'"
                    
                    # Отправляем сообщение напрямую через API
                    send_message_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": response_text
                    }
                    requests.post(send_message_url, json=payload)
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            
        except Exception as e:
            # Детальное логирование ошибки
            error_details = traceback.format_exc()
            
            # Отправляем ответ с ошибкой
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': str(e),
                'details': error_details
            }).encode())
    
    def do_GET(self):
        # Для проверки доступности API
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Информация о версии и состоянии
        response_data = {
            'status': 'active',
            'message': 'Simplified Telegram webhook is running',
            'timestamp': 'now',
            'bot_token_status': 'Available' if BOT_TOKEN else 'Missing',
            'version': 'v1.2 (ultra-simple)'
        }
        
        self.wfile.write(json.dumps(response_data).encode())