"""
🔑 KEYWORD EXTRACTOR - Extractor Avanzado de Keywords
Sistema inteligente de extracción y análisis de palabras clave con NLP
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from collections import Counter, defaultdict
import statistics
from pathlib import Path
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Extractor de keywords que proporciona:
    - Extracción de keywords de texto
    - Análisis de frecuencia
    - Detección de bi-gramas y tri-gramas
    - Score de relevancia
    - Clustering semántico
    - Sugerencias de keywords relacionadas
    - Filtrado de stopwords
    - Expansión de keywords
    - Análisis de intención de búsqueda
    """
    
    # =========================================================================
    # STOPWORDS Y CONFIGURACIÓN
    # =========================================================================
    
    # Stopwords en español (palabras comunes a ignorar)
    STOPWORDS = {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
        'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo',
        'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese',
        'si', 'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy', 'sin',
        'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo', 'yo',
        'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así', 'primero',
        'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella',
        'sí', 'día', 'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
        'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde', 'ahora', 'parte',
        'después', 'vida', 'quedar', 'siempre', 'creer', 'hablar', 'llevar', 'dejar',
        'nada', 'cada', 'seguir', 'menos', 'nuevo', 'encontrar', 'algo', 'solo',
        'mundo', 'país', 'contra', 'cual', 'durante', 'ha', 'son', 'fue', 'sido',
        'estaba', 'puede', 'pueden', 'puedo', 'esta', 'estos', 'estas', 'ese', 'esa'
    }
    
    # Palabras clave del dominio esotérico
    DOMAIN_KEYWORDS = {
        'esoterico': [
            'amarres', 'hechizos', 'brujería', 'magia', 'tarot', 'videncia',
            'rituales', 'conjuros', 'limpieza', 'espiritual', 'energía',
            'consulta', 'lectura', 'cartas', 'astrología', 'horóscopo',
            'predicción', 'futuro', 'destino', 'protección', 'amor', 'suerte',
            'dinero', 'trabajo', 'salud', 'pareja', 'reconciliación'
        ],
        'servicios': [
            'consulta', 'sesión', 'lectura', 'ritual', 'servicio', 'trabajo',
            'análisis', 'interpretación', 'guía', 'ayuda', 'solución'
        ],
        'cualidades': [
            'efectivo', 'poderoso', 'profesional', 'experto', 'certificado',
            'garantizado', 'rápido', 'urgente', 'discreto', 'confidencial'
        ]
    }
    
    # Patrones de intención de búsqueda
    INTENT_PATTERNS = {
        'informational': [
            r'\bqué\s+(?:es|son)',
            r'\bcómo\s+(?:hacer|funciona)',
            r'\b(?:significa|significado)',
            r'\b(?:tipos|clases)\s+de',
            r'\b(?:diferencia|diferencias)\s+entre'
        ],
        'transactional': [
            r'\b(?:comprar|adquirir|contratar)',
            r'\b(?:precio|costo|cuánto)',
            r'\b(?:servicio|servicios)',
            r'\b(?:consulta|sesión)',
            r'\bonline\b'
        ],
        'navigational': [
            r'\b(?:sitio|página)\s+(?:web|oficial)',
            r'\bcontacto\b',
            r'\bdirección\b',
            r'\bteléfono\b'
        ],
        'local': [
            r'\bcerca\s+de\s+mí',
            r'\ben\s+\w+',  # ciudad/ubicación
            r'\b(?:local|zona|área)'
        ]
    }
    
    # Modificadores de keywords
    MODIFIERS = {
        'location': ['en', 'de', 'cerca', 'local'],
        'quality': ['mejor', 'bueno', 'top', 'profesional', 'experto'],
        'price': ['barato', 'económico', 'precio', 'costo', 'gratis'],
        'urgency': ['urgente', 'rápido', 'inmediato', 'ahora', 'ya'],
        'time': ['24 horas', 'hoy', 'mañana', 'horario']
    }
    
    def __init__(
        self,
        domain: str = 'esoterico',
        min_word_length: int = 3,
        max_keywords: int = 50,
        include_ngrams: bool = True
    ):
        """
        Inicializa el extractor de keywords.
        
        Args:
            domain: Dominio del negocio ('esoterico', 'generic')
            min_word_length: Longitud mínima de palabras
            max_keywords: Máximo de keywords a extraer
            include_ngrams: Incluir bi-gramas y tri-gramas
        """
        self.domain = domain
        self.min_word_length = min_word_length
        self.max_keywords = max_keywords
        self.include_ngrams = include_ngrams
        
        # Keywords del dominio
        self.domain_words = self.DOMAIN_KEYWORDS.get(domain, [])
        
        # Cache de keywords extraídas
        self.cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Estadísticas
        self.stats = {
            'total_extractions': 0,
            'total_keywords_extracted': 0,
            'avg_relevance_score': 0.0
        }
        
        logger.info(f"✅ KeywordExtractor inicializado")
        logger.info(f"   - Domain: {domain}")
        logger.info(f"   - Min word length: {min_word_length}")
        logger.info(f"   - Include n-grams: {include_ngrams}")
    
    # =========================================================================
    # EXTRACCIÓN PRINCIPAL
    # =========================================================================
    
    def extract(
        self,
        text: str,
        existing_keywords: Optional[List[str]] = None,
        boost_domain: bool = True,
        min_frequency: int = 1
    ) -> Dict[str, Any]:
        """
        Extrae keywords de un texto.
        
        Args:
            text: Texto a analizar
            existing_keywords: Keywords existentes para comparar
            boost_domain: Dar bonus a keywords del dominio
            min_frequency: Frecuencia mínima para incluir keyword
        
        Returns:
            Diccionario con keywords extraídas y análisis
        """
        extraction_id = f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🔑 Extrayendo keywords: {extraction_id}")
        logger.info(f"   - Texto: {len(text)} caracteres")
        
        # Verificar cache
        text_hash = self._hash_text(text)
        if text_hash in self.cache:
            logger.info(f"✅ Keywords obtenidas de caché")
            return self.cache[text_hash]
        
        # Normalizar texto
        normalized_text = self._normalize_text(text)
        
        # 1. Extraer palabras individuales
        single_keywords = self._extract_single_words(
            normalized_text,
            min_frequency=min_frequency,
            boost_domain=boost_domain
        )
        
        # 2. Extraer n-gramas (bi-gramas y tri-gramas)
        ngrams = []
        if self.include_ngrams:
            ngrams = self._extract_ngrams(
                normalized_text,
                min_frequency=min_frequency,
                boost_domain=boost_domain
            )
        
        # 3. Combinar y rankear
        all_keywords = single_keywords + ngrams
        all_keywords = self._rank_keywords(all_keywords, text)
        
        # 4. Limitar cantidad
        all_keywords = all_keywords[:self.max_keywords]
        
        # 5. Análisis adicional
        keyword_clusters = self._cluster_keywords(all_keywords)
        intent_analysis = self._analyze_intent(text)
        related_suggestions = self._generate_related_keywords(all_keywords)
        
        # 6. Comparar con keywords existentes
        comparison = None
        if existing_keywords:
            comparison = self._compare_with_existing(all_keywords, existing_keywords)
        
        # Construir resultado
        result = {
            'extraction_id': extraction_id,
            'timestamp': datetime.now().isoformat(),
            'total_keywords': len(all_keywords),
            'keywords': all_keywords,
            'single_words': len(single_keywords),
            'ngrams': len(ngrams),
            'clusters': keyword_clusters,
            'intent_analysis': intent_analysis,
            'related_suggestions': related_suggestions,
            'comparison': comparison,
            'statistics': self._calculate_statistics(all_keywords),
            'top_keywords': all_keywords[:10]
        }
        
        # Guardar en cache
        self.cache[text_hash] = result
        
        # Actualizar estadísticas
        self.stats['total_extractions'] += 1
        self.stats['total_keywords_extracted'] += len(all_keywords)
        
        if all_keywords:
            avg_score = statistics.mean([kw['relevance_score'] for kw in all_keywords])
            self.stats['avg_relevance_score'] = round(avg_score, 2)
        
        logger.info(f"✅ Extracción completada")
        logger.info(f"   - Keywords extraídas: {len(all_keywords)}")
        logger.info(f"   - Single words: {len(single_keywords)}")
        logger.info(f"   - N-grams: {len(ngrams)}")
        
        return result
    
    # =========================================================================
    # EXTRACCIÓN DE PALABRAS
    # =========================================================================
    
    def _extract_single_words(
        self,
        text: str,
        min_frequency: int = 1,
        boost_domain: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extrae palabras individuales.
        
        Args:
            text: Texto normalizado
            min_frequency: Frecuencia mínima
            boost_domain: Boost para palabras del dominio
        
        Returns:
            Lista de keywords con metadata
        """
        # Extraer palabras
        words = re.findall(r'\b[a-záéíóúñü]+\b', text.lower())
        
        # Filtrar por longitud y stopwords
        filtered_words = [
            w for w in words
            if len(w) >= self.min_word_length and w not in self.STOPWORDS
        ]
        
        # Contar frecuencias
        word_counts = Counter(filtered_words)
        
        # Filtrar por frecuencia mínima
        word_counts = {
            word: count for word, count in word_counts.items()
            if count >= min_frequency
        }
        
        # Crear lista de keywords con metadata
        keywords = []
        
        for word, frequency in word_counts.items():
            # Calcular relevancia base
            relevance = self._calculate_base_relevance(word, frequency, len(filtered_words))
            
            # Boost por dominio
            if boost_domain and self._is_domain_keyword(word):
                relevance *= 1.5
            
            keyword_data = {
                'keyword': word,
                'type': 'single',
                'frequency': frequency,
                'relevance_score': round(min(100, relevance), 1),
                'is_domain': self._is_domain_keyword(word),
                'length': len(word)
            }
            
            keywords.append(keyword_data)
        
        return keywords
    
    def _extract_ngrams(
        self,
        text: str,
        min_frequency: int = 1,
        boost_domain: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extrae bi-gramas y tri-gramas.
        
        Args:
            text: Texto normalizado
            min_frequency: Frecuencia mínima
            boost_domain: Boost para n-gramas del dominio
        
        Returns:
            Lista de n-gramas con metadata
        """
        words = re.findall(r'\b[a-záéíóúñü]+\b', text.lower())
        
        # Filtrar stopwords
        filtered_words = [w for w in words if w not in self.STOPWORDS]
        
        ngrams = []
        
        # Bi-gramas (2 palabras)
        bigrams = []
        for i in range(len(filtered_words) - 1):
            bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
            bigrams.append(bigram)
        
        bigram_counts = Counter(bigrams)
        
        # Tri-gramas (3 palabras)
        trigrams = []
        for i in range(len(filtered_words) - 2):
            trigram = f"{filtered_words[i]} {filtered_words[i+1]} {filtered_words[i+2]}"
            trigrams.append(trigram)
        
        trigram_counts = Counter(trigrams)
        
        # Procesar bi-gramas
        for ngram, frequency in bigram_counts.items():
            if frequency >= min_frequency:
                relevance = self._calculate_ngram_relevance(
                    ngram, frequency, len(bigrams), 2
                )
                
                if boost_domain and self._contains_domain_keyword(ngram):
                    relevance *= 1.3
                
                ngrams.append({
                    'keyword': ngram,
                    'type': 'bigram',
                    'frequency': frequency,
                    'relevance_score': round(min(100, relevance), 1),
                    'is_domain': self._contains_domain_keyword(ngram),
                    'length': len(ngram)
                })
        
        # Procesar tri-gramas
        for ngram, frequency in trigram_counts.items():
            if frequency >= min_frequency:
                relevance = self._calculate_ngram_relevance(
                    ngram, frequency, len(trigrams), 3
                )
                
                if boost_domain and self._contains_domain_keyword(ngram):
                    relevance *= 1.2
                
                ngrams.append({
                    'keyword': ngram,
                    'type': 'trigram',
                    'frequency': frequency,
                    'relevance_score': round(min(100, relevance), 1),
                    'is_domain': self._contains_domain_keyword(ngram),
                    'length': len(ngram)
                })
        
        return ngrams
    
    # =========================================================================
    # CÁLCULO DE RELEVANCIA
    # =========================================================================
    
    def _calculate_base_relevance(
        self,
        word: str,
        frequency: int,
        total_words: int
    ) -> float:
        """
        Calcula score de relevancia base para una palabra.
        
        Args:
            word: Palabra a evaluar
            frequency: Frecuencia de aparición
            total_words: Total de palabras en el texto
        
        Returns:
            Score de relevancia (0-100)
        """
        # Factor 1: Frecuencia relativa (40%)
        freq_score = (frequency / total_words * 100) if total_words > 0 else 0
        freq_score = min(freq_score * 40, 40)
        
        # Factor 2: Longitud de palabra (20%)
        # Palabras más largas tienden a ser más específicas
        length_score = min(len(word) / 15 * 20, 20)
        
        # Factor 3: Rareza (40%)
        # Palabras menos comunes son más relevantes
        # (Simulado - en producción usar IDF de corpus)
        rarity_score = 20  # Base
        
        # Bonus por palabras del dominio
        if self._is_domain_keyword(word):
            rarity_score += 20
        
        total_score = freq_score + length_score + rarity_score
        
        return total_score
    
    def _calculate_ngram_relevance(
        self,
        ngram: str,
        frequency: int,
        total_ngrams: int,
        n: int
    ) -> float:
        """
        Calcula relevancia de un n-grama.
        
        Args:
            ngram: N-grama a evaluar
            frequency: Frecuencia
            total_ngrams: Total de n-gramas
            n: Número de palabras (2 o 3)
        
        Returns:
            Score de relevancia
        """
        # N-gramas tienen bonus base por ser más específicos
        base_score = 30
        
        # Factor frecuencia
        freq_score = (frequency / total_ngrams * 50) if total_ngrams > 0 else 0
        
        # Bonus por longitud
        length_bonus = n * 5
        
        # Bonus si contiene palabras del dominio
        domain_bonus = 15 if self._contains_domain_keyword(ngram) else 0
        
        total_score = base_score + freq_score + length_bonus + domain_bonus
        
        return total_score
    
    def _rank_keywords(
        self,
        keywords: List[Dict[str, Any]],
        original_text: str
    ) -> List[Dict[str, Any]]:
        """
        Rankea keywords por relevancia y contexto.
        
        Args:
            keywords: Lista de keywords a rankear
            original_text: Texto original
        
        Returns:
            Keywords ordenadas por relevancia
        """
        text_lower = original_text.lower()
        
        for keyword in keywords:
            kw_text = keyword['keyword']
            
            # Factor posición (primeras apariciones son más importantes)
            first_position = text_lower.find(kw_text)
            if first_position >= 0:
                # Boost si aparece en los primeros 100 caracteres
                if first_position < 100:
                    keyword['relevance_score'] += 10
                elif first_position < 300:
                    keyword['relevance_score'] += 5
            
            # Factor co-ocurrencia con palabras del dominio
            context_window = 50  # caracteres antes y después
            if first_position >= 0:
                start = max(0, first_position - context_window)
                end = min(len(text_lower), first_position + len(kw_text) + context_window)
                context = text_lower[start:end]
                
                # Contar palabras del dominio en contexto
                domain_count = sum(
                    1 for domain_word in self.domain_words
                    if domain_word in context
                )
                
                keyword['relevance_score'] += domain_count * 2
            
            # Normalizar score
            keyword['relevance_score'] = min(100, keyword['relevance_score'])
            keyword['relevance_score'] = round(keyword['relevance_score'], 1)
        
        # Ordenar por relevancia
        keywords.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return keywords
    
    # =========================================================================
    # CLUSTERING Y AGRUPACIÓN
    # =========================================================================
    
    def _cluster_keywords(
        self,
        keywords: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Agrupa keywords por tema/categoría.
        
        Args:
            keywords: Lista de keywords
        
        Returns:
            Diccionario de clusters
        """
        clusters = defaultdict(list)
        
        # Categorías del dominio esotérico
        categories = {
            'amor_pareja': ['amor', 'pareja', 'amarres', 'reconciliación', 'matrimonio'],
            'dinero_prosperidad': ['dinero', 'prosperidad', 'suerte', 'fortuna', 'abundancia'],
            'salud_proteccion': ['salud', 'protección', 'limpieza', 'energía', 'bienestar'],
            'servicios': ['consulta', 'lectura', 'sesión', 'ritual', 'servicio'],
            'herramientas': ['tarot', 'cartas', 'videncia', 'astrología', 'horóscopo'],
            'caracteristicas': ['profesional', 'efectivo', 'garantizado', 'rápido', 'experto']
        }
        
        for keyword in keywords:
            kw_text = keyword['keyword'].lower()
            categorized = False
            
            for category, category_words in categories.items():
                if any(word in kw_text for word in category_words):
                    clusters[category].append(keyword['keyword'])
                    categorized = True
                    break
            
            if not categorized:
                clusters['otros'].append(keyword['keyword'])
        
        # Convertir a dict regular
        return dict(clusters)
    
    # =========================================================================
    # ANÁLISIS DE INTENCIÓN
    # =========================================================================
    
    def _analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        Analiza la intención de búsqueda del texto.
        
        Args:
            text: Texto a analizar
        
        Returns:
            Análisis de intención
        """
        text_lower = text.lower()
        
        intent_scores = {}
        
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            score = 0
            matches = []
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
                    matches.append(pattern)
            
            if score > 0:
                intent_scores[intent_type] = {
                    'score': score,
                    'matches': len(matches)
                }
        
        # Determinar intención principal
        primary_intent = 'unknown'
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1]['score'])[0]
        
        return {
            'primary_intent': primary_intent,
            'intent_scores': intent_scores,
            'description': self._get_intent_description(primary_intent)
        }
    
    def _get_intent_description(self, intent: str) -> str:
        """Obtiene descripción de intención."""
        descriptions = {
            'informational': 'Usuario busca información o aprender',
            'transactional': 'Usuario quiere contratar/comprar servicio',
            'navigational': 'Usuario busca sitio/contacto específico',
            'local': 'Usuario busca servicio en ubicación cercana',
            'unknown': 'Intención no clara'
        }
        return descriptions.get(intent, 'Intención no definida')
    
    # =========================================================================
    # SUGERENCIAS Y EXPANSIÓN
    # =========================================================================
    
    def _generate_related_keywords(
        self,
        keywords: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Genera keywords relacionadas basándose en las extraídas.
        
        Args:
            keywords: Keywords base
        
        Returns:
            Lista de keywords relacionadas sugeridas
        """
        related = set()
        
        # Extraer keywords principales
        top_keywords = [kw['keyword'] for kw in keywords[:5]]
        
        for keyword in top_keywords:
            # Agregar modificadores
            for modifier_type, modifiers in self.MODIFIERS.items():
                for modifier in modifiers[:2]:  # Top 2 de cada tipo
                    # Diferentes combinaciones
                    related.add(f"{keyword} {modifier}")
                    related.add(f"{modifier} {keyword}")
            
            # Si es palabra del dominio, agregar combinaciones con servicios
            if self._is_domain_keyword(keyword):
                services = ['consulta', 'servicio', 'profesional', 'experto']
                for service in services:
                    related.add(f"{keyword} {service}")
                    related.add(f"{service} de {keyword}")
        
        # Limitar cantidad
        related_list = list(related)[:20]
        
        return related_list
    
    def expand_keyword(
        self,
        keyword: str,
        expansion_type: str = 'all'
    ) -> List[str]:
        """
        Expande una keyword con modificadores.
        
        Args:
            keyword: Keyword base
            expansion_type: Tipo de expansión ('location', 'quality', 'price', 'all')
        
        Returns:
            Lista de keywords expandidas
        """
        expanded = [keyword]  # Incluir original
        
        if expansion_type == 'all':
            modifier_types = self.MODIFIERS.keys()
        else:
            modifier_types = [expansion_type] if expansion_type in self.MODIFIERS else []
        
        for mod_type in modifier_types:
            modifiers = self.MODIFIERS[mod_type]
            
            for modifier in modifiers:
                expanded.append(f"{keyword} {modifier}")
                expanded.append(f"{modifier} {keyword}")
                
                # Long-tail
                if mod_type == 'location':
                    expanded.append(f"{keyword} {modifier} mí")
        
        return list(set(expanded))  # Eliminar duplicados
    
    # =========================================================================
    # COMPARACIÓN Y ANÁLISIS
    # =========================================================================
    
    def _compare_with_existing(
        self,
        extracted: List[Dict[str, Any]],
        existing: List[str]
    ) -> Dict[str, Any]:
        """
        Compara keywords extraídas con existentes.
        
        Args:
            extracted: Keywords extraídas
            existing: Keywords existentes
        
        Returns:
            Análisis de comparación
        """
        extracted_set = set([kw['keyword'].lower() for kw in extracted])
        existing_set = set([kw.lower() for kw in existing])
        
        # Keywords comunes
        common = extracted_set.intersection(existing_set)
        
        # Keywords nuevas (extraídas pero no en existentes)
        new_keywords = extracted_set - existing_set
        
        # Keywords faltantes (existentes pero no extraídas)
        missing = existing_set - extracted_set
        
        # Calcular match rate
        match_rate = (len(common) / len(existing_set) * 100) if existing_set else 0
        
        comparison = {
            'total_extracted': len(extracted_set),
            'total_existing': len(existing_set),
            'common_keywords': list(common),
            'common_count': len(common),
            'new_keywords': list(new_keywords)[:10],  # Top 10
            'new_count': len(new_keywords),
            'missing_keywords': list(missing),
            'missing_count': len(missing),
            'match_rate': round(match_rate, 1),
            'recommendation': self._generate_comparison_recommendation(
                match_rate,
                len(new_keywords),
                len(missing)
            )
        }
        
        return comparison
    
    def _generate_comparison_recommendation(
        self,
        match_rate: float,
        new_count: int,
        missing_count: int
    ) -> str:
        """Genera recomendación basada en comparación."""
        if match_rate >= 80:
            return "Alta coincidencia - Keywords existentes están bien alineadas"
        elif match_rate >= 60:
            if new_count > 5:
                return f"Considera agregar {new_count} keywords nuevas detectadas"
            else:
                return "Buena alineación con keywords existentes"
        elif match_rate >= 40:
            return f"Coincidencia moderada - Revisa {new_count} keywords nuevas y {missing_count} faltantes"
        else:
            return "Baja coincidencia - Considera actualizar lista de keywords"
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    def _calculate_statistics(
        self,
        keywords: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calcula estadísticas de keywords extraídas."""
        if not keywords:
            return {}
        
        relevance_scores = [kw['relevance_score'] for kw in keywords]
        frequencies = [kw['frequency'] for kw in keywords]
        
        # Contar tipos
        type_counts = Counter([kw['type'] for kw in keywords])
        
        # Contar keywords de dominio
        domain_count = sum(1 for kw in keywords if kw.get('is_domain', False))
        
        stats = {
            'total_keywords': len(keywords),
            'avg_relevance': round(statistics.mean(relevance_scores), 1),
            'max_relevance': round(max(relevance_scores), 1),
            'min_relevance': round(min(relevance_scores), 1),
            'avg_frequency': round(statistics.mean(frequencies), 1),
            'max_frequency': max(frequencies),
            'type_distribution': dict(type_counts),
            'domain_keywords': domain_count,
            'domain_percentage': round(domain_count / len(keywords) * 100, 1)
        }
        
        return stats
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para procesamiento."""
        # Convertir a minúsculas
        text = text.lower()
        
        # Eliminar URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Eliminar emails
        text = re.sub(r'\S+@\S+', '', text)
        
        # Eliminar números standalone
        text = re.sub(r'\b\d+\b', '', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _is_domain_keyword(self, word: str) -> bool:
        """Verifica si palabra es del dominio."""
        return any(
            domain_word in word.lower()
            for category_words in self.DOMAIN_KEYWORDS.values()
            for domain_word in category_words
        )
    
    def _contains_domain_keyword(self, text: str) -> bool:
        """Verifica si texto contiene palabra del dominio."""
        text_lower = text.lower()
        return any(
            domain_word in text_lower
            for category_words in self.DOMAIN_KEYWORDS.values()
            for domain_word in category_words
        )
    
    def _hash_text(self, text: str) -> str:
        """Genera hash del texto para caché."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def clear_cache(self) -> int:
        """Limpia caché."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️ Caché limpiada: {count} entradas")
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del extractor."""
        return {
            **self.stats,
            'cache_size': len(self.cache)
        }
    
    def export_keywords(
        self,
        keywords: List[Dict[str, Any]],
        format: str = 'json'
    ) -> str:
        """
        Exporta keywords a formato especificado.
        
        Args:
            keywords: Keywords a exportar
            format: Formato ('json', 'csv', 'text')
        
        Returns:
            Keywords en formato string
        """
        if format == 'json':
            return json.dumps(keywords, indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Keyword', 'Type', 'Frequency', 'Relevance', 'Is Domain'])
            
            # Rows
            for kw in keywords:
                writer.writerow([
                    kw['keyword'],
                    kw['type'],
                    kw['frequency'],
                    kw['relevance_score'],
                    kw.get('is_domain', False)
                ])
            
            return output.getvalue()
        
        elif format == 'text':
            output = []
            for i, kw in enumerate(keywords, 1):
                output.append(
                    f"{i}. {kw['keyword']} (relevancia: {kw['relevance_score']:.1f}, freq: {kw['frequency']})"
                )
            return '\n'.join(output)
        
        return str(keywords)


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_keyword_extractor(
    domain: str = 'esoterico',
    max_keywords: int = 50
) -> KeywordExtractor:
    """
    Factory function para crear extractor.
    
    Args:
        domain: Dominio del negocio
        max_keywords: Máximo de keywords
    
    Returns:
        Instancia de KeywordExtractor
    """
    return KeywordExtractor(
        domain=domain,
        max_keywords=max_keywords
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🔑 KEYWORD EXTRACTOR - Ejemplo de Uso")
    print("="*60)
    
    # Crear extractor
    extractor = KeywordExtractor(domain='esoterico')
    
    # Texto de ejemplo
    sample_text = """
    Amarres de amor efectivos y profesionales. Recupera a tu pareja con 
    magia blanca poderosa. Brujería profesional con resultados garantizados 
    en 24 horas. Consulta gratis disponible. Tarot y lectura de cartas.
    Rituales de amor y reconciliación. Hechizos para atraer el amor verdadero.
    Servicios de limpieza espiritual y protección. Consulta con experta en 
    amarres y conjuros. Resultados rápidos y discretos. Bruja certificada 
    con años de experiencia en rituales de amor y prosperidad.
    """
    
    print(f"\n📝 Texto de ejemplo:")
    print(f"{sample_text[:150]}...")
    
    # Extraer keywords
    print(f"\n🔍 Extrayendo keywords...")
    
    result = extractor.extract(
        text=sample_text,
        boost_domain=True,
        min_frequency=1
    )
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("✅ KEYWORDS EXTRAÍDAS")
    print("="*60)
    
    print(f"\n📊 Resumen:")
    print(f"   Total keywords: {result['total_keywords']}")
    print(f"   Palabras individuales: {result['single_words']}")
    print(f"   N-gramas: {result['ngrams']}")
    
    print(f"\n🏆 Top 10 Keywords por Relevancia:")
    for i, kw in enumerate(result['top_keywords'], 1):
        domain_badge = "🎯" if kw.get('is_domain') else "  "
        print(f"   {i}. {domain_badge} {kw['keyword']}")
        print(f"      Relevancia: {kw['relevance_score']:.1f} | Freq: {kw['frequency']} | Tipo: {kw['type']}")
    
    # Clusters
    print(f"\n📂 Keywords por Categoría:")
    for category, kws in result['clusters'].items():
        if kws:
            print(f"\n   {category.upper().replace('_', ' ')}:")
            for kw in kws[:5]:
                print(f"      • {kw}")
    
    # Intención
    intent = result['intent_analysis']
    print(f"\n🎯 Análisis de Intención:")
    print(f"   Intención principal: {intent['primary_intent']}")
    print(f"   Descripción: {intent['description']}")
    
    # Sugerencias
    print(f"\n💡 Keywords Relacionadas Sugeridas:")
    for i, suggestion in enumerate(result['related_suggestions'][:10], 1):
        print(f"   {i}. {suggestion}")
    
    # Estadísticas
    stats = result['statistics']
    print(f"\n📈 Estadísticas:")
    print(f"   Relevancia promedio: {stats['avg_relevance']:.1f}")
    print(f"   Frecuencia promedio: {stats['avg_frequency']:.1f}")
    print(f"   Keywords del dominio: {stats['domain_keywords']} ({stats['domain_percentage']:.1f}%)")
    
    # Expansión de keyword
    print(f"\n🔄 Ejemplo de Expansión de Keyword:")
    base_keyword = "amarres de amor"
    expanded = extractor.expand_keyword(base_keyword, 'all')
    print(f"   Base: '{base_keyword}'")
    print(f"   Expandida a {len(expanded)} variaciones:")
    for exp in expanded[:8]:
        print(f"      • {exp}")
    
    # Exportación
    print(f"\n💾 Exportación (primeras 5 keywords en formato texto):")
    export_text = extractor.export_keywords(result['top_keywords'][:5], format='text')
    print(export_text)
    
    # Estadísticas del extractor
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DEL EXTRACTOR")
    print("="*60)
    
    extractor_stats = extractor.get_statistics()
    print(f"   Total extracciones: {extractor_stats['total_extractions']}")
    print(f"   Keywords extraídas: {extractor_stats['total_keywords_extracted']}")
    print(f"   Relevancia promedio: {extractor_stats['avg_relevance_score']:.1f}")
    print(f"   Tamaño de caché: {extractor_stats['cache_size']}")
    
    print("\n" + "="*60)