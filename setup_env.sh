#!/bin/bash

# ========================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ========================================

echo "🔧 Configurando variables de entorno para APIs de IA..."

# Solicitar API keys al usuario
echo ""
echo "📝 Por favor, ingresa tus API keys:"
echo ""

# OpenAI API Key
echo "🤖 OpenAI API Key (requerida para GPT-4, GPT-3.5):"
echo "   Obtén tu key en: https://platform.openai.com/api-keys"
read -p "   Ingresa tu OpenAI API Key: " OPENAI_KEY

# Gemini API Key (opcional)
echo ""
echo "🔴 Google Gemini API Key (opcional):"
echo "   Obtén tu key en: https://makersuite.google.com/app/apikey"
read -p "   Ingresa tu Gemini API Key (o presiona Enter para omitir): " GEMINI_KEY

# Anthropic API Key (opcional)
echo ""
echo "🟣 Anthropic Claude API Key (opcional):"
echo "   Obtén tu key en: https://console.anthropic.com/"
read -p "   Ingresa tu Anthropic API Key (o presiona Enter para omitir): " ANTHROPIC_KEY

# Crear archivo .env
echo ""
echo "📄 Creando archivo .env..."

cat > .env << EOF
# ========================================
# VARIABLES DE ENTORNO - GOOGLE ADS DASHBOARD
# ========================================

# ========================================
# GOOGLE ADS API
# ========================================
# Nota: Las credenciales de Google Ads deben estar en config/google-ads.yaml
# Este script solo configura las API keys de IA

# ========================================
# APIs DE IA
# ========================================
OPENAI_API_KEY=${OPENAI_KEY}
GEMINI_API_KEY=${GEMINI_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}

# ========================================
# CONFIGURACIÓN DE APLICACIÓN
# ========================================
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
SECRET_KEY=sk_prod_7K9mN2pQ8vX4wR6tY1uE3sA5bC9dF2gH8jL0mN4pQ7rT6yU9iO1eW3sD5fG8hJ2k
LOG_LEVEL=INFO
EOF

# Exportar variables para la sesión actual
export OPENAI_API_KEY="${OPENAI_KEY}"
export GEMINI_API_KEY="${GEMINI_KEY}"
export ANTHROPIC_API_KEY="${ANTHROPIC_KEY}"

echo "✅ Archivo .env creado exitosamente"
echo "✅ Variables exportadas para la sesión actual"
echo ""
echo "🚀 Ahora puedes reiniciar la aplicación con:"
echo "   source venv/bin/activate && streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
echo ""
echo "⚠️  IMPORTANTE: Nunca compartas tu archivo .env en repositorios públicos"
