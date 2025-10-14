#!/bin/bash

echo "🚀 Iniciando Streamlit en modo RÁPIDO..."

# Limpiar cache viejo
./scripts/cleanup_cache.sh

# Variables de optimización
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_RUNNER_FAST_RERUNS=true

# Iniciar con configuración optimizada
streamlit run app.py \
    --server.port=8501 \
    --server.headless=true \
    --server.runOnSave=false \
    --browser.gatherUsageStats=false \
    --logger.level=warning

echo "✅ Streamlit iniciado en modo RÁPIDO"