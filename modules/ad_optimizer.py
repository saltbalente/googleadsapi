"""
🎯 AD OPTIMIZER - Optimizador Inteligente de Anuncios
Sistema avanzado de análisis, scoring y optimización de anuncios con IA
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter
import statistics

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdOptimizer:
    """
    Optimizador inteligente de anuncios que proporciona:
    - Scoring de calidad (1-10) para cada elemento
    - Detección de problemas y repeticiones
    - Sugerencias de mejora con IA
    - Análisis de palabras clave
    - Optimización automática
    - Validación avanzada contra políticas
    """
    
    # Palabras prohibidas y problemáticas
    FORBIDDEN_WORDS = [
        'gratis siempre', '100% garantizado', 'milagro', 'infalible',
        'engaño', 'estafa', 'magia negra gratuita', 'seguro que funciona',
        'nunca falla', 'totalmente gratis', 'sin riesgo alguno'
    ]
    
    # Palabras de poder positivas
    POWER_WORDS = [
        'garantizado', 'efectivo', 'profesional', 'experto', 'certificado',
        'poderoso', 'rápido', 'inmediato', 'real', 'auténtico', 'discreto',
        'personalizado', 'exclusivo', 'comprobado', 'urgente', 'ahora'
    ]
    
    # Palabras de acción (CTAs)
    ACTION_WORDS = [
        'descubre', 'obtén', 'consigue', 'solicita', 'pide', 'consulta',
        'conoce', 'aprende', 'mejora', 'transforma', 'cambia', 'encuentra',
        'recibe', 'accede', 'contacta', 'llama', 'escribe'
    ]
    
    # Palabras emocionales
    EMOTIONAL_WORDS = [
        'amor', 'felicidad', 'paz', 'esperanza', 'confianza', 'seguridad',
        'protección', 'éxito', 'prosperidad', 'armonía', 'bienestar'
    ]
    
    def __init__(
        self,
        ai_provider=None,
        enable_ai_suggestions: bool = True,
        strict_mode: bool = False
    ):
        """
        Inicializa el optimizador de anuncios.
        
        Args:
            ai_provider: Proveedor de IA para sugerencias (opcional)
            enable_ai_suggestions: Habilitar sugerencias con IA
            strict_mode: Modo estricto de validación
        """
        self.ai_provider = ai_provider
        self.enable_ai_suggestions = enable_ai_suggestions
        self.strict_mode = strict_mode
        
        # Estadísticas
        self.optimization_stats = {
            'total_optimizations': 0,
            'avg_score_before': 0.0,
            'avg_score_after': 0.0,
            'improvements': 0
        }
        
        logger.info(f"✅ AdOptimizer inicializado")
        logger.info(f"   - AI sugerencias: {'Habilitadas' if enable_ai_suggestions else 'Deshabilitadas'}")
        logger.info(f"   - Modo estricto: {'ON' if strict_mode else 'OFF'}")
    
    # =========================================================================
    # SCORING DE CALIDAD
    # =========================================================================
    
    def score_headline(self, headline: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calcula score de calidad para un titular (1-10).
        
        Args:
            headline: Titular a evaluar
            keywords: Keywords opcionales para contexto
        
        Returns:
            Diccionario con score y detalles
        """
        score = 10.0
        issues = []
        strengths = []
        recommendations = []
        
        # Validar longitud
        length = len(headline)
        
        if length > 30:
            score -= 3.0
            issues.append(f"Excede límite de 30 caracteres ({length} chars)")
        elif length > 28:
            score -= 1.0
            issues.append(f"Cerca del límite ({length}/30 chars)")
        elif length < 15:
            score -= 1.5
            issues.append(f"Muy corto, podría ser más descriptivo ({length} chars)")
        else:
            strengths.append(f"Longitud óptima ({length} chars)")
        
        # Validar mayúsculas
        if headline.isupper():
            score -= 2.0
            issues.append("Todo en mayúsculas (prohibido)")
        elif sum(1 for c in headline if c.isupper()) / len(headline) > 0.5:
            score -= 1.0
            issues.append("Demasiadas mayúsculas")
        
        # Validar caracteres especiales problemáticos
        forbidden_chars = ['!', '?', '¡', '¿']
        for char in forbidden_chars:
            if char in headline:
                score -= 1.0
                issues.append(f"Contiene caracter prohibido: '{char}'")
                break
        
        # Validar palabras prohibidas
        headline_lower = headline.lower()
        for forbidden in self.FORBIDDEN_WORDS:
            if forbidden in headline_lower:
                score -= 2.5
                issues.append(f"Contiene frase prohibida: '{forbidden}'")
        
        # Puntos positivos: palabras de poder
        power_word_count = sum(1 for word in self.POWER_WORDS if word in headline_lower)
        if power_word_count > 0:
            score += min(power_word_count * 0.5, 1.5)
            strengths.append(f"Contiene {power_word_count} palabra(s) de poder")
        
        # Puntos positivos: palabras de acción
        action_word_count = sum(1 for word in self.ACTION_WORDS if word in headline_lower)
        if action_word_count > 0:
            score += min(action_word_count * 0.3, 1.0)
            strengths.append(f"Contiene {action_word_count} palabra(s) de acción")
        
        # Validar keywords si se proporcionan
        if keywords:
            keyword_matches = sum(1 for kw in keywords if kw.lower() in headline_lower)
            if keyword_matches > 0:
                score += min(keyword_matches * 0.5, 1.5)
                strengths.append(f"Incluye {keyword_matches} keyword(s) relevante(s)")
            else:
                score -= 0.5
                recommendations.append("Considera incluir keywords relevantes")
        
        # Validar números (generan confianza)
        if any(char.isdigit() for char in headline):
            score += 0.3
            strengths.append("Incluye números (genera confianza)")
        
        # Validar repeticiones de palabras
        words = headline_lower.split()
        word_counts = Counter(words)
        repeated = [word for word, count in word_counts.items() if count > 1 and len(word) > 3]
        if repeated:
            score -= 0.5
            issues.append(f"Palabras repetidas: {', '.join(repeated)}")
        
        # Normalizar score
        score = max(1.0, min(10.0, score))
        
        # Generar recomendaciones basadas en issues
        if not recommendations:
            if score < 7:
                recommendations.append("Revisa los problemas detectados y ajusta el titular")
            if length > 25:
                recommendations.append("Considera acortar para mejor visibilidad móvil")
            if power_word_count == 0:
                recommendations.append("Agrega palabras de impacto: garantizado, efectivo, profesional")
        
        result = {
            'text': headline,
            'score': round(score, 1),
            'grade': self._score_to_grade(score),
            'length': length,
            'issues': issues,
            'strengths': strengths,
            'recommendations': recommendations,
            'metrics': {
                'power_words': power_word_count,
                'action_words': action_word_count,
                'has_numbers': any(char.isdigit() for char in headline),
                'capitalization_ratio': sum(1 for c in headline if c.isupper()) / len(headline) if headline else 0
            }
        }
        
        logger.debug(f"📊 Headline scored: {score:.1f}/10 - '{headline[:30]}...'")
        
        return result
    
    def score_description(
        self, 
        description: str, 
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calcula score de calidad para una descripción (1-10).
        
        Args:
            description: Descripción a evaluar
            keywords: Keywords opcionales para contexto
        
        Returns:
            Diccionario con score y detalles
        """
        score = 10.0
        issues = []
        strengths = []
        recommendations = []
        
        # Validar longitud
        length = len(description)
        
        if length > 90:
            score -= 3.0
            issues.append(f"Excede límite de 90 caracteres ({length} chars)")
        elif length > 85:
            score -= 1.0
            issues.append(f"Cerca del límite ({length}/90 chars)")
        elif length < 40:
            score -= 1.5
            issues.append(f"Muy corta, agrega más detalles ({length} chars)")
        else:
            strengths.append(f"Longitud óptima ({length} chars)")
        
        # Validar mayúsculas
        if description.isupper():
            score -= 2.0
            issues.append("Todo en mayúsculas (prohibido)")
        
        # Validar caracteres especiales problemáticos
        forbidden_chars = ['!', '?', '¡', '¿']
        for char in forbidden_chars:
            if char in description:
                score -= 0.8
                issues.append(f"Contiene caracter prohibido: '{char}'")
                break
        
        # Validar palabras prohibidas
        description_lower = description.lower()
        for forbidden in self.FORBIDDEN_WORDS:
            if forbidden in description_lower:
                score -= 2.5
                issues.append(f"Contiene frase prohibida: '{forbidden}'")
        
        # Puntos positivos: palabras de poder
        power_word_count = sum(1 for word in self.POWER_WORDS if word in description_lower)
        if power_word_count > 0:
            score += min(power_word_count * 0.3, 1.0)
            strengths.append(f"Contiene {power_word_count} palabra(s) de poder")
        
        # Puntos positivos: palabras emocionales
        emotional_count = sum(1 for word in self.EMOTIONAL_WORDS if word in description_lower)
        if emotional_count > 0:
            score += min(emotional_count * 0.3, 1.0)
            strengths.append(f"Contiene {emotional_count} palabra(s) emocional(es)")
        
        # Validar CTA (Call to Action)
        has_cta = any(action in description_lower for action in self.ACTION_WORDS)
        if has_cta:
            score += 0.5
            strengths.append("Incluye llamada a la acción")
        else:
            recommendations.append("Considera agregar una llamada a la acción")
        
        # Validar keywords si se proporcionan
        if keywords:
            keyword_matches = sum(1 for kw in keywords if kw.lower() in description_lower)
            if keyword_matches > 0:
                score += min(keyword_matches * 0.4, 1.2)
                strengths.append(f"Incluye {keyword_matches} keyword(s) relevante(s)")
        
        # Validar estructura (puntos, comas)
        if '.' in description or ',' in description:
            score += 0.3
            strengths.append("Buena estructura con puntuación")
        
        # Validar beneficio explícito
        benefit_keywords = ['resultado', 'garantía', 'efectivo', 'profesional', 'experiencia']
        has_benefit = any(benefit in description_lower for benefit in benefit_keywords)
        if has_benefit:
            score += 0.4
            strengths.append("Menciona beneficios o garantías")
        
        # Normalizar score
        score = max(1.0, min(10.0, score))
        
        # Generar recomendaciones
        if not recommendations:
            if score < 7:
                recommendations.append("Revisa los problemas detectados")
            if not has_cta:
                recommendations.append("Agrega: Consulta gratis, Solicita ahora, etc.")
            if not has_benefit:
                recommendations.append("Menciona beneficios concretos o garantías")
        
        result = {
            'text': description,
            'score': round(score, 1),
            'grade': self._score_to_grade(score),
            'length': length,
            'issues': issues,
            'strengths': strengths,
            'recommendations': recommendations,
            'metrics': {
                'power_words': power_word_count,
                'emotional_words': emotional_count,
                'has_cta': has_cta,
                'has_benefit': has_benefit,
                'has_punctuation': '.' in description or ',' in description
            }
        }
        
        logger.debug(f"📊 Description scored: {score:.1f}/10")
        
        return result
    
    def score_ad(
        self,
        headlines: List[str],
        descriptions: List[str],
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calcula score completo de un anuncio.
        
        Args:
            headlines: Lista de titulares
            descriptions: Lista de descripciones
            keywords: Keywords opcionales
        
        Returns:
            Diccionario con scoring completo del anuncio
        """
        logger.info(f"📊 Scoring anuncio completo...")
        
        # Score de titulares
        headline_scores = []
        for i, headline in enumerate(headlines):
            if headline.strip():
                score_data = self.score_headline(headline, keywords)
                score_data['index'] = i
                headline_scores.append(score_data)
        
        # Score de descripciones
        description_scores = []
        for i, description in enumerate(descriptions):
            if description.strip():
                score_data = self.score_description(description, keywords)
                score_data['index'] = i
                description_scores.append(score_data)
        
        # Calcular promedios
        avg_headline_score = statistics.mean([h['score'] for h in headline_scores]) if headline_scores else 0
        avg_description_score = statistics.mean([d['score'] for d in description_scores]) if description_scores else 0
        
        # Score general (ponderado)
        overall_score = (avg_headline_score * 0.6 + avg_description_score * 0.4)
        
        # Contar issues totales
        total_issues = sum(len(h['issues']) for h in headline_scores) + \
                      sum(len(d['issues']) for d in description_scores)
        
        # Análisis de diversidad
        diversity_score = self._calculate_diversity(headlines, descriptions)
        
        # Análisis de keywords
        keyword_analysis = self._analyze_keyword_usage(headlines, descriptions, keywords) if keywords else {}
        
        result = {
            'overall_score': round(overall_score, 1),
            'overall_grade': self._score_to_grade(overall_score),
            'headline_scores': headline_scores,
            'description_scores': description_scores,
            'avg_headline_score': round(avg_headline_score, 1),
            'avg_description_score': round(avg_description_score, 1),
            'total_issues': total_issues,
            'diversity_score': diversity_score,
            'keyword_analysis': keyword_analysis,
            'summary': self._generate_summary(
                overall_score,
                headline_scores,
                description_scores,
                total_issues
            ),
            'top_recommendations': self._generate_top_recommendations(
                headline_scores,
                description_scores,
                keyword_analysis
            )
        }
        
        logger.info(f"✅ Scoring completado: {overall_score:.1f}/10 ({result['overall_grade']})")
        
        return result
    
    # =========================================================================
    # OPTIMIZACIÓN AUTOMÁTICA
    # =========================================================================
    
    def optimize_headline(
        self,
        headline: str,
        keywords: Optional[List[str]] = None,
        target_score: float = 8.0
    ) -> Dict[str, Any]:
        """
        Optimiza automáticamente un titular.
        
        Args:
            headline: Titular a optimizar
            keywords: Keywords para contexto
            target_score: Score objetivo (1-10)
        
        Returns:
            Diccionario con titular optimizado y mejoras
        """
        logger.info(f"🔧 Optimizando titular: '{headline[:30]}...'")
        
        # Score inicial
        initial_score_data = self.score_headline(headline, keywords)
        initial_score = initial_score_data['score']
        
        if initial_score >= target_score:
            logger.info(f"✅ Titular ya cumple objetivo ({initial_score:.1f} >= {target_score})")
            return {
                'original': headline,
                'optimized': headline,
                'initial_score': initial_score,
                'final_score': initial_score,
                'improvements': [],
                'changed': False
            }
        
        optimized = headline
        improvements = []
        
        # 1. Corregir longitud
        if len(optimized) > 30:
            # Truncar inteligentemente
            optimized = self._truncate_intelligently(optimized, 30)
            improvements.append("Ajustada longitud a límite de 30 caracteres")
        
        # 2. Remover caracteres prohibidos
        forbidden_chars = ['!', '?', '¡', '¿']
        for char in forbidden_chars:
            if char in optimized:
                optimized = optimized.replace(char, '')
                improvements.append(f"Removido caracter prohibido: '{char}'")
        
        # 3. Corregir mayúsculas excesivas
        if optimized.isupper():
            optimized = optimized.title()
            improvements.append("Corregido uso de mayúsculas")
        
        # 4. Remover palabras prohibidas
        optimized_lower = optimized.lower()
        for forbidden in self.FORBIDDEN_WORDS:
            if forbidden in optimized_lower:
                # Reemplazar con alternativa
                optimized = optimized.replace(forbidden, '')
                optimized = ' '.join(optimized.split())  # Limpiar espacios
                improvements.append(f"Removida frase prohibida")
        
        # 5. Agregar palabra de poder si falta y hay espacio
        if len(optimized) < 25:
            has_power_word = any(word in optimized.lower() for word in self.POWER_WORDS)
            if not has_power_word:
                power_word = 'Efectivo'
                if len(optimized + ' ' + power_word) <= 30:
                    optimized = f"{optimized} {power_word}"
                    improvements.append(f"Agregada palabra de poder: '{power_word}'")
        
        # 6. Limpiar espacios múltiples
        optimized = ' '.join(optimized.split())
        
        # Score final
        final_score_data = self.score_headline(optimized, keywords)
        final_score = final_score_data['score']
        
        result = {
            'original': headline,
            'optimized': optimized,
            'initial_score': initial_score,
            'final_score': final_score,
            'improvement': round(final_score - initial_score, 1),
            'improvements': improvements,
            'changed': optimized != headline,
            'meets_target': final_score >= target_score,
            'initial_data': initial_score_data,
            'final_data': final_score_data
        }
        
        logger.info(f"✅ Optimización completada: {initial_score:.1f} → {final_score:.1f}")
        
        return result
    
    def optimize_description(
        self,
        description: str,
        keywords: Optional[List[str]] = None,
        target_score: float = 8.0
    ) -> Dict[str, Any]:
        """
        Optimiza automáticamente una descripción.
        
        Args:
            description: Descripción a optimizar
            keywords: Keywords para contexto
            target_score: Score objetivo (1-10)
        
        Returns:
            Diccionario con descripción optimizada y mejoras
        """
        logger.info(f"🔧 Optimizando descripción...")
        
        # Score inicial
        initial_score_data = self.score_description(description, keywords)
        initial_score = initial_score_data['score']
        
        if initial_score >= target_score:
            logger.info(f"✅ Descripción ya cumple objetivo ({initial_score:.1f} >= {target_score})")
            return {
                'original': description,
                'optimized': description,
                'initial_score': initial_score,
                'final_score': initial_score,
                'improvements': [],
                'changed': False
            }
        
        optimized = description
        improvements = []
        
        # 1. Corregir longitud
        if len(optimized) > 90:
            optimized = self._truncate_intelligently(optimized, 90)
            improvements.append("Ajustada longitud a límite de 90 caracteres")
        
        # 2. Remover caracteres prohibidos
        forbidden_chars = ['!', '?', '¡', '¿']
        for char in forbidden_chars:
            if char in optimized:
                optimized = optimized.replace(char, '.')
                improvements.append(f"Reemplazado caracter prohibido '{char}' por '.'")
        
        # 3. Corregir mayúsculas
        if optimized.isupper():
            optimized = optimized.capitalize()
            improvements.append("Corregido uso de mayúsculas")
        
        # 4. Remover palabras prohibidas
        for forbidden in self.FORBIDDEN_WORDS:
            if forbidden in optimized.lower():
                optimized = optimized.replace(forbidden, '')
                optimized = ' '.join(optimized.split())
                improvements.append("Removida frase prohibida")
        
        # 5. Agregar CTA si falta y hay espacio
        has_cta = any(action in optimized.lower() for action in self.ACTION_WORDS)
        if not has_cta and len(optimized) < 75:
            cta = "Consulta ahora."
            if len(optimized + ' ' + cta) <= 90:
                optimized = f"{optimized} {cta}"
                improvements.append(f"Agregado CTA: '{cta}'")
        
        # 6. Limpiar espacios
        optimized = ' '.join(optimized.split())
        
        # Score final
        final_score_data = self.score_description(optimized, keywords)
        final_score = final_score_data['score']
        
        result = {
            'original': description,
            'optimized': optimized,
            'initial_score': initial_score,
            'final_score': final_score,
            'improvement': round(final_score - initial_score, 1),
            'improvements': improvements,
            'changed': optimized != description,
            'meets_target': final_score >= target_score,
            'initial_data': initial_score_data,
            'final_data': final_score_data
        }
        
        logger.info(f"✅ Optimización completada: {initial_score:.1f} → {final_score:.1f}")
        
        return result
    
    def optimize_ad(
        self,
        headlines: List[str],
        descriptions: List[str],
        keywords: Optional[List[str]] = None,
        target_score: float = 8.0,
        optimize_all: bool = False
    ) -> Dict[str, Any]:
        """
        Optimiza un anuncio completo.
        
        Args:
            headlines: Lista de titulares
            descriptions: Lista de descripciones
            keywords: Keywords opcionales
            target_score: Score objetivo
            optimize_all: Si False, solo optimiza elementos con score < target
        
        Returns:
            Diccionario con anuncio optimizado
        """
        logger.info(f"🚀 Optimizando anuncio completo...")
        
        optimized_headlines = []
        optimized_descriptions = []
        
        total_improvements = 0
        
        # Optimizar titulares
        for headline in headlines:
            if not headline.strip():
                optimized_headlines.append(headline)
                continue
            
            score_data = self.score_headline(headline, keywords)
            
            if optimize_all or score_data['score'] < target_score:
                opt_result = self.optimize_headline(headline, keywords, target_score)
                optimized_headlines.append(opt_result['optimized'])
                total_improvements += len(opt_result['improvements'])
            else:
                optimized_headlines.append(headline)
        
        # Optimizar descripciones
        for description in descriptions:
            if not description.strip():
                optimized_descriptions.append(description)
                continue
            
            score_data = self.score_description(description, keywords)
            
            if optimize_all or score_data['score'] < target_score:
                opt_result = self.optimize_description(description, keywords, target_score)
                optimized_descriptions.append(opt_result['optimized'])
                total_improvements += len(opt_result['improvements'])
            else:
                optimized_descriptions.append(description)
        
        # Scores antes y después
        initial_score = self.score_ad(headlines, descriptions, keywords)
        final_score = self.score_ad(optimized_headlines, optimized_descriptions, keywords)
        
        result = {
            'original': {
                'headlines': headlines,
                'descriptions': descriptions
            },
            'optimized': {
                'headlines': optimized_headlines,
                'descriptions': optimized_descriptions
            },
            'initial_score': initial_score['overall_score'],
            'final_score': final_score['overall_score'],
            'improvement': round(final_score['overall_score'] - initial_score['overall_score'], 1),
            'total_improvements': total_improvements,
            'initial_analysis': initial_score,
            'final_analysis': final_score,
            'timestamp': datetime.now().isoformat()
        }
        
        # Actualizar estadísticas
        self._update_optimization_stats(result)
        
        logger.info(f"✅ Optimización de anuncio completada")
        logger.info(f"   Score: {initial_score['overall_score']:.1f} → {final_score['overall_score']:.1f}")
        logger.info(f"   Mejoras aplicadas: {total_improvements}")
        
        return result
    
    # =========================================================================
    # DETECCIÓN DE PROBLEMAS
    # =========================================================================
    
    def detect_repetitions(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Detecta palabras y frases repetidas en el anuncio.
        
        Args:
            headlines: Lista de titulares
            descriptions: Lista de descripciones
        
        Returns:
            Diccionario con análisis de repeticiones
        """
        all_text = ' '.join(headlines + descriptions).lower()
        words = re.findall(r'\b\w+\b', all_text)
        
        # Contar palabras (excluir comunes)
        common_words = {'el', 'la', 'los', 'las', 'de', 'en', 'y', 'a', 'con', 'para', 'por'}
        significant_words = [w for w in words if len(w) > 3 and w not in common_words]
        
        word_counts = Counter(significant_words)
        repeated_words = {word: count for word, count in word_counts.items() if count > 2}
        
        # Detectar frases repetidas (2-3 palabras)
        phrases = []
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            phrases.append(phrase)
        
        phrase_counts = Counter(phrases)
        repeated_phrases = {phrase: count for phrase, count in phrase_counts.items() if count > 1}
        
        result = {
            'has_repetitions': len(repeated_words) > 0 or len(repeated_phrases) > 0,
            'repeated_words': repeated_words,
            'repeated_phrases': repeated_phrases,
            'total_repeated_words': len(repeated_words),
            'total_repeated_phrases': len(repeated_phrases),
            'recommendations': []
        }
        
        if result['has_repetitions']:
            result['recommendations'].append("Considera usar sinónimos para mayor variedad")
            if len(repeated_words) > 3:
                result['recommendations'].append("Demasiadas palabras repetidas, varía el vocabulario")
        
        return result
    
    def detect_policy_violations(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Detecta posibles violaciones de políticas de Google Ads.
        
        Args:
            headlines: Lista de titulares
            descriptions: Lista de descripciones
        
        Returns:
            Diccionario con violaciones detectadas
        """
        violations = []
        warnings = []
        
        all_headlines = ' '.join(headlines).lower()
        all_descriptions = ' '.join(descriptions).lower()
        all_text = all_headlines + ' ' + all_descriptions
        
        # Palabras prohibidas
        for forbidden in self.FORBIDDEN_WORDS:
            if forbidden in all_text:
                violations.append({
                    'type': 'forbidden_word',
                    'severity': 'high',
                    'text': forbidden,
                    'message': f"Contiene frase prohibida: '{forbidden}'"
                })
        
        # Caracteres prohibidos
        forbidden_chars = ['!', '?', '¡', '¿']
        for char in forbidden_chars:
            if char in all_headlines:
                violations.append({
                    'type': 'forbidden_char',
                    'severity': 'high',
                    'text': char,
                    'message': f"Titulares contienen caracter prohibido: '{char}'"
                })
            elif char in all_descriptions:
                warnings.append({
                    'type': 'forbidden_char',
                    'severity': 'medium',
                    'text': char,
                    'message': f"Descripciones contienen caracter no recomendado: '{char}'"
                })
        
        # Mayúsculas excesivas
        for headline in headlines:
            if headline.isupper():
                violations.append({
                    'type': 'all_caps',
                    'severity': 'high',
                    'text': headline,
                    'message': "Titular completamente en mayúsculas (prohibido)"
                })
        
        # Longitud excedida
        for i, headline in enumerate(headlines):
            if len(headline) > 30:
                violations.append({
                    'type': 'length_exceeded',
                    'severity': 'high',
                    'text': headline,
                    'message': f"Titular {i+1} excede 30 caracteres ({len(headline)} chars)"
                })
        
        for i, description in enumerate(descriptions):
            if len(description) > 90:
                violations.append({
                    'type': 'length_exceeded',
                    'severity': 'high',
                    'text': description,
                    'message': f"Descripción {i+1} excede 90 caracteres ({len(description)} chars)"
                })
        
        result = {
            'compliant': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'total_violations': len(violations),
            'total_warnings': len(warnings),
            'severity_breakdown': {
                'high': len([v for v in violations if v['severity'] == 'high']),
                'medium': len([v for v in violations + warnings if v['severity'] == 'medium']),
                'low': len([v for v in warnings if v['severity'] == 'low'])
            }
        }
        
        return result
    
    # =========================================================================
    # SUGERENCIAS CON IA
    # =========================================================================
    
    def suggest_improvements_with_ai(
        self,
        text: str,
        text_type: str = 'headline',
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Genera sugerencias de mejora usando IA.
        
        Args:
            text: Texto a mejorar
            text_type: 'headline' o 'description'
            keywords: Keywords para contexto
        
        Returns:
            Diccionario con sugerencias de IA
        """
        if not self.enable_ai_suggestions or not self.ai_provider:
            return {
                'available': False,
                'message': 'Sugerencias con IA no disponibles'
            }
        
        try:
            # Construir prompt para IA
            if text_type == 'headline':
                max_length = 30
                prompt = f"""Mejora este titular para un anuncio de Google Ads:

Titular actual: "{text}"
Máximo: {max_length} caracteres
Keywords: {', '.join(keywords) if keywords else 'N/A'}

Genera 3 alternativas mejoradas que:
- Sean más impactantes y persuasivas
- Incluyan keywords relevantes
- Respeten el límite de caracteres
- Usen palabras de poder: garantizado, efectivo, profesional
- Sean claras y directas

Responde solo con las 3 alternativas, una por línea."""

            else:  # description
                max_length = 90
                prompt = f"""Mejora esta descripción para un anuncio de Google Ads:

Descripción actual: "{text}"
Máximo: {max_length} caracteres
Keywords: {', '.join(keywords) if keywords else 'N/A'}

Genera 2 alternativas mejoradas que:
- Sean más persuasivas y detalladas
- Incluyan un llamado a la acción claro
- Mencionen beneficios concretos
- Respeten el límite de caracteres
- Sean profesionales y creíbles

Responde solo con las 2 alternativas, una por línea."""
            
            # Llamar a IA (simulado - adaptar según proveedor real)
            logger.info(f"🤖 Solicitando sugerencias a IA para {text_type}...")
            
            # NOTA: Aquí iría la llamada real al proveedor de IA
            # Por ahora, retornamos estructura de respuesta
            
            return {
                'available': True,
                'original': text,
                'suggestions': [],  # Aquí irían las sugerencias de IA
                'prompt_used': prompt,
                'message': 'Funcionalidad de IA pendiente de integración con proveedor'
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando sugerencias con IA: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _score_to_grade(self, score: float) -> str:
        """Convierte score numérico a calificación letra."""
        if score >= 9:
            return 'A+'
        elif score >= 8:
            return 'A'
        elif score >= 7:
            return 'B'
        elif score >= 6:
            return 'C'
        elif score >= 5:
            return 'D'
        else:
            return 'F'
    
    def _truncate_intelligently(self, text: str, max_length: int) -> str:
        """Trunca texto inteligentemente en límite de palabra."""
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length]
        
        # Buscar último espacio para truncar en palabra completa
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # Si el espacio está cerca del final
            return truncated[:last_space].strip()
        else:
            return truncated.strip()
    
    def _calculate_diversity(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> float:
        """Calcula score de diversidad del contenido (0-10)."""
        all_words = []
        
        for headline in headlines:
            words = headline.lower().split()
            all_words.extend(words)
        
        for description in descriptions:
            words = description.lower().split()
            all_words.extend(words)
        
        if not all_words:
            return 0.0
        
        unique_words = len(set(all_words))
        total_words = len(all_words)
        
        diversity_ratio = unique_words / total_words
        diversity_score = diversity_ratio * 10
        
        return round(diversity_score, 1)
    
    def _analyze_keyword_usage(
        self,
        headlines: List[str],
        descriptions: List[str],
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Analiza uso de keywords en el anuncio."""
        all_text = ' '.join(headlines + descriptions).lower()
        
        keyword_usage = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = all_text.count(keyword_lower)
            keyword_usage[keyword] = count
        
        total_keywords_used = sum(1 for count in keyword_usage.values() if count > 0)
        
        return {
            'total_keywords': len(keywords),
            'keywords_used': total_keywords_used,
            'usage_rate': round(total_keywords_used / len(keywords) * 100, 1) if keywords else 0,
            'keyword_counts': keyword_usage,
            'unused_keywords': [kw for kw, count in keyword_usage.items() if count == 0]
        }
    
    def _generate_summary(
        self,
        overall_score: float,
        headline_scores: List[Dict],
        description_scores: List[Dict],
        total_issues: int
    ) -> str:
        """Genera resumen textual del análisis."""
        grade = self._score_to_grade(overall_score)
        
        if overall_score >= 8:
            quality = "excelente"
        elif overall_score >= 7:
            quality = "buena"
        elif overall_score >= 6:
            quality = "aceptable"
        else:
            quality = "necesita mejoras"
        
        summary = f"El anuncio tiene una calidad {quality} con score {overall_score:.1}/10 ({grade}). "
        
        if total_issues == 0:
            summary += "No se detectaron problemas. "
        elif total_issues <= 3:
            summary += f"Se detectaron {total_issues} problema(s) menor(es). "
        else:
            summary += f"Se detectaron {total_issues} problemas que deben corregirse. "
        
        return summary
    
    def _generate_top_recommendations(
        self,
        headline_scores: List[Dict],
        description_scores: List[Dict],
        keyword_analysis: Dict[str, Any]
    ) -> List[str]:
        """Genera las principales recomendaciones del análisis."""
        recommendations = []
        
        # Priorizar por score bajo
        low_headlines = [h for h in headline_scores if h['score'] < 7]
        low_descriptions = [d for d in description_scores if d['score'] < 7]
        
        if low_headlines:
            recommendations.append(
                f"Mejorar {len(low_headlines)} titular(es) con score bajo"
            )
        
        if low_descriptions:
            recommendations.append(
                f"Mejorar {len(low_descriptions)} descripción(es) con score bajo"
            )
        
        # Keywords no usadas
        if keyword_analysis.get('unused_keywords'):
            unused = len(keyword_analysis['unused_keywords'])
            if unused > 0:
                recommendations.append(
                    f"Incorporar {unused} keyword(s) no utilizada(s)"
                )
        
        # Si no hay recomendaciones críticas
        if not recommendations:
            recommendations.append("El anuncio está bien optimizado")
            recommendations.append("Considera hacer pruebas A/B para mejorar rendimiento")
        
        return recommendations[:5]  # Top 5
    
    def _update_optimization_stats(self, result: Dict[str, Any]) -> None:
        """Actualiza estadísticas de optimización."""
        self.optimization_stats['total_optimizations'] += 1
        
        initial = result['initial_score']
        final = result['final_score']
        
        # Actualizar promedios
        total = self.optimization_stats['total_optimizations']
        
        self.optimization_stats['avg_score_before'] = round(
            (self.optimization_stats['avg_score_before'] * (total - 1) + initial) / total,
            2
        )
        
        self.optimization_stats['avg_score_after'] = round(
            (self.optimization_stats['avg_score_after'] * (total - 1) + final) / total,
            2
        )
        
        if final > initial:
            self.optimization_stats['improvements'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del optimizador."""
        return {
            **self.optimization_stats,
            'improvement_rate': round(
                self.optimization_stats['improvements'] / 
                self.optimization_stats['total_optimizations'] * 100, 1
            ) if self.optimization_stats['total_optimizations'] > 0 else 0,
            'avg_improvement': round(
                self.optimization_stats['avg_score_after'] - 
                self.optimization_stats['avg_score_before'], 2
            )
        }


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_optimizer(
    ai_provider=None,
    enable_ai_suggestions: bool = True,
    strict_mode: bool = False
) -> AdOptimizer:
    """
    Factory function para crear una instancia de AdOptimizer.
    
    Args:
        ai_provider: Proveedor de IA opcional
        enable_ai_suggestions: Habilitar sugerencias con IA
        strict_mode: Modo estricto de validación
    
    Returns:
        Instancia de AdOptimizer
    """
    return AdOptimizer(
        ai_provider=ai_provider,
        enable_ai_suggestions=enable_ai_suggestions,
        strict_mode=strict_mode
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🎯 AD OPTIMIZER - Ejemplo de Uso")
    print("="*60)
    
    # Crear optimizador
    optimizer = AdOptimizer(enable_ai_suggestions=False)
    
    # Anuncio de ejemplo
    headlines = [
        "AMARRES DE AMOR GARANTIZADOS!!!",  # Problemas: mayúsculas, caracteres prohibidos
        "Recupera a Tu Pareja Ya",  # Bueno
        "Hechizos Efectivos",  # Corto pero OK
        "Brujería Profesional con Resultados Rápidos"  # Bueno
    ]
    
    descriptions = [
        "Amarres de amor efectivos y discretos. Resultados garantizados en 24-48 horas.",
        "Recupera a tu pareja con magia blanca poderosa",  # Corta
        "CONSULTA GRATIS AHORA MISMO!!!!"  # Problemas
    ]
    
    keywords = ["amarres de amor", "hechizos", "brujería profesional"]
    
    # Scoring completo
    print("\n" + "-"*60)
    print("📊 SCORING DE ANUNCIO")
    print("-"*60)
    
    score_result = optimizer.score_ad(headlines, descriptions, keywords)
    
    print(f"\n✅ Score General: {score_result['overall_score']}/10 ({score_result['overall_grade']})")
    print(f"   - Titulares: {score_result['avg_headline_score']}/10")
    print(f"   - Descripciones: {score_result['avg_description_score']}/10")
    print(f"   - Issues totales: {score_result['total_issues']}")
    print(f"\n📝 Resumen: {score_result['summary']}")
    
    print(f"\n💡 Recomendaciones principales:")
    for i, rec in enumerate(score_result['top_recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Optimización automática
    print("\n" + "-"*60)
    print("🔧 OPTIMIZACIÓN AUTOMÁTICA")
    print("-"*60)
    
    opt_result = optimizer.optimize_ad(headlines, descriptions, keywords, target_score=8.0)
    
    print(f"\n✅ Optimización completada:")
    print(f"   - Score inicial: {opt_result['initial_score']}/10")
    print(f"   - Score final: {opt_result['final_score']}/10")
    print(f"   - Mejora: +{opt_result['improvement']}")
    print(f"   - Mejoras aplicadas: {opt_result['total_improvements']}")
    
    print(f"\n📊 Ejemplo de titular optimizado:")
    print(f"   Original: {headlines[0]}")
    print(f"   Optimizado: {opt_result['optimized']['headlines'][0]}")
    
    # Estadísticas
    print("\n" + "-"*60)
    print("📈 ESTADÍSTICAS DEL OPTIMIZADOR")
    print("-"*60)
    
    stats = optimizer.get_statistics()
    print(f"\n✅ Total optimizaciones: {stats['total_optimizations']}")
    print(f"✅ Tasa de mejora: {stats['improvement_rate']}%")
    print(f"✅ Mejora promedio: +{stats['avg_improvement']}")