from http.server import BaseHTTPRequestHandler
import json
import os
import asyncio
import logging
import sqlite3
import traceback
from datetime import datetime
import re
from decimal import Decimal
from typing import Dict, Optional, Tuple, List, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Глобальные переменные
telegram_app = None
db_connection = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Категории расходов
CATEGORIES = [
    ["🍔 Еда", "🍺 Бары", "☕ Кофе", "🛍️ Магазины"],
    ["🚕 Транспорт", "🏠 Жилье", "📺 Развлечения", "💊 Здоровье"],
    ["💳 Подписки", "📚 Образование", "👕 Одежда", "🐶 Питомцы"],
    ["💻 Техника", "📡 Связь", "💁 Услуги", "🔎 Прочее"],
    ["💰 Доход", "💸 Инвестиции", "🎁 Подарки", "👠 Красота"]
]

# === КЛАСС РЕЗУЛЬТАТА ПАРСИНГА ===
class ParsedTransaction:
    """Результат парсинга транзакции"""
    def __init__(self, 
                 amount: Optional[float] = None,
                 description: Optional[str] = None,
                 category: Optional[str] = None,
                 level: int = 0,
                 confidence: float = 0.0):
        self.amount = amount
        self.description = description
        self.category = category
        self.level = level
        self.confidence = confidence

# === СИСТЕМА ПАРСИНГА ТРАНЗАКЦИЙ (4 УРОВНЯ) ===
class TransactionPipeline:
    """
    4-уровневая система парсинга и обработки транзакций
    
    Уровни:
    1. Простой парсинг числового ввода
    2. Парсинг строки формата "сумма описание"
    3. Определение категории по ключевым словам
    4. Заглушка для расширенного AI анализа
    """
    
    def __init__(self):
        # Словарь для определения категорий по ключевым словам
        self.category_keywords = {
            "🍔 Еда": ["еда", "продукты", "магазин", "супермаркет", "ашан", "пятерочка", "магнит", "перекресток"],
            "🍺 Бары": ["бар", "паб", "пиво", "алкоголь", "вино", "виски", "коктейль", "ресторан", "кафе"],
            "☕ Кофе": ["кофе", "капучино", "латте", "эспрессо", "старбакс", "кофейня", "чай"],
            "🚕 Транспорт": ["такси", "автобус", "метро", "проезд", "транспорт", "яндекс такси", "убер", "каршеринг", "бензин", "заправка"],
            "🏠 Жилье": ["аренда", "квартира", "коммуналка", "жкх", "счета", "ипотека", "квартплата"],
            "📺 Развлечения": ["кино", "театр", "концерт", "шоу", "музей", "выставка", "игры", "развлечения", "вечеринка"],
            "💊 Здоровье": ["аптека", "лекарства", "врач", "больница", "медицина", "стоматолог", "анализы"],
            "💳 Подписки": ["подписка", "сервис", "нетфликс", "spotify", "apple", "яндекс плюс", "subscription"],
            "📚 Образование": ["обучение", "курсы", "тренинг", "книги", "образование", "учеба"],
            "👕 Одежда": ["одежда", "обувь", "зара", "h&m", "спортмастер", "вещи", "шмотки"],
            "🐶 Питомцы": ["питомец", "собака", "кошка", "ветеринар", "корм", "зоомагазин"],
            "💻 Техника": ["техника", "гаджет", "ноутбук", "телефон", "электроника", "компьютер", "аксессуары"],
            "📡 Связь": ["связь", "интернет", "телефон", "мобильный", "сотовый", "wifi", "роутер"],
            "💁 Услуги": ["услуги", "стрижка", "маникюр", "салон", "химчистка", "ремонт", "клининг"],
            "💰 Доход": ["зарплата", "доход", "получил", "поступление", "перевод", "гонорар", "аванс"],
            "💸 Инвестиции": ["инвестиции", "акции", "биржа", "валюта", "крипта", "вклад", "депозит"],
            "🎁 Подарки": ["подарок", "поздравление", "презент", "сувенир", "подарил"],
            "👠 Красота": ["красота", "косметика", "макияж", "парфюм", "спа", "маска", "крем"],
            "🔎 Прочее": ["прочее", "разное", "другое", "misc", "other"]
        }
        
        # Расширенный словарь сленга и сокращений
        self.slang_dict = {
            "пятихатка": "500", "пятихатку": "500",
            "косарь": "1000", "косаря": "1000", "косарей": "1000",
            "полтинник": "50", "полтинника": "50",
            "сотка": "100", "сотку": "100", "сотни": "100",
            "червонец": "10", "червонца": "10",
            "пятерка": "5", "пятерку": "5",
            "десятка": "10", "десятку": "10",
            "стольник": "100", "стольника": "100",
            "полтос": "50", "полтоса": "50",
            "тыща": "1000", "тыщу": "1000", "тысяча": "1000",
            "штука": "1000", "штуку": "1000",
            "полтора": "1.5", "полторы": "1.5"
        }
    
    def level1_numeric_parse(self, text: str) -> ParsedTransaction:
        """Уровень 1: Обработка чисто числового ввода"""
        # Только число без описания
        if text.replace('.', '', 1).isdigit():
            try:
                amount = float(text.replace(',', '.'))
                return ParsedTransaction(
                    amount=amount,
                    description=None,
                    category=None,
                    level=1,
                    confidence=1.0
                )
            except ValueError:
                pass
        return None
    
    def level2_amount_description_parse(self, text: str) -> ParsedTransaction:
        """Уровень 2: Парсинг строки формата 'сумма описание'"""
        # Нормализация текста (замена сленга)
        for slang, number in self.slang_dict.items():
            text = re.sub(rf'\b{slang}\b', number, text.lower())
        
        # Паттерны для извлечения суммы и описания
        patterns = [
            # [Сумма] [Описание] - "500 кофе"
            r'^(\d+(?:[.,]\d{1,2})?)\s+(.+)$',
            # [Описание] [Сумма] - "такси 500"
            r'^(.+)\s+(\d+(?:[.,]\d{1,2})?)$',
            # [Сумма] на [Описание] - "500 на кофе"
            r'^(\d+(?:[.,]\d{1,2})?)\s+на\s+(.+)$',
            # [Описание] за [Сумма] - "кофе за 500"
            r'^(.+)\s+за\s+(\d+(?:[.,]\d{1,2})?)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                groups = match.groups()
                # Определяем, что является суммой, а что описанием
                for group in groups:
                    if re.match(r'^\d+(?:[.,]\d{1,2})?$', group):
                        amount_str = group
                        description = next((g for g in groups if g != group), "")
                        try:
                            amount = float(amount_str.replace(',', '.'))
                            return ParsedTransaction(
                                amount=amount,
                                description=description.strip(),
                                category=None,  # Категория определяется на уровне 3
                                level=2,
                                confidence=0.9
                            )
                        except ValueError:
                            continue
        
        return None
    
    def level3_category_determination(self, transaction: ParsedTransaction) -> ParsedTransaction:
        """Уровень 3: Определение категории по ключевым словам"""
        if not transaction or not transaction.description:
            return transaction
        
        # Копия транзакции для обновления
        result = ParsedTransaction(
            amount=transaction.amount,
            description=transaction.description,
            category=transaction.category,
            level=3,
            confidence=transaction.confidence
        )
        
        # Приведение к нижнему регистру для поиска
        description_lower = transaction.description.lower()
        
        # Поиск ключевых слов для определения категории
        best_match = None
        best_score = 0
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    score = len(keyword) / len(description_lower)  # Более длинные совпадения имеют больший вес
                    if score > best_score:
                        best_score = score
                        best_match = category
        
        if best_match:
            result.category = best_match
            result.confidence = min(0.7 + best_score, 0.95)  # Повышаем уверенность, но не выше 0.95
        else:
            result.category = "🔎 Прочее"  # Если категория не определена, используем "Прочее"
            result.confidence = 0.5  # Низкая уверенность для неопределенных категорий
        
        return result
    
    def level4_ai_enhanced_parsing(self, transaction: ParsedTransaction) -> ParsedTransaction:
        """
        Уровень 4: Заглушка для расширенного AI анализа
        В полной версии здесь был бы вызов AI для анализа транзакций
        """
        # В упрощенной версии просто возвращаем результат уровня 3
        if transaction:
            transaction.level = 4
        return transaction
    
    def process(self, text: str) -> ParsedTransaction:
        """Основной метод обработки - проходит все 4 уровня"""
        # Уровень 1: Числовой ввод
        result = self.level1_numeric_parse(text)
        
        # Уровень 2: Парсинг "сумма описание"
        if not result:
            result = self.level2_amount_description_parse(text)
        
        # Если уровни 1-2 не дали результата, возвращаем None
        if not result:
            return None
        
        # Уровень 3: Определение категории
        if result.description:  # Если есть описание, определяем категорию
            result = self.level3_category_determination(result)
        
        # Уровень 4: Расширенный анализ (заглушка)
        result = self.level4_ai_enhanced_parsing(result)
        
        return result

# === ФУНКЦИИ БАЗЫ ДАННЫХ ===
def init_database():
    """SQLite инициализация"""
    global db_connection
    try:
        # Для серверлесс функций используем in-memory БД
        db_connection = sqlite3.connect(':memory:')
        cursor = db_connection.cursor()
        
        # Создаем базовые таблицы
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS temp_amounts (
            user_id INTEGER PRIMARY KEY, 
            amount REAL, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        db_connection.commit()
        logger.info("SQLite база данных успешно инициализирована")
        return True
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        return False

def save_user(user_id, first_name, username=None):
    """Cохранение пользователя в БД"""
    try:
        if db_connection is None:
            init_database()
            
        cursor = db_connection.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, first_name, username) VALUES (?, ?, ?)",
            (user_id, first_name, username)
        )
        db_connection.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
        return False

def save_temp_amount(user_id, amount):
    """Cохранение временной суммы для выбора категории"""
    try:
        if db_connection is None:
            init_database()
            
        cursor = db_connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO temp_amounts (user_id, amount) VALUES (?, ?)",
            (user_id, amount)
        )
        db_connection.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения временной суммы: {e}")
        return False

def get_temp_amount(user_id):
    """Pетрив сохраненной суммы"""
    try:
        if db_connection is None:
            init_database()
            
        cursor = db_connection.cursor()
        cursor.execute("SELECT amount FROM temp_amounts WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Ошибка получения временной суммы: {e}")
        return None

def save_transaction(user_id, amount, category, description=None):
    """Cохранение транзакции в БД"""
    try:
        if db_connection is None:
            init_database()
            
        cursor = db_connection.cursor()
        cursor.execute(
            "INSERT INTO transactions (user_id, amount, category, description) VALUES (?, ?, ?, ?)",
            (user_id, amount, category, description)
        )
        db_connection.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения транзакции: {e}")
        return False

# === ФУНКЦИИ TELEGRAM БОТА ===
def get_bot_token():
    """Получение токена бота из переменных окружения"""
    # Пробуем получить токен из переменных окружения
    token = os.getenv('BOT_TOKEN')
    
    # Если токен не найден, используем жестко заданный токен
    if not token:
        logger.warning("Токен бота не найден в переменных окружения, используем заданный токен")
        token = "8129552663:AAGgaGHk0rOJ2R6aJ1rEdgvsiZxMBP6--cs"
    
    return token

def get_categories_keyboard():
    """Создание клавиатуры категорий"""
    keyboard = []
    
    for row_idx, row in enumerate(CATEGORIES):
        inline_row = []
        for col_idx, category in enumerate(row):
            callback_data = f"category_{row_idx}_{col_idx}"
            inline_row.append(InlineKeyboardButton(category, callback_data=callback_data))
        keyboard.append(inline_row)
    
    return InlineKeyboardMarkup(keyboard)

async def init_telegram_app():
    """Инициализация Telegram Application"""
    global telegram_app
    
    try:
        if telegram_app is None:
            token = get_bot_token()
            logger.info(f"Получен токен бота: {token[:5]}...")
            telegram_app = Application.builder().token(token).build()
            
            # Добавляем базовые хендлеры
            telegram_app.add_handler(CommandHandler("start", handle_start))
            telegram_app.add_handler(CommandHandler("stats", handle_stats))
            telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            telegram_app.add_handler(CallbackQueryHandler(handle_callback))
            
            await telegram_app.initialize()
            logger.info("Telegram Application успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации Telegram Application: {e}")
        logger.error(traceback.format_exc())
        raise e
        
    return telegram_app

async def handle_start(update, context):
    """Обработка команды /start"""
    try:
        user = update.effective_user
        user_id = user.id
        logger.info(f"Получена команда /start от пользователя {user_id}")
        
        # Сохраняем пользователя в БД
        save_user(user_id, user.first_name, user.username)
        
        # Прямой ответ для быстрого тестирования
        try:
            await update.message.reply_text("Привет! Я работаю. Идет загрузка меню...")
        except Exception as e:
            logger.error(f"Ошибка при отправке быстрого ответа: {e}")
        
        welcome_text = f"""🚀 Добро пожаловать в финансового бота!

👋 Привет, {user.first_name}!

💸 Введите расход в формате: "500 кофе"
📊 Или просто сумму: "500" для выбора категории

📈 /stats - посмотреть статистику расходов

🎉 Бот работает на Vercel!
✨ Полная 4-уровневая система парсинга"""
        
        await update.message.reply_text(welcome_text)
        logger.info(f"Отправлено приветственное сообщение пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка в handle_start: {e}")
        logger.error(traceback.format_exc())
        # Попытка отправить сообщение об ошибке
        try:
            if update and update.message:
                await update.message.reply_text("Произошла ошибка при обработке команды. Попробуйте еще раз.")
        except:
            pass

async def handle_stats(update, context):
    """Обработка команды /stats для статистики"""
    try:
        user = update.effective_user
        user_id = user.id
        logger.info(f"Получена команда /stats от пользователя {user_id}")
        
        # Заглушка для статистики (в полной версии была бы реальная статистика из БД)
        stats_text = f"""📊 Статистика расходов

🔄 Транзакций обработано: 0
💰 Всего потрачено: 0 ₽

🏆 Топ категорий:
1. Данные пока отсутствуют

⏳ В следующих обновлениях будет доступна полная статистика!"""
        
        await update.message.reply_text(stats_text)
        logger.info(f"Отправлена статистика пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка в handle_stats: {e}")

async def handle_message(update, context):
    """Обработка входящих сообщений"""
    try:
        message_text = update.message.text
        user = update.effective_user
        user_id = user.id
        logger.info(f"Получено сообщение от пользователя {user_id}: {message_text}")
        
        # Создаем экземпляр парсера транзакций
        transaction_pipeline = TransactionPipeline()
        
        # Обрабатываем сообщение через 4-уровневую систему
        parsed = transaction_pipeline.process(message_text)
        
        if parsed:
            # Если есть успешно распаршенная транзакция
            if parsed.level == 1 and not parsed.description:
                # Уровень 1: Только сумма - предлагаем выбрать категорию
                save_temp_amount(user_id, parsed.amount)
                response = f"💰 Сумма: {parsed.amount} ₽\n\n🔍 Выберите категорию:"
                await update.message.reply_text(response, reply_markup=get_categories_keyboard())
            else:
                # Уровень 2-4: Полная транзакция с описанием и категорией
                if parsed.category:
                    # Сохраняем транзакцию в БД
                    save_transaction(user_id, parsed.amount, parsed.category, parsed.description)
                    response = f"✅ Расход добавлен!\n\n💰 Сумма: {parsed.amount} ₽"
                    if parsed.description:
                        response += f"\n📝 Описание: {parsed.description}"
                    response += f"\n🏷️ Категория: {parsed.category}"
                    response += f"\n🔄 Уровень обработки: {parsed.level}"
                    await update.message.reply_text(response)
                else:
                    # Если категория не определена (не должно происходить)
                    save_temp_amount(user_id, parsed.amount)
                    response = f"💰 Сумма: {parsed.amount} ₽\n📝 Описание: {parsed.description}\n\n🔍 Выберите категорию:"
                    await update.message.reply_text(response, reply_markup=get_categories_keyboard())
        else:
            # Если парсинг не удался
            response = "❓ Не понял сообщение. Попробуйте формат '500 кофе' или просто '500'."
            await update.message.reply_text(response)
        
        logger.info(f"Отправлен ответ пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await update.message.reply_text("Произошла ошибка при обработке сообщения. Попробуйте еще раз.")

async def handle_callback(update, context):
    """Обработка callback запросов"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        callback_data = query.data
        logger.info(f"Получен callback от пользователя {user_id}: {callback_data}")
        
        # Обработка выбора категории
        if callback_data.startswith('category_'):
            # Извлекаем индексы категории
            _, row_idx, col_idx = callback_data.split('_')
            row_idx, col_idx = int(row_idx), int(col_idx)
            
            # Получаем название категории
            category = CATEGORIES[row_idx][col_idx]
            
            # Получаем сохраненную сумму
            amount = get_temp_amount(user_id)
            
            if amount is not None:
                # Сохраняем транзакцию
                save_transaction(user_id, amount, category)
                
                # Отправляем подтверждение
                response = f"✅ Расход добавлен!\n\n💰 Сумма: {amount} ₽\n🏷️ Категория: {category}"
                await query.edit_message_text(text=response)
            else:
                await query.answer("Произошла ошибка: сумма не найдена")
        else:
            await query.answer("Неизвестный callback")
            
    except Exception as e:
        logger.error(f"Ошибка в handle_callback: {e}")
        await update.callback_query.answer("Произошла ошибка. Попробуйте еще раз.")

# === HANDLER ДЛЯ VERCEL ===
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Получаем длину контента
            content_length = int(self.headers['Content-Length'])
            # Чтение данных запроса
            post_data = self.rfile.read(content_length)
            
            logger.info(f"Получен POST запрос с длиной контента: {content_length}")
            
            # Обработка данных от Telegram
            try:
                update_dict = json.loads(post_data.decode('utf-8'))
                logger.info(f"Получены данные от Telegram: {json.dumps(update_dict)[:200]}...")
                
                # Проверка наличия команды /start
                if "message" in update_dict and "text" in update_dict["message"] and update_dict["message"]["text"] == "/start":
                    logger.info("Обнаружена команда /start")
                
                update = Update.de_json(update_dict, None)
                
                # Инициализация и обработка обновления
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info("Инициализация Telegram Application")
                app_instance = loop.run_until_complete(init_telegram_app())
                logger.info("Обработка обновления Telegram")
                loop.run_until_complete(app_instance.process_update(update))
                logger.info("Обработка обновления Telegram завершена")
            except Exception as e:
                logger.error(f"Ошибка при обработке обновления Telegram: {e}")
                logger.error(traceback.format_exc())
                raise e
            
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
        
        # Информация о версии и состоянии
        response_data = {
            'status': 'active',
            'message': 'Telegram webhook is running',
            'timestamp': datetime.now().isoformat(),
            'features': '4-level transaction parsing system',
            'version': '1.1',
            'last_update': '2025-08-31',
            'env_variables': {
                'BOT_TOKEN': 'Available' if os.getenv('BOT_TOKEN') else 'Missing',
            }
        }
        
        self.wfile.write(json.dumps(response_data).encode())