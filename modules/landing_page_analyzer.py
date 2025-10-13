"""
🚀 LANDING PAGE ANALYZER - Analizador de Landing Pages
Sistema de análisis automático de páginas de destino para extracción de contenido y generación de anuncios
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import re
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time
from collections import Counter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LandingPageAnalyzer:
    """
    Analizador de landing pages que proporciona:
    - Extracción de keywords del contenido
    - Identificación de titulares principales
    - Extracción de meta tags (title, description)
    - Detección de CTAs (Call to Actions)
    - Análisis de estructura y SEO
    - Generación automática de anuncios basados en contenido
    - Validación de URLs
    - Análisis de competidores
    """
    
    # Headers para requests (simular navegador real)
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Palabras comunes a excluir (stopwords en español)
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
        'decir', 'mundo', 'país', 'contra', 'cual', 'durante', 'todo', 'tiempo'
    }
    
    # Selectores CSS comunes para CTAs
    CTA_SELECTORS = [
        'button', 'a.btn', 'a.button', '.cta', '.call-to-action',
        'input[type="submit"]', '[class*="btn"]', '[class*="button"]',
        '[class*="cta"]', '[id*="cta"]'
    ]
    
    # Selectores para headlines
    HEADLINE_SELECTORS = ['h1', 'h2', '.hero-title', '.main-title', '.headline']
    
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        delay_between_requests: float = 1.0
    ):
        """
        Inicializa el analizador de landing pages.
        
        Args:
            timeout: Timeout para requests en segundos
            max_retries: Número máximo de reintentos
            delay_between_requests: Delay entre requests (rate limiting)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        
        # Cache de páginas analizadas
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        # Estadísticas
        self.stats = {
            'total_analyzed': 0,
            'successful': 0,
            'failed': 0,
            'cache_hits': 0
        }
        
        logger.info(f"✅ LandingPageAnalyzer inicializado")
        logger.info(f"   - Timeout: {timeout}s")
        logger.info(f"   - Max retries: {max_retries}")
    
    # =========================================================================
    # ANÁLISIS PRINCIPAL
    # =========================================================================
    
    def analyze(
        self,
        url: str,
        extract_keywords: bool = True,
        extract_ctas: bool = True,
        extract_images: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analiza una landing page completa.
        
        Args:
            url: URL de la página a analizar
            extract_keywords: Extraer keywords del contenido
            extract_ctas: Extraer CTAs
            extract_images: Extraer URLs de imágenes
            use_cache: Usar caché si está disponible
        
        Returns:
            Diccionario con análisis completo
        """
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🔍 Analizando landing page: {url}")
        
        # Validar URL
        if not self._is_valid_url(url):
            return {
                'success': False,
                'error': 'URL inválida',
                'url': url
            }
        
        # Verificar caché
        if use_cache and url in self.cache:
            logger.info(f"✅ Resultado obtenido de caché: {url}")
            self.stats['cache_hits'] += 1
            cached_result = self.cache[url].copy()
            cached_result['from_cache'] = True
            return cached_result
        
        try:
            # Obtener contenido HTML
            html_content = self._fetch_page(url)
            
            if not html_content:
                return {
                    'success': False,
                    'error': 'No se pudo obtener el contenido de la página',
                    'url': url
                }
            
            # Parsear HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraer meta tags
            meta_data = self._extract_meta_tags(soup)
            
            # Extraer headlines
            headlines = self._extract_headlines(soup)
            
            # Extraer texto principal
            main_text = self._extract_main_text(soup)
            
            # Extraer keywords
            keywords = []
            if extract_keywords:
                keywords = self._extract_keywords(soup, main_text)
            
            # Extraer CTAs
            ctas = []
            if extract_ctas:
                ctas = self._extract_ctas(soup)
            
            # Extraer imágenes
            images = []
            if extract_images:
                images = self._extract_images(soup, url)
            
            # Analizar estructura
            structure_analysis = self._analyze_structure(soup)
            
            # Análisis SEO básico
            seo_analysis = self._analyze_seo(soup, meta_data)
            
            # Generar sugerencias para anuncios
            ad_suggestions = self._generate_ad_suggestions(
                meta_data=meta_data,
                headlines=headlines,
                keywords=keywords,
                ctas=ctas
            )
            
            # Construir resultado
            result = {
                'success': True,
                'analysis_id': analysis_id,
                'url': url,
                'analyzed_at': datetime.now().isoformat(),
                'meta_data': meta_data,
                'headlines': headlines,
                'main_text_preview': main_text[:500] if main_text else '',
                'keywords': keywords,
                'ctas': ctas,
                'images': images,
                'structure': structure_analysis,
                'seo_analysis': seo_analysis,
                'ad_suggestions': ad_suggestions,
                'content_length': len(main_text),
                'word_count': len(main_text.split()) if main_text else 0
            }
            
            # Guardar en caché
            self.cache[url] = result
            
            # Actualizar estadísticas
            self.stats['total_analyzed'] += 1
            self.stats['successful'] += 1
            
            logger.info(f"✅ Análisis completado: {url}")
            logger.info(f"   - Keywords extraídas: {len(keywords)}")
            logger.info(f"   - CTAs detectados: {len(ctas)}")
            logger.info(f"   - Headlines: {len(headlines)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analizando página {url}: {e}")
            
            self.stats['total_analyzed'] += 1
            self.stats['failed'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'analyzed_at': datetime.now().isoformat()
            }
    
    # =========================================================================
    # OBTENCIÓN DE CONTENIDO
    # =========================================================================
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Obtiene el contenido HTML de una página.
        
        Args:
            url: URL de la página
        
        Returns:
            Contenido HTML o None si falla
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Intento {attempt + 1}/{self.max_retries}: {url}")
                
                response = requests.get(
                    url,
                    headers=self.DEFAULT_HEADERS,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                # Delay para rate limiting
                if self.delay_between_requests > 0:
                    time.sleep(self.delay_between_requests)
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error en intento {attempt + 1}: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Todos los intentos fallaron para {url}")
                    return None
        
        return None
    
    # =========================================================================
    # EXTRACCIÓN DE META TAGS
    # =========================================================================
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae meta tags importantes (title, description, keywords, og:tags).
        
        Args:
            soup: Objeto BeautifulSoup
        
        Returns:
            Diccionario con meta tags
        """
        meta_data = {
            'title': '',
            'description': '',
            'keywords': '',
            'og_title': '',
            'og_description': '',
            'og_image': '',
            'canonical': ''
        }
        
        # Title tag
        title_tag = soup.find('title')
        if title_tag:
            meta_data['title'] = title_tag.get_text(strip=True)
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_data['description'] = meta_desc.get('content', '')
        
        # Meta keywords
        meta_kw = soup.find('meta', attrs={'name': 'keywords'})
        if meta_kw:
            meta_data['keywords'] = meta_kw.get('content', '')
        
        # Open Graph tags
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title:
            meta_data['og_title'] = og_title.get('content', '')
        
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            meta_data['og_description'] = og_desc.get('content', '')
        
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        if og_image:
            meta_data['og_image'] = og_image.get('content', '')
        
        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            meta_data['canonical'] = canonical.get('href', '')
        
        return meta_data
    
    # =========================================================================
    # EXTRACCIÓN DE HEADLINES
    # =========================================================================
    
    def _extract_headlines(self, soup: BeautifulSoup) -> List[str]:
        """
        Extrae headlines principales de la página (h1, h2, hero titles).
        
        Args:
            soup: Objeto BeautifulSoup
        
        Returns:
            Lista de headlines
        """
        headlines = []
        
        for selector in self.HEADLINE_SELECTORS:
            elements = soup.select(selector)
            
            for element in elements:
                text = element.get_text(strip=True)
                
                if text and len(text) > 10 and len(text) < 150:
                    if text not in headlines:
                        headlines.append(text)
        
        # Limitar a top 10
        return headlines[:10]
    
    # =========================================================================
    # EXTRACCIÓN DE TEXTO PRINCIPAL
    # =========================================================================
    
    def _extract_main_text(self, soup: BeautifulSoup) -> str:
        """
        Extrae el texto principal del contenido, excluyendo elementos irrelevantes.
        
        Args:
            soup: Objeto BeautifulSoup
        
        Returns:
            Texto principal
        """
        # Remover elementos irrelevantes
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Extraer texto de elementos principales
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
            
            # Limpiar espacios múltiples
            text = re.sub(r'\s+', ' ', text)
            
            return text
        
        return ''
    
    # =========================================================================
    # EXTRACCIÓN DE KEYWORDS
    # =========================================================================
    
    def _extract_keywords(
        self,
        soup: BeautifulSoup,
        main_text: str,
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Extrae keywords del contenido usando frecuencia y relevancia.
        
        Args:
            soup: Objeto BeautifulSoup
            main_text: Texto principal
            top_n: Número de keywords a retornar
        
        Returns:
            Lista de keywords con scores
        """
        # Combinar texto de múltiples fuentes
        all_text = main_text
        
        # Agregar texto de meta tags
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            all_text += ' ' + meta_desc.get('content', '')
        
        meta_kw = soup.find('meta', attrs={'name': 'keywords'})
        if meta_kw:
            all_text += ' ' + meta_kw.get('content', '')
        
        # Normalizar texto
        text_lower = all_text.lower()
        
        # Extraer palabras
        words = re.findall(r'\b[a-záéíóúñü]{3,}\b', text_lower)
        
        # Filtrar stopwords
        filtered_words = [w for w in words if w not in self.STOPWORDS]
        
        # Contar frecuencias
        word_counts = Counter(filtered_words)
        
        # Extraer bi-gramas (frases de 2 palabras)
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in self.STOPWORDS and words[i+1] not in self.STOPWORDS:
                bigram = f"{words[i]} {words[i+1]}"
                bigrams.append(bigram)
        
        bigram_counts = Counter(bigrams)
        
        # Combinar resultados
        keywords = []
        
        # Palabras individuales (top 15)
        for word, count in word_counts.most_common(15):
            if len(word) > 3:
                keywords.append({
                    'keyword': word,
                    'type': 'single',
                    'frequency': count,
                    'relevance_score': self._calculate_keyword_relevance(
                        word, soup, count, len(filtered_words)
                    )
                })
        
        # Bi-gramas (top 5)
        for bigram, count in bigram_counts.most_common(5):
            if count >= 2:  # Aparecer al menos 2 veces
                keywords.append({
                    'keyword': bigram,
                    'type': 'phrase',
                    'frequency': count,
                    'relevance_score': self._calculate_keyword_relevance(
                        bigram, soup, count, len(bigrams)
                    )
                })
        
        # Ordenar por relevancia
        keywords.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return keywords[:top_n]
    
    def _calculate_keyword_relevance(
        self,
        keyword: str,
        soup: BeautifulSoup,
        frequency: int,
        total_words: int
    ) -> float:
        """
        Calcula score de relevancia de una keyword.
        
        Args:
            keyword: Keyword a evaluar
            soup: Objeto BeautifulSoup
            frequency: Frecuencia de aparición
            total_words: Total de palabras
        
        Returns:
            Score de relevancia (0-100)
        """
        score = 0.0
        
        # Factor 1: Frecuencia (30%)
        frequency_score = (frequency / total_words * 1000) if total_words > 0 else 0
        score += frequency_score * 0.3
        
        # Factor 2: Aparición en título (25%)
        title = soup.find('title')
        if title and keyword.lower() in title.get_text().lower():
            score += 25
        
        # Factor 3: Aparición en h1/h2 (20%)
        for h in soup.find_all(['h1', 'h2']):
            if keyword.lower() in h.get_text().lower():
                score += 10
        
        # Factor 4: Aparición en meta description (15%)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and keyword.lower() in meta_desc.get('content', '').lower():
            score += 15
        
        # Factor 5: Aparición en URLs/links (10%)
        for link in soup.find_all('a', href=True):
            if keyword.lower() in link['href'].lower():
                score += 5
                break
        
        return min(100, score)
    
    # =========================================================================
    # EXTRACCIÓN DE CTAs
    # =========================================================================
    
    def _extract_ctas(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extrae Call-To-Actions de la página.
        
        Args:
            soup: Objeto BeautifulSoup
        
        Returns:
            Lista de CTAs con texto y tipo
        """
        ctas = []
        seen_texts = set()
        
        for selector in self.CTA_SELECTORS:
            elements = soup.select(selector)
            
            for element in elements:
                text = element.get_text(strip=True)
                
                # Filtrar CTAs válidos
                if text and 5 <= len(text) <= 50 and text not in seen_texts:
                    cta_type = self._classify_cta(text)
                    
                    ctas.append({
                        'text': text,
                        'type': cta_type,
                        'element': element.name,
                        'has_link': bool(element.get('href'))
                    })
                    
                    seen_texts.add(text)
        
        return ctas[:10]  # Top 10 CTAs
    
    def _classify_cta(self, text: str) -> str:
        """Clasifica tipo de CTA basado en el texto."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['comprar', 'compra', 'adquirir', 'pagar']):
            return 'purchase'
        elif any(word in text_lower for word in ['registr', 'suscri', 'unir', 'empezar']):
            return 'signup'
        elif any(word in text_lower for word in ['consulta', 'contacta', 'llama', 'escribe']):
            return 'contact'
        elif any(word in text_lower for word in ['descargar', 'obtener', 'recibir']):
            return 'download'
        elif any(word in text_lower for word in ['ver', 'conocer', 'descubrir', 'explorar']):
            return 'explore'
        else:
            return 'other'
    
    # =========================================================================
    # EXTRACCIÓN DE IMÁGENES
    # =========================================================================
    
    def _extract_images(
        self,
        soup: BeautifulSoup,
        base_url: str,
        max_images: int = 10
    ) -> List[Dict[str, str]]:
        """
        Extrae URLs de imágenes de la página.
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base para resolver rutas relativas
            max_images: Número máximo de imágenes
        
        Returns:
            Lista de imágenes con URLs y alt text
        """
        images = []
        seen_urls = set()
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            
            if not src:
                continue
            
            # Resolver URL relativa
            full_url = urljoin(base_url, src)
            
            # Evitar duplicados
            if full_url in seen_urls:
                continue
            
            seen_urls.add(full_url)
            
            images.append({
                'url': full_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
            
            if len(images) >= max_images:
                break
        
        return images
    
    # =========================================================================
    # ANÁLISIS DE ESTRUCTURA
    # =========================================================================
    
    def _analyze_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analiza la estructura de la página.
        
        Args:
            soup: Objeto BeautifulSoup
        
        Returns:
            Diccionario con análisis de estructura
        """
        structure = {
            'has_header': bool(soup.find('header')),
            'has_footer': bool(soup.find('footer')),
            'has_nav': bool(soup.find('nav')),
            'has_main': bool(soup.find('main')),
            'h1_count': len(soup.find_all('h1')),
            'h2_count': len(soup.find_all('h2')),
            'h3_count': len(soup.find_all('h3')),
            'paragraph_count': len(soup.find_all('p')),
            'link_count': len(soup.find_all('a')),
            'image_count': len(soup.find_all('img')),
            'form_count': len(soup.find_all('form')),
            'has_mobile_viewport': bool(
                soup.find('meta', attrs={'name': 'viewport'})
            )
        }
        
        return structure
    
    # =========================================================================
    # ANÁLISIS SEO
    # =========================================================================
    
    def _analyze_seo(
        self,
        soup: BeautifulSoup,
        meta_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Realiza análisis SEO básico.
        
        Args:
            soup: Objeto BeautifulSoup
            meta_data: Meta tags extraídos
        
        Returns:
            Análisis SEO
        """
        issues = []
        recommendations = []
        score = 100  # Empezar con 100 y restar por problemas
        
        # Verificar title
        if not meta_data.get('title'):
            issues.append('Falta title tag')
            score -= 20
        elif len(meta_data['title']) < 30:
            recommendations.append('Title tag muy corto (mínimo 30 caracteres)')
            score -= 5
        elif len(meta_data['title']) > 60:
            recommendations.append('Title tag muy largo (máximo 60 caracteres)')
            score -= 5
        
        # Verificar meta description
        if not meta_data.get('description'):
            issues.append('Falta meta description')
            score -= 15
        elif len(meta_data['description']) < 120:
            recommendations.append('Meta description muy corta (mínimo 120 caracteres)')
            score -= 5
        elif len(meta_data['description']) > 160:
            recommendations.append('Meta description muy larga (máximo 160 caracteres)')
            score -= 5
        
        # Verificar H1
        h1_tags = soup.find_all('h1')
        if len(h1_tags) == 0:
            issues.append('Falta H1 tag')
            score -= 15
        elif len(h1_tags) > 1:
            recommendations.append('Múltiples H1 tags (solo debe haber uno)')
            score -= 10
        
        # Verificar imágenes sin alt
        images_without_alt = len([
            img for img in soup.find_all('img')
            if not img.get('alt')
        ])
        
        if images_without_alt > 0:
            recommendations.append(f'{images_without_alt} imágenes sin atributo alt')
            score -= min(10, images_without_alt * 2)
        
        # Verificar canonical
        if not meta_data.get('canonical'):
            recommendations.append('Considera agregar canonical URL')
            score -= 5
        
        # Verificar viewport (mobile)
        if not soup.find('meta', attrs={'name': 'viewport'}):
            issues.append('Falta meta viewport (no optimizado para móvil)')
            score -= 10
        
        score = max(0, score)
        
        seo_analysis = {
            'score': score,
            'grade': self._seo_score_to_grade(score),
            'issues': issues,
            'recommendations': recommendations,
            'summary': self._generate_seo_summary(score, issues, recommendations)
        }
        
        return seo_analysis
    
    def _seo_score_to_grade(self, score: int) -> str:
        """Convierte score SEO a grado."""
        if score >= 90:
            return 'Excelente'
        elif score >= 75:
            return 'Bueno'
        elif score >= 60:
            return 'Aceptable'
        elif score >= 40:
            return 'Necesita Mejoras'
        else:
            return 'Pobre'
    
    def _generate_seo_summary(
        self,
        score: int,
        issues: List[str],
        recommendations: List[str]
    ) -> str:
        """Genera resumen SEO."""
        if score >= 90:
            return "Excelente optimización SEO. La página cumple con las mejores prácticas."
        elif score >= 75:
            return f"Buena optimización SEO con {len(recommendations)} mejoras menores sugeridas."
        elif score >= 60:
            return f"Optimización SEO aceptable. Se detectaron {len(issues)} problemas y {len(recommendations)} recomendaciones."
        else:
            return f"Requiere mejoras importantes en SEO. Se detectaron {len(issues)} problemas críticos."
    
    # =========================================================================
    # GENERACIÓN DE SUGERENCIAS PARA ANUNCIOS
    # =========================================================================
    
    def _generate_ad_suggestions(
        self,
        meta_data: Dict[str, Any],
        headlines: List[str],
        keywords: List[Dict[str, Any]],
        ctas: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Genera sugerencias automáticas para crear anuncios.
        
        Args:
            meta_data: Meta tags
            headlines: Headlines extraídos
            keywords: Keywords extraídas
            ctas: CTAs detectados
        
        Returns:
            Sugerencias para anuncios
        """
        suggestions = {
            'suggested_headlines': [],
            'suggested_descriptions': [],
            'suggested_keywords': [],
            'suggested_ctas': []
        }
        
        # Sugerir headlines (basados en H1/title)
        if meta_data.get('title'):
            # Truncar a 30 caracteres si es necesario
            title_headline = meta_data['title'][:30]
            if len(meta_data['title']) > 30:
                title_headline = title_headline.rsplit(' ', 1)[0]  # Cortar en palabra
            suggestions['suggested_headlines'].append(title_headline)
        
        for headline in headlines[:3]:
            if len(headline) <= 30:
                suggestions['suggested_headlines'].append(headline)
            else:
                # Truncar inteligentemente
                truncated = headline[:30]
                truncated = truncated.rsplit(' ', 1)[0]
                suggestions['suggested_headlines'].append(truncated)
        
        # Sugerir descriptions (basadas en meta description)
        if meta_data.get('description'):
            desc = meta_data['description']
            if len(desc) <= 90:
                suggestions['suggested_descriptions'].append(desc)
            else:
                # Truncar a 90 caracteres
                truncated_desc = desc[:90]
                truncated_desc = truncated_desc.rsplit(' ', 1)[0]
                suggestions['suggested_descriptions'].append(truncated_desc)
        
        # Si tenemos headlines, crear descripción alternativa
        if headlines:
            alt_desc = f"{headlines[0][:60]}. Más información disponible."
            if len(alt_desc) <= 90:
                suggestions['suggested_descriptions'].append(alt_desc)
        
        # Sugerir keywords (top keywords por relevancia)
        top_keywords = sorted(
            keywords,
            key=lambda x: x['relevance_score'],
            reverse=True
        )[:15]
        
        suggestions['suggested_keywords'] = [kw['keyword'] for kw in top_keywords]
        
        # Sugerir CTAs (los más relevantes)
        contact_ctas = [cta for cta in ctas if cta['type'] == 'contact']
        other_ctas = [cta for cta in ctas if cta['type'] != 'contact']
        
        # Priorizar CTAs de contacto
        for cta in (contact_ctas + other_ctas)[:5]:
            suggestions['suggested_ctas'].append(cta['text'])
        
        return suggestions
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _is_valid_url(self, url: str) -> bool:
        """Valida formato de URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def clear_cache(self) -> int:
        """
        Limpia la caché de páginas analizadas.
        
        Returns:
            Número de entradas eliminadas
        """
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️ Caché limpiada: {count} entradas eliminadas")
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del analizador."""
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'success_rate': round(
                (self.stats['successful'] / self.stats['total_analyzed'] * 100)
                if self.stats['total_analyzed'] > 0 else 0,
                2
            )
        }
    
    def get_cached_analysis(self, url: str) -> Optional[Dict[str, Any]]:
        """Obtiene análisis de caché si existe."""
        return self.cache.get(url)
    
    def export_analysis(
        self,
        analysis: Dict[str, Any],
        format: str = 'json'
    ) -> str:
        """
        Exporta análisis a formato especificado.
        
        Args:
            analysis: Análisis a exportar
            format: Formato ('json' o 'text')
        
        Returns:
            Análisis en formato string
        """
        if format == 'json':
            import json
            return json.dumps(analysis, indent=2, ensure_ascii=False)
        
        elif format == 'text':
            output = []
            output.append("="*60)
            output.append("ANÁLISIS DE LANDING PAGE")
            output.append("="*60)
            output.append(f"\nURL: {analysis.get('url', 'N/A')}")
            output.append(f"Fecha: {analysis.get('analyzed_at', 'N/A')}")
            
            output.append("\n--- META DATOS ---")
            meta = analysis.get('meta_data', {})
            output.append(f"Title: {meta.get('title', 'N/A')}")
            output.append(f"Description: {meta.get('description', 'N/A')}")
            
            output.append("\n--- KEYWORDS EXTRAÍDAS ---")
            for i, kw in enumerate(analysis.get('keywords', [])[:10], 1):
                output.append(f"{i}. {kw['keyword']} (score: {kw['relevance_score']:.1f})")
            
            output.append("\n--- CTAs DETECTADOS ---")
            for i, cta in enumerate(analysis.get('ctas', []), 1):
                output.append(f"{i}. {cta['text']} ({cta['type']})")
            
            output.append("\n--- ANÁLISIS SEO ---")
            seo = analysis.get('seo_analysis', {})
            output.append(f"Score: {seo.get('score', 0)}/100 ({seo.get('grade', 'N/A')})")
            
            if seo.get('issues'):
                output.append("\nProblemas:")
                for issue in seo['issues']:
                    output.append(f"  • {issue}")
            
            return '\n'.join(output)
        
        return ''


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_landing_page_analyzer(
    timeout: int = 10,
    max_retries: int = 3
) -> LandingPageAnalyzer:
    """
    Factory function para crear analizador.
    
    Args:
        timeout: Timeout en segundos
        max_retries: Reintentos máximos
    
    Returns:
        Instancia de LandingPageAnalyzer
    """
    return LandingPageAnalyzer(
        timeout=timeout,
        max_retries=max_retries
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🚀 LANDING PAGE ANALYZER - Ejemplo de Uso")
    print("="*60)
    
    # Crear analizador
    analyzer = LandingPageAnalyzer()
    
    # URL de ejemplo (cambiar por una real)
    test_url = "https://example.com"
    
    print(f"\n🔍 Analizando: {test_url}")
    
    # Analizar página
    result = analyzer.analyze(
        url=test_url,
        extract_keywords=True,
        extract_ctas=True,
        extract_images=False
    )
    
    if result['success']:
        print("\n✅ Análisis completado exitosamente")
        print(f"\n📊 RESUMEN:")
        print(f"   - Keywords extraídas: {len(result['keywords'])}")
        print(f"   - Headlines: {len(result['headlines'])}")
        print(f"   - CTAs: {len(result['ctas'])}")
        print(f"   - SEO Score: {result['seo_analysis']['score']}/100")
        
        print(f"\n🔑 TOP 5 KEYWORDS:")
        for i, kw in enumerate(result['keywords'][:5], 1):
            print(f"   {i}. {kw['keyword']} (relevancia: {kw['relevance_score']:.1f})")
        
        print(f"\n💡 SUGERENCIAS PARA ANUNCIOS:")
        suggestions = result['ad_suggestions']
        
        print("\n   Headlines sugeridos:")
        for h in suggestions['suggested_headlines'][:3]:
            print(f"      • {h}")
        
        print("\n   Descripciones sugeridas:")
        for d in suggestions['suggested_descriptions'][:2]:
            print(f"      • {d}")
        
        print("\n   CTAs sugeridos:")
        for cta in suggestions['suggested_ctas'][:3]:
            print(f"      • {cta}")
    
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
    
    # Estadísticas
    print("\n📈 ESTADÍSTICAS:")
    stats = analyzer.get_statistics()
    print(f"   - Total analizadas: {stats['total_analyzed']}")
    print(f"   - Exitosas: {stats['successful']}")
    print(f"   - Tasa de éxito: {stats['success_rate']:.1f}%")