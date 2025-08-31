# Инструкция по деплою Telegram бота на Vercel

## Подготовка

1. Убедитесь, что у вас есть токен бота от @BotFather
2. Имеется аккаунт на Vercel (https://vercel.com)

## Деплой проекта

### Через интерфейс Vercel

1. Откройте [Vercel Dashboard](https://vercel.com/dashboard)
2. Нажмите "Add New..." → "Project"
3. Импортируйте репозиторий или загрузите файлы
4. На странице настройки:
   - Установите фреймворк "Other"
   - Добавьте переменную окружения `BOT_TOKEN`
5. Нажмите "Deploy"

## Настройка webhook

После успешного деплоя необходимо настроить webhook:

1. Откройте в браузере:
   ```
   https://ваш-домен.vercel.app/api/set-webhook
   ```

2. Или используйте cURL:
   ```
   curl -X POST https://ваш-домен.vercel.app/api/set-webhook
   ```

## Проверка работы бота

1. Откройте чат с вашим ботом в Telegram
2. Отправьте команду `/start`
3. Попробуйте отправить сумму (например, "500")
4. Попробуйте отправить сумму и описание (например, "500 кофе")

## Сервисные эндпоинты

- `/health` - Статус здоровья в формате JSON
- `/api/webhook` (GET) - Статус активности webhook

## Типичные проблемы

1. **Ошибка 404 (NO_RESPONSE_FROM_FUNCTION)**:
   - Проверьте пути в `vercel.json`
   - Убедитесь, что файлы содержат класс `handler`

2. **Ошибка при сборке (FUNCTION_INVOCATION_FAILED)**:
   - Проверьте зависимости в `requirements.txt`

3. **Ошибка в работе webhook**:
   - Проверьте переменные окружения
   - Проверьте логи в консоли Vercel проект для минимальной проверки

3. **Timeout при деплое**:
   - Уменьшите размер зависимостей
   - Упростите код обработчиков

## Дополнительные ресурсы

- [Документация Vercel для Python](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Troubleshooting Serverless Functions](https://vercel.com/docs/functions/serverless-functions/troubleshooting)