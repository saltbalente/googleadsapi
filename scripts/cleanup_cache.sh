#!/bin/bash

echo "🧹 Limpiando cache de Streamlit..."

# Limpiar cache de Streamlit
rm -rf ~/.streamlit/cache

# Limpiar pycache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Limpiar archivos .pyc
find . -type f -name "*.pyc" -delete

# Limpiar logs antiguos
find . -type f -name "*.log" -mtime +7 -delete

echo "✅ Limpieza completada"