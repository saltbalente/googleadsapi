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

class DescriptionVariationEngine:
    """🎨 MOTOR DE VARIACIÓN DE DESCRIPCIONES - ANTI-REPETICIÓN"""
    
    STRUCTURES_BANK = [
        # SET 1 - TRANSFORMACIÓN
        {
            "name": "TRANSFORMACIÓN",
            "desc1": {
                "pattern": "ACCIÓN + BENEFICIO + CTA",
                "verbs": ["Transforma", "Renueva", "Fortalece", "Mejora"],
                "benefits": ["Tu Relación", "Tu Vida", "Tu Situación"],
                "ctas": ["Consulta Ya", "Llama 24h", "WhatsApp Ahora"]
            },
            "desc2": {
                "pattern": "RESULTADO + TIEMPO + CTA",
                "results": ["Garantizado", "Efectivo", "Real", "Comprobado"],
                "times": ["En 7 Días", "En 24h", "Rápido"],
                "ctas": ["Agenda Cita", "Contáctanos", "Llama Ya"]
            },
            "desc3": {
                "pattern": "PREGUNTA + SOLUCIÓN + CTA",
                "questions": ["¿Necesitas", "¿Buscas", "¿Quieres"],
                "solutions": ["Solución Real", "Ayuda Profesional", "Expertos Disponibles"],
                "ctas": ["Consulta Gratis", "Primera Sesión Free", "Pregunta Ahora"]
            },
            "desc4": {
                "pattern": "AUTORIDAD + DIFERENCIADOR + CTA",
                "authorities": ["Especialistas", "Expertos", "Profesionales"],
                "differentiators": ["Atención Personalizada", "Resultados Reales", "Método Único"],
                "ctas": ["Disponible 24/7", "Respuesta Rápida", "Escribe Ya"]
            }
        },
        
        # SET 2 - URGENCIA
        {
            "name": "URGENCIA",
            "desc1": {
                "pattern": "DOLOR + SOLUCIÓN + CTA",
                "pains": ["¿Perdiste", "¿Alejaste", "¿Extrañas"],
                "solutions": ["Te Ayudamos Ya", "Solución Inmediata", "Recupera Hoy"],
                "ctas": ["Llama Ahora", "WhatsApp 24h", "Chat Directo"]
            },
            "desc2": {
                "pattern": "EXPERIENCIA + CREDIBILIDAD + CTA",
                "experiences": ["20 Años", "Expertos", "Maestros"],
                "credentials": ["Miles De Casos", "Resultados Probados", "Testimonios Reales"],
                "ctas": ["Consulta Gratis", "Agenda Sesión", "Llama Ya"]
            },
            "desc3": {
                "pattern": "SERVICIO + BENEFICIO + CTA",
                "services": ["Que Funciona", "Efectivo", "Real"],
                "benefits": ["Sin Esperas", "Atención Inmediata", "Resultados Rápidos"],
                "ctas": ["Escríbenos Hoy", "Llama Gratis", "Chat Ahora"]
            },
            "desc4": {
                "pattern": "TIEMPO + RESULTADO + CTA",
                "times": ["En Pocos Días", "En 24 Horas", "Rápido"],
                "results": ["Comprobado", "Efectivo", "Real"],
                "ctas": ["Consulta Ahora", "Contacto Inmediato", "Llama 24h"]
            }
        },
        
        # SET 3 - CREDIBILIDAD
        {
            "name": "CREDIBILIDAD",
            "desc1": {
                "pattern": "TRAYECTORIA + ESPECIALIZACIÓN + CTA",
                "trajectories": ["Años De Práctica", "Tradición Familiar", "Experiencia"],
                "specializations": ["Casos Complejos", "Situaciones Difíciles", "Todo Tipo"],
                "ctas": ["Primera Consulta Free", "Evaluación Gratis", "Pregunta Ya"]
            },
            "desc2": {
                "pattern": "PRUEBA SOCIAL + INVITACIÓN + CTA",
                "proofs": ["Clientes Satisfechos", "Testimonios Reales", "Casos Exitosos"],
                "invitations": ["Únete A Ellos", "Tú También Puedes", "Compruébalo"],
                "ctas": ["Contacta Ya", "Agenda Hoy", "Llama Gratis"]
            },
            "desc3": {
                "pattern": "MÉTODO + GARANTÍA + CTA",
                "methods": ["Técnicas Ancestrales", "Rituales Efectivos", "Sistema Único"],
                "guarantees": ["Resultados Garantizados", "Sin Riesgos", "Confidencial"],
                "ctas": ["Consulta Confidencial", "Llama Discreto", "WhatsApp Ya"]
            },
            "desc4": {
                "pattern": "DIFERENCIACIÓN + CTA",
                "differentiations": ["A Diferencia De Otros", "Método Real", "Técnica Comprobada"],
                "ctas": ["Comprueba Tú Mismo", "Verifica Ahora", "Llama Ya"]
            }
        },
        
        # SET 4 - CURIOSIDAD
        {
            "name": "CURIOSIDAD",
            "desc1": {
                "pattern": "SECRETO + REVELACIÓN + CTA",
                "secrets": ["El Método", "La Técnica", "El Secreto"],
                "revelations": ["Que Funciona", "Expertos Usan", "Da Resultados"],
                "ctas": ["Descúbrelo Ya", "Conócelo Ahora", "Pregunta Ya"]
            },
            "desc2": {
                "pattern": "PROBLEMA + SOLUCIÓN + CTA",
                "problems": ["¿Por Qué Falla", "¿Por Qué No Funciona"],
                "solutions": ["Tenemos La Solución", "Lo Hacemos Bien"],
                "ctas": ["Consulta Expertos", "Llama Ya", "Escribe Ya"]
            },
            "desc3": {
                "pattern": "DESEO + SOLUCIÓN + CTA",
                "desires": ["Quieres", "Necesitas", "Buscas"],
                "solutions": ["Tenemos La Respuesta", "Método Que Funciona"],
                "ctas": ["Prueba Ahora", "Compruébalo", "Verifica Gratis"]
            },
            "desc4": {
                "pattern": "CALIDAD + CTA",
                "qualities": ["Profesional", "Efectivo", "Real"],
                "ctas": ["Consulta Precio", "Pregunta Sin Compromiso", "Llama Ya"]
            }
        }
    ]
    
    @staticmethod
    def get_varied_descriptions(
        keywords: List[str],
        num_descriptions: int,
        variation_seed: int,
        exclude_descriptions: List[str] = []
    ) -> str:
        """Genera instrucciones de descripción con VARIACIÓN GARANTIZADA"""
        
        structure_set = DescriptionVariationEngine.STRUCTURES_BANK[
            variation_seed % len(DescriptionVariationEngine.STRUCTURES_BANK)
        ]
        
        kw_desc = []
        for i in range(num_descriptions):
            kw_desc.append(keywords[i % len(keywords)] if keywords else f"keyword{i+1}")
        
        excluded_text = ""
        if exclude_descriptions:
            excluded_text = f"""
🚫 **DESCRIPCIONES YA USADAS (EVITAR >85% SIMILITUD):**
{chr(10).join([f"   ❌ '{desc[:65]}...'" for desc in exclude_descriptions[:10]])}
"""
        
        instructions = f"""
════════════════════════════════════════════════════════════════
📝 DESCRIPCIONES ÚNICAS - SET: {structure_set['name']} (#{variation_seed + 1})
════════════════════════════════════════════════════════════════

{excluded_text}

**📄 Descripción 1 - {structure_set['desc1']['pattern']}**
🔑 Keyword: "{kw_desc[0]}"
📏 60-75 caracteres
💡 Combinar creativamente elementos de: {', '.join(list(structure_set['desc1'].values())[1][:3])}

**📄 Descripción 2 - {structure_set['desc2']['pattern']}**
🔑 Keyword: "{kw_desc[1]}"
📏 65-80 caracteres
💡 Combinar: {', '.join(list(structure_set['desc2'].values())[1][:3])}

**📄 Descripción 3 - {structure_set['desc3']['pattern']}**
🔑 Keyword: "{kw_desc[2]}"
📏 70-85 caracteres
💡 Combinar: {', '.join(list(structure_set['desc3'].values())[1][:3])}

**📄 Descripción 4 - {structure_set['desc4']['pattern']}**
🔑 Keyword: "{kw_desc[3]}"
📏 75-90 caracteres
💡 Combinar: {', '.join(list(structure_set['desc4'].values())[1][:3])}

✨ REGLAS:
1. Cada descripción 100% DIFERENTE
2. Capitalizar Cada Palabra
3. SIN signos ! ? al final
4. Incluir keyword naturalmente
5. CTAs variados

════════════════════════════════════════════════════════════════
"""
        
        return instructions


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

✅ **OBLIGATORIO - ESTRUCTURAS CORRECTAS:**
- "Amarres De Amor Efectivos" ← CORRECTO
- "Brujos Especializados En Amarres" ← CORRECTO
- "Hechizo Para Que Regrese" ← CORRECTO
- "Ritual Para Recuperar Amor" ← CORRECTO

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
**DESCRIPCIONES:** 60-90 caracteres | Capitalizar Cada Palabra | Sin ! ?

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
    "Desc única 1 (60-75 chars)",
    "Desc única 2 (65-80 chars)",
    "Desc única 3 (70-85 chars)",
    "Desc única 4 (75-90 chars)"
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
# EXPORTACIÓN
# ============================================================================

__all__ = [
    'KeywordProcessor',
    'AdQualityValidator',
    'AdScoringSystem',
    'SearchIntentPatterns',
    'DescriptionVariationEngine',
    'AdPromptTemplates',
    'MagneticAdPrompts'
]