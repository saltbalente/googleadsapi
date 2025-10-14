#!/bin/bash

echo "🚀 Google Ads Dashboard 2030 - Network Mode"
echo "================================================"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detectar IP
MAC_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)

if [ -z "$MAC_IP" ]; then
    echo -e "${RED}❌ No se pudo detectar la IP local${NC}"
    echo "   Verifica tu conexión WiFi/Ethernet"
    exit 1
fi

echo -e "${GREEN}📡 IP Local: $MAC_IP${NC}"
echo "🌐 Puerto: 8502"
echo "================================================"

# Verificar firewall
echo ""
echo "🔥 Verificando firewall..."
FW_STATUS=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate)

if [[ $FW_STATUS == *"enabled"* ]]; then
    echo -e "${YELLOW}⚠️  Firewall activo. Asegúrate de permitir Python${NC}"
    echo "   Ejecuta: sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python)"
fi

echo ""
echo "================================================"
echo -e "${GREEN}✅ URLs de acceso:${NC}"
echo ""
echo "   📱 Desde tu celular (misma WiFi):"
echo -e "   ${GREEN}http://$MAC_IP:8502${NC}"
echo ""
echo "   💻 Desde este Mac:"
echo "   http://localhost:8502"
echo ""
echo "================================================"

# Verificar qrencode
if command -v qrencode &> /dev/null; then
    echo ""
    echo "📱 Escanea este QR desde tu celular:"
    echo ""
    qrencode -t ANSIUTF8 "http://$MAC_IP:8502"
    echo ""
else
    echo ""
    echo "💡 Tip: Instala qrencode para ver un QR code"
    echo "   brew install qrencode"
fi

echo "================================================"
echo "🚀 Iniciando servidor..."
echo "   Presiona Ctrl+C para detener"
echo "================================================"
echo ""

# Iniciar Streamlit
streamlit run google_ads_dashboard2.py \
    --server.address=0.0.0.0 \
    --server.port=8502 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=true