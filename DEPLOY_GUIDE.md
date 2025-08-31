# Инструкция по деплою на Vercel

## Подготовка к деплою

1. Убедитесь, что у вас установлен Vercel CLI:
   ```
   npm install -g vercel
   ```

2. Авторизуйтесь в Vercel:
   ```
   vercel login
   ```

## Деплой проекта

### Способ 1: С использованием Vercel CLI

1. Перейдите в директорию проекта:
   ```
   cd /Users/dima.rothstein/Desktop/Remy/vercel_test
   ```

2. Запустите деплой:
   ```
   vercel
   ```

3. Следуйте инструкциям в интерактивном режиме.

### Способ 2: Через GitHub

1. Загрузите проект на GitHub:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <URL вашего GitHub репозитория>
   git push -u origin main
   ```

2. Импортируйте проект на Vercel через [vercel.com/new](https://vercel.com/new)

## Проверка деплоя

После успешного деплоя проверьте следующие эндпоинты:

- `/` - Должен вернуть "API is running successfully!"
- `/test` - Должен вернуть "Hello from Python on Vercel!"
- `/health` - Должен вернуть статус здоровья в формате JSON

## Распространенные проблемы и их решения

1. **Ошибка 404 (NO_RESPONSE_FROM_FUNCTION)**:
   - Проверьте, что пути в `vercel.json` точно соответствуют структуре файлов
   - Убедитесь, что все файлы имеют класс `handler` с методом `do_GET`

2. **Ошибка при сборке (FUNCTION_INVOCATION_FAILED)**:
   - Проверьте зависимости в `requirements.txt`
   - Упростите проект для минимальной проверки

3. **Timeout при деплое**:
   - Уменьшите размер зависимостей
   - Упростите код обработчиков

## Дополнительные ресурсы

- [Документация Vercel для Python](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Troubleshooting Serverless Functions](https://vercel.com/docs/functions/serverless-functions/troubleshooting)