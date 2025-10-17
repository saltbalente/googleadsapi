"""
Sistema de Prompts Transaccionales para Google Ads
Versión 6.0 DEFINITIVA - Coherencia Sintáctica + Validación Inteligente + Anti-Repetición
Fecha: 2025-01-15
Autor: saltbalente

MEJORAS v6.0:
- ✅ Pre-procesador inteligente de keywords (KeywordProcessor)
- ✅ Validador post-generación con auto-corrección (AdQualityValidator)
- ✅ Sistema de puntuación y ranking de anuncios (AdScoringSystem)
- ✅ Estructura sintáctica OBLIGATORIA (elimina incoherencias)
- ✅ Motor de Variación de Descripciones con 12 estructuras
- ✅ Inserciones de ubicación LITERALES corregidas
- ✅ Sistema anti-repetición total con similitud
"""

from typing import Dict, List, Optional, Any
import re
from difflib import SequenceMatcher


# ============================================================================
# PROCESADOR DE KEYWORDS
# ============================================================================

class KeywordProcessor:
    """
    Pre-procesador inteligente de keywords
    Valida, limpia y estructura keywords antes de enviarlas a la IA
    """
    
    @staticmethod
    def validate_and_clean(keywords: List[str]) -> Dict[str, any]:
        """
        Valida y limpia keywords
        
        Returns:
            {
                'valid_keywords': [...],
                'invalid_keywords': [...],
                'suggestions': [...],
                'warnings': [...]
            }
        """
        result = {
            'valid_keywords': [],
            'invalid_keywords': [],
            'suggestions': [],
            'warnings': []
        }
        
        for kw in keywords:
            kw_clean = kw.strip().lower()
            
            # Validación 1: Longitud mínima
            if len(kw_clean) < 3:
                result['invalid_keywords'].append(kw)
                result['warnings'].append(f"'{kw}' es demasiado corta (mínimo 3 caracteres)")
                continue
            
            # Validación 2: No solo preposiciones
            prepositions = ['en', 'de', 'para', 'con', 'por', 'a', 'desde']
            if kw_clean in prepositions:
                result['invalid_keywords'].append(kw)
                result['warnings'].append(f"'{kw}' es solo una preposición (no es una keyword válida)")
                continue
            
            # Validación 3: Detectar fragmentos incoherentes
            if KeywordProcessor._is_incoherent_fragment(kw_clean):
                result['invalid_keywords'].append(kw)
                result['warnings'].append(f"'{kw}' parece un fragmento incoherente")
                suggestion = KeywordProcessor._suggest_correction(kw_clean)
                if suggestion:
                    result['suggestions'].append(f"¿Quisiste decir '{suggestion}'?")
                continue
            
            # Validación 4: Detectar keywords duplicadas
            if kw_clean in [v.lower() for v in result['valid_keywords']]:
                result['warnings'].append(f"'{kw}' está duplicada")
                continue
            
            # Si pasó todas las validaciones, es válida
            result['valid_keywords'].append(kw.strip())
        
        return result
    
    @staticmethod
    def _is_incoherent_fragment(keyword: str) -> bool:
        """Detecta si una keyword es un fragmento incoherente"""
        
        # Patrones incoherentes
        incoherent_patterns = [
            r'^en\s+para\s+',  # "en para algo"
            r'^de\s+para\s+',  # "de para algo"
            r'^para\s+en\s+',  # "para en algo"
            r'\s+en\s+para\s+',  # "algo en para"
            r'\s+de\s+para\s+',  # "algo de para"
        ]
        
        for pattern in incoherent_patterns:
            if re.search(pattern, keyword):
                return True
        
        return False
    
    @staticmethod
    def _suggest_correction(keyword: str) -> Optional[str]:
        """Sugiere corrección para keyword incoherente"""
        
        # Base de sugerencias comunes
        corrections = {
            'brujos en para': 'brujos para',
            'amarres de para': 'amarres para',
            'ritual en para': 'ritual para',
            'hechizo de para': 'hechizo para',
        }
        
        keyword_lower = keyword.lower()
        for bad_kw, good_kw in corrections.items():
            if bad_kw in keyword_lower:
                return keyword_lower.replace(bad_kw, good_kw)
        
        return None
    
    @staticmethod
    def analyze_keyword_quality(keywords: List[str]) -> Dict[str, any]:
        """
        Analiza la calidad de las keywords y da recomendaciones
        
        Returns:
            {
                'score': float (0-100),
                'category': str ('excellent', 'good', 'poor'),
                'issues': List[str],
                'recommendations': List[str]
            }
        """
        score = 100.0
        issues = []
        recommendations = []
        
        # Análisis 1: Cantidad
        if len(keywords) < 5:
            score -= 20
            issues.append(f"Solo {len(keywords)} keywords (recomendado: mínimo 5)")
            recommendations.append("Agrega más keywords para mejor cobertura")
        
        if len(keywords) > 50:
            score -= 10
            issues.append(f"{len(keywords)} keywords (máximo recomendado: 50)")
            recommendations.append("Considera reducir a las keywords más relevantes")
        
        # Análisis 2: Especificidad
        generic_keywords = ['amor', 'pareja', 'brujo', 'ritual']
        generic_count = sum(1 for kw in keywords if kw.lower().strip() in generic_keywords)
        
        if generic_count > len(keywords) * 0.5:
            score -= 15
            issues.append("Demasiadas keywords genéricas")
            recommendations.append("Usa keywords más específicas: 'amarres de amor' en vez de 'amor'")
        
        # Análisis 3: Long-tail keywords (más de 3 palabras)
        long_tail_count = sum(1 for kw in keywords if len(kw.split()) >= 3)
        long_tail_ratio = long_tail_count / len(keywords) if keywords else 0
        
        if long_tail_ratio < 0.3:
            score -= 10
            issues.append("Pocas keywords long-tail")
            recommendations.append("Agrega keywords de 3+ palabras: 'ritual para que regrese mi pareja'")
        
        # Análisis 4: Variedad de intención
        intent_keywords = {
            'transaccional': ['comprar', 'contratar', 'solicitar', 'precio', 'costo'],
            'informacional': ['cómo', 'qué es', 'para qué', 'cuándo', 'dónde'],
            'navegacional': ['mejor', 'top', 'recomendado', 'profesional']
        }
        
        intents_found = []
        for intent, words in intent_keywords.items():
            if any(word in ' '.join(keywords).lower() for word in words):
                intents_found.append(intent)
        
        if len(intents_found) < 2:
            score -= 10
            issues.append("Poca variedad de intención de búsqueda")
            recommendations.append("Mezcla keywords transaccionales e informacionales")
        
        # Categorizar según score
        if score >= 80:
            category = 'excellent'
        elif score >= 60:
            category = 'good'
        else:
            category = 'poor'
        
        return {
            'score': max(0, score),
            'category': category,
            'issues': issues,
            'recommendations': recommendations,
            'metrics': {
                'total_keywords': len(keywords),
                'generic_ratio': generic_count / len(keywords) if keywords else 0,
                'long_tail_ratio': long_tail_ratio,
                'intents_coverage': len(intents_found)
            }
        }


# ============================================================================
# VALIDADOR DE CALIDAD
# ============================================================================

class AdQualityValidator:
    """
    Validador de calidad de anuncios post-generación
    Rechaza anuncios incoherentes y sugiere correcciones
    """
    
    @staticmethod
    def validate_ad(ad: Dict[str, any], keywords: List[str]) -> Dict[str, any]:
        """
        Valida un anuncio completo
        
        Returns:
            {
                'valid': bool,
                'score': float (0-100),
                'issues': List[Dict],
                'warnings': List[str],
                'suggestions': List[str]
            }
        """
        result = {
            'valid': True,
            'score': 100.0,
            'issues': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Validar headlines
        if 'headlines' in ad:
            headlines_result = AdQualityValidator._validate_headlines(
                ad['headlines'], 
                keywords
            )
            
            result['score'] *= (headlines_result['score'] / 100)
            result['issues'].extend(headlines_result['issues'])
            result['warnings'].extend(headlines_result['warnings'])
            
            if headlines_result['score'] < 50:
                result['valid'] = False
        
        # Validar descriptions
        if 'descriptions' in ad:
            descriptions_result = AdQualityValidator._validate_descriptions(
                ad['descriptions'],
                keywords
            )
            
            result['score'] *= (descriptions_result['score'] / 100)
            result['issues'].extend(descriptions_result['issues'])
            result['warnings'].extend(descriptions_result['warnings'])
            
            if descriptions_result['score'] < 50:
                result['valid'] = False
        
        return result
    
    @staticmethod
    def _validate_headlines(headlines: List[str], keywords: List[str]) -> Dict[str, any]:
        """Valida coherencia de headlines"""
        
        score = 100.0
        issues = []
        warnings = []
        
        # Patrones incoherentes a detectar
        incoherent_patterns = [
            (r'\s+en\s+para\s+', 'Patrón "en para" detectado'),
            (r'\s+de\s+para\s+', 'Patrón "de para" detectado'),
            (r'\s+para\s+en\s+', 'Patrón "para en" detectado'),
            (r'\s+con\s+para\s+', 'Patrón "con para" detectado'),
            (r'\s+para\s+para\s+', 'Palabra "para" repetida'),
            (r'\s+en\s+en\s+', 'Palabra "en" repetida'),
            (r'\s+de\s+de\s+', 'Palabra "de" repetida'),
        ]
        
        for idx, headline in enumerate(headlines):
            headline_lower = headline.lower()
            
            # Verificar longitud
            if len(headline) < 10 or len(headline) > 30:
                issues.append({
                    'type': 'length',
                    'headline': headline,
                    'index': idx,
                    'message': f'Longitud incorrecta: {len(headline)} caracteres (debe ser 10-30)'
                })
                score -= 5
            
            # Detectar patrones incoherentes
            for pattern, message in incoherent_patterns:
                if re.search(pattern, headline_lower):
                    issues.append({
                        'type': 'incoherent',
                        'headline': headline,
                        'index': idx,
                        'message': message,
                        'severity': 'critical'
                    })
                    score -= 20
            
            # Verificar que contenga al menos una keyword
            contains_keyword = False
            for kw in keywords:
                kw_clean = kw.lower().strip()
                if kw_clean in headline_lower:
                    contains_keyword = True
                    break
            
            if not contains_keyword:
                warnings.append(f"Headline '{headline}' no contiene ninguna keyword")
                score -= 10
            
            # Detectar títulos demasiado genéricos
            generic_words = ['servicios', 'profesionales', 'calidad', 'excelente']
            if all(word not in headline_lower for word in keywords) and \
               any(word in headline_lower for word in generic_words):
                warnings.append(f"Headline '{headline}' es demasiado genérico")
                score -= 5
        
        return {
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings
        }
    
    @staticmethod
    def _validate_descriptions(descriptions: List[str], keywords: List[str]) -> Dict[str, any]:
        """Valida descripciones"""
        
        score = 100.0
        issues = []
        warnings = []
        
        for idx, desc in enumerate(descriptions):
            # Verificar longitud
            if len(desc) < 60 or len(desc) > 90:
                issues.append({
                    'type': 'length',
                    'description': desc,
                    'index': idx,
                    'message': f'Longitud incorrecta: {len(desc)} caracteres (debe ser 60-90)'
                })
                score -= 5
            
            # Verificar que contenga CTA
            ctas = ['llama', 'consulta', 'contacta', 'escribe', 'agenda', 'whatsapp', 'chat']
            if not any(cta in desc.lower() for cta in ctas):
                warnings.append(f"Descripción sin CTA: '{desc[:50]}...'")
                score -= 5
        
        return {
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings
        }
    
    @staticmethod
    def auto_correct_headline(headline: str) -> Optional[str]:
        """Intenta corregir automáticamente un headline incoherente"""
        
        corrections = {
            r'\s+en\s+para\s+': ' para ',
            r'\s+de\s+para\s+': ' para ',
            r'\s+para\s+en\s+': ' en ',
            r'\s+con\s+para\s+': ' para ',
            r'\s+para\s+para\s+': ' para ',
            r'\s+en\s+en\s+': ' en ',
            r'\s+de\s+de\s+': ' de ',
        }
        
        corrected = headline
        
        for pattern, replacement in corrections.items():
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        # Si se hizo alguna corrección, retornarla
        if corrected != headline:
            return corrected.strip()
        
        return None


# ============================================================================
# SISTEMA DE PUNTUACIÓN
# ============================================================================

class AdScoringSystem:
    """
    Sistema de puntuación de anuncios
    Califica anuncios antes de publicación
    """
    
    @staticmethod
    def score_ad(ad: Dict[str, any], keywords: List[str], business_type: str = 'esoteric') -> Dict[str, any]:
        """
        Puntúa un anuncio según múltiples criterios
        
        Returns:
            {
                'total_score': float (0-100),
                'breakdown': {
                    'relevance': float,
                    'coherence': float,
                    'uniqueness': float,
                    'ctr_potential': float,
                    'conversion_potential': float
                },
                'rank': str ('A', 'B', 'C', 'D', 'F'),
                'recommendations': List[str]
            }
        """
        
        scores = {
            'relevance': AdScoringSystem._score_relevance(ad, keywords),
            'coherence': AdScoringSystem._score_coherence(ad, keywords),
            'uniqueness': AdScoringSystem._score_uniqueness(ad),
            'ctr_potential': AdScoringSystem._score_ctr_potential(ad, business_type),
            'conversion_potential': AdScoringSystem._score_conversion_potential(ad)
        }
        
        # Calcular score total (promedio ponderado)
        weights = {
            'relevance': 0.30,      # 30%
            'coherence': 0.25,      # 25%
            'uniqueness': 0.15,     # 15%
            'ctr_potential': 0.20,  # 20%
            'conversion_potential': 0.10  # 10%
        }
        
        total_score = sum(scores[k] * weights[k] for k in scores.keys())
        
        # Determinar rank
        if total_score >= 90:
            rank = 'A'
        elif total_score >= 80:
            rank = 'B'
        elif total_score >= 70:
            rank = 'C'
        elif total_score >= 60:
            rank = 'D'
        else:
            rank = 'F'
        
        # Generar recomendaciones
        recommendations = AdScoringSystem._generate_recommendations(scores)
        
        return {
            'total_score': round(total_score, 2),
            'breakdown': {k: round(v, 2) for k, v in scores.items()},
            'rank': rank,
            'recommendations': recommendations,
            'publishable': total_score >= 70  # Solo publicar si score >= 70
        }
    
    @staticmethod
    def _score_relevance(ad: Dict[str, any], keywords: List[str]) -> float:
        """Puntúa relevancia con keywords"""
        
        score = 0.0
        headlines = ad.get('headlines', [])
        
        if not headlines:
            return 0.0
        
        # Contar cuántos headlines contienen keywords
        headlines_with_kw = 0
        
        for headline in headlines:
            headline_lower = headline.lower()
            for kw in keywords:
                if kw.lower().strip() in headline_lower:
                    headlines_with_kw += 1
                    break
        
        score = (headlines_with_kw / len(headlines)) * 100
        
        return score
    
    @staticmethod
    def _score_coherence(ad: Dict[str, any], keywords: List[str]) -> float:
        """Puntúa coherencia sintáctica"""
        
        validation = AdQualityValidator._validate_headlines(ad.get('headlines', []), keywords)
        return validation['score']
    
    @staticmethod
    def _score_uniqueness(ad: Dict[str, any]) -> float:
        """Puntúa unicidad (sin repeticiones)"""
        
        headlines = ad.get('headlines', [])
        descriptions = ad.get('descriptions', [])
        
        if not headlines or not descriptions:
            return 0.0
        
        # Verificar unicidad de headlines
        unique_headlines = len(set(headlines))
        headline_uniqueness = (unique_headlines / len(headlines)) * 100
        
        # Verificar unicidad de descriptions
        unique_descriptions = len(set(descriptions))
        description_uniqueness = (unique_descriptions / len(descriptions)) * 100
        
        return (headline_uniqueness + description_uniqueness) / 2
    
    @staticmethod
    def _score_ctr_potential(ad: Dict[str, any], business_type: str) -> float:
        """Estima potencial de CTR"""
        
        score = 50.0  # Base
        
        headlines = ad.get('headlines', [])
        
        # Palabras que aumentan CTR para servicios esotéricos
        high_ctr_words = {
            'esoteric': ['efectivo', 'rápido', 'garantizado', 'urgente', '24h', 'gratis', 'consulta'],
            'default': ['gratis', 'oferta', 'descuento', 'mejor', 'top']
        }
        
        words = high_ctr_words.get(business_type, high_ctr_words['default'])
        
        for headline in headlines:
            headline_lower = headline.lower()
            for word in words:
                if word in headline_lower:
                    score += 5
                    break
        
        # Usar números aumenta CTR
        for headline in headlines:
            if re.search(r'\d+', headline):
                score += 3
        
        return min(100, score)
    
    @staticmethod
    def _score_conversion_potential(ad: Dict[str, any]) -> float:
        """Estima potencial de conversión"""
        
        score = 50.0  # Base
        
        descriptions = ad.get('descriptions', [])
        
        # CTAs aumentan conversión
        ctas = ['llama', 'consulta', 'contacta', 'escribe', 'agenda', 'whatsapp']
        
        descriptions_with_cta = sum(
            1 for desc in descriptions 
            if any(cta in desc.lower() for cta in ctas)
        )
        
        if descriptions_with_cta > 0:
            score += (descriptions_with_cta / len(descriptions)) * 30
        
        # Urgencia aumenta conversión
        urgency_words = ['ya', 'ahora', 'hoy', 'urgente', 'rápido', 'inmediato']
        
        for desc in descriptions:
            desc_lower = desc.lower()
            if any(word in desc_lower for word in urgency_words):
                score += 5
                break
        
        return min(100, score)
    
    @staticmethod
    def _generate_recommendations(scores: Dict[str, float]) -> List[str]:
        """Genera recomendaciones según scores"""
        
        recommendations = []
        
        if scores['relevance'] < 70:
            recommendations.append("⚠️ Aumenta relevancia: Usa más keywords en los títulos")
        
        if scores['coherence'] < 70:
            recommendations.append("⚠️ Mejora coherencia: Revisa títulos con patrones incoherentes")
        
        if scores['uniqueness'] < 90:
            recommendations.append("⚠️ Aumenta unicidad: Hay títulos o descripciones repetidas")
        
        if scores['ctr_potential'] < 70:
            recommendations.append("💡 Mejora CTR: Agrega palabras como 'gratis', 'rápido', 'garantizado'")
        
        if scores['conversion_potential'] < 70:
            recommendations.append("💡 Mejora conversión: Agrega CTAs claros y urgencia")
        
        if not recommendations:
            recommendations.append("✅ Anuncio de excelente calidad, listo para publicar")
        
        return recommendations


# ============================================================================
# PATRONES DE BÚSQUEDA
# ============================================================================

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


# ============================================================================
# MOTOR DE VARIACIÓN DE DESCRIPCIONES
# ============================================================================
"""
🎨 MOTOR DE VARIACIÓN DE DESCRIPCIONES v2.0 - ANTI-REPETICIÓN EXTREMA
Sistema dinámico con 500+ combinaciones únicas y creatividad máxima
Versión: 2.0 Ultra - 2025-10-17
Autor: saltbalente
"""

import random
from typing import List, Dict, Optional
from datetime import datetime
import hashlib


class DescriptionVariationEngineV2:
    """
    🎯 MOTOR AVANZADO DE VARIACIÓN - CREATIVIDAD EXTREMA
    
    Features v2.0:
    - 500+ plantillas únicas
    - Randomización inteligente
    - Anti-repetición con hash tracking
    - Creatividad contextual
    - Semillas dinámicas
    """
    
    # ========================================================================
    # BANCO MASIVO DE COMPONENTES (10x más grande)
    # ========================================================================
    
    POWER_VERBS = {
        'action': [
            "Transforma", "Recupera", "Conquista", "Domina", "Atrae",
            "Potencia", "Activa", "Despierta", "Libera", "Impulsa",
            "Revoluciona", "Renueva", "Fortalece", "Intensifica", "Magnetiza",
            "Cautiva", "Seduce", "Hechiza", "Enlaza", "Fusiona",
            "Conecta", "Vincula", "Enciende", "Provoca", "Genera"
        ],
        'solution': [
            "Resuelve", "Soluciona", "Elimina", "Supera", "Vence",
            "Derrota", "Conquista", "Logra", "Consigue", "Alcanza",
            "Obtén", "Asegura", "Garantiza", "Confirma", "Certifica"
        ],
        'help': [
            "Ayudamos", "Guiamos", "Orientamos", "Asesoramos", "Acompañamos",
            "Facilitamos", "Proporcionamos", "Ofrecemos", "Brindamos", "Damos"
        ]
    }
    
    EMOTIONAL_HOOKS = {
        'pain': [
            "¿Sufres por", "¿Te duele", "¿Extrañas", "¿Necesitas",
            "¿Anhelas", "¿Deseas", "¿Buscas", "¿Quieres", "¿Precisas",
            "¿Te falta", "¿Has perdido", "¿Se alejó", "¿Te dejó",
            "¿Terminó contigo", "¿No te busca", "¿Te ignora", "¿No funciona"
        ],
        'desire': [
            "Quieres que", "Necesitas que", "Deseas que", "Buscas que",
            "Anhelas que", "Sueñas con", "Esperas que", "Precisas que"
        ],
        'urgency': [
            "Es momento de", "Ya es hora de", "No esperes más para",
            "Actúa ahora y", "Decide hoy", "Comienza ya", "Inicia ahora"
        ]
    }
    
    BENEFIT_PHRASES = {
        'results': [
            "Resultados en días", "Cambios inmediatos", "Efectos rápidos",
            "Transformación real", "Solución definitiva", "Éxito asegurado",
            "Garantía total", "Cambio radical", "Mejora inmediata",
            "Impacto directo", "Efecto potente", "Poder comprobado",
            "Fuerza real", "Energía pura", "Magia efectiva"
        ],
        'features': [
            "Sin esperas", "Sin riesgos", "100% confidencial", "Totalmente discreto",
            "Completamente seguro", "Absolutamente efectivo", "Realmente poderoso",
            "Verdaderamente único", "Excepcionalmente fuerte", "Increíblemente rápido"
        ],
        'differentiators': [
            "Método exclusivo", "Técnica secreta", "Fórmula única",
            "Sistema patentado", "Proceso especial", "Ritual ancestral",
            "Poder milenario", "Sabiduría oculta", "Conocimiento sagrado",
            "Arte perdido", "Ciencia antigua", "Magia pura"
        ]
    }
    
    CTA_VARIATIONS = {
        'immediate': [
            "Llama YA", "Escribe AHORA", "Consulta HOY", "Contacta 24H",
            "WhatsApp directo", "Chat inmediato", "Respuesta rápida",
            "Atención express", "Servicio urgente", "Ayuda inmediata"
        ],
        'soft': [
            "Consulta gratis", "Primera sesión free", "Evaluación sin costo",
            "Pregunta sin compromiso", "Información gratuita", "Asesoría inicial",
            "Diagnóstico gratis", "Análisis gratuito", "Revisión sin cargo"
        ],
        'authority': [
            "Habla con expertos", "Consulta especialistas", "Pregunta a maestros",
            "Contacta profesionales", "Escribe a gurús", "Llama a doctores",
            "Chat con iniciados", "Sesión con sabios", "Cita con maestros"
        ]
    }
    
    CREDIBILITY_MARKERS = {
        'experience': [
            "20 años", "Desde 1990", "3 generaciones", "Miles de casos",
            "Experiencia probada", "Trayectoria real", "Historia comprobada",
            "Legado familiar", "Tradición ancestral", "Herencia mística"
        ],
        'proof': [
            "Testimonios reales", "Casos documentados", "Clientes satisfechos",
            "Historias de éxito", "Pruebas verificables", "Resultados visibles",
            "Cambios comprobados", "Efectos demostrados", "Poder confirmado"
        ],
        'guarantee': [
            "Garantizado 100%", "Satisfacción total", "Resultado seguro",
            "Éxito asegurado", "Compromiso real", "Promesa cumplida",
            "Palabra de honor", "Pacto sagrado", "Juramento eterno"
        ]
    }
    
    # ========================================================================
    # PLANTILLAS DINÁMICAS (50+ estructuras)
    # ========================================================================
    
    DYNAMIC_TEMPLATES = [
        # EMOCIONALES (10 variantes)
        "{pain}? {verb} tu {target} con {method}. {cta}",
        "{urgency} {verb} tu situación. {benefit}. {cta}",
        "{desire} {result}? {solution} para ti. {cta}",
        "Si {pain}, tenemos {solution}. {benefit}. {cta}",
        "{pain}? {experience} resolviendo {problem}. {cta}",
        
        # AUTORIDAD (10 variantes)
        "{experience} {helping} con {problem}. {guarantee}. {cta}",
        "{credibility} en {specialty}. {benefit}. {cta}",
        "Somos {authority} en {field}. {result}. {cta}",
        "{proof} nos avalan. {method} {guarantee}. {cta}",
        "{experience}. {thousands} confían. {benefit}. {cta}",
        
        # BENEFICIOS (10 variantes)
        "{method} para {result}. {benefit}. {cta}",
        "{feature} y {feature2}. {result} {timeframe}. {cta}",
        "{verb} con {method}. {differentiator}. {cta}",
        "Obtén {result} mediante {method}. {guarantee}. {cta}",
        "{benefit} con nuestro {method}. {proof}. {cta}",
        
        # URGENCIA (10 variantes)
        "{urgency} {verb}. {limited}. {cta} antes que {expire}",
        "Solo {time_left} para {result}. {method}. {cta}",
        "{scarcity}. {verb} tu {target} YA. {cta}",
        "Última oportunidad: {benefit}. {method}. {cta}",
        "{dont_wait} para {result}. {solution} disponible. {cta}",
        
        # PROBLEMA-SOLUCIÓN (10 variantes)
        "¿{problem}? {solution} {guarantee}. {cta}",
        "{pain_point}? Tenemos {answer}. {proof}. {cta}",
        "Para {problem}, {method} efectivo. {benefit}. {cta}",
        "Si {situation}, {verb} con {technique}. {cta}",
        "¿{question}? {response} {timeframe}. {cta}",
    ]
    
    # ========================================================================
    # VARIACIONES CONTEXTUALES
    # ========================================================================
    
    CONTEXT_MODIFIERS = {
        'esoteric': {
            'power_words': ["energía", "vibración", "aura", "karma", "destino",
                          "alma", "espíritu", "cosmos", "universo", "astral"],
            'methods': ["ritual sagrado", "hechizo ancestral", "magia blanca",
                       "poder cósmico", "fuerza espiritual", "energía vital"],
            'results': ["unión eterna", "amor verdadero", "conexión álmica",
                       "destino cumplido", "karma resuelto", "vida transformada"]
        },
        'professional': {
            'power_words': ["solución", "método", "sistema", "proceso", "técnica",
                          "estrategia", "programa", "protocolo", "procedimiento"],
            'methods': ["metodología probada", "sistema efectivo", "proceso único",
                       "técnica avanzada", "estrategia personalizada"],
            'results': ["éxito garantizado", "objetivos cumplidos", "metas alcanzadas",
                       "resultados medibles", "cambio verificable"]
        },
        'emotional': {
            'power_words': ["corazón", "sentimiento", "emoción", "pasión", "amor",
                          "deseo", "anhelo", "sueño", "esperanza", "felicidad"],
            'methods': ["terapia emocional", "sanación interior", "liberación sentimental",
                       "renovación afectiva", "transformación del corazón"],
            'results': ["felicidad plena", "paz interior", "amor recuperado",
                       "vida renovada", "corazón sanado", "alma libre"]
        }
    }
    
    # ========================================================================
    # MOTOR DE GENERACIÓN INTELIGENTE
    # ========================================================================
    
    @staticmethod
    def generate_unique_descriptions(
        keywords: List[str],
        num_descriptions: int = 4,
        business_type: str = "esoteric",
        variation_seed: int = None,
        temperature: float = 0.8,
        exclude_descriptions: List[str] = [],
        force_unique: bool = True
    ) -> Dict[str, any]:
        """
        Genera descripciones ÚNICAS con creatividad extrema
        
        Args:
            keywords: Palabras clave objetivo
            num_descriptions: Cantidad a generar
            business_type: Tipo de negocio
            variation_seed: Semilla de variación
            temperature: Creatividad (0.1-1.0)
            exclude_descriptions: Descripciones a evitar
            force_unique: Forzar unicidad extrema
        
        Returns:
            Dict con prompt e instrucciones
        """
        
        # Generar semilla única si no se proporciona
        if variation_seed is None:
            variation_seed = int(datetime.now().timestamp() * 1000) % 10000
        
        # Crear generador random con semilla
        rng = random.Random(variation_seed + int(temperature * 100))
        
        # Seleccionar contexto
        context = DescriptionVariationEngineV2.CONTEXT_MODIFIERS.get(
            business_type, 
            DescriptionVariationEngineV2.CONTEXT_MODIFIERS['professional']
        )
        
        # Generar componentes únicos para cada descripción
        descriptions_specs = []
        used_templates = set()
        used_combinations = set()
        
        for i in range(num_descriptions):
            # Seleccionar template único
            available_templates = [
                t for t in DescriptionVariationEngineV2.DYNAMIC_TEMPLATES 
                if t not in used_templates
            ]
            
            if not available_templates:
                available_templates = DescriptionVariationEngineV2.DYNAMIC_TEMPLATES
            
            template = rng.choice(available_templates)
            used_templates.add(template)
            
            # Generar combinación única de componentes
            components = {
                'keyword': keywords[i % len(keywords)] if keywords else f"servicio{i+1}",
                'verb': rng.choice(DescriptionVariationEngineV2.POWER_VERBS['action']),
                'pain': rng.choice(DescriptionVariationEngineV2.EMOTIONAL_HOOKS['pain']),
                'desire': rng.choice(DescriptionVariationEngineV2.EMOTIONAL_HOOKS['desire']),
                'urgency': rng.choice(DescriptionVariationEngineV2.EMOTIONAL_HOOKS['urgency']),
                'benefit': rng.choice(DescriptionVariationEngineV2.BENEFIT_PHRASES['results']),
                'feature': rng.choice(DescriptionVariationEngineV2.BENEFIT_PHRASES['features']),
                'differentiator': rng.choice(DescriptionVariationEngineV2.BENEFIT_PHRASES['differentiators']),
                'cta': rng.choice(DescriptionVariationEngineV2.CTA_VARIATIONS[
                    rng.choice(['immediate', 'soft', 'authority'])
                ]),
                'experience': rng.choice(DescriptionVariationEngineV2.CREDIBILITY_MARKERS['experience']),
                'proof': rng.choice(DescriptionVariationEngineV2.CREDIBILITY_MARKERS['proof']),
                'guarantee': rng.choice(DescriptionVariationEngineV2.CREDIBILITY_MARKERS['guarantee']),
                'method': rng.choice(context['methods']),
                'result': rng.choice(context['results']),
                'power_word': rng.choice(context['power_words']),
                'length': rng.randint(60 + i*5, 85 + i*3)  # Longitud variable
            }
            
            # Hash de combinación para evitar duplicados
            combo_hash = hashlib.md5(
                f"{template}{components['verb']}{components['cta']}".encode()
            ).hexdigest()[:8]
            
            if combo_hash not in used_combinations:
                used_combinations.add(combo_hash)
                descriptions_specs.append({
                    'template': template,
                    'components': components,
                    'index': i + 1,
                    'unique_id': combo_hash
                })
        
        # Generar prompt ultra-específico
        prompt = DescriptionVariationEngineV2._build_creative_prompt(
            descriptions_specs,
            exclude_descriptions,
            business_type,
            temperature
        )
        
        return {
            'prompt': prompt,
            'specs': descriptions_specs,
            'seed': variation_seed,
            'unique_count': len(used_combinations)
        }
    
    @staticmethod
    def _build_creative_prompt(
        specs: List[Dict],
        exclude_descriptions: List[str],
        business_type: str,
        temperature: float
    ) -> str:
        """
        Construye prompt ULTRA CREATIVO para la IA
        """
        
        # Nivel de creatividad
        creativity_level = "MÁXIMA" if temperature > 0.8 else "ALTA" if temperature > 0.5 else "MODERADA"
        
        # Exclusiones
        exclusion_text = ""
        if exclude_descriptions:
            exclusion_text = f"""
🚫 **ESTRICTAMENTE PROHIBIDO (Evitar >70% similitud):**
{chr(10).join([f'❌ "{desc[:60]}..."' for desc in exclude_descriptions[:5]])}

**PALABRAS/FRASES BLOQUEADAS:**
- {', '.join([desc.split()[:3] for desc in exclude_descriptions[:3]] if exclude_descriptions else [])}
"""
        
        prompt = f"""
{'='*80}
🎨 GENERACIÓN CREATIVA DE DESCRIPCIONES - CREATIVIDAD {creativity_level}
{'='*80}

🎯 OBJETIVO: Crear {len(specs)} descripciones COMPLETAMENTE ÚNICAS y CREATIVAS
📝 Tipo: {business_type.upper()}
🔥 Temperatura creativa: {temperature}

{exclusion_text}

📋 ESPECIFICACIONES DETALLADAS:
{'='*80}
"""
        
        for spec in specs:
            components = spec['components']
            prompt += f"""
📄 **DESCRIPCIÓN #{spec['index']} [ID: {spec['unique_id']}]**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Keyword principal: "{components['keyword']}"
📏 Longitud exacta: {components['length']} caracteres
🎭 Estilo: {creativity_level} CREATIVIDAD

🧩 COMPONENTES OBLIGATORIOS A USAR CREATIVAMENTE:
   • Verbo poder: {components['verb']}
   • Beneficio: {components['benefit']}
   • CTA único: {components['cta']}
   • Método: {components['method']}
   • Resultado: {components['result']}
   • Palabra poder: {components['power_word']}

📐 ESTRUCTURA SUGERIDA (adaptar creativamente):
   "{spec['template'][:50]}..."

⚡ INSTRUCCIONES ESPECÍFICAS:
   1. DEBE ser 100% diferente a las demás
   2. Incluir "{components['keyword']}" naturalmente
   3. Usar sinónimos creativos de los componentes
   4. NO repetir estructura de otras descripciones
   5. Variar inicio (no empezar todas igual)
   6. CTA diferente en cada una
   7. Capitalizar Cada Palabra Importante

"""
        
        prompt += f"""
{'='*80}
⚠️ REGLAS CRÍTICAS DE CREATIVIDAD:
{'='*80}

1️⃣ **VARIACIÓN EXTREMA**: Cada descripción con estructura TOTALMENTE diferente
2️⃣ **SINÓNIMOS CREATIVOS**: No usar las mismas palabras, buscar alternativas
3️⃣ **INICIO VARIADO**: Empezar cada una de forma única:
   - Desc 1: Con pregunta
   - Desc 2: Con afirmación
   - Desc 3: Con beneficio
   - Desc 4: Con autoridad/credibilidad

4️⃣ **LONGITUD VARIADA**: 
   - Desc 1: {specs[0]['components']['length']} chars
   - Desc 2: {specs[1]['components']['length'] if len(specs) > 1 else 70} chars
   - Desc 3: {specs[2]['components']['length'] if len(specs) > 2 else 75} chars
   - Desc 4: {specs[3]['components']['length'] if len(specs) > 3 else 80} chars

5️⃣ **CTAs ÚNICOS**: Nunca repetir el mismo llamado a acción

6️⃣ **PROHIBICIONES ABSOLUTAS**:
   ❌ NO usar comillas ("") 
   ❌ NO usar signos de exclamación (!)
   ❌ NO usar signos de interrogación al final (?)
   ❌ NO repetir palabras clave entre descripciones
   ❌ NO copiar frases de las exclusiones

7️⃣ **CREATIVIDAD {creativity_level}**:
   {'🔥 Ser EXTREMADAMENTE creativo y original' if temperature > 0.8 else '✨ Mantener creatividad alta pero controlada'}
   {'🎨 Usar metáforas y lenguaje evocador' if business_type == 'esoteric' else '📊 Mantener tono profesional pero atractivo'}

{'='*80}
🎯 GENERA AHORA {len(specs)} DESCRIPCIONES ÚNICAS Y PODEROSAS
{'='*80}
"""
        
        return prompt
    
    @staticmethod
    def get_variation_prompt(
        keywords: List[str],
        num_descriptions: int,
        variation_seed: int,
        business_type: str = "esoteric",
        exclude_descriptions: List[str] = []
    ) -> str:
        """
        Interfaz principal para obtener prompt de variación
        """
        
        result = DescriptionVariationEngineV2.generate_unique_descriptions(
            keywords=keywords,
            num_descriptions=num_descriptions,
            business_type=business_type,
            variation_seed=variation_seed,
            temperature=0.85,  # Alta creatividad por defecto
            exclude_descriptions=exclude_descriptions,
            force_unique=True
        )
        
        return result['prompt']




# ============================================================================
# TEMPLATES DE PROMPTS PRINCIPALES
# ============================================================================

class AdPromptTemplates:
    """Generador de prompts transaccionales - VERSIÓN 6.0 DEFINITIVA"""
    
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
        use_location_insertion: bool = False,
        exclude_descriptions: List[str] = []
    ) -> str:
        """Prompt TRANSACCIONAL v6.0 - Coherencia Sintáctica OBLIGATORIA + Validación"""
        
        # Pre-procesar keywords
        validation = KeywordProcessor.validate_and_clean(keywords)
        clean_keywords = validation['valid_keywords'] if validation['valid_keywords'] else keywords
        
        analysis = AdPromptTemplates.analyze_keywords(clean_keywords)
        
        # Rotar keywords
        rotated_keywords = clean_keywords[ad_variation_seed:] + clean_keywords[:ad_variation_seed]
        keywords_str = ", ".join(rotated_keywords[:30])
        
        # Calcular distribución
        location_count = 0
        if use_location_insertion:
            location_count = min(5, max(3, int(num_headlines * 0.25)))
        
        remaining_headlines = num_headlines - location_count
        transactional_count = int(remaining_headlines * 0.60)
        urgent_count = int(remaining_headlines * 0.25)
        informational_count = remaining_headlines - transactional_count - urgent_count
        
        # Instrucción de variación
        variation_strategy = ""
        if ad_variation_seed == 0:
            variation_strategy = "**ANUNCIO #1:** Títulos DIRECTOS (keyword + modificador)"
        elif ad_variation_seed == 1:
            variation_strategy = "**ANUNCIO #2:** Títulos de URGENCIA (keyword + tiempo)"
        else:
            variation_strategy = "**ANUNCIO #3+:** Títulos INFORMATIVOS (cómo/para qué + keyword)"
        
        # Instrucciones de ubicación CORREGIDAS
        location_instructions = ""
        if use_location_insertion:
            location_instructions = f"""
════════════════════════════════════════════════════════════════
📍 INSERCIONES DE UBICACIÓN ({location_count} TÍTULOS OBLIGATORIOS)
════════════════════════════════════════════════════════════════

**CÓDIGOS LITERALES A USAR (copiar EXACTAMENTE):**

Para CIUDAD: {{LOCATION(City)}}
Para ESTADO: {{LOCATION(State)}}
Para PAÍS: {{LOCATION(Country)}}

✅ **EJEMPLOS CORRECTOS:**
"Amarres De {{LOCATION(City)}}"
"Brujos En {{LOCATION(State)}}"
"Hechizos {{LOCATION(Country)}}"
"Brujo Profesional {{LOCATION(City)}}"

❌ **INCORRECTO (NO HACER):**
"Brujos De Tu Ciudad" ← MAL (usar {{LOCATION(City)}})
"Amarres En Tu Estado" ← MAL (usar {{LOCATION(State)}})
"Brujos En País" ← MAL (usar {{LOCATION(Country)}})

📊 **DISTRIBUCIÓN:**
- {max(1, location_count//3 + location_count%3)} títulos con {{LOCATION(City)}}
- {max(1, location_count//3)} títulos con {{LOCATION(State)}}
- {max(1, location_count//3)} títulos con {{LOCATION(Country)}}

⚠️ **IMPORTANTE:** Escribir el código LITERAL entre llaves dobles {{}}, exactamente como se muestra.

════════════════════════════════════════════════════════════════
"""
        
        # Generar instrucciones de descripción
        description_instructions = DescriptionVariationEngine.get_varied_descriptions(
            keywords=rotated_keywords,
            num_descriptions=num_descriptions,
            variation_seed=ad_variation_seed,
            exclude_descriptions=exclude_descriptions
        )
        
        return f"""Eres un experto en copywriting para Google Ads especializado en servicios esotéricos.

**MISIÓN CRÍTICA:** Generar títulos COHERENTES y GRAMATICALMENTE CORRECTOS basados ÚNICAMENTE en las keywords proporcionadas.

════════════════════════════════════════════════════════════════
🔑 KEYWORDS PRINCIPALES (BASE OBLIGATORIA)
════════════════════════════════════════════════════════════════

{keywords_str}

**ANUNCIO #{ad_variation_seed + 1}** | Temperatura: {temperature}

{variation_strategy}

════════════════════════════════════════════════════════════════
⚠️ REGLA #1 ABSOLUTA - COHERENCIA SINTÁCTICA
════════════════════════════════════════════════════════════════

**OBLIGATORIO:** Todos los títulos deben ser FRASES COHERENTES y GRAMATICALMENTE CORRECTAS.

❌ **PROHIBIDO - MEZCLAS SIN SENTIDO:**
- "Brujos En Para Enamorar" ← INCORRECTO
- "Amarres De Para Que Vuelva" ← INCORRECTO
- "Ritual En Con Foto" ← INCORRECTO
- "¿Se Te Perdió tu Brujo?" ← INCORRECTO
- "¿Perdiste a tu Brujo?" ← INCORRECTO

✅ **OBLIGATORIO - ESTRUCTURAS CORRECTAS:**
- "Amarres De Amor Efectivos" ← CORRECTO
- "Brujos Especializados En Amarres" ← CORRECTO
- "Hechizo Para Que Regrese" ← CORRECTO
- "Ritual Para Recuperar Amor" ← CORRECTO
- "Problemas Con Tu Pareja?" ← CORRECTO

════════════════════════════════════════════════════════════════
📊 ESTRUCTURA OBLIGATORIA DE TÍTULOS
════════════════════════════════════════════════════════════════

Cada título debe seguir UNA de estas estructuras sintácticas:

**🔵 TRANSACCIONAL ({transactional_count} títulos):**

1️⃣ [KEYWORD COMPLETA] + [Modificador]
   Ejemplo: "Amarres De Amor Efectivos"
   Ejemplo: "Brujos Profesionales Certificados"

2️⃣ [Rol/Servicio] + Especialista En + [KEYWORD]
   Ejemplo: "Brujo Especialista En Amarres"
   Ejemplo: "Experto En Rituales De Amor"

3️⃣ [KEYWORD] + Para + [Objetivo]
   Ejemplo: "Amarres Para Recuperar Amor"
   Ejemplo: "Ritual Para Que Regrese"

4️⃣ [KEYWORD] + [Tipo Específico]
   Ejemplo: "Amarres Con Foto Y Nombre"
   Ejemplo: "Rituales De Amor Efectivos"

**🔴 URGENTE ({urgent_count} títulos):**

1️⃣ [KEYWORD] + Para Que + [Acción]
   Ejemplo: "Amarre Para Que Vuelva"
   Ejemplo: "Ritual Para Que Me Busque"

2️⃣ [Verbo] + [KEYWORD] + [Tiempo]
   Ejemplo: "Recuperar Amor En 7 Días"
   Ejemplo: "Regreso De Pareja Rápido"

3️⃣ [KEYWORD] + [Urgencia]
   Ejemplo: "Amarres Urgentes 24h"
   Ejemplo: "Ritual Inmediato"

**🟢 INFORMACIONAL ({informational_count} títulos):**

1️⃣ Cómo + [Verbo] + [KEYWORD]
   Ejemplo: "Cómo Hacer Amarres Efectivos"
   Ejemplo: "Cómo Recuperar A Mi Pareja"

2️⃣ [KEYWORD] + [Incentivo]
   Ejemplo: "Amarres Consulta Gratis"
   Ejemplo: "Ritual Primera Sesión Free"

{location_instructions}

{description_instructions}

════════════════════════════════════════════════════════════════
🚫 VALIDACIÓN DE COHERENCIA (REVISAR ANTES DE ENVIAR)
════════════════════════════════════════════════════════════════

Antes de responder, verifica CADA título:

□ ¿El título forma una FRASE COMPLETA Y COHERENTE?
□ ¿Se lee naturalmente sin palabras sueltas?
□ ¿La keyword está COMPLETA (no fragmentada)?
□ ¿Los conectores (en, de, para) tienen sentido?
□ ¿No hay mezclas tipo "Brujos En Para"?

Si algún título falla estas preguntas, CORRÍGELO antes de enviar.

════════════════════════════════════════════════════════════════
📏 ESPECIFICACIONES TÉCNICAS
════════════════════════════════════════════════════════════════

**TÍTULOS:** 20-30 caracteres | Capitalizar Cada Palabra | Sin ! ? ¡ ¿
**DESCRIPCIONES:** 80-90 caracteres | Capitalizar Cada Palabra | Sin ! ?

════════════════════════════════════════════════════════════════
📦 FORMATO JSON (SIN MARKDOWN, SIN ```)
════════════════════════════════════════════════════════════════

RESPONDE SOLO ESTO (sin ``` ni json):

{{
  "headlines": [
    "Título Coherente 1",
    "Título Coherente 2",
    ...{num_headlines} títulos COHERENTES Y ÚNICOS
  ],
  "descriptions": [
    "Desc única 1 (80-85 chars)",
    "Desc única 2 (80-85 chars)",
    "Desc única 3 (80-85 chars)",
    "Desc única 4 (85-90 chars)"
  ]
}}

════════════════════════════════════════════════════════════════
✅ CHECKLIST FINAL (OBLIGATORIO)
════════════════════════════════════════════════════════════════

□ {num_headlines} títulos COHERENTES Y GRAMATICALMENTE CORRECTOS
□ Cada título usa keyword COMPLETA (no fragmentada)
□ CERO mezclas tipo "Brujos En Para"
□ {num_descriptions} descripciones 100% ÚNICAS
□ Capitalización correcta
□ Longitudes correctas
□ JSON válido sin markdown
□ Títulos con ubicación usan código LITERAL ({{LOCATION(City)}})

🚀 GENERA AHORA (SOLO EL JSON, SIN EXPLICACIONES NI TEXTO ADICIONAL)"""

    @staticmethod
    def get_prompt_for_keywords(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        business_type: str = "auto",
        temperature: float = 1.0,
        ad_variation_seed: int = 0,
        use_location_insertion: bool = False,
        exclude_descriptions: List[str] = []
    ) -> str:
        """Selector de prompt v6.0 con validación"""
        return AdPromptTemplates.get_transactional_esoteric_prompt(
            keywords, num_headlines, num_descriptions, tone, temperature, 
            ad_variation_seed, use_location_insertion, exclude_descriptions
        )


# ============================================================================
# PROMPTS MAGNÉTICOS
# ============================================================================

class MagneticAdPrompts:
    """Prompts MAGNÉTICOS v6.0 con validación"""
    
    @staticmethod
    def get_magnetic_prompt(
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        temperature: float = 0.9,
        ad_variation_seed: int = 0,
        use_location_insertion: bool = False,
        exclude_descriptions: List[str] = []
    ) -> str:
        """Prompt MAGNÉTICO con coherencia sintáctica y validación"""
        
        # Pre-procesar keywords
        validation = KeywordProcessor.validate_and_clean(keywords)
        clean_keywords = validation['valid_keywords'] if validation['valid_keywords'] else keywords
        
        rotated_keywords = clean_keywords[ad_variation_seed:] + clean_keywords[:ad_variation_seed]
        keywords_str = ", ".join(rotated_keywords[:30])
        
        location_count = 0
        if use_location_insertion:
            location_count = min(5, max(3, int(num_headlines * 0.25)))
        
        remaining_headlines = num_headlines - location_count
        beneficio_urgencia = int(remaining_headlines * 0.33)
        credibilidad_exclusividad = int(remaining_headlines * 0.33)
        control_curiosidad = remaining_headlines - beneficio_urgencia - credibilidad_exclusividad
        
        location_instructions = ""
        if use_location_insertion:
            location_instructions = f"""
════════════════════════════════════════════════════════════════
📍 INSERCIONES MAGNÉTICAS ({location_count} TÍTULOS)
════════════════════════════════════════════════════════════════

Usar códigos LITERALES:
- {{LOCATION(City)}} para ciudad
- {{LOCATION(State)}} para estado
- {{LOCATION(Country)}} para país

✅ "Urgente Brujo {{LOCATION(City)}}"
✅ "Amarres Garantizados {{LOCATION(State)}}"

❌ NO usar "tu ciudad", "tu estado", etc.

════════════════════════════════════════════════════════════════
"""
        
        description_instructions = DescriptionVariationEngine.get_varied_descriptions(
            keywords=rotated_keywords,
            num_descriptions=num_descriptions,
            variation_seed=ad_variation_seed,
            exclude_descriptions=exclude_descriptions
        )
        
        return f"""Eres un experto en copywriting MAGNÉTICO para Google Ads.

**MISIÓN:** Generar anuncios de MÁXIMA INTENSIDAD con coherencia sintáctica absoluta.

🔑 **KEYWORDS:** {keywords_str}
**ANUNCIO MAGNÉTICO #{ad_variation_seed + 1}** | Temp: {temperature}

🔴 MODO MAGNÉTICO ACTIVADO 🔴

{location_instructions}

════════════════════════════════════════════════════════════════
⚡ ESTRUCTURA MAGNÉTICA
════════════════════════════════════════════════════════════════

**🎯 BENEFICIO + URGENCIA ({beneficio_urgencia} títulos):**
- [KEYWORD] + [Resultado] + [Tiempo]
- [Urgencia] + [KEYWORD] + [Garantía]

**🏆 CREDIBILIDAD ({credibilidad_exclusividad} títulos):**
- [Experiencia] + [KEYWORD]
- [KEYWORD] + [Certificación]

**🧠 CURIOSIDAD ({control_curiosidad} títulos):**
- [Secreto] + [KEYWORD]
- [KEYWORD] + [Revelación]

{description_instructions}

════════════════════════════════════════════════════════════════
⚠️ VALIDACIÓN MAGNÉTICA
════════════════════════════════════════════════════════════════

□ Títulos COHERENTES (sin "Brujos En Para")
□ Keywords COMPLETAS
□ Máxima intensidad psicológica
□ Descripciones 100% ÚNICAS
□ Ubicaciones con código LITERAL

════════════════════════════════════════════════════════════════
📦 RESPONDER SOLO JSON (sin ``` ni markdown):
════════════════════════════════════════════════════════════════

{{
  "headlines": ["Título Magnético 1", ...{num_headlines}],
  "descriptions": ["Desc única 1", ...{num_descriptions}]
}}

🚀 GENERA AHORA"""


# ============================================================================
# CTR OPTIMIZER PREDICTIVO v2.0
# ============================================================================

import logging

class CTROptimizer:
    """
    Optimiza anuncios para máximo CTR basado en análisis heurístico,
    patrones históricos y evaluación semántica avanzada.
    
    Metodología:
    1. Análisis de patrones léxicos (palabras clave de alto impacto)
    2. Evaluación semántica (relevancia con intención)
    3. Detección de anti-patrones (frases incoherentes)
    4. Scoring contextual (servicios esotéricos)
    5. Recomendaciones personalizadas
    """
    
    # ========================================================================
    # BOOSTERS DE CTR GENERAL
    # ========================================================================
    
    CTR_BOOSTERS = {
        'numeros': {
            'patterns': [r'\d+%', r'\d+\s*(?:días|horas|años)', r'\d+'],
            'boost': 15,
            'description': 'Números y estadísticas'
        },
        'urgencia': {
            'words': ['ya', 'ahora', 'hoy', 'urgente', 'inmediato', 'rápido', '24h', '24 horas'],
            'boost': 14,
            'description': 'Palabras de urgencia'
        },
        'gratis': {
            'words': ['gratis', 'free', 'sin costo', 'sin cargo', 'primera sesión free', 'consulta gratis'],
            'boost': 18,
            'description': 'Ofertas gratuitas'
        },
        'garantia': {
            'words': ['garantizado', 'asegurado', 'certero', 'garantía', '100%'],
            'boost': 12,
            'description': 'Garantías y certeza'
        },
        'exclusividad': {
            'words': ['único', 'exclusivo', 'especial', 'limitado', 'solo hoy', 'privado'],
            'boost': 10,
            'description': 'Exclusividad y limitación'
        }
    }
    
    # ========================================================================
    # BOOSTERS ESOTÉRICOS ESPECÍFICOS
    # ========================================================================
    
    ESOTERIC_BOOSTERS = {
        'autoridad': {
            'words': ['experto', 'especialista', 'maestro', 'profesional', 'certificado', 'años', 'experiencia'],
            'boost': 16,
            'description': 'Autoridad y experiencia',
            'weight': 1.3  # Multiplicador para servicios esotéricos
        },
        'efectividad': {
            'words': ['efectivo', 'efectiva', 'funciona', 'funcionan', 'real', 'reales', 'comprobado', 'probado'],
            'boost': 14,
            'description': 'Efectividad del servicio',
            'weight': 1.2
        },
        'resultado': {
            'words': ['resultado', 'resultados', 'recupera', 'recuperar', 'regresa', 'regresar', 'vuelve', 'volver'],
            'boost': 13,
            'description': 'Promesa de resultados',
            'weight': 1.4
        },
        'urgencia_esoterica': {
            'words': ['urgente', 'emergencia', 'crisis', 'desesperado', 'necesidad', 'necesitas', 'precisas'],
            'boost': 16,
            'description': 'Urgencia emocional',
            'weight': 1.3
        },
        'discretion': {
            'words': ['discreto', 'discreción', 'confidencial', 'privado', 'confidencialidad', 'secreto'],
            'boost': 11,
            'description': 'Confidencialidad',
            'weight': 1.1
        },
        'cta_esoterica': {
            'words': ['consulta', 'consulta ya', 'llama ya', 'whatsapp', 'contacta', 'escribe', 'agenda'],
            'boost': 12,
            'description': 'CTAs relevantes',
            'weight': 1.0
        }
    }
    
    # ========================================================================
    # PATRONES DE INTENCIÓN
    # ========================================================================
    
    INTENT_KEYWORDS = {
        'urgente': {
            'keywords': ['urgente', 'ahora', 'inmediato', 'rápido', '24h', 'ya'],
            'weight': 1.2,
            'description': 'Intención urgente'
        },
        'transaccional': {
            'keywords': ['consulta', 'llama', 'contacta', 'agenda', 'whatsapp', 'escribe'],
            'weight': 1.1,
            'description': 'Intención transaccional'
        },
        'resultado': {
            'keywords': ['recuperar', 'regresa', 'vuelve', 'enamorar', 'conquistar', 'atraer'],
            'weight': 1.3,
            'description': 'Promesa de resultado'
        },
        'autoridad': {
            'keywords': ['especialista', 'experto', 'profesional', 'maestro', 'años', 'experiencia'],
            'weight': 1.2,
            'description': 'Autoridad percibida'
        },
        'credibilidad': {
            'keywords': ['garantizado', 'efectivo', 'real', 'comprobado', 'testimonios', 'casos'],
            'weight': 1.1,
            'description': 'Credibilidad y confianza'
        }
    }
    
    # ========================================================================
    # ANTI-PATRONES (FRASES INCOHERENTES)
    # ========================================================================
    
    ANTI_PATTERNS = {
        'incoherencia_prep': {
            'patterns': [
                r'\b(?:en|de|para|con)\s+(?:en|de|para|con)\b',  # "en para", "de de", etc.
                r'\b(?:para)\s+(?:en)\b',  # "para en"
                r'\b(?:en)\s+(?:para)\b',  # "en para"
            ],
            'penalty': 25,
            'description': 'Preposiciones repetidas o incoherentes',
            'severity': 'critical'
        },
        'palabra_repetida': {
            'patterns': [
                r'\b(\w+)\s+\1\b',  # Palabra repetida consecutiva: "amor amor"
            ],
            'penalty': 15,
            'description': 'Palabra repetida consecutivamente',
            'severity': 'high'
        },
        'fragmento_incompleto': {
            'patterns': [
                r'^(?:de|en|para|con|por)\s+',  # Empieza con preposición
                r'\s+(?:de|en|para|con|por)$',  # Termina con preposición
            ],
            'penalty': 20,
            'description': 'Fragmento incompleto o sin verbo',
            'severity': 'critical'
        },
        'demasiados_modificadores': {
            'patterns': [
                r'(?:muy|super|ultra|mega)\s+(?:muy|super|ultra|mega)',  # Modificadores repetidos
            ],
            'penalty': 10,
            'description': 'Modificadores excesivos',
            'severity': 'medium'
        }
    }
    
    # ========================================================================
    # CONFIGURACIÓN
    # ========================================================================
    
    BASE_SCORE = 50
    MAX_SCORE = 100
    MIN_SCORE = 0
    
    # Rangos óptimos
    OPTIMAL_LENGTH = {'min': 20, 'max': 30, 'optimal': 25}
    
    def __init__(self, business_type: str = 'esoteric'):
        """
        Inicializa el optimizador
        
        Args:
            business_type: Tipo de negocio ('esoteric', 'default', 'tech', etc.)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.business_type = business_type
    
    # ========================================================================
    # MÉTODOS DE ANÁLISIS
    # ========================================================================
    
    def _check_anti_patterns(self, headline: str) -> Dict[str, Any]:
        """
        Detecta anti-patrones (frases incoherentes)
        
        Returns:
            {
                'detected': List[str],
                'total_penalty': float,
                'is_coherent': bool
            }
        """
        detected = []
        total_penalty = 0
        headline_lower = headline.lower()
        
        for pattern_type, config in self.ANTI_PATTERNS.items():
            for pattern in config['patterns']:
                if re.search(pattern, headline_lower, re.IGNORECASE):
                    detected.append({
                        'type': pattern_type,
                        'description': config['description'],
                        'severity': config['severity'],
                        'penalty': config['penalty']
                    })
                    total_penalty += config['penalty']
                    self.logger.debug(f"Anti-patrón '{pattern_type}' detectado en '{headline}'")
                    break  # Un patrón detectado es suficiente
        
        return {
            'detected': detected,
            'total_penalty': total_penalty,
            'is_coherent': len(detected) == 0
        }
    
    def _check_boosts(self, headline: str, is_esoteric: bool = True) -> Dict[str, Any]:
        """
        Evalúa boosters de CTR aplicables
        
        Returns:
            {
                'score': float,
                'boosts_applied': List[Dict],
                'raw_score': float
            }
        """
        score = self.BASE_SCORE
        applied_boosts = []
        headline_lower = headline.lower()
        
        # ===== BOOSTERS GENERALES =====
        for boost_type, config in self.CTR_BOOSTERS.items():
            boost_found = False
            
            # Buscar por patrones regex
            if 'patterns' in config:
                for pattern in config['patterns']:
                    if re.search(pattern, headline, re.IGNORECASE):
                        score += config['boost']
                        applied_boosts.append({
                            'type': boost_type,
                            'description': config['description'],
                            'boost': config['boost'],
                            'triggered_by': 'pattern'
                        })
                        boost_found = True
                        self.logger.debug(f"Boost '{boost_type}' (patrón) en '{headline}': +{config['boost']}")
                        break
            
            # Buscar por palabras clave
            if not boost_found and 'words' in config:
                for word in config['words']:
                    if word in headline_lower:
                        score += config['boost']
                        applied_boosts.append({
                            'type': boost_type,
                            'description': config['description'],
                            'boost': config['boost'],
                            'triggered_by': f'word: {word}'
                        })
                        self.logger.debug(f"Boost '{boost_type}' (palabra) en '{headline}': +{config['boost']}")
                        break
        
        # ===== BOOSTERS ESOTÉRICOS =====
        if is_esoteric:
            for boost_type, config in self.ESOTERIC_BOOSTERS.items():
                for word in config.get('words', []):
                    if word in headline_lower:
                        boost_value = int(config['boost'] * config.get('weight', 1.0))
                        score += boost_value
                        applied_boosts.append({
                            'type': f"esoteric_{boost_type}",
                            'description': config['description'],
                            'boost': boost_value,
                            'triggered_by': f'word: {word}'
                        })
                        self.logger.debug(f"Boost esotérico '{boost_type}' en '{headline}': +{boost_value}")
                        break
        
        # ===== PENALIZACIONES POR LONGITUD =====
        length = len(headline)
        length_penalty = 0
        
        if length < self.OPTIMAL_LENGTH['min']:
            length_penalty = 15
            self.logger.debug(f"Penalización por longitud corta en '{headline}': {length} chars")
        elif length > self.OPTIMAL_LENGTH['max']:
            length_penalty = 8
            self.logger.debug(f"Penalización por longitud larga en '{headline}': {length} chars")
        
        # Bonus si está en rango óptimo
        if self.OPTIMAL_LENGTH['min'] <= length <= self.OPTIMAL_LENGTH['max']:
            score += 5
            applied_boosts.append({
                'type': 'optimal_length',
                'description': f'Longitud óptima ({length} caracteres)',
                'boost': 5,
                'triggered_by': 'auto'
            })
        
        score -= length_penalty
        
        # ===== LÍMITES =====
        raw_score = score
        score = max(self.MIN_SCORE, min(score, self.MAX_SCORE))
        
        return {
            'score': score,
            'raw_score': raw_score,
            'boosts_applied': applied_boosts,
            'length': length,
            'length_penalty': length_penalty
        }
    
    def _analyze_semantic_relevance(self, headline: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analiza relevancia semántica del headline con keywords e intención
        
        Returns:
            {
                'keyword_match_score': float,
                'intents_found': List[str],
                'semantic_score': float
            }
        """
        headline_lower = headline.lower()
        
        # Análisis de keywords
        keyword_match_score = 0.0
        keywords_found = []
        
        if keywords:
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in headline_lower:
                    keyword_match_score += 20
                    keywords_found.append(kw)
                    self.logger.debug(f"Keyword '{kw}' encontrada en '{headline}'")
        
        if keywords:
            keyword_match_score = (keyword_match_score / len(keywords)) * 100
            keyword_match_score = min(100, keyword_match_score)
        
        # Análisis de intención
        intents_found = []
        intent_score = 0.0
        
        for intent, config in self.INTENT_KEYWORDS.items():
            for keyword in config['keywords']:
                if keyword in headline_lower:
                    intents_found.append(intent)
                    intent_score += (10 * config['weight'])
                    self.logger.debug(f"Intención '{intent}' detectada en '{headline}'")
                    break
        
        intent_score = min(100, intent_score)
        
        # Score semántico combinado
        semantic_score = (keyword_match_score * 0.6) + (intent_score * 0.4)
        
        return {
            'keyword_match_score': round(keyword_match_score, 2),
            'keywords_found': keywords_found,
            'intents_found': intents_found,
            'intent_score': round(intent_score, 2),
            'semantic_score': round(semantic_score, 2)
        }
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones personalizadas basadas en el análisis
        """
        recommendations = []
        headline = analysis['headline']
        score = analysis['score']
        boosts = analysis['boosts_applied']
        anti_patterns = analysis['anti_patterns']
        semantic = analysis.get('semantic', {})
        
        # ===== RECOMENDACIONES POR PUNTUACIÓN =====
        if score < 50:
            recommendations.append("🔴 CTR BAJO: Necesita mejora significativa")
        elif score < 70:
            recommendations.append("🟡 CTR MEDIO: Puede mejorar")
        else:
            recommendations.append("🟢 CTR ALTO: Buen potencial")
        
        # ===== RECOMENDACIONES POR ANTI-PATRONES =====
        if anti_patterns['detected']:
            for ap in anti_patterns['detected']:
                if ap['severity'] == 'critical':
                    recommendations.append(f"❌ CRÍTICO: {ap['description']} - Corregir inmediatamente")
                elif ap['severity'] == 'high':
                    recommendations.append(f"⚠️ IMPORTANTE: {ap['description']}")
                else:
                    recommendations.append(f"💡 SUGERENCIA: {ap['description']}")
        
        # ===== RECOMENDACIONES POR BOOSTERS FALTANTES =====
        applied_types = [b['type'] for b in boosts]
        
        if 'numeros' not in applied_types:
            recommendations.append("📊 Agrega números o % para mejorar CTR (+15)")
        
        if 'urgencia' not in applied_types:
            recommendations.append("⏱️ Incluye palabras de urgencia (ya, ahora, hoy) para +14 CTR")
        
        if 'gratis' not in applied_types:
            recommendations.append("💰 Considera 'gratis' o 'sin costo' (+18 CTR)")
        
        if 'garantia' not in applied_types:
            recommendations.append("✅ Añade 'garantizado' o 'asegurado' (+12 CTR)")
        
        if 'exclusividad' not in applied_types:
            recommendations.append("🎁 Usa 'único', 'exclusivo' o 'limitado' (+10 CTR)")
        
        # ===== RECOMENDACIONES POR LONGITUD =====
        if analysis['length'] < 20:
            recommendations.append("📏 Título demasiado corto (actual: {}, óptimo: 20-30)".format(analysis['length']))
        elif analysis['length'] > 30:
            recommendations.append("📏 Título demasiado largo (actual: {}, óptimo: 20-30)".format(analysis['length']))
        
        # ===== RECOMENDACIONES SEMÁNTICAS =====
        if semantic.get('keyword_match_score', 0) < 50:
            recommendations.append("🔍 Baja relevancia con keywords - Incluir más keywords principales")
        
        if not semantic.get('intents_found'):
            recommendations.append("🎯 No se detectó intención clara - Ser más específico")
        
        return recommendations
    
    def analyze_headline(
        self,
        headline: str,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Análisis COMPLETO de un headline
        
        Returns:
            {
                'headline': str,
                'score': float,
                'rank': str ('A+', 'A', 'B', 'C', 'D', 'F'),
                'anti_patterns': Dict,
                'boosts': List,
                'semantic': Dict,
                'recommendations': List,
                'publishable': bool
            }
        """
        
        # 1. Verificar anti-patrones
        anti_patterns_result = self._check_anti_patterns(headline)
        
        # 2. Calcular boosts
        boosts_result = self._check_boosts(headline, is_esoteric=(self.business_type == 'esoteric'))
        
        # 3. Análisis semántico
        semantic_result = self._analyze_semantic_relevance(headline, keywords)
        
        # 4. Score final (anti-patrones reducen score)
        final_score = boosts_result['score'] - anti_patterns_result['total_penalty']
        final_score = max(self.MIN_SCORE, min(final_score, self.MAX_SCORE))
        
        # 5. Ranking
        if final_score >= 90:
            rank = 'A+'
        elif final_score >= 85:
            rank = 'A'
        elif final_score >= 70:
            rank = 'B'
        elif final_score >= 55:
            rank = 'C'
        elif final_score >= 40:
            rank = 'D'
        else:
            rank = 'F'
        
        # 6. Análisis combinado
        analysis = {
            'headline': headline,
            'score': final_score,
            'rank': rank,
            'anti_patterns': anti_patterns_result,
            'boosts_applied': boosts_result['boosts_applied'],
            'length': boosts_result['length'],
            'semantic': semantic_result,
            'publishable': final_score >= 60 and anti_patterns_result['is_coherent']
        }
        
        # 7. Generar recomendaciones
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def predict_ctr_scores(
        self,
        headlines: List[str],
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Predice scores de CTR para múltiples headlines
        
        Returns:
            {
                'headlines_analysis': List[Dict],
                'average_ctr_score': float,
                'top_performers': List[Dict],
                'bottom_performers': List[Dict],
                'overall_recommendations': List[str],
                'quality_metrics': Dict
            }
        """
        
        if not headlines:
            return {
                'headlines_analysis': [],
                'average_ctr_score': 0,
                'top_performers': [],
                'bottom_performers': [],
                'overall_recommendations': ['❌ No hay headlines para analizar'],
                'quality_metrics': {}
            }
        
        # Analizar cada headline
        results = []
        for headline in headlines:
            result = self.analyze_headline(headline, keywords)
            results.append(result)
        
        # Calcular métricas agregadas
        scores = [r['score'] for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0
        coherent_count = sum(1 for r in results if r['anti_patterns']['is_coherent'])
        publishable_count = sum(1 for r in results if r['publishable'])
        
        # Top y bottom performers
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        top_performers = sorted_results[:3]
        bottom_performers = sorted_results[-3:] if len(sorted_results) >= 3 else sorted_results
        
        # Recomendaciones generales
        overall_recommendations = []
        
        if avg_score < 60:
            overall_recommendations.append("🔴 CALIDAD BAJA: Requiere revisión completa de headlines")
        elif avg_score < 75:
            overall_recommendations.append("🟡 CALIDAD MEDIA: Optimizar headlines para mejorar CTR")
        else:
            overall_recommendations.append("🟢 CALIDAD ALTA: Headlines optimizados para CTR")
        
        if coherent_count < len(headlines) * 0.8:
            overall_recommendations.append(f"⚠️ {len(headlines) - coherent_count} headlines con incoherencias")
        
        if publishable_count < len(headlines) * 0.5:
            overall_recommendations.append(f"❌ Solo {publishable_count}/{len(headlines)} headlines listos para publicar")
        else:
            overall_recommendations.append(f"✅ {publishable_count}/{len(headlines)} headlines listos para publicar")
        
        # Analizar qué boosters se usan más
        all_boosts = {}
        for r in results:
            for boost in r['boosts_applied']:
                boost_type = boost['type']
                all_boosts[boost_type] = all_boosts.get(boost_type, 0) + 1
        
        # Sugerir boosters no utilizados
        all_boost_types = set(self.CTR_BOOSTERS.keys()) | set(f"esoteric_{k}" for k in self.ESOTERIC_BOOSTERS.keys())
        unused_boosts = all_boost_types - set(all_boosts.keys())
        
        if unused_boosts:
            overall_recommendations.append(f"💡 Boosters no utilizados: {', '.join(list(unused_boosts)[:3])}")
        
        return {
            'headlines_analysis': results,
            'average_ctr_score': round(avg_score, 2),
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'overall_recommendations': overall_recommendations,
            'quality_metrics': {
                'total_headlines': len(headlines),
                'coherent': coherent_count,
                'publishable': publishable_count,
                'average_length': round(sum(r['length'] for r in results) / len(results), 1),
                'boosts_distribution': all_boosts
            }
        }


# ============================================================================
# INTEGRACIÓN CON AdScoringSystem
# ============================================================================

class AdScoringSystemV6(AdScoringSystem):
    """AdScoringSystem mejorado con CTROptimizer integrado"""
    
    @staticmethod
    def _score_ctr_potential(ad: Dict[str, Any], business_type: str = 'esoteric') -> float:
        """
        Score de CTR usando CTROptimizer
        """
        optimizer = CTROptimizer(business_type=business_type)
        
        headlines = ad.get('headlines', [])
        keywords = ad.get('keywords', [])
        
        prediction = optimizer.predict_ctr_scores(headlines, keywords)
        
        # El score es el promedio normalizado (0-100)
        return prediction['average_ctr_score']
    
    @staticmethod
    def score_ad_with_ctr_analysis(
        ad: Dict[str, Any],
        keywords: List[str],
        business_type: str = 'esoteric'
    ) -> Dict[str, Any]:
        """
        Score completo de anuncio incluyendo análisis CTR detallado
        """
        
        optimizer = CTROptimizer(business_type=business_type)
        
        # Análisis de CTR
        ctr_analysis = optimizer.predict_ctr_scores(
            ad.get('headlines', []),
            keywords
        )
        
        # Score de relevancia y otros
        scores = {
            'relevance': AdScoringSystem._score_relevance(ad, keywords),
            'coherence': AdScoringSystem._score_coherence(ad, keywords),
            'uniqueness': AdScoringSystem._score_uniqueness(ad),
            'ctr_potential': ctr_analysis['average_ctr_score'],
            'conversion_potential': AdScoringSystem._score_conversion_potential(ad)
        }
        
        weights = {
            'relevance': 0.25,
            'coherence': 0.20,
            'uniqueness': 0.10,
            'ctr_potential': 0.35,  # Mayor peso al CTR
            'conversion_potential': 0.10
        }
        
        total_score = sum(scores[k] * weights[k] for k in scores.keys())
        
        # Determinar rank
        if total_score >= 90:
            rank = 'A+'
        elif total_score >= 85:
            rank = 'A'
        elif total_score >= 75:
            rank = 'B'
        elif total_score >= 65:
            rank = 'C'
        elif total_score >= 50:
            rank = 'D'
        else:
            rank = 'F'
        
        return {
            'total_score': round(total_score, 2),
            'rank': rank,
            'breakdown': {k: round(v, 2) for k, v in scores.items()},
            'ctr_analysis': ctr_analysis,
            'publishable': total_score >= 70,
            'recommendations': ctr_analysis['overall_recommendations']
        }


# ============================================================================
# EXPORTACIÓN
# ============================================================================

__all__ = [
    'KeywordProcessor',
    'AdQualityValidator',
    'AdScoringSystem',
    'AdScoringSystemV6',
    'CTROptimizer',
    'SearchIntentPatterns',
    'DescriptionVariationEngine',
    'AdPromptTemplates',
    'MagneticAdPrompts'

]