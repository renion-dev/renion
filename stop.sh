#!/bin/bash
echo "🛑 Зупинка веб-сервера..."
pkill -f uvicorn
echo "✅ Сервер зупинено"
