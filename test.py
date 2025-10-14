import os
from dotenv import load_dotenv
from modules.ai_ad_generator import AIAdGenerator

# Cargar variables de entorno
load_dotenv()

# Inicializar
generator = AIAdGenerator()

# ✅ Obtener API key del .env
API_KEY = os.getenv('OPENAI_API_KEY')

if not API_KEY:
    print("❌ Error: No se encontró OPENAI_API_KEY en .env")
    exit(1)

print(f"✅ API Key cargada: {API_KEY[:20]}...")

# ✅ CAMBIAR MODELO A GPT-4o
if not generator.set_provider('openai', api_key=API_KEY, model='gpt-4o'):  # ← CAMBIO AQUÍ
    print("❌ Error configurando OpenAI")
    exit(1)

print("✅ Proveedor OpenAI configurado correctamente")

# Resto del código igual...
result = generator.generate_batch(
    keywords=["amarres de amor", "brujería para pareja", "recuperar ex"],
    num_ads=3,
    num_headlines=15,
    num_descriptions=4,
    temperature=1.0,
    tone="profesional",
    business_type="esoteric",
    save_to_csv=True
)

# Ver resultados...
print(f"\n{'='*60}")
print(f"📊 RESULTADOS FINALES")
print(f"{'='*60}")
print(f"✅ Exitosos: {result['successful']}/{result['total_requested']}")
print(f"❌ Fallidos: {result['failed']}/{result['total_requested']}")
print(f"📈 Tasa de éxito: {result['success_rate']:.1f}%")
print(f"🏷️  Batch ID: {result['batch_id']}")

for ad in result['ads']:
    print(f"\n{'='*60}")
    print(f"📝 Anuncio #{ad.get('ad_number', '?')} de {ad.get('total_ads_in_batch', '?')}")
    print(f"{'='*60}")
    
    if 'error' in ad and ad['error']:
        print(f"❌ Error: {ad['error']}")
    else:
        print(f"✅ Títulos: {len(ad.get('headlines', []))}")
        print(f"✅ Descripciones: {len(ad.get('descriptions', []))}")
        
        # Mostrar 5 títulos de ejemplo
        print(f"\n📋 Primeros 5 títulos:")
        for i, h in enumerate(ad.get('headlines', [])[:5], 1):
            print(f"   {i}. {h} ({len(h)} chars)")
        
        # Mostrar 2 descripciones de ejemplo
        print(f"\n📝 Primeras 2 descripciones:")
        for i, d in enumerate(ad.get('descriptions', [])[:2], 1):
            print(f"   {i}. {d} ({len(d)} chars)")

print(f"\n{'='*60}")
print(f"✅ Test completado")
print(f"{'='*60}")