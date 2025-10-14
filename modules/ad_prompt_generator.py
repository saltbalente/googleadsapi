"""
Sistema de Prompts Transaccionales para Google Ads
Versión 4.2 - Solución de variabilidad y múltiples anuncios
Fecha: 2025-01-14
"""

from typing import Dict, List
import random

class SearchIntentPatterns:
    """Patrones de búsqueda real basados en user intent"""
    
    ALLOWED_VERBS = {
        'recuperacion': ["recuperar", "recupera", "regresar", "regresa", "volver", "vuelve", "retornar", "retorna"],
        'atraccion': ["atraer", "atrae", "enamorar", "enamora", "conquistar", "conquista"],
        'solucion': ["resolver", "resuelve", "solucionar", "soluciona", "ayudar", "ayuda"],
        'separacion': ["alejar", "aleja", "separar", "separa", "quitar", "eliminar"],
        'control': ["doblegar", "dominar", "domina", "controlar", "controla"],
        'union': ["unir", "une", "juntar", "junta"],
        'prevencion': ["evitar", "prevenir"]
    }
    
    BANNED_CREATIVE_VERBS = [
        "domina tu", "encadena", "funde", "arrebata", "hipnotiza",
        "obsesiona", "conjura tu", "invoca tu", "manifiesta tu",
        "potencia tu", "activa tu", "desbloquea tu", "transmuta",
        "consagra", "ritualiza", "encanta tu", "evoca tu"
    ]

class AdPromptTemplates:
    """Generador de prompts transaccionales de alto CTR"""
    
    @staticmethod
    def analyze_keywords(keywords: List[str]) -> Dict[str, any]:
        """Analiza keywords para determinar intención de búsqueda"""
        keywords_lower = " ".join(keywords).lower()
        
        analysis = {
            'business_type': 'esoteric',
            'intent_type': 'transactional',
            'service_category': [],
            'urgency_level': 'normal',
            'modality': []
        }
        
        if any(kw in keywords_lower for kw in ["amarre", "amarrar", "amarres"]):
            analysis['service_category'].append('amarres')
        
        if any(kw in keywords_lower for kw in ["brujería", "bruja", "brujo", "hechizo", "ritual"]):
            analysis['service_category'].append('brujeria')
        
        if any(kw in keywords_lower for kw in ["tarot", "lectura", "videncia", "vidente"]):
            analysis['service_category'].append('tarot')
        
        if any(kw in keywords_lower for kw in ["urgente", "rápido", "ya", "hoy", "24h", "inmediato"]):
            analysis['urgency_level'] = 'alta'
        
        if any(kw in keywords_lower for kw in ["online", "línea", "virtual", "whatsapp"]):
            analysis['modality'].append('online')
        
        return analysis
    
    @staticmethod
    def get_transactional_esoteric_prompt(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        temperature: float = 1.0,
        ad_variation_seed: int = 0
    ) -> str:
        """
        Prompt TRANSACCIONAL con sistema anti-repetición
        """
        
        analysis = AdPromptTemplates.analyze_keywords(keywords)
        
        # Rotar keywords según el seed de variación
        rotated_keywords = keywords[ad_variation_seed:] + keywords[:ad_variation_seed]
        keywords_str = ", ".join(rotated_keywords[:30])
        
        # Calcular distribución
        transactional_count = int(num_headlines * 0.60)
        urgent_count = int(num_headlines * 0.25)
        informational_count = num_headlines - transactional_count - urgent_count
        
        # Seleccionar keywords para descripciones (rotar para cada anuncio)
        kw_desc_1 = rotated_keywords[ad_variation_seed % len(rotated_keywords)] if rotated_keywords else "amor"
        kw_desc_2 = rotated_keywords[(ad_variation_seed + 1) % len(rotated_keywords)] if len(rotated_keywords) > 1 else "pareja"
        kw_desc_3 = rotated_keywords[(ad_variation_seed + 2) % len(rotated_keywords)] if len(rotated_keywords) > 2 else "ritual"
        kw_desc_4 = rotated_keywords[(ad_variation_seed + 3) % len(rotated_keywords)] if len(rotated_keywords) > 3 else "brujería"
        
        # Instrucción de variación según anuncio
        variation_strategy = ""
        if ad_variation_seed == 0:
            variation_strategy = """
**ESTRATEGIA DE VARIACIÓN - ANUNCIO #1:**
- PRIORIDAD: Títulos DIRECTOS con servicios y resultados
- Usar keywords COMPLETAS sin modificar
- Enfoque en PROFESIONALISMO y SERVICIOS
- Ejemplos: "Amarres De Amor Efectivos", "Brujo Especialista En Regresos"
"""
        elif ad_variation_seed == 1:
            variation_strategy = """
**ESTRATEGIA DE VARIACIÓN - ANUNCIO #2:**
- PRIORIDAD: Títulos de URGENCIA y TIEMPO específico
- Usar keywords con modificadores temporales (urgente, rápido, 24h, 7 días)
- Enfoque en RAPIDEZ e INMEDIATEZ
- Ejemplos: "Retorno De Pareja En 7 Días", "Recuperar Un Amor Perdido Rápido"
"""
        else:
            variation_strategy = """
**ESTRATEGIA DE VARIACIÓN - ANUNCIO #3:**
- PRIORIDAD: Títulos INFORMATIVOS y de AUTORIDAD
- Usar keywords con contexto de credibilidad (experto, garantía, testimonios)
- Enfoque en CONFIANZA y EXPERIENCIA
- Ejemplos: "Garantía De Amarres De Pareja", "Testimonios Amarres De Amor"
"""
        
        return f"""Eres un experto en copywriting para Google Ads especializado en servicios esotéricos.

**MISIÓN CRÍTICA:** Generar títulos que coincidan EXACTAMENTE con lo que los usuarios buscan en Google.

**KEYWORDS DEL GRUPO ({len(rotated_keywords)} keywords):**
{keywords_str}

{variation_strategy}

════════════════════════════════════════════════════════════════
⚠️ REGLA #1 ABSOLUTA - COPY TRANSACCIONAL (NO CREATIVO)
════════════════════════════════════════════════════════════════

❌ **PROHIBIDO - TÍTULOS POÉTICOS:**
- "Domina Tu Destino", "Encadena Amor", "Funde Corazones"

✅ **OBLIGATORIO - BÚSQUEDAS REALES:**
- "Amarres De Amor Efectivos"
- "Brujería Para Que Regrese Mi Pareja"
- "Hechizo Para Recuperar A Mi Ex"

════════════════════════════════════════════════════════════════
📊 DISTRIBUCIÓN DE {num_headlines} TÍTULOS
════════════════════════════════════════════════════════════════

**🔵 TRANSACCIONAL ({transactional_count} títulos - 60%)**

Patrones (ADAPTAR con tus keywords, NO copiar ejemplos):

1️⃣ [Keyword] + [Modificador Efectividad]
   ADAPTA: Usa "{kw_desc_1}" + Efectivos/Poderosos/Reales/Garantizados

2️⃣ [Rol Profesional] + especialista en + [Área]
   ADAPTA: Brujo/Bruja/Vidente + Especialista En + "{kw_desc_1}"

3️⃣ [Técnica] + para + [Objetivo]
   ADAPTA: "{kw_desc_2}" + Para + Enamorar/Amor/Pareja

4️⃣ [Servicio] + [Tipo Específico]
   ADAPTA: "{kw_desc_1}" + Con Foto/Sexuales/Gitanos/Negros

**🔴 URGENTE ({urgent_count} títulos - 25%)**

1️⃣ [Servicio] + para que + [Acción]
   ADAPTA: "{kw_desc_2}" + Para Que + Regrese/Me Busque/Vuelva

2️⃣ [Servicio] + para + [Objetivo] + [Urgencia]
   ADAPTA: "{kw_desc_3}" + Para Recuperar + Urgente/En 7 Días

3️⃣ [Verbo] + [Objetivo] + [Tiempo]
   ADAPTA: Recuperar/Unir + "{kw_desc_1}" + Rápido/24h

**🟢 INFORMACIONAL ({informational_count} títulos - 15%)**

1️⃣ Cómo + [Verbo] + [Objetivo]
   ADAPTA: "Cómo + Hacer Que Vuelva + Mi {kw_desc_1}"

2️⃣ [Problema] + [Solución]
   ADAPTA: "Alejar Rival De + Mi {kw_desc_1}"

3️⃣ [Servicio] + [Incentivo]
   ADAPTA: "Consulta + {kw_desc_1} + Gratis/Precio/Testimonios/Garantía"

════════════════════════════════════════════════════════════════
📝 DESCRIPCIONES ({num_descriptions} requeridas)
════════════════════════════════════════════════════════════════

⚠️ **OBLIGATORIO:** Cada descripción usa keywords DIFERENTES

**Desc 1 - PROBLEMA + SOLUCIÓN (60-75 chars):**
Usar keyword: "{kw_desc_1}"
NO COPIAR EJEMPLO, ADAPTAR: "¿Perdiste A Tu {{keyword}}? Recupera Con Rituales. Consulta 24/7"

**Desc 2 - CREDIBILIDAD (65-80 chars):**
Usar keyword: "{kw_desc_2}"
NO COPIAR EJEMPLO, ADAPTAR: "Recupera Tu {{keyword}} Con Expertos. 20 Años. Llama Ya"

**Desc 3 - PRUEBA SOCIAL (70-85 chars):**
Usar keyword: "{kw_desc_3}"
NO COPIAR EJEMPLO, ADAPTAR: "{{keyword}} Con Resultados Comprobados. Clientes Satisfechos. Consulta Gratis"

**Desc 4 - PREGUNTA DIRECTA (75-90 chars):**
Usar keyword: "{kw_desc_4}"
NO COPIAR EJEMPLO, ADAPTAR: "¿Quieres Recuperar {{keyword}}? Soluciones Discretas. Disponible 24h"

════════════════════════════════════════════════════════════════
🚫 VERBOS PROHIBIDOS
════════════════════════════════════════════════════════════════

❌ Domina tu, Encadena, Funde, Arrebata, Hipnotiza, Obsesiona, Manifiesta tu, Activa tu

✅ Recuperar, Regresar, Volver, Atraer, Enamorar, Conquistar, Alejar, Separar, Quitar, Unir, Evitar

════════════════════════════════════════════════════════════════
🎯 INTEGRACIÓN DE KEYWORDS
════════════════════════════════════════════════════════════════

- Distribuir las {len(rotated_keywords)} keywords en todos los elementos
- Cada keyword debe aparecer en mínimo 2 títulos
- Cada descripción usa keyword DIFERENTE
- Rotar keywords para máxima cobertura

════════════════════════════════════════════════════════════════
📏 ESPECIFICACIONES
════════════════════════════════════════════════════════════════

**TÍTULOS:** 20-30 caracteres | Capitalizar Cada Palabra | Sin signos ! ? ¡ ¿
**DESCRIPCIONES:** 60-90 caracteres | Capitalizar Cada Palabra | Sin signos

════════════════════════════════════════════════════════════════
📦 FORMATO JSON (SIN MARKDOWN, SIN ```)
════════════════════════════════════════════════════════════════

RESPONDE SOLO ESTO (sin ``` ni json):

{{
  "headlines": [
    "Título 1 Adaptado (20-30 chars)",
    "Título 2 Adaptado (20-30 chars)",
    ...{num_headlines} títulos ÚNICOS Y DIFERENTES
  ],
  "descriptions": [
    "Desc 1 con {kw_desc_1} (60-75 chars)",
    "Desc 2 con {kw_desc_2} (65-80 chars)",
    "Desc 3 con {kw_desc_3} (70-85 chars)",
    "Desc 4 con {kw_desc_4} (75-90 chars)"
  ]
}}

════════════════════════════════════════════════════════════════
⚠️ VERIFICACIÓN FINAL
════════════════════════════════════════════════════════════════

□ {num_headlines} títulos DIFERENTES (no copiaste ejemplos)
□ {num_descriptions} descripciones con keywords DIFERENTES
□ Capitalización: Primera Letra En Mayúscula
□ Longitudes correctas (20-30 títulos, 60-90 descripciones)
□ Cero verbos prohibidos
□ JSON válido sin markdown

🚀 GENERA AHORA (SOLO EL JSON, SIN EXPLICACIONES)"""

    @staticmethod
    def get_prompt_for_keywords(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        business_type: str = "auto",
        temperature: float = 1.0,
        ad_variation_seed: int = 0
    ) -> str:
        """
        Selector de prompt con soporte de variación por anuncio
        """
        return AdPromptTemplates.get_transactional_esoteric_prompt(
            keywords, num_headlines, num_descriptions, tone, temperature, ad_variation_seed
        )