#!/bin/bash
echo "🧹 Звільнення порту 8000..."
# Зупиняємо всі процеси uvicorn
pkill -f uvicorn 2>/dev/null || echo "⚠️ Процеси uvicorn не знайдені"
# Додатково вбиваємо будь-який процес на порту 8000
if command -v lsof &> /dev/null; then
    lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "✅ Процес на порту 8000 зупинено" || echo "ℹ️ Порт 8000 вільний"
else
    echo "ℹ️ lsof не знайдено, пропускаємо додаткову перевірку"
fi
sleep 1
echo "🚀 Запуск веб-сервера..."
uvicorn src.interfaces.web:app --host 0.0.0.0 --port 8000 --reload &
echo "✅ Сервер запущено на http://localhost:8000"
