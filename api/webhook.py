from http.server import BaseHTTPRequestHandler
import json
import os
import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные переменные
telegram_app = None

def get_bot_token():
    """Получение токена бота из переменных окружения"""
    token = os.getenv('BOT_TOKEN')
    if not token:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    return token

async def init_telegram_app():
    """Инициализация Telegram Application"""
    global telegram_app
    
    if telegram_app is None:
        token = get_bot_token()
        telegram_app = Application.builder().token(token).build()
        
        # Добавляем базовые хендлеры
        telegram_app.add_handler(CommandHandler("start", handle_start))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        await telegram_app.initialize()
        
    return telegram_app

async def handle_start(update, context):
    """Обработка команды /start"""
    user = update.effective_user
    welcome_text = f"""🚀 Добро пожаловать в финансового бота!

👋 Привет, {user.first_name}!

💸 Введите расход в формате: "500 кофе"
📊 Или просто сумму: "500"

🎉 Бот работает на Vercel!"""
    
    await update.message.reply_text(welcome_text)

async def handle_message(update, context):
    """Базовая обработка сообщений"""
    message_text = update.message.text
    user_id = update.effective_user.id
    
    # Простой парсинг расходов
    if message_text.isdigit():
        # Только сумма
        amount = float(message_text)
        response = f"💰 Сумма: {amount} ₽\n\n🔍 Выберите категорию или добавьте описание"
    else:
        # Пытаемся парсить "сумма описание"
        parts = message_text.split()
        if len(parts) >= 2 and parts[0].replace('.', '', 1).isdigit():
            amount = float(parts[0])
            description = ' '.join(parts[1:])
            
            response = f"✅ Расход добавлен!\n\n💰 Сумма: {amount} ₽\n📝 Описание: {description}\n🏷️ Категория: Прочее"
        else:
            response = "❓ Не понял. Попробуйте: '500 кофе' или просто '500'"
    
    await update.message.reply_text(response)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Получаем длину контента
            content_length = int(self.headers['Content-Length'])
            # Чтение данных запроса
            post_data = self.rfile.read(content_length)
            
            # Обработка данных от Telegram
            update_dict = json.loads(post_data.decode('utf-8'))
            update = Update.de_json(update_dict, None)
            
            # Инициализация и обработка обновления
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            app_instance = loop.run_until_complete(init_telegram_app())
            loop.run_until_complete(app_instance.process_update(update))
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            # Отправляем ответ с ошибкой
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': str(e)
            }).encode())
    
    def do_GET(self):
        # Для проверки доступности API
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'status': 'active',
            'message': 'Telegram webhook is running',
            'timestamp': datetime.now().isoformat()
        }).encode())