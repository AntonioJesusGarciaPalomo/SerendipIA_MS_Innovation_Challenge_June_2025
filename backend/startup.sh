#!/bin/bash

echo "🚀 Iniciando aplicación RAG Document Upload en Azure App Service"
echo "📍 Directorio actual: $(pwd)"
echo "📁 Contenido directorio: $(ls -la)"

# Establecer variables de entorno para Python
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"
export PORT=${PORT:-8000}

# Verificar estructura de directorios
echo "🔍 Verificando estructura de directorios..."
find /home/site/wwwroot -type f -name "*.py" | head -10

# Verificar que main.py existe
if [ ! -f "/home/site/wwwroot/src/main.py" ]; then
    echo "❌ No se encontró /home/site/wwwroot/src/main.py"
    echo "📁 Contenido de src/: $(ls -la /home/site/wwwroot/src/ 2>/dev/null || echo 'Directorio no existe')"
    exit 1
fi

# Verificar archivos estáticos
echo "🎨 Verificando archivos estáticos..."
if [ -d "/home/site/wwwroot/src/static" ]; then
    echo "✅ Directorio static encontrado: $(ls -la /home/site/wwwroot/src/static | wc -l) archivos"
else
    echo "⚠️ No se encontró directorio static"
fi

# Instalar dependencias si es necesario
echo "📦 Verificando dependencias..."
cd /home/site/wwwroot
pip install --upgrade pip

# Verificar que las dependencias están instaladas
python -c "import fastapi, uvicorn, azure.storage.blob; print('✅ Dependencias principales OK')" || {
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
}

echo "🐍 Verificando importación del módulo principal..."
python -c "from src.main import app; print('✅ Aplicación importada correctamente')" || {
    echo "❌ Error importando aplicación"
    exit 1
}

echo "🚀 Iniciando servidor con Gunicorn..."
cd /home/site/wwwroot

# Usar Gunicorn con configuración optimizada para Azure App Service
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --keepalive 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload \
    src.main:app