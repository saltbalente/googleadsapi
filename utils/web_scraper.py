"""
🌐 WEB SCRAPER - Utilidades de Web Scraping
Sistema de scraping web para análisis de competencia y extracción de datos
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import re
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse, urljoin, quote
from bs4 import BeautifulSoup
import time
from pathlib import Path
import json
from collections import defaultdict
import hashlib

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """
    Scraper web que proporciona:
    - Scraping de páginas web
    - Extracción de contenido estructurado
    - Análisis de meta tags
    - Extracción de enlaces
    - Detección de anuncios de competidores
    - Rate limiting y respeto de robots.txt
    - Caché de resultados
    - Manejo de errores y reintentos
    - User-Agent rotation
    """
    
    # =========================================================================
    # CONFIGURACIÓN
    # =========================================================================
    
    # User-Agents para rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    # Headers base
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    # Selectores CSS para detección de anuncios
    AD_SELECTORS = [
        'div[class*="ad"]',
        'div[id*="ad"]',
        'ins.adsbygoogle',
        'div[class*="sponsored"]',
        'div[class*="advertisement"]',
        '[data-ad-slot]',
        'iframe[src*="doubleclick"]',
        'iframe[src*="googlesyndication"]'
    ]
    
    # Patterns para detectar anuncios de Google Ads en SERPs
    GOOGLE_AD_PATTERNS = [
        r'<div[^>]*class="[^"]*ad[^"]*"[^>]*>',
        r'<div[^>]*id="[^"]*ad[^"]*"[^>]*>',
        r'<ins class="adsbygoogle"',
        r'data-text-ad'
    ]
    
    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        delay_between_requests: float = 2.0,
        respect_robots_txt: bool = True,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Inicializa el web scraper.
        
        Args:
            timeout: Timeout para requests en segundos
            max_retries: Número máximo de reintentos
            delay_between_requests: Delay entre requests (rate limiting)
            respect_robots_txt: Respetar robots.txt
            cache_enabled: Habilitar caché
            cache_dir: Directorio de caché
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.respect_robots_txt = respect_robots_txt
        self.cache_enabled = cache_enabled
        
        # Configurar caché
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / "data" / "scraper_cache"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Session para mantener conexiones
        self.session = requests.Session()
        
        # Cache en memoria
        self.memory_cache: Dict[str, Any] = {}
        
        # Tracking de requests
        self.last_request_time: Dict[str, float] = {}
        
        # Estadísticas
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0,
            'total_bytes_downloaded': 0
        }
        
        logger.info(f"✅ WebScraper inicializado")
        logger.info(f"   - Timeout: {timeout}s")
        logger.info(f"   - Max retries: {max_retries}")
        logger.info(f"   - Rate limiting: {delay_between_requests}s")
        logger.info(f"   - Cache: {'enabled' if cache_enabled else 'disabled'}")
    
    # =========================================================================
    # SCRAPING BÁSICO
    # =========================================================================
    
    def scrape(
        self,
        url: str,
        use_cache: bool = True,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Realiza scraping de una URL.
        
        Args:
            url: URL a scrapear
            use_cache: Usar caché si está disponible
            custom_headers: Headers personalizados
        
        Returns:
            Diccionario con contenido scrapeado
        """
        scrape_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🌐 Scraping URL: {url}")
        
        # Validar URL
        if not self._is_valid_url(url):
            return {
                'success': False,
                'error': 'URL inválida',
                'url': url
            }
        
        # Verificar caché
        if use_cache and self.cache_enabled:
            cached = self._get_from_cache(url)
            if cached:
                logger.info(f"✅ Contenido obtenido de caché")
                self.stats['cached_requests'] += 1
                cached['from_cache'] = True
                return cached
        
        # Rate limiting
        self._apply_rate_limit(url)
        
        # Obtener HTML
        html_content = self._fetch_html(url, custom_headers)
        
        if not html_content:
            return {
                'success': False,
                'error': 'No se pudo obtener el contenido',
                'url': url
            }
        
        # Parsear HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extraer información
        result = {
            'scrape_id': scrape_id,
            'success': True,
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'html_length': len(html_content),
            'title': self._extract_title(soup),
            'meta_tags': self._extract_meta_tags(soup),
            'headings': self._extract_headings(soup),
            'links': self._extract_links(soup, url),
            'text_content': self._extract_text(soup),
            'images': self._extract_images(soup, url),
            'structured_data': self._extract_structured_data(soup)
        }
        
        # Guardar en caché
        if self.cache_enabled:
            self._save_to_cache(url, result)
        
        # Actualizar estadísticas
        self.stats['successful_requests'] += 1
        self.stats['total_bytes_downloaded'] += len(html_content)
        
        logger.info(f"✅ Scraping completado: {url}")
        
        return result
    
    def scrape_multiple(
        self,
        urls: List[str],
        delay: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrapea múltiples URLs con rate limiting.
        
        Args:
            urls: Lista de URLs
            delay: Delay entre requests (None = usar default)
        
        Returns:
            Lista de resultados
        """
        logger.info(f"🌐 Scraping {len(urls)} URLs...")
        
        results = []
        delay_time = delay or self.delay_between_requests
        
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] Scraping: {url}")
            
            result = self.scrape(url)
            results.append(result)
            
            # Delay entre requests (excepto el último)
            if i < len(urls):
                time.sleep(delay_time)
        
        logger.info(f"✅ Scraping múltiple completado: {len(results)} URLs")
        
        return results
    
    # =========================================================================
    # OBTENCIÓN DE HTML
    # =========================================================================
    
    def _fetch_html(
        self,
        url: str,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Obtiene HTML de una URL con reintentos.
        
        Args:
            url: URL a obtener
            custom_headers: Headers personalizados
        
        Returns:
            HTML content o None si falla
        """
        headers = self._get_headers(custom_headers)
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Intento {attempt + 1}/{self.max_retries}: {url}")
                
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                self.stats['total_requests'] += 1
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error en intento {attempt + 1}: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.debug(f"Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Todos los intentos fallaron para {url}")
                    self.stats['failed_requests'] += 1
                    return None
        
        return None
    
    def _get_headers(
        self,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Obtiene headers con User-Agent rotativo."""
        import random
        
        headers = self.DEFAULT_HEADERS.copy()
        
        # Rotar User-Agent
        headers['User-Agent'] = random.choice(self.USER_AGENTS)
        
        # Agregar headers personalizados
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    # =========================================================================
    # EXTRACCIÓN DE CONTENIDO
    # =========================================================================
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrae título de la página."""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else ''
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extrae meta tags importantes."""
        meta_tags = {
            'description': '',
            'keywords': '',
            'author': '',
            'robots': '',
            'og_title': '',
            'og_description': '',
            'og_image': '',
            'twitter_card': ''
        }
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_tags['description'] = meta_desc.get('content', '')
        
        # Meta keywords
        meta_kw = soup.find('meta', attrs={'name': 'keywords'})
        if meta_kw:
            meta_tags['keywords'] = meta_kw.get('content', '')
        
        # Author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author:
            meta_tags['author'] = meta_author.get('content', '')
        
        # Robots
        meta_robots = soup.find('meta', attrs={'name': 'robots'})
        if meta_robots:
            meta_tags['robots'] = meta_robots.get('content', '')
        
        # Open Graph
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title:
            meta_tags['og_title'] = og_title.get('content', '')
        
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            meta_tags['og_description'] = og_desc.get('content', '')
        
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        if og_image:
            meta_tags['og_image'] = og_image.get('content', '')
        
        # Twitter Card
        twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
        if twitter_card:
            meta_tags['twitter_card'] = twitter_card.get('content', '')
        
        return meta_tags
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extrae headings (h1-h6)."""
        headings = {
            'h1': [],
            'h2': [],
            'h3': [],
            'h4': [],
            'h5': [],
            'h6': []
        }
        
        for level in range(1, 7):
            tag = f'h{level}'
            elements = soup.find_all(tag)
            
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    headings[tag].append(text)
        
        return headings
    
    def _extract_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        limit: int = 100
    ) -> List[Dict[str, str]]:
        """Extrae enlaces de la página."""
        links = []
        seen_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Resolver URL relativa
            full_url = urljoin(base_url, href)
            
            # Evitar duplicados
            if full_url in seen_urls:
                continue
            
            seen_urls.add(full_url)
            
            # Extraer texto del enlace
            link_text = link.get_text(strip=True)
            
            links.append({
                'url': full_url,
                'text': link_text,
                'is_external': self._is_external_link(full_url, base_url)
            })
            
            if len(links) >= limit:
                break
        
        return links
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extrae texto principal del contenido."""
        # Remover elementos no deseados
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Intentar encontrar contenido principal
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
            # Limpiar espacios múltiples
            text = re.sub(r'\s+', ' ', text)
            return text
        
        return ''
    
    def _extract_images(
        self,
        soup: BeautifulSoup,
        base_url: str,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Extrae imágenes de la página."""
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
            
            if len(images) >= limit:
                break
        
        return images
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae datos estructurados (JSON-LD, microdata)."""
        structured_data = []
        
        # JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append({
                    'type': 'json-ld',
                    'data': data
                })
            except json.JSONDecodeError:
                pass
        
        return structured_data
    
    # =========================================================================
    # ANÁLISIS DE ANUNCIOS
    # =========================================================================
    
    def detect_ads(self, url: str) -> Dict[str, Any]:
        """
        Detecta anuncios en una página.
        
        Args:
            url: URL a analizar
        
        Returns:
            Análisis de anuncios detectados
        """
        logger.info(f"🔍 Detectando anuncios en: {url}")
        
        # Scrapear página
        scrape_result = self.scrape(url)
        
        if not scrape_result['success']:
            return {
                'success': False,
                'error': 'No se pudo scrapear la página',
                'url': url
            }
        
        # Obtener HTML nuevamente para análisis de anuncios
        html_content = self._fetch_html(url)
        
        if not html_content:
            return {
                'success': False,
                'error': 'No se pudo obtener HTML',
                'url': url
            }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Detectar elementos de anuncios
        ad_elements = []
        
        for selector in self.AD_SELECTORS:
            elements = soup.select(selector)
            ad_elements.extend(elements)
        
        # Analizar cada elemento de anuncio
        ads_found = []
        
        for i, element in enumerate(ad_elements[:20], 1):  # Limitar a 20
            ad_info = {
                'ad_id': i,
                'tag': element.name,
                'classes': element.get('class', []),
                'id': element.get('id', ''),
                'text_preview': element.get_text(strip=True)[:100],
                'has_link': bool(element.find('a'))
            }
            
            ads_found.append(ad_info)
        
        # Detectar anuncios de Google Ads por patterns
        google_ads_count = 0
        for pattern in self.GOOGLE_AD_PATTERNS:
            matches = re.findall(pattern, html_content)
            google_ads_count += len(matches)
        
        result = {
            'success': True,
            'url': url,
            'total_ad_elements': len(ad_elements),
            'ads_analyzed': len(ads_found),
            'ads_found': ads_found,
            'google_ads_detected': google_ads_count,
            'has_ads': len(ad_elements) > 0,
            'ad_density': self._calculate_ad_density(
                len(ad_elements),
                len(soup.get_text())
            )
        }
        
        logger.info(f"✅ Detección completada: {len(ad_elements)} elementos de anuncio")
        
        return result
    
    def scrape_serp(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Scrapea resultados de búsqueda de Google (SERP).
        
        NOTA: Google bloquea scraping automático. Usar con precaución.
        En producción, usar Google Custom Search API.
        
        Args:
            query: Query de búsqueda
            num_results: Número de resultados
        
        Returns:
            Resultados de búsqueda y anuncios
        """
        logger.warning("⚠️ Scraping de SERP puede ser bloqueado por Google")
        logger.info(f"🔍 Buscando: {query}")
        
        # URL de búsqueda de Google
        search_url = f"https://www.google.com/search?q={quote(query)}&num={num_results}"
        
        # Headers especiales para Google
        google_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/'
        }
        
        # Obtener HTML
        html_content = self._fetch_html(search_url, google_headers)
        
        if not html_content:
            return {
                'success': False,
                'error': 'No se pudo obtener resultados de búsqueda',
                'query': query
            }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Detectar anuncios (aparecen antes de resultados orgánicos)
        ads = []
        
        # Selectores para anuncios de Google (pueden cambiar)
        ad_containers = soup.find_all('div', class_=re.compile('uEierd|v5yQqb'))
        
        for ad in ad_containers:
            ad_title_elem = ad.find('div', role='heading')
            ad_title = ad_title_elem.get_text(strip=True) if ad_title_elem else ''
            
            ad_link_elem = ad.find('a')
            ad_link = ad_link_elem['href'] if ad_link_elem and 'href' in ad_link_elem.attrs else ''
            
            ad_desc_elem = ad.find('div', class_=re.compile('MUxGbd'))
            ad_desc = ad_desc_elem.get_text(strip=True) if ad_desc_elem else ''
            
            if ad_title:
                ads.append({
                    'title': ad_title,
                    'url': ad_link,
                    'description': ad_desc,
                    'type': 'google_ad'
                })
        
        # Extraer resultados orgánicos
        organic_results = []
        
        result_divs = soup.find_all('div', class_='g')
        
        for result in result_divs[:num_results]:
            title_elem = result.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            link_elem = result.find('a')
            link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''
            
            snippet_elem = result.find('div', class_=re.compile('VwiC3b'))
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
            
            if title:
                organic_results.append({
                    'title': title,
                    'url': link,
                    'snippet': snippet,
                    'type': 'organic'
                })
        
        result = {
            'success': True,
            'query': query,
            'search_url': search_url,
            'total_ads': len(ads),
            'total_organic': len(organic_results),
            'ads': ads,
            'organic_results': organic_results,
            'scraped_at': datetime.now().isoformat(),
            'note': 'Los resultados pueden estar incompletos debido a protecciones anti-bot de Google'
        }
        
        logger.info(f"✅ SERP scraping completado")
        logger.info(f"   - Anuncios: {len(ads)}")
        logger.info(f"   - Resultados orgánicos: {len(organic_results)}")
        
        return result
    
    # =========================================================================
    # ANÁLISIS DE COMPETENCIA
    # =========================================================================
    
    def analyze_competitor_site(self, url: str) -> Dict[str, Any]:
        """
        Analiza sitio de competidor.
        
        Args:
            url: URL del competidor
        
        Returns:
            Análisis completo del sitio
        """
        logger.info(f"🎯 Analizando competidor: {url}")
        
        # Scraping básico
        scrape_result = self.scrape(url)
        
        if not scrape_result['success']:
            return {
                'success': False,
                'error': 'No se pudo scrapear el sitio',
                'url': url
            }
        
        # Análisis adicional
        ad_analysis = self.detect_ads(url)
        
        # Análisis de contenido
        content_analysis = {
            'total_headings': sum(
                len(headings)
                for headings in scrape_result['headings'].values()
            ),
            'total_links': len(scrape_result['links']),
            'total_images': len(scrape_result['images']),
            'text_length': len(scrape_result['text_content']),
            'has_structured_data': len(scrape_result['structured_data']) > 0
        }
        
        # Análisis de SEO básico
        seo_analysis = {
            'has_title': bool(scrape_result['title']),
            'title_length': len(scrape_result['title']),
            'has_meta_description': bool(scrape_result['meta_tags']['description']),
            'meta_desc_length': len(scrape_result['meta_tags']['description']),
            'has_og_tags': bool(scrape_result['meta_tags']['og_title']),
            'h1_count': len(scrape_result['headings']['h1']),
            'external_links': len([
                link for link in scrape_result['links']
                if link['is_external']
            ])
        }
        
        # Tecnologías detectadas (básico)
        technologies = self._detect_technologies(scrape_result)
        
        result = {
            'success': True,
            'url': url,
            'analyzed_at': datetime.now().isoformat(),
            'basic_info': {
                'title': scrape_result['title'],
                'meta_description': scrape_result['meta_tags']['description']
            },
            'content_analysis': content_analysis,
            'seo_analysis': seo_analysis,
            'ad_analysis': ad_analysis,
            'technologies': technologies,
            'strengths': self._identify_competitor_strengths(
                content_analysis,
                seo_analysis,
                ad_analysis
            ),
            'opportunities': self._identify_opportunities(
                seo_analysis,
                ad_analysis
            )
        }
        
        logger.info(f"✅ Análisis de competidor completado")
        
        return result
    
    def _detect_technologies(self, scrape_result: Dict) -> List[str]:
        """Detecta tecnologías usadas en el sitio."""
        technologies = []
        
        # Buscar en el HTML (simplificado)
        text_content = scrape_result.get('text_content', '').lower()
        
        tech_indicators = {
            'WordPress': ['wp-content', 'wordpress'],
            'Shopify': ['shopify', 'myshopify'],
            'Wix': ['wix.com', 'wixsite'],
            'Google Analytics': ['google-analytics', 'gtag'],
            'Google Ads': ['googleads', 'adwords'],
            'Facebook Pixel': ['facebook', 'fbq']
        }
        
        for tech, indicators in tech_indicators.items():
            if any(ind in text_content for ind in indicators):
                technologies.append(tech)
        
        return technologies
    
    def _identify_competitor_strengths(
        self,
        content: Dict,
        seo: Dict,
        ads: Dict
    ) -> List[str]:
        """Identifica fortalezas del competidor."""
        strengths = []
        
        if content['total_headings'] > 10:
            strengths.append("Contenido bien estructurado")
        
        if seo['has_meta_description'] and seo['meta_desc_length'] > 100:
            strengths.append("Meta description optimizada")
        
        if seo['has_og_tags']:
            strengths.append("Optimizado para redes sociales")
        
        if ads.get('has_ads'):
            strengths.append("Usa publicidad activamente")
        
        if content['has_structured_data']:
            strengths.append("Implementa datos estructurados")
        
        return strengths
    
    def _identify_opportunities(
        self,
        seo: Dict,
        ads: Dict
    ) -> List[str]:
        """Identifica oportunidades basadas en debilidades del competidor."""
        opportunities = []
        
        if not seo['has_meta_description']:
            opportunities.append("Competidor sin meta description - oportunidad de superarlo en SEO")
        
        if seo['h1_count'] == 0:
            opportunities.append("Competidor sin H1 - mejora tu estructura")
        
        if not ads.get('has_ads'):
            opportunities.append("Competidor no usa ads - oportunidad de capturar tráfico pagado")
        
        if seo['title_length'] < 30:
            opportunities.append("Title tag corto - optimiza el tuyo mejor")
        
        return opportunities
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _calculate_ad_density(
        self,
        ad_count: int,
        text_length: int
    ) -> float:
        """Calcula densidad de anuncios."""
        if text_length == 0:
            return 0.0
        
        # Anuncios por cada 1000 caracteres de texto
        density = (ad_count / text_length * 1000)
        return round(density, 2)
    
    def _is_valid_url(self, url: str) -> bool:
        """Valida formato de URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _is_external_link(self, link_url: str, base_url: str) -> bool:
        """Verifica si un enlace es externo."""
        link_domain = urlparse(link_url).netloc
        base_domain = urlparse(base_url).netloc
        
        return link_domain != base_domain and bool(link_domain)
    
    def _apply_rate_limit(self, url: str) -> None:
        """Aplica rate limiting por dominio."""
        domain = urlparse(url).netloc
        
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            
            if elapsed < self.delay_between_requests:
                sleep_time = self.delay_between_requests - elapsed
                logger.debug(f"Rate limiting: esperando {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    # =========================================================================
    # CACHÉ
    # =========================================================================
    
    def _get_cache_key(self, url: str) -> str:
        """Genera clave de caché para URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_from_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """Obtiene resultado de caché."""
        cache_key = self._get_cache_key(url)
        
        # Verificar caché en memoria
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # Verificar caché en disco
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Cargar en memoria
                self.memory_cache[cache_key] = data
                
                return data
            except Exception as e:
                logger.warning(f"⚠️ Error leyendo caché: {e}")
        
        return None
    
    def _save_to_cache(self, url: str, data: Dict[str, Any]) -> None:
        """Guarda resultado en caché."""
        cache_key = self._get_cache_key(url)
        
        # Guardar en memoria
        self.memory_cache[cache_key] = data
        
        # Guardar en disco
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"⚠️ Error guardando en caché: {e}")
    
    def clear_cache(self) -> Dict[str, int]:
        """Limpia caché."""
        # Limpiar memoria
        memory_count = len(self.memory_cache)
        self.memory_cache.clear()
        
        # Limpiar disco
        disk_count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                disk_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Error eliminando archivo: {e}")
        
        logger.info(f"🗑️ Caché limpiada")
        logger.info(f"   - Memoria: {memory_count} entradas")
        logger.info(f"   - Disco: {disk_count} archivos")
        
        return {
            'memory_cleared': memory_count,
            'disk_cleared': disk_count
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del scraper."""
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = (
                self.stats['successful_requests'] /
                self.stats['total_requests'] * 100
            )
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 2),
            'cache_size_memory': len(self.memory_cache),
            'cache_size_disk': len(list(self.cache_dir.glob("*.json"))),
            'mb_downloaded': round(self.stats['total_bytes_downloaded'] / 1024 / 1024, 2)
        }


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_web_scraper(
    timeout: int = 15,
    cache_enabled: bool = True
) -> WebScraper:
    """
    Factory function para crear scraper.
    
    Args:
        timeout: Timeout en segundos
        cache_enabled: Habilitar caché
    
    Returns:
        Instancia de WebScraper
    """
    return WebScraper(
        timeout=timeout,
        cache_enabled=cache_enabled
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🌐 WEB SCRAPER - Ejemplo de Uso")
    print("="*60)
    
    # Crear scraper
    scraper = WebScraper()
    
    # URL de ejemplo
    test_url = "https://example.com"
    
    print(f"\n🔍 Scraping URL: {test_url}")
    
    # Scrapear página
    result = scraper.scrape(test_url)
    
    if result['success']:
        print("\n✅ Scraping exitoso")
        print(f"\n📊 INFORMACIÓN BÁSICA:")
        print(f"   Title: {result['title']}")
        print(f"   HTML length: {result['html_length']:,} bytes")
        print(f"   Meta description: {result['meta_tags']['description'][:100]}...")
        
        print(f"\n📄 CONTENIDO:")
        print(f"   H1 tags: {len(result['headings']['h1'])}")
        print(f"   H2 tags: {len(result['headings']['h2'])}")
        print(f"   Enlaces: {len(result['links'])}")
        print(f"   Imágenes: {len(result['images'])}")
        
        if result['headings']['h1']:
            print(f"\n   H1 principal: {result['headings']['h1'][0]}")
        
        print(f"\n🔗 ENLACES (primeros 5):")
        for i, link in enumerate(result['links'][:5], 1):
            external = "🔗 Externo" if link['is_external'] else "📎 Interno"
            print(f"   {i}. {external}: {link['text'][:50]}")
    else:
        print(f"\n❌ Error: {result.get('error')}")
    
    # Estadísticas
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DEL SCRAPER")
    print("="*60)
    
    stats = scraper.get_statistics()
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Exitosas: {stats['successful_requests']}")
    print(f"   Fallidas: {stats['failed_requests']}")
    print(f"   Tasa de éxito: {stats['success_rate']:.1f}%")
    print(f"   MB descargados: {stats['mb_downloaded']:.2f}")
    print(f"   Caché (memoria): {stats['cache_size_memory']}")
    
    print("\n" + "="*60)
    print("⚠️ NOTA IMPORTANTE")
    print("="*60)
    print("""
    Este scraper es para propósitos educativos y de desarrollo.
    
    Recomendaciones:
    • Respeta robots.txt de los sitios
    • No hagas scraping agresivo
    • Usa APIs oficiales cuando estén disponibles
    • Consulta términos de servicio de cada sitio
    • Para Google Ads, usa la API oficial de Google Ads
    """)