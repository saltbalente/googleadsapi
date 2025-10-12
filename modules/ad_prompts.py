"""
Sistema Avanzado de Prompts Especializados para Generación de Anuncios
Versión 2.0 - Optimizado para máxima conversión y cumplimiento de políticas
"""

from typing import Dict, List, Tuple
import re

class AdPromptTemplates:
    """Plantillas de prompts especializadas por tipo de negocio con IA contextual"""
    
    # ==================== ANÁLISIS INTELIGENTE DE KEYWORDS ====================
    
    @staticmethod
    def analyze_keywords(keywords: List[str]) -> Dict[str, any]:
        """
        Analiza las keywords para extraer intención, contexto y oportunidades
        
        Returns:
            Dict con análisis completo de las keywords
        """
        keywords_lower = " ".join(keywords).lower()
        
        analysis = {
            'business_type': 'generic',
            'intent': [],
            'emotion_level': 'medio',
            'urgency_type': 'normal',
            'pain_points': [],
            'solutions': [],
            'service_modality': [],
            'target_audience': 'general',
            'competitive_angle': []
        }
        
        # Detectar tipo de negocio
        if any(kw in keywords_lower for kw in [
            "amarre", "amarrar", "hechizo", "brujería", "magia",
            "tarot", "videncia", "brujo", "bruja", "ritual"
        ]):
            analysis['business_type'] = 'esoteric'
            
            # Sub-categorías esotéricas
            if any(kw in keywords_lower for kw in ["amarre", "amarrar", "amor", "pareja"]):
                analysis['intent'].append('recuperar_amor')
                analysis['emotion_level'] = 'alto'
                analysis['pain_points'] = ['pérdida amorosa', 'ruptura', 'distancia emocional']
                analysis['solutions'] = ['amarres efectivos', 'rituales de amor', 'unión espiritual']
            
            if any(kw in keywords_lower for kw in ["tarot", "lectura", "cartas", "videncia"]):
                analysis['intent'].append('buscar_respuestas')
                analysis['emotion_level'] = 'medio'
                analysis['pain_points'] = ['incertidumbre', 'dudas', 'necesidad de claridad']
                analysis['solutions'] = ['respuestas claras', 'orientación', 'visión del futuro']
            
            if any(kw in keywords_lower for kw in ["limpia", "limpieza", "protección", "negatividad"]):
                analysis['intent'].append('proteccion_energia')
                analysis['pain_points'] = ['mala suerte', 'energías negativas', 'bloqueos']
                analysis['solutions'] = ['limpieza profunda', 'protección espiritual', 'renovación']
        
        # Detectar modalidad de servicio
        if any(kw in keywords_lower for kw in ["online", "línea", "virtual", "whatsapp"]):
            analysis['service_modality'].append('online')
        
        if any(kw in keywords_lower for kw in ["rápido", "urgente", "inmediato", "24h", "hoy"]):
            analysis['urgency_type'] = 'alta'
        
        # Detectar audiencia objetivo
        if any(kw in keywords_lower for kw in ["mujer", "femenino", "ella"]):
            analysis['target_audience'] = 'mujeres'
        elif any(kw in keywords_lower for kw in ["hombre", "masculino", "él"]):
            analysis['target_audience'] = 'hombres'
        
        # Ángulos competitivos
        if any(kw in keywords_lower for kw in ["efectivo", "real", "verdadero", "funciona"]):
            analysis['competitive_angle'].append('efectividad_comprobada')
        
        if any(kw in keywords_lower for kw in ["barato", "económico", "precio"]):
            analysis['competitive_angle'].append('precio_accesible')
        
        if any(kw in keywords_lower for kw in ["experto", "profesional", "maestro"]):
            analysis['competitive_angle'].append('experiencia_profesional')
        
        return analysis
    
    # ==================== GENERADORES DE COMPONENTES ====================
    
    @staticmethod
    def get_power_verbs(business_type: str, intent: List[str]) -> List[str]:
        """Retorna verbos de acción ultra-potentes según contexto"""
        
        verbs = {
            'esoteric_amor': [
                "Recupera", "Regresa", "Atrae", "Conquista", "Enamora",
                "Une", "Enlaza", "Hechiza", "Embruja", "Retorna"
            ],
            'esoteric_respuestas': [
                "Descubre", "Revela", "Conoce", "Consulta", "Aclara",
                "Anticipa", "Visualiza", "Conecta", "Pregunta"
            ],
            'esoteric_proteccion': [
                "Protege", "Limpia", "Libera", "Desbloquea", "Renueva",
                "Fortalece", "Sana", "Purifica", "Neutraliza"
            ],
            'generic': [
                "Consigue", "Obtén", "Descubre", "Aprovecha", "Mejora",
                "Aumenta", "Optimiza", "Transforma", "Alcanza"
            ]
        }
        
        if business_type == 'esoteric':
            if 'recuperar_amor' in intent:
                return verbs['esoteric_amor']
            elif 'buscar_respuestas' in intent:
                return verbs['esoteric_respuestas']
            elif 'proteccion_energia' in intent:
                return verbs['esoteric_proteccion']
        
        return verbs['generic']
    
    @staticmethod
    def get_urgency_phrases(urgency_type: str, modality: List[str]) -> List[str]:
        """Frases de urgencia calibradas según tipo"""
        
        if urgency_type == 'alta':
            base = ["ahora", "hoy", "24h", "inmediato", "urgente"]
        else:
            base = ["disponible", "rápido", "pronto", "efectivo"]
        
        if 'online' in modality:
            base.extend(["online", "en línea", "por WhatsApp"])
        
        return base
    
    @staticmethod
    def get_credibility_markers(competitive_angle: List[str]) -> List[str]:
        """Marcadores de credibilidad según ventaja competitiva"""
        
        markers = []
        
        if 'efectividad_comprobada' in competitive_angle:
            markers.extend([
                "Resultados reales",
                "Clientes satisfechos",
                "Métodos comprobados"
            ])
        
        if 'experiencia_profesional' in competitive_angle:
            markers.extend([
                "Años de experiencia",
                "Experto certificado",
                "Maestro reconocido"
            ])
        
        if 'precio_accesible' in competitive_angle:
            markers.extend([
                "Precios accesibles",
                "Primera consulta gratis",
                "Sin cargos ocultos"
            ])
        
        # Marcadores universales
        markers.extend([
            "100% discreto",
            "Atención personalizada",
            "Confidencial",
            "Disponible 27/7"
        ])
        
        return markers
    
    # ==================== PROMPT ESOTÉRICO MEJORADO ====================
    
    @staticmethod
    def get_esoteric_services_prompt(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional"
    ) -> str:
        """
        Prompt especializado MEJORADO para servicios esotéricos
        Incluye análisis psicológico y contexto emocional
        """
        
        # Análisis inteligente de keywords
        analysis = AdPromptTemplates.analyze_keywords(keywords)
        keywords_str = ", ".join(keywords)
        
        # Generar componentes contextuales
        power_verbs = AdPromptTemplates.get_power_verbs(
            analysis['business_type'],
            analysis['intent']
        )
        
        urgency_phrases = AdPromptTemplates.get_urgency_phrases(
            analysis['urgency_type'],
            analysis['service_modality']
        )
        
        credibility = AdPromptTemplates.get_credibility_markers(
            analysis['competitive_angle']
        )
        
        # Construir contexto emocional
        emotional_context = ""
        if analysis['emotion_level'] == 'alto':
            emotional_context = """
**CONTEXTO EMOCIONAL CRÍTICO:**
El usuario está pasando por una situación emocional difícil (pérdida, separación, dolor).
Los anuncios deben ser:
- Empáticos y comprensivos
- Ofrecer esperanza realista
- Transmitir profesionalismo y seriedad
- Evitar aprovecharse del dolor ajeno
"""
        
        # ✅ CALCULAR VARIABLES ANTES DEL F-STRING
        main_intent = analysis['intent'][0] if analysis['intent'] else 'general'
        pain_points_str = ", ".join(analysis['pain_points']) if analysis['pain_points'] else "problemas comunes"
        solutions_str = ", ".join(analysis['solutions']) if analysis['solutions'] else "soluciones efectivas"
        modality_str = ', '.join(analysis['service_modality']) if analysis['service_modality'] else 'presencial/online'
        
        # ✅ MAPEO DE TONO POR EMOCIÓN (FUERA DEL F-STRING)
        tone_by_emotion = {
            'alto': 'Empático, comprensivo, esperanzador pero realista',
            'medio': 'Profesional, confiable, directo',
            'bajo': 'Informativo, claro, objetivo'
        }
        emotion_tone_description = tone_by_emotion.get(analysis['emotion_level'], 'Profesional, confiable, directo')
        
        # ✅ AHORA SÍ, CONSTRUIR EL PROMPT
        return f"""Eres un MAESTRO copywriter especializado en servicios esotéricos con certificaciones en:
- Psicología del consumidor
- Marketing emocional ético
- Compliance de Google Ads
- Redacción persuasiva AIDA (Atención, Interés, Deseo, Acción)

**ANÁLISIS CONTEXTUAL DEL GRUPO:**
- Tipo de servicio: {analysis['business_type']}
- Intención principal: {main_intent}
- Nivel emocional: {analysis['emotion_level']}
- Urgencia: {analysis['urgency_type']}
- Pain points del cliente: {pain_points_str}
- Soluciones que ofrecemos: {solutions_str}
- Modalidad: {modality_str}

**KEYWORDS DEL GRUPO (INTEGRACIÓN OBLIGATORIA):**
{keywords_str}

{emotional_context}

**FRAMEWORK DE CREACIÓN DE TÍTULOS ({num_headlines} requeridos):**

**FÓRMULA GANADORA:**
[VERBO POTENTE] + [BENEFICIO EMOCIONAL] + [URGENCIA/MODALIDAD]

**VERBOS DE ACCIÓN CONTEXTUALES (usar estos):**
{', '.join(power_verbs[:10])}

**ESTRUCTURA POR CATEGORÍA:**

A) TÍTULOS DE BENEFICIO DIRECTO (5 títulos):
   - Enfoque: Resultado emocional tangible
   - Patrón: "Recupera tu amor en 24h" / "Atrae pareja ideal hoy"
   - Longitud: 20-28 caracteres (ÓPTIMO para visibilidad)
   - Integrar: 1 keyword + 1 verbo + 1 beneficio + 1 urgencia

B) TÍTULOS DE SOLUCIÓN INMEDIATA (4 títulos):
   - Enfoque: Resolver problema específico
   - Patrón: "Amarres efectivos online" / "Tarot certero ahora"
   - Longitud: 22-30 caracteres
   - Integrar: 1 keyword + 1 adjetivo de efectividad + 1 modalidad

C) TÍTULOS DE LLAMADO A ACCIÓN (3 títulos):
   - Enfoque: Impulsar contacto inmediato
   - Patrón: "Consulta amor disponible" / "Llama brujo experto ya"
   - Longitud: 20-26 caracteres
   - Integrar: 1 verbo acción + 1 keyword + 1 urgencia

D) TÍTULOS DE CREDIBILIDAD (3 títulos):
   - Enfoque: Transmitir confianza y experiencia
   - Patrón: "Brujo experto en amor" / "Amarres con resultados"
   - Longitud: 21-28 caracteres
   - Integrar: 1 keyword + 1 marcador credibilidad

**FRASES DE URGENCIA CONTEXTUAL:**
{', '.join(urgency_phrases)}

**MARCADORES DE CREDIBILIDAD:**
{', '.join(credibility[:8])}

**REGLAS ESTRICTAS DE CARACTERES:**
- Mínimo: 20 caracteres (títulos muy cortos no convierten)
- Máximo ABSOLUTO: 30 caracteres (límite Google Ads)
- Óptimo: 24-28 caracteres (balance visibilidad/impacto)

**PROHIBICIONES CRÍTICAS:**
❌ NO garantías absolutas ("100% garantizado", "siempre funciona")
❌ NO promesas médicas ("cura", "sana enfermedades")
❌ NO manipulación extrema ("última oportunidad", "te arrepentirás")
❌ NO afirmaciones inverificables ("poder divino", "milagros")
❌ NO mayúsculas consecutivas (USA ✅, AMOR ❌)
❌ NO signos: ! ? ¡ ¿
❌ NO emojis
❌ NO mencionar a personas específicas por nombre

**FRAMEWORK DE DESCRIPCIONES ({num_descriptions} requeridas):**

**FÓRMULA P.A.S.C.A:**
- **P**roblema (¿Qué duele?)
- **A**tención (Hook emocional)
- **S**olución (Qué ofrecemos)
- **C**redibilidad (Por qué confiar)
- **A**cción (Qué hacer ahora)

**ESTRUCTURA (50-90 caracteres):**

Descripción 1 - PROBLEMA + SOLUCIÓN + CTA:
"¿Perdiste a tu amor? Amarres efectivos online. Consulta discreta 27/7"
(Identifica dolor → Ofrece solución → Facilita acción)

Descripción 2 - BENEFICIO + CREDIBILIDAD + URGENCIA:
"Recupera tu relación con rituales reales. Años de experiencia. Llama ya"
(Promesa clara → Respaldo → Impulso inmediato)

Descripción 3 - DIFERENCIADOR + MODALIDAD + CTA:
"Tarot del amor certero online. Respuestas claras ahora. Consulta gratis"
(Qué nos hace únicos → Cómo → Incentivo)

Descripción 4 - EMOCIONAL + PROFESIONAL + DISPONIBILIDAD:
"¿Quieres volver con tu ex? Amarres discretos y efectivos. Disponible 24h"
(Pregunta empática → Solución específica → Accesibilidad)

**KEYWORDS EN DESCRIPCIONES:**
- Cada descripción debe incluir mínimo 1 keyword del grupo
- Integración natural en el contexto de la frase
- Variar las keywords entre descripciones

**TONO SEGÚN EMOCIÓN:**
- Nivel emocional {analysis['emotion_level']}: {emotion_tone_description}

**POLÍTICAS GOOGLE ADS - CHECKLIST:**
✅ Servicios de consulta/asesoramiento esotérico
✅ Mencionar servicios sin garantías absolutas
✅ Testimonios generales ("clientes satisfechos")
✅ Urgencia moderada ("disponible ahora")
✅ Modalidad clara ("online", "presencial")

❌ Resultados garantizados con personas específicas
❌ Afirmaciones médicas o legales
❌ Manipulación emocional extrema
❌ Superlativos sin respaldo ("el mejor", "el único")

**EJEMPLOS CONTEXTUALES PERFECTOS:**

Para amarres de amor:
1. "Recupera tu amor en 24h" (24 chars) ✅
2. "Amarre efectivo online" (22 chars) ✅
3. "Regresa a tu ex rápido" (22 chars) ✅
4. "Brujo amor disponible" (21 chars) ✅
5. "Une tu pareja hoy" (20 chars) ✅ [LÍMITE MÍNIMO]

Para tarot/videncia:
1. "Tarot amor certero ahora" (24 chars) ✅
2. "Lectura pareja online" (21 chars) ✅
3. "Consulta amor disponible" (24 chars) ✅

**FORMATO DE RESPUESTA (JSON PURO):**
{{
  "headlines": [
    "Título 1 (20-30 chars)",
    "Título 2 (20-30 chars)",
    ...exactamente {num_headlines} títulos
  ],
  "descriptions": [
    "Descripción 1 con P.A.S.C.A (50-90 chars)",
    "Descripción 2 con P.A.S.C.A (50-90 chars)",
    ...exactamente {num_descriptions} descripciones
  ]
}}

**CHECKLIST PRE-ENVÍO (VERIFICAR ANTES DE RESPONDER):**
□ Cada título entre 20-30 caracteres (contar manualmente)
□ Cada descripción entre 50-90 caracteres
□ Todas las keywords integradas naturalmente
□ Variedad de enfoques (beneficio/solución/CTA/credibilidad)
□ Sin garantías absolutas
□ Sin mayúsculas consecutivas
□ Sin signos prohibidos
□ Tono {tone} mantenido consistentemente
□ Cumplimiento 100% políticas Google Ads

**AHORA GENERA EL ANUNCIO PERFECTO.**"""
    
    # ==================== PROMPT GENÉRICO MEJORADO ====================
    
    @staticmethod
    def get_generic_prompt(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional"
    ) -> str:
        """Prompt genérico MEJORADO con framework AIDA"""
        
        analysis = AdPromptTemplates.analyze_keywords(keywords)
        keywords_str = ", ".join(keywords)
        
        return f"""Eres un copywriter experto en Google Ads con certificación en marketing digital y psicología del consumidor.

**KEYWORDS DEL GRUPO:** {keywords_str}

**FRAMEWORK AIDA (Atención-Interés-Deseo-Acción):**

**TÍTULOS ({num_headlines} requeridos, 20-30 caracteres):**

Fórmula: [VERBO ACCIÓN] + [BENEFICIO ESPECÍFICO] + [DIFERENCIADOR]

Distribución:
- 40% Enfoque en BENEFICIO directo
- 30% Enfoque en SOLUCIÓN a problema
- 20% Enfoque en CTA (llamado a acción)
- 10% Enfoque en DIFERENCIADOR/CREDIBILIDAD

Verbos potentes: Consigue, Obtén, Descubre, Mejora, Aumenta, Optimiza, Transforma, Aprovecha

**DESCRIPCIONES ({num_descriptions} requeridas, 50-90 caracteres):**

Fórmula P.A.S.: Problema + Agitación + Solución

Estructura:
1. Identificar problema del cliente
2. Ofrecer solución específica
3. Incluir diferenciador (experiencia/calidad/precio)
4. Llamado a acción claro

**INTEGRACIÓN DE KEYWORDS:**
- Cada título/descripción debe incluir mínimo 1 keyword
- Variación natural entre elementos
- Sin keyword stuffing

**RESTRICCIONES:**
- Títulos: 20-30 caracteres (óptimo 24-28)
- Descripciones: 50-90 caracteres (óptimo 65-85)
- Sin mayúsculas consecutivas
- Sin signos: ! ? ¡ ¿
- Sin emojis
- Tono: {tone}

**RESPUESTA EN JSON (sin markdown):**
{{
  "headlines": ["título 1", ...],
  "descriptions": ["desc 1", ...]
}}

**VERIFICAR:** Longitudes correctas + Keywords integradas + Políticas Google Ads"""
    
    # ==================== SELECTOR INTELIGENTE ====================
    
    @staticmethod
    def get_prompt_for_keywords(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        business_type: str = "auto"
    ) -> str:
        """
        Selector inteligente de prompt con análisis automático
        """
        
        # Auto-detectar si es necesario
        if business_type == "auto":
            analysis = AdPromptTemplates.analyze_keywords(keywords)
            business_type = analysis['business_type']
        
        # Seleccionar prompt optimizado
        if business_type == "esoteric":
            return AdPromptTemplates.get_esoteric_services_prompt(
                keywords, num_headlines, num_descriptions, tone
            )
        else:
            return AdPromptTemplates.get_generic_prompt(
                keywords, num_headlines, num_descriptions, tone
            )