#!/bin/bash
echo "🧹 Очищення порту 8000..."
pkill -f uvicorn 2>/dev/null || echo "Сервер не був запущений"
echo "🚀 Запуск веб-сервера..."
uvicorn src.interfaces.web:app --host 0.0.0.0 --port 8000 --reload &
echo "✅ Сервер запущено на http://localhost:8000"
