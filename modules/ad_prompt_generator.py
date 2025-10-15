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
        ad_variation_seed: int = 0,
        use_location_insertion: bool = False  # ✅ NUEVO parámetro
    ) -> str:
        """
        Prompt TRANSACCIONAL con sistema anti-repetición
        Soporta inserciones de ubicación para mejorar CTR
        """
        
        analysis = AdPromptTemplates.analyze_keywords(keywords)
        
        # Rotar keywords según el seed de variación
        rotated_keywords = keywords[ad_variation_seed:] + keywords[:ad_variation_seed]
        keywords_str = ", ".join(rotated_keywords[:30])
        
        # Calcular distribución
        # Si use_location_insertion está activo, reservar 3-5 títulos para ubicaciones
        location_count = 0
        if use_location_insertion:
            location_count = min(5, max(3, int(num_headlines * 0.25)))  # 3-5 títulos con ubicación
        
        remaining_headlines = num_headlines - location_count
        transactional_count = int(remaining_headlines * 0.60)
        urgent_count = int(remaining_headlines * 0.25)
        informational_count = remaining_headlines - transactional_count - urgent_count
        
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
        
        # ✅ Instrucciones de inserción de ubicación
        location_instructions = ""
        if use_location_insertion:
            location_instructions = f"""
════════════════════════════════════════════════════════════════
📍 INSERCIONES DE UBICACIÓN (OBLIGATORIO - {location_count} TÍTULOS)
════════════════════════════════════════════════════════════════

**IMPORTANTE:** Debes generar EXACTAMENTE {location_count} títulos con inserciones de ubicación.

**CÓDIGOS DE INSERCIÓN DISPONIBLES:**

1️⃣ **{{LOCATION(City)}}** - Inserta la ciudad del usuario
   Ejemplos:
   - "Curandero En {{LOCATION(City)}}"
   - "Amarres De Amor {{LOCATION(City)}}"
   - "Brujo Efectivo En {{LOCATION(City)}}"

2️⃣ **{{LOCATION(State)}}** - Inserta el estado/provincia
   Ejemplos:
   - "Brujos Especializados {{LOCATION(State)}}"
   - "Hechizos Reales En {{LOCATION(State)}}"
   - "Amarres Efectivos {{LOCATION(State)}}"

3️⃣ **{{LOCATION(Country)}}** - Inserta el país
   Ejemplos:
   - "Amarres En {{LOCATION(Country)}}"
   - "Servicios Esotéricos {{LOCATION(Country)}}"

**DISTRIBUCIÓN REQUERIDA:**
- {location_count} títulos CON inserción de ubicación
- Usar los 3 tipos: City ({location_count//3 + 1}), State ({location_count//3}), Country ({location_count//3})
- Los títulos con ubicación MEJORAN EL CTR hasta un 30%

**REGLAS PARA INSERCIONES:**
✅ Colocar la inserción al FINAL o EN MEDIO del título
✅ Mantener longitud total: 20-30 caracteres (contando el código)
✅ NO usar signos de puntuación cerca de las inserciones
✅ Capitalizar Cada Palabra excepto el código de inserción

**EJEMPLOS CORRECTOS:**
✅ "Brujo Profesional {{LOCATION(City)}}"
✅ "Amarres En {{LOCATION(State)}}"
✅ "Curandero Efectivo {{LOCATION(Country)}}"

**EJEMPLOS INCORRECTOS:**
❌ "Brujo En {{LOCATION(City)}}!" (signos de puntuación)
❌ "{{LOCATION(City)}}" (solo la inserción, falta keyword)
❌ "Brujo {{location(city)}}" (mal formato, debe ser mayúsculas)

════════════════════════════════════════════════════════════════
"""
        
        return f"""Eres un experto en copywriting para Google Ads especializado en servicios esotéricos.

**MISIÓN CRÍTICA:** Generar títulos que coincidan EXACTAMENTE con lo que los usuarios buscan en Google.

**KEYWORDS DEL GRUPO ({len(rotated_keywords)} keywords):**
{keywords_str}

{variation_strategy}

{location_instructions}

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

{"**📍 UBICACIÓN (" + str(location_count) + " títulos con inserciones)**" if use_location_insertion else ""}

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

════════════════════════════════════════════════════════════════
🚨 ADVERTENCIA CRÍTICA - LEER ANTES DE GENERAR
════════════════════════════════════════════════════════════════

❌ **PROHIBIDO ABSOLUTAMENTE:**
1. Copiar los ejemplos del prompt textualmente
2. Usar las mismas descripciones que los ejemplos
3. Repetir descripciones entre anuncios

✅ **OBLIGATORIO:**
1. ADAPTAR los ejemplos con TUS keywords reales
2. Cada descripción DEBE ser ÚNICA y DIFERENTE
3. Ninguna descripción puede repetirse

**EJEMPLO DE LO QUE NO DEBES HACER:**
❌ "¿Perdiste A Tu amor? Recupera Con Rituales. Consulta 24/7" (copiado del ejemplo)

**EJEMPLO DE LO QUE SÍ DEBES HACER:**
✅ "¿Tu Pareja Te Dejó? Amarres Efectivos De Retorno. Whatsapp 24h" (adaptado con keywords reales)

🚀 GENERA AHORA (SOLO EL JSON, SIN EXPLICACIONES)"""

    @staticmethod
    def get_prompt_for_keywords(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        business_type: str = "auto",
        temperature: float = 1.0,
        ad_variation_seed: int = 0,
        use_location_insertion: bool = False  # ✅ NUEVO parámetro
    ) -> str:
        """
        Selector de prompt con soporte de variación por anuncio y ubicaciones
        """
        return AdPromptTemplates.get_transactional_esoteric_prompt(
            keywords, num_headlines, num_descriptions, tone, temperature, ad_variation_seed, use_location_insertion
        )


class MagneticAdPrompts:
    """
    Prompts de alta intensidad psicológica para servicios esotéricos
    Modo MAGNÉTICO - Máxima conversión
    """
    
    @staticmethod
    def get_magnetic_prompt(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        temperature: float = 0.9,
        ad_variation_seed: int = 0,
        use_location_insertion: bool = False  # ✅ NUEVO parámetro
    ) -> str:
        """
        Prompt MAGNÉTICO de alta intensidad psicológica
        Diseñado para máxima conversión en servicios esotéricos
        Soporta inserciones de ubicación para mejorar CTR
        """
        
        # Rotar keywords según el seed de variación
        rotated_keywords = keywords[ad_variation_seed:] + keywords[:ad_variation_seed]
        keywords_str = ", ".join(rotated_keywords[:30])
        
        # Distribución magnética optimizada
        # Si use_location_insertion está activo, reservar 3-5 títulos para ubicaciones
        location_count = 0
        if use_location_insertion:
            location_count = min(5, max(3, int(num_headlines * 0.25)))  # 3-5 títulos con ubicación
        
        remaining_headlines = num_headlines - location_count
        beneficio_urgencia = int(remaining_headlines * 0.33)  # ~33%
        credibilidad_exclusividad = int(remaining_headlines * 0.33)  # ~33%
        control_curiosidad = remaining_headlines - beneficio_urgencia - credibilidad_exclusividad  # ~33%
        
        # Keywords específicas para cada descripción
        kw_desc_1 = rotated_keywords[ad_variation_seed % len(rotated_keywords)] if rotated_keywords else "amor"
        kw_desc_2 = rotated_keywords[(ad_variation_seed + 1) % len(rotated_keywords)] if len(rotated_keywords) > 1 else "pareja"
        kw_desc_3 = rotated_keywords[(ad_variation_seed + 2) % len(rotated_keywords)] if len(rotated_keywords) > 2 else "ritual"
        kw_desc_4 = rotated_keywords[(ad_variation_seed + 3) % len(rotated_keywords)] if len(rotated_keywords) > 3 else "brujería"
        
        # ✅ Instrucciones de inserción de ubicación (igual que en el prompt transaccional)
        location_instructions = ""
        if use_location_insertion:
            location_instructions = f"""
════════════════════════════════════════════════════════════════
📍 INSERCIONES DE UBICACIÓN MAGNÉTICAS ({location_count} TÍTULOS)
════════════════════════════════════════════════════════════════

**OBLIGATORIO:** Generar {location_count} títulos con MÁXIMA INTENSIDAD + ubicación.

**CÓDIGOS DE INSERCIÓN:**
- 🏙️ **{{LOCATION(City)}}** - Ciudad
- 🗺️ **{{LOCATION(State)}}** - Estado/Provincia  
- 🌍 **{{LOCATION(Country)}}** - País

**EJEMPLOS MAGNÉTICOS CON UBICACIÓN:**
✅ "Urgente Brujo {{LOCATION(City)}}"
✅ "Amarres Garantizados {{LOCATION(State)}}"
✅ "Único Especialista {{LOCATION(Country)}}"

**DISTRIBUCIÓN:**
- {location_count//3 + 1} con City
- {location_count//3} con State
- {location_count//3} con Country

════════════════════════════════════════════════════════════════
"""
        
        return f"""Eres un experto en copywriting MAGNÉTICO para Google Ads especializado en servicios esotéricos de alta conversión.

**MISIÓN CRÍTICA:** Generar anuncios con MÁXIMA INTENSIDAD PSICOLÓGICA que generen acción inmediata.

**KEYWORDS DEL GRUPO ({len(rotated_keywords)} keywords):**
{keywords_str}

🔴 MODO MAGNÉTICO ACTIVADO - ALTA INTENSIDAD PSICOLÓGICA 🔴

{location_instructions}

════════════════════════════════════════════════════════════════
⚡ DISTRIBUCIÓN MAGNÉTICA DE {num_headlines} TÍTULOS
════════════════════════════════════════════════════════════════

**🎯 BENEFICIO + URGENCIA ({beneficio_urgencia} títulos)**
Patrones de alta conversión:

1️⃣ [Keyword] + [Resultado Inmediato] + [Tiempo]
   ADAPTA: "{kw_desc_1}" + En 24 Horas/7 Días/Esta Semana

2️⃣ [Problema] + [Solución Definitiva]
   ADAPTA: "Perdiste {kw_desc_2}? Recupera Ya"

3️⃣ [Acción] + [Beneficio] + [Garantía]
   ADAPTA: "Recupera {kw_desc_1} Garantizado"

4️⃣ [Urgencia] + [Servicio] + [Resultado]
   ADAPTA: "Urgente {kw_desc_2} Que Funciona"

5️⃣ [Tiempo] + para + [Objetivo]
   ADAPTA: "7 Días Para Recuperar {kw_desc_1}"

**🏆 CREDIBILIDAD + EXCLUSIVIDAD ({credibilidad_exclusividad} títulos)**
Patrones de autoridad:

1️⃣ [Años] + Años + [Especialidad]
   ADAPTA: "20 Años En {kw_desc_1}"

2️⃣ [Número] + Casos + [Resultado]
   ADAPTA: "500 Casos De {kw_desc_2} Exitosos"

3️⃣ [Rol] + Certificado + [Área]
   ADAPTA: "Brujo Certificado En {kw_desc_1}"

4️⃣ [Exclusividad] + [Servicio]
   ADAPTA: "Único Especialista En {kw_desc_2}"

5️⃣ [Garantía] + [Servicio] + [Resultado]
   ADAPTA: "Garantía Total {kw_desc_1}"

**🧠 CONTROL + CURIOSIDAD ({control_curiosidad} títulos)**
Patrones psicológicos:

1️⃣ [Secreto] + [Técnica] + [Resultado]
   ADAPTA: "Secreto Para {kw_desc_1} Efectivo"

2️⃣ [Método] + Que + [Autoridades] + [Acción]
   ADAPTA: "Método Que Brujos Usan Para {kw_desc_2}"

3️⃣ [Descubrimiento] + [Beneficio]
   ADAPTA: "Descubre Cómo {kw_desc_1} Funciona"

4️⃣ [Razón] + Por Qué + [Problema]
   ADAPTA: "Por Qué {kw_desc_2} No Funciona"

5️⃣ [Técnica] + [Resultado] + Sin + [Obstáculo]
   ADAPTA: "{kw_desc_1} Sin Fallar"

════════════════════════════════════════════════════════════════
🔥 DESCRIPCIONES MAGNÉTICAS ({num_descriptions} requeridas)
════════════════════════════════════════════════════════════════

**Desc 1 - DOLOR + SOLUCIÓN INMEDIATA (60-75 chars):**
Keyword: "{kw_desc_1}"
Patrón: "¿[Problema]? [Solución] En [Tiempo]. [Acción]"
ADAPTA: "¿Perdiste Tu {{keyword}}? Recupera En 7 Días. Consulta Ya"

**Desc 2 - AUTORIDAD + PRUEBA (65-80 chars):**
Keyword: "{kw_desc_2}"
Patrón: "[Experiencia] En [Área]. [Resultado]. [Contacto]"
ADAPTA: "20 Años En {{keyword}}. Resultados Garantizados. Llama 24h"

**Desc 3 - EXCLUSIVIDAD + URGENCIA (70-85 chars):**
Keyword: "{kw_desc_3}"
Patrón: "[Único] [Método] Para [Resultado]. [Limitación] [Acción]"
ADAPTA: "Único Método Para {{keyword}} Efectivo. Solo Hoy. Consulta Gratis"

**Desc 4 - CURIOSIDAD + ACCIÓN (75-90 chars):**
Keyword: "{kw_desc_4}"
Patrón: "[Secreto] Que [Expertos] No Quieren Que Sepas. [Acción]"
ADAPTA: "Secreto De {{keyword}} Que Brujos No Revelan. Descúbrelo Ahora"

════════════════════════════════════════════════════════════════
🚫 PALABRAS MAGNÉTICAS PERMITIDAS
════════════════════════════════════════════════════════════════

✅ PODER: Efectivo, Poderoso, Real, Garantizado, Comprobado, Infalible
✅ TIEMPO: Inmediato, Rápido, 24h, 7 días, Urgente, Ya, Ahora
✅ EXCLUSIVIDAD: Único, Secreto, Especial, Exclusivo, Privado
✅ AUTORIDAD: Experto, Maestro, Certificado, Profesional, Años
✅ RESULTADO: Garantizado, Seguro, Efectivo, Comprobado, Real

════════════════════════════════════════════════════════════════
🎯 INTEGRACIÓN MAGNÉTICA DE KEYWORDS
════════════════════════════════════════════════════════════════

- Cada keyword debe generar DESEO INMEDIATO
- Usar modificadores de INTENSIDAD (muy, súper, ultra, mega)
- Combinar con EMOCIONES (amor, pasión, deseo, necesidad)
- Agregar URGENCIA temporal (hoy, ya, ahora, inmediato)

════════════════════════════════════════════════════════════════
📏 ESPECIFICACIONES MAGNÉTICAS
════════════════════════════════════════════════════════════════

**TÍTULOS:** 20-30 caracteres | Capitalizar Cada Palabra | SIN signos ! ? ¡ ¿
**DESCRIPCIONES:** 60-90 caracteres | Capitalizar Cada Palabra | SIN signos

════════════════════════════════════════════════════════════════
📦 FORMATO JSON MAGNÉTICO (SIN MARKDOWN, SIN ```)
════════════════════════════════════════════════════════════════

RESPONDE SOLO ESTO (sin ``` ni json):

{{
  "headlines": [
    "Título Magnético 1 (20-30 chars)",
    "Título Magnético 2 (20-30 chars)",
    ...{num_headlines} títulos ÚNICOS con MÁXIMA INTENSIDAD
  ],
  "descriptions": [
    "Desc magnética 1 con {kw_desc_1} (60-75 chars)",
    "Desc magnética 2 con {kw_desc_2} (65-80 chars)",
    "Desc magnética 3 con {kw_desc_3} (70-85 chars)",
    "Desc magnética 4 con {kw_desc_4} (75-90 chars)"
  ]
}}

════════════════════════════════════════════════════════════════
🔥 VERIFICACIÓN MAGNÉTICA FINAL
════════════════════════════════════════════════════════════════

□ {num_headlines} títulos con MÁXIMA INTENSIDAD PSICOLÓGICA
□ {num_descriptions} descripciones que generan ACCIÓN INMEDIATA
□ Cada elemento provoca DESEO y URGENCIA
□ Keywords integradas con PODER EMOCIONAL
□ JSON válido sin markdown
□ CERO palabras débiles o genéricas

🚀 GENERA ANUNCIOS MAGNÉTICOS AHORA (SOLO EL JSON, SIN EXPLICACIONES)"""