"""
🔥 BATCH GENERATOR - Generador Masivo de Anuncios
Sistema de generación masiva de anuncios con múltiples variaciones
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchGenerator:
    """
    Generador masivo de anuncios con capacidades de:
    - Generación paralela de múltiples anuncios
    - Variaciones de tonos automáticas
    - Comparación lado a lado de resultados
    - Gestión de cola de generación
    - Caché de resultados
    - Métricas de rendimiento
    """
    
    def __init__(
        self, 
        ai_generator,
        max_workers: int = 3,
        enable_cache: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Inicializa el generador masivo.
        
        Args:
            ai_generator: Instancia de AIAdGenerator
            max_workers: Número máximo de workers paralelos
            enable_cache: Habilitar caché de resultados
            cache_dir: Directorio para caché (None = usar default)
        """
        self.ai_generator = ai_generator
        self.max_workers = max_workers
        self.enable_cache = enable_cache
        
        # Configurar directorio de caché
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / "data" / "batch_cache"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado interno
        self.generation_history: List[Dict[str, Any]] = []
        self.cache: Dict[str, Any] = {}
        
        # Métricas
        self.stats = {
            'total_batches': 0,
            'total_ads_generated': 0,
            'total_errors': 0,
            'avg_generation_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info(f"✅ BatchGenerator inicializado")
        logger.info(f"   - Max workers: {max_workers}")
        logger.info(f"   - Cache habilitado: {enable_cache}")
        logger.info(f"   - Cache dir: {self.cache_dir}")
    
    # =========================================================================
    # GENERACIÓN MASIVA - MÉTODO PRINCIPAL
    # =========================================================================
    
    def generate_batch(
        self,
        keywords: List[str],
        num_variations: int = 5,
        tones: Optional[List[str]] = None,
        num_headlines: int = 15,
        num_descriptions: int = 4,
        user: str = "saltbalente",
        validate: bool = True,
        business_type: str = "auto",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Genera un batch de múltiples anuncios con diferentes configuraciones.
        
        Args:
            keywords: Lista de palabras clave
            num_variations: Número de variaciones a generar
            tones: Lista de tonos a usar (None = usar tonos predeterminados)
            num_headlines: Número de títulos por anuncio
            num_descriptions: Número de descripciones por anuncio
            user: Usuario que genera
            validate: Validar anuncios generados
            business_type: Tipo de negocio
            use_cache: Usar caché si está disponible
        
        Returns:
            Diccionario con resultados del batch
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        
        logger.info(f"🔥 Iniciando generación masiva: {batch_id}")
        logger.info(f"   - Variaciones: {num_variations}")
        logger.info(f"   - Keywords: {len(keywords)}")
        logger.info(f"   - Tonos: {tones or 'automático'}")
        
        # Preparar tonos si no se proporcionan
        if not tones:
            tones = self._get_default_tones()
        
        # Asegurar que tenemos suficientes tonos
        if len(tones) < num_variations:
            tones = tones * (num_variations // len(tones) + 1)
        
        tones = tones[:num_variations]
        
        # Verificar caché
        cache_key = self._generate_cache_key(keywords, tones, num_headlines, num_descriptions)
        
        if use_cache and self.enable_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"✅ Resultado obtenido de caché: {cache_key}")
                self.stats['cache_hits'] += 1
                return cached_result
        
        self.stats['cache_misses'] += 1
        
        # Generar anuncios en paralelo
        try:
            ads = self._generate_parallel(
                keywords=keywords,
                tones=tones,
                num_headlines=num_headlines,
                num_descriptions=num_descriptions,
                user=user,
                validate=validate,
                business_type=business_type
            )
            
            # Calcular tiempo total
            total_time = time.time() - start_time
            
            # Construir resultado
            result = {
                'batch_id': batch_id,
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'config': {
                    'keywords': keywords,
                    'num_variations': num_variations,
                    'tones': tones,
                    'num_headlines': num_headlines,
                    'num_descriptions': num_descriptions,
                    'business_type': business_type,
                    'validate': validate
                },
                'ads': ads,
                'successful_ads': len([ad for ad in ads if not ad.get('error')]),
                'failed_ads': len([ad for ad in ads if ad.get('error')]),
                'total_time': round(total_time, 2),
                'avg_time_per_ad': round(total_time / len(ads), 2) if ads else 0,
                'comparison': self._generate_comparison_data(ads)
            }
            
            # Actualizar estadísticas
            self._update_stats(result)
            
            # Guardar en historial
            self.generation_history.append(result)
            
            # Guardar en caché
            if self.enable_cache:
                self._save_to_cache(cache_key, result)
            
            logger.info(f"✅ Batch completado: {batch_id}")
            logger.info(f"   - Exitosos: {result['successful_ads']}/{len(ads)}")
            logger.info(f"   - Tiempo total: {total_time:.2f}s")
            logger.info(f"   - Tiempo promedio: {result['avg_time_per_ad']:.2f}s por anuncio")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en generación masiva: {e}", exc_info=True)
            
            error_result = {
                'batch_id': batch_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'config': {
                    'keywords': keywords,
                    'num_variations': num_variations,
                    'tones': tones
                }
            }
            
            self.stats['total_errors'] += 1
            
            return error_result
    
    # =========================================================================
    # GENERACIÓN PARALELA
    # =========================================================================
    
    def _generate_parallel(
        self,
        keywords: List[str],
        tones: List[str],
        num_headlines: int,
        num_descriptions: int,
        user: str,
        validate: bool,
        business_type: str
    ) -> List[Dict[str, Any]]:
        """
        Genera múltiples anuncios en paralelo usando ThreadPoolExecutor.
        
        Args:
            keywords: Keywords a usar
            tones: Lista de tonos (uno por anuncio)
            num_headlines: Número de títulos
            num_descriptions: Número de descripciones
            user: Usuario
            validate: Validar anuncios
            business_type: Tipo de negocio
        
        Returns:
            Lista de anuncios generados
        """
        ads = []
        
        # Crear tareas de generación
        tasks = []
        for i, tone in enumerate(tones):
            task = {
                'variation_id': i + 1,
                'keywords': keywords,
                'tone': tone,
                'num_headlines': num_headlines,
                'num_descriptions': num_descriptions,
                'user': user,
                'validate': validate,
                'business_type': business_type
            }
            tasks.append(task)
        
        logger.info(f"🚀 Ejecutando {len(tasks)} generaciones en paralelo")
        
        # Ejecutar en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_task = {
                executor.submit(self._generate_single_ad, task): task 
                for task in tasks
            }
            
            # Recolectar resultados conforme se completan
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    ad_result = future.result()
                    ads.append(ad_result)
                    
                    if ad_result.get('error'):
                        logger.warning(f"⚠️ Variación {task['variation_id']} falló: {ad_result['error']}")
                    else:
                        logger.info(f"✅ Variación {task['variation_id']} completada")
                        
                except Exception as e:
                    logger.error(f"❌ Error en variación {task['variation_id']}: {e}")
                    ads.append({
                        'variation_id': task['variation_id'],
                        'tone': task['tone'],
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Ordenar por variation_id
        ads.sort(key=lambda x: x.get('variation_id', 0))
        
        return ads
    
    def _generate_single_ad(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un solo anuncio (función auxiliar para paralelización).
        
        Args:
            task: Diccionario con parámetros de generación
        
        Returns:
            Diccionario con anuncio generado
        """
        variation_id = task['variation_id']
        start_time = time.time()
        
        try:
            logger.debug(f"🔄 Generando variación {variation_id} con tono '{task['tone']}'")
            
            # Llamar al generador de IA
            generated = self.ai_generator.generate_ad(
                keywords=task['keywords'],
                num_ads=1,
                num_headlines=task['num_headlines'],
                num_descriptions=task['num_descriptions'],
                tone=task['tone'],
                user=task['user'],
                validate=task['validate'],
                business_type=task['business_type']
            )
            
            if not generated or len(generated) == 0:
                raise ValueError("El generador no retornó anuncios")
            
            ad = generated[0]
            
            # Agregar metadata de variación
            ad['variation_id'] = variation_id
            ad['generation_time'] = round(time.time() - start_time, 2)
            
            return ad
            
        except Exception as e:
            logger.error(f"❌ Error generando variación {variation_id}: {e}")
            
            return {
                'variation_id': variation_id,
                'tone': task['tone'],
                'error': str(e),
                'generation_time': round(time.time() - start_time, 2),
                'timestamp': datetime.now().isoformat()
            }
    
    # =========================================================================
    # GENERACIÓN CON VARIACIONES AUTOMÁTICAS
    # =========================================================================
    
    def generate_with_auto_variations(
        self,
        keywords: List[str],
        num_variations: int = 5,
        num_headlines: int = 15,
        num_descriptions: int = 4,
        user: str = "saltbalente",
        business_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Genera anuncios con variaciones automáticas de tono.
        
        Esta función crea variaciones automáticas probando diferentes tonos
        para el mismo conjunto de keywords.
        
        Args:
            keywords: Lista de palabras clave
            num_variations: Número de variaciones (máx 7)
            num_headlines: Títulos por anuncio
            num_descriptions: Descripciones por anuncio
            user: Usuario
            business_type: Tipo de negocio
        
        Returns:
            Resultado del batch con variaciones automáticas
        """
        # Tonos automáticos en orden de efectividad
        auto_tones = [
            "emocional",
            "urgente",
            "profesional",
            "místico",
            "esperanzador",
            "poderoso",
            "tranquilizador"
        ]
        
        # Limitar variaciones
        num_variations = min(num_variations, len(auto_tones))
        selected_tones = auto_tones[:num_variations]
        
        logger.info(f"🎨 Generando con variaciones automáticas de tono")
        logger.info(f"   - Tonos: {', '.join(selected_tones)}")
        
        return self.generate_batch(
            keywords=keywords,
            num_variations=num_variations,
            tones=selected_tones,
            num_headlines=num_headlines,
            num_descriptions=num_descriptions,
            user=user,
            validate=True,
            business_type=business_type
        )
    
    # =========================================================================
    # COMPARACIÓN Y ANÁLISIS
    # =========================================================================
    
    def _generate_comparison_data(self, ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera datos de comparación entre los anuncios generados.
        
        Args:
            ads: Lista de anuncios a comparar
        
        Returns:
            Diccionario con datos de comparación
        """
        if not ads:
            return {}
        
        # Filtrar anuncios exitosos
        valid_ads = [ad for ad in ads if not ad.get('error')]
        
        if not valid_ads:
            return {'error': 'No hay anuncios válidos para comparar'}
        
        comparison = {
            'total_ads': len(ads),
            'valid_ads': len(valid_ads),
            'by_tone': {},
            'headline_stats': {},
            'description_stats': {},
            'validation_stats': {}
        }
        
        # Agrupar por tono
        for ad in valid_ads:
            tone = ad.get('tone', 'unknown')
            
            if tone not in comparison['by_tone']:
                comparison['by_tone'][tone] = {
                    'count': 0,
                    'avg_headlines': 0,
                    'avg_descriptions': 0,
                    'avg_generation_time': 0
                }
            
            comparison['by_tone'][tone]['count'] += 1
            comparison['by_tone'][tone]['avg_headlines'] += len(ad.get('headlines', []))
            comparison['by_tone'][tone]['avg_descriptions'] += len(ad.get('descriptions', []))
            comparison['by_tone'][tone]['avg_generation_time'] += ad.get('generation_time', 0)
        
        # Calcular promedios por tono
        for tone, data in comparison['by_tone'].items():
            count = data['count']
            if count > 0:
                data['avg_headlines'] = round(data['avg_headlines'] / count, 1)
                data['avg_descriptions'] = round(data['avg_descriptions'] / count, 1)
                data['avg_generation_time'] = round(data['avg_generation_time'] / count, 2)
        
        # Estadísticas de validación
        validated_ads = [ad for ad in valid_ads if ad.get('validation_result')]
        
        if validated_ads:
            total_valid_headlines = sum(
                ad['validation_result']['summary']['valid_headlines'] 
                for ad in validated_ads
            )
            total_valid_descriptions = sum(
                ad['validation_result']['summary']['valid_descriptions'] 
                for ad in validated_ads
            )
            
            comparison['validation_stats'] = {
                'ads_with_validation': len(validated_ads),
                'avg_valid_headlines': round(total_valid_headlines / len(validated_ads), 1),
                'avg_valid_descriptions': round(total_valid_descriptions / len(validated_ads), 1)
            }
        
        return comparison
    
    def compare_ads(
        self,
        ad_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compara múltiples anuncios del historial.
        
        Args:
            ad_ids: IDs de los anuncios a comparar
            metrics: Métricas específicas a comparar (None = todas)
        
        Returns:
            Diccionario con comparación detallada
        """
        # Buscar anuncios en historial
        ads_to_compare = []
        
        for batch in self.generation_history:
            for ad in batch.get('ads', []):
                ad_id = ad.get('id')
                if ad_id in ad_ids:
                    ads_to_compare.append(ad)
        
        if len(ads_to_compare) < 2:
            return {
                'error': f'Se necesitan al menos 2 anuncios para comparar. Encontrados: {len(ads_to_compare)}'
            }
        
        # Métricas por defecto
        if not metrics:
            metrics = ['headlines', 'descriptions', 'tone', 'validation']
        
        comparison = {
            'compared_ads': len(ads_to_compare),
            'metrics': {}
        }
        
        # Comparar cada métrica
        for metric in metrics:
            if metric == 'headlines':
                comparison['metrics']['headlines'] = self._compare_headlines(ads_to_compare)
            elif metric == 'descriptions':
                comparison['metrics']['descriptions'] = self._compare_descriptions(ads_to_compare)
            elif metric == 'tone':
                comparison['metrics']['tone'] = self._compare_tones(ads_to_compare)
            elif metric == 'validation':
                comparison['metrics']['validation'] = self._compare_validation(ads_to_compare)
        
        return comparison
    
    def _compare_headlines(self, ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compara titulares entre anuncios."""
        headline_data = {
            'total_unique_headlines': 0,
            'avg_headlines_per_ad': 0,
            'length_distribution': {},
            'common_words': []
        }
        
        all_headlines = []
        for ad in ads:
            headlines = ad.get('headlines', [])
            all_headlines.extend(headlines)
        
        unique_headlines = set(all_headlines)
        headline_data['total_unique_headlines'] = len(unique_headlines)
        headline_data['avg_headlines_per_ad'] = round(len(all_headlines) / len(ads), 1)
        
        # Distribución de longitud
        for headline in all_headlines:
            length_range = f"{(len(headline) // 5) * 5}-{(len(headline) // 5) * 5 + 4}"
            headline_data['length_distribution'][length_range] = \
                headline_data['length_distribution'].get(length_range, 0) + 1
        
        return headline_data
    
    def _compare_descriptions(self, ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compara descripciones entre anuncios."""
        description_data = {
            'total_unique_descriptions': 0,
            'avg_descriptions_per_ad': 0,
            'length_distribution': {}
        }
        
        all_descriptions = []
        for ad in ads:
            descriptions = ad.get('descriptions', [])
            all_descriptions.extend(descriptions)
        
        unique_descriptions = set(all_descriptions)
        description_data['total_unique_descriptions'] = len(unique_descriptions)
        description_data['avg_descriptions_per_ad'] = round(len(all_descriptions) / len(ads), 1)
        
        # Distribución de longitud
        for desc in all_descriptions:
            length_range = f"{(len(desc) // 10) * 10}-{(len(desc) // 10) * 10 + 9}"
            description_data['length_distribution'][length_range] = \
                description_data['length_distribution'].get(length_range, 0) + 1
        
        return description_data
    
    def _compare_tones(self, ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compara tonos entre anuncios."""
        tone_distribution = {}
        
        for ad in ads:
            tone = ad.get('tone', 'unknown')
            tone_distribution[tone] = tone_distribution.get(tone, 0) + 1
        
        return {
            'tone_distribution': tone_distribution,
            'most_common_tone': max(tone_distribution, key=tone_distribution.get) if tone_distribution else None
        }
    
    def _compare_validation(self, ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compara resultados de validación entre anuncios."""
        validation_data = {
            'ads_validated': 0,
            'avg_valid_headlines': 0,
            'avg_valid_descriptions': 0,
            'best_performing_ad': None
        }
        
        validated_ads = [ad for ad in ads if ad.get('validation_result')]
        validation_data['ads_validated'] = len(validated_ads)
        
        if validated_ads:
            total_valid_h = sum(
                ad['validation_result']['summary']['valid_headlines'] 
                for ad in validated_ads
            )
            total_valid_d = sum(
                ad['validation_result']['summary']['valid_descriptions'] 
                for ad in validated_ads
            )
            
            validation_data['avg_valid_headlines'] = round(total_valid_h / len(validated_ads), 1)
            validation_data['avg_valid_descriptions'] = round(total_valid_d / len(validated_ads), 1)
            
            # Mejor anuncio
            best_ad = max(
                validated_ads,
                key=lambda x: (
                    x['validation_result']['summary']['valid_headlines'] +
                    x['validation_result']['summary']['valid_descriptions']
                )
            )
            
            validation_data['best_performing_ad'] = {
                'id': best_ad.get('id'),
                'tone': best_ad.get('tone'),
                'valid_headlines': best_ad['validation_result']['summary']['valid_headlines'],
                'valid_descriptions': best_ad['validation_result']['summary']['valid_descriptions']
            }
        
        return validation_data
    
    # =========================================================================
    # CACHE
    # =========================================================================
    
    def _generate_cache_key(
        self, 
        keywords: List[str], 
        tones: List[str],
        num_headlines: int,
        num_descriptions: int
    ) -> str:
        """Genera una clave única para caché basada en parámetros."""
        import hashlib
        
        key_string = json.dumps({
            'keywords': sorted(keywords),
            'tones': sorted(tones),
            'num_headlines': num_headlines,
            'num_descriptions': num_descriptions
        }, sort_keys=True)
        
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obtiene resultado de caché."""
        # Buscar en memoria
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Buscar en disco
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                # Cargar en memoria
                self.cache[cache_key] = result
                
                return result
            except Exception as e:
                logger.warning(f"⚠️ Error leyendo caché: {e}")
                return None
        
        return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Guarda resultado en caché."""
        # Guardar en memoria
        self.cache[cache_key] = result
        
        # Guardar en disco
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Resultado guardado en caché: {cache_key}")
        except Exception as e:
            logger.warning(f"⚠️ Error guardando en caché: {e}")
    
    def clear_cache(self) -> Dict[str, int]:
        """
        Limpia toda la caché (memoria y disco).
        
        Returns:
            Diccionario con estadísticas de limpieza
        """
        # Limpiar memoria
        memory_cleared = len(self.cache)
        self.cache.clear()
        
        # Limpiar disco
        disk_cleared = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                disk_cleared += 1
            except Exception as e:
                logger.warning(f"⚠️ Error eliminando archivo de caché: {e}")
        
        logger.info(f"🗑️ Caché limpiada")
        logger.info(f"   - Memoria: {memory_cleared} entradas")
        logger.info(f"   - Disco: {disk_cleared} archivos")
        
        return {
            'memory_cleared': memory_cleared,
            'disk_cleared': disk_cleared
        }
    
    # =========================================================================
    # ESTADÍSTICAS Y UTILIDADES
    # =========================================================================
    
    def _update_stats(self, result: Dict[str, Any]) -> None:
        """Actualiza estadísticas internas."""
        self.stats['total_batches'] += 1
        self.stats['total_ads_generated'] += result.get('successful_ads', 0)
        
        # Actualizar tiempo promedio
        total_time = result.get('total_time', 0)
        current_avg = self.stats['avg_generation_time']
        total_batches = self.stats['total_batches']
        
        self.stats['avg_generation_time'] = round(
            (current_avg * (total_batches - 1) + total_time) / total_batches,
            2
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del generador masivo.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'history_size': len(self.generation_history),
            'cache_hit_rate': round(
                self.stats['cache_hits'] / 
                (self.stats['cache_hits'] + self.stats['cache_misses']) * 100, 2
            ) if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0
        }
    
    def get_history(
        self, 
        limit: Optional[int] = None,
        successful_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historial de generaciones.
        
        Args:
            limit: Número máximo de entradas a retornar
            successful_only: Solo retornar generaciones exitosas
        
        Returns:
            Lista de generaciones históricas
        """
        history = self.generation_history
        
        if successful_only:
            history = [h for h in history if h.get('success', False)]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def _get_default_tones(self) -> List[str]:
        """Obtiene lista de tonos por defecto."""
        return [
            "emocional",
            "urgente",
            "profesional",
            "místico",
            "esperanzador",
            "poderoso",
            "tranquilizador"
        ]
    
    def export_batch_results(
        self, 
        batch_id: str,
        format: str = 'json'
    ) -> Optional[str]:
        """
        Exporta resultados de un batch a archivo.
        
        Args:
            batch_id: ID del batch a exportar
            format: Formato de exportación ('json' o 'csv')
        
        Returns:
            Path del archivo exportado o None si falló
        """
        # Buscar batch en historial
        batch = None
        for b in self.generation_history:
            if b.get('batch_id') == batch_id:
                batch = b
                break
        
        if not batch:
            logger.error(f"❌ Batch '{batch_id}' no encontrado")
            return None
        
        export_dir = Path(__file__).parent.parent / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            export_file = export_dir / f"{batch_id}_{timestamp}.json"
            
            try:
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(batch, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ Batch exportado: {export_file}")
                return str(export_file)
                
            except Exception as e:
                logger.error(f"❌ Error exportando a JSON: {e}")
                return None
        
        elif format == 'csv':
            import csv
            
            export_file = export_dir / f"{batch_id}_{timestamp}.csv"
            
            try:
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Header
                    writer.writerow([
                        'Variation ID', 'Tone', 'Num Headlines', 
                        'Num Descriptions', 'Generation Time', 'Has Error'
                    ])
                    
                    # Rows
                    for ad in batch.get('ads', []):
                        writer.writerow([
                            ad.get('variation_id', ''),
                            ad.get('tone', ''),
                            len(ad.get('headlines', [])),
                            len(ad.get('descriptions', [])),
                            ad.get('generation_time', ''),
                            'Yes' if ad.get('error') else 'No'
                        ])
                
                logger.info(f"✅ Batch exportado: {export_file}")
                return str(export_file)
                
            except Exception as e:
                logger.error(f"❌ Error exportando a CSV: {e}")
                return None
        
        else:
            logger.error(f"❌ Formato de exportación no soportado: {format}")
            return None


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_batch_generator(
    ai_generator,
    max_workers: int = 3,
    enable_cache: bool = True
) -> BatchGenerator:
    """
    Factory function para crear una instancia de BatchGenerator.
    
    Args:
        ai_generator: Instancia de AIAdGenerator
        max_workers: Número máximo de workers paralelos
        enable_cache: Habilitar caché
    
    Returns:
        Instancia de BatchGenerator
    """
    return BatchGenerator(
        ai_generator=ai_generator,
        max_workers=max_workers,
        enable_cache=enable_cache
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🔥 BATCH GENERATOR - Ejemplo de Uso")
    print("="*60)
    print("\nEste módulo requiere una instancia de AIAdGenerator.")
    print("Ejemplo de uso:")
    print("""
    from modules.ai_ad_generator import AIAdGenerator
    from modules.batch_generator import BatchGenerator
    
    # Crear generador de IA
    ai_gen = AIAdGenerator()
    ai_gen.set_provider('openai', api_key='tu-api-key', model='gpt-4')
    
    # Crear generador masivo
    batch_gen = BatchGenerator(ai_gen, max_workers=3)
    
    # Generar batch
    result = batch_gen.generate_batch(
        keywords=['amarres de amor', 'hechizos efectivos'],
        num_variations=5,
        tones=['emocional', 'urgente', 'místico', 'profesional', 'poderoso']
    )
    
    print(f"Generados: {result['successful_ads']} anuncios")
    print(f"Tiempo total: {result['total_time']}s")
    
    # Ver estadísticas
    stats = batch_gen.get_statistics()
    print(f"Total generados: {stats['total_ads_generated']}")
    """)