"""
AI Ad Generator Module
Motor principal que coordina generación, validación y almacenamiento de anuncios
"""

import os
import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib

from modules.ai_providers import AIProvider, OpenAIProvider, GeminiProvider
from utils.ad_validator import GoogleAdsValidator

logger = logging.getLogger(__name__)

class AIAdGenerator:
    """Motor principal de generación de anuncios con IA"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Inicializa el generador de anuncios
        
        Args:
            storage_path: Ruta personalizada para el CSV. Si es None, usa ~/dashboard-google-ads-data/
        """
        self.provider: Optional[AIProvider] = None
        self.validator = GoogleAdsValidator()
        self.storage_path = self._setup_storage_path(storage_path)
        self._initialize_csv()
        
        logger.info(f"✅ AIAdGenerator inicializado. Storage: {self.storage_path}")
    
    def _setup_storage_path(self, custom_path: Optional[str]) -> str:
        """Configura la ruta de almacenamiento"""
        if custom_path:
            return custom_path
        
        # Usar directorio home del usuario
        home_dir = Path.home()
        data_dir = home_dir / "dashboard-google-ads-data"
        
        # Crear directorio si no existe
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directorio de datos: {data_dir}")
        except Exception as e:
            logger.error(f"❌ Error creando directorio: {e}")
            # Fallback a directorio actual
            data_dir = Path.cwd() / "data"
            data_dir.mkdir(exist_ok=True)
        
        return str(data_dir / "generated_ads.csv")
    
    def _initialize_csv(self):
        """Inicializa el archivo CSV si no existe"""
        if not os.path.exists(self.storage_path):
            headers = [
                'id',
                'timestamp',
                'user',
                'provider',
                'model',
                'keywords',
                'tone',
                'num_ads',
                'num_headlines',
                'num_descriptions',
                'headlines',
                'descriptions',
                'validation_status',
                'valid_headlines',
                'invalid_headlines',
                'valid_descriptions',
                'invalid_descriptions',
                'validation_errors',
                'published',
                'campaign_id',
                'ad_group_id',
                'published_at'
            ]
            
            try:
                with open(self.storage_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
                logger.info(f"✅ CSV inicializado: {self.storage_path}")
            except Exception as e:
                logger.error(f"❌ Error inicializando CSV: {e}")
    
    def set_provider(self, provider_type: str, api_key: str, model: str = None) -> bool:
        """
        Configura el proveedor de IA
        
        Args:
            provider_type: 'openai' o 'gemini'
            api_key: Clave API del proveedor
            model: Modelo específico a usar
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            provider_type = provider_type.lower().strip()
            
            if provider_type == 'openai':
                self.provider = OpenAIProvider(api_key, model or "gpt-4")
                logger.info(f"🤖 Proveedor configurado: OpenAI ({model or 'gpt-4'})")
            elif provider_type == 'gemini':
                self.provider = GeminiProvider(api_key, model or "gemini-pro")
                logger.info(f"🤖 Proveedor configurado: Gemini ({model or 'gemini-pro'})")
            else:
                raise ValueError(f"Proveedor no soportado: {provider_type}")
            
            # Verificar conexión
            if not self.provider.test_connection():
                raise ConnectionError("No se pudo conectar con el proveedor")
            
            logger.info("✅ Conexión con proveedor exitosa")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando proveedor {provider_type}: {e}")
            self.provider = None
            return False
    
    def generate_ad(self, keywords: List[str], num_ads: int = 1, 
                   num_headlines: int = 15, num_descriptions: int = 4,
                   tone: str = "profesional", user: str = "saltbalente",
                   validate: bool = True, business_type: str = "auto") -> List[Dict[str, Any]]:
        """
        Genera anuncios usando el proveedor configurado
        
        Args:
            keywords: Lista de palabras clave
            num_ads: Número de anuncios a generar
            num_headlines: Títulos por anuncio
            num_descriptions: Descripciones por anuncio
            tone: Tono del anuncio
            user: Usuario que genera el anuncio
            validate: Si validar contra políticas de Google Ads
            business_type: Tipo de negocio ('auto', 'esoteric', 'generic')
        
        Returns:
            Lista de anuncios generados con validación
        """
        
        logger.info("="*60)
        logger.info("🚀 INICIANDO GENERACIÓN DE ANUNCIOS")
        logger.info(f"📋 Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
        logger.info(f"🔢 Cantidad: {num_ads} anuncios")
        logger.info(f"📝 Títulos: {num_headlines}, Descripciones: {num_descriptions}")
        logger.info(f"🎭 Tono: {tone}")
        logger.info(f"🏢 Tipo de negocio: {business_type}")
        logger.info(f"👤 Usuario: {user}")
        logger.info("="*60)
        
        # Validar que hay proveedor
        if not self.provider:
            logger.error("❌ No hay proveedor de IA configurado")
            return [{
                'error': 'No hay proveedor configurado',
                'headlines': [],
                'descriptions': []
            }]
        
        logger.info(f"🤖 Proveedor activo: {self.provider.__class__.__name__}")
        logger.info(f"🔧 Modelo: {getattr(self.provider, 'model', 'unknown')}")
        
        generated_ads = []
        
        for i in range(num_ads):
            logger.info(f"\n{'='*40}")
            logger.info(f"📦 Generando anuncio {i+1}/{num_ads}")
            logger.info(f"{'='*40}")
            
            try:
                logger.info("📤 Llamando al proveedor de IA...")
                
                # ✅ LLAMADA AL PROVEEDOR
                ad_data = self.provider.generate_ad(
                    keywords=keywords,
                    num_headlines=num_headlines,
                    num_descriptions=num_descriptions,
                    tone=tone,
                    business_type=business_type
                )
                
                logger.info("📥 Respuesta recibida del proveedor")
                
                # ✅ VALIDAR QUE ad_data ES UN DICT
                if not isinstance(ad_data, dict):
                    logger.error(f"❌ Respuesta no es dict: {type(ad_data)}")
                    continue
                
                logger.info(f"🔍 Keys en respuesta: {list(ad_data.keys())}")
                
                # ✅ VERIFICAR SI HAY ERROR
                if 'error' in ad_data and ad_data['error']:
                    logger.error(f"❌ Error del proveedor: {ad_data['error']}")
                    generated_ads.append(ad_data)  # ✅ AGREGAR INCLUSO SI HAY ERROR para que se muestre
                    continue
                
                # ✅ VERIFICAR QUE HAY HEADLINES
                if 'headlines' not in ad_data or not ad_data['headlines']:
                    logger.error(f"❌ No hay headlines en respuesta")
                    logger.error(f"Respuesta completa: {ad_data}")
                    generated_ads.append({
                        'error': 'No se generaron títulos',
                        'headlines': [],
                        'descriptions': [],
                        'raw_response': ad_data
                    })
                    continue
                
                # ✅ VERIFICAR QUE HAY DESCRIPTIONS
                if 'descriptions' not in ad_data or not ad_data['descriptions']:
                    logger.error(f"❌ No hay descriptions en respuesta")
                    logger.error(f"Respuesta completa: {ad_data}")
                    generated_ads.append({
                        'error': 'No se generaron descripciones',
                        'headlines': ad_data.get('headlines', []),
                        'descriptions': [],
                        'raw_response': ad_data
                    })
                    continue
                
                logger.info(f"✅ Contenido recibido:")
                logger.info(f"   - {len(ad_data['headlines'])} títulos")
                logger.info(f"   - {len(ad_data['descriptions'])} descripciones")
                
                # ✅ FILTRAR POR LONGITUD (SEGURIDAD ADICIONAL)
                original_headlines_count = len(ad_data['headlines'])
                ad_data['headlines'] = [
                    h for h in ad_data['headlines'] 
                    if isinstance(h, str) and 15 <= len(h.strip()) <= 30
                ]
                
                if len(ad_data['headlines']) < original_headlines_count:
                    logger.warning(f"⚠️ Filtrados {original_headlines_count - len(ad_data['headlines'])} títulos por longitud")
                
                original_descriptions_count = len(ad_data['descriptions'])
                ad_data['descriptions'] = [
                    d for d in ad_data['descriptions'] 
                    if isinstance(d, str) and 40 <= len(d.strip()) <= 90
                ]
                
                if len(ad_data['descriptions']) < original_descriptions_count:
                    logger.warning(f"⚠️ Filtradas {original_descriptions_count - len(ad_data['descriptions'])} descripciones por longitud")
                
                # ✅ VERIFICAR MÍNIMOS
                if len(ad_data['headlines']) < 3:
                    logger.error(f"❌ Insuficientes títulos válidos: {len(ad_data['headlines'])}/3 mínimo")
                    generated_ads.append({
                        'error': f'Solo se generaron {len(ad_data["headlines"])} títulos válidos (mínimo 3)',
                        'headlines': ad_data['headlines'],
                        'descriptions': ad_data['descriptions']
                    })
                    continue
                
                if len(ad_data['descriptions']) < 2:
                    logger.error(f"❌ Insuficientes descripciones válidas: {len(ad_data['descriptions'])}/2 mínimo")
                    generated_ads.append({
                        'error': f'Solo se generaron {len(ad_data["descriptions"])} descripciones válidas (mínimo 2)',
                        'headlines': ad_data['headlines'],
                        'descriptions': ad_data['descriptions']
                    })
                    continue
                
                logger.info(f"✅ Validación de cantidades pasada")
                
                # ✅ VALIDAR CON GOOGLE ADS VALIDATOR
                if validate:
                    logger.info("🔍 Ejecutando validación de políticas...")
                    try:
                        validation_result = self.validator.validate_ad(
                            headlines=ad_data['headlines'],
                            descriptions=ad_data['descriptions']
                        )
                        ad_data['validation_result'] = validation_result
                        
                        if validation_result.get('valid'):
                            logger.info(f"✅ Validación exitosa")
                        else:
                            logger.warning(f"⚠️ Validación con advertencias")
                            if 'errors' in validation_result:
                                for error in validation_result['errors'][:3]:
                                    logger.warning(f"   - {error}")
                    
                    except Exception as val_error:
                        logger.error(f"❌ Error en validación: {val_error}")
                        ad_data['validation_result'] = {
                            'valid': False,
                            'error': str(val_error)
                        }
                
                # ✅ AGREGAR METADATA
                ad_data['id'] = f"AD_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                ad_data['timestamp'] = datetime.now().isoformat()
                ad_data['keywords'] = keywords
                ad_data['tone'] = tone
                ad_data['user'] = user
                ad_data['business_type'] = business_type
                
                # ✅ AGREGAR A LA LISTA
                generated_ads.append(ad_data)
                
                logger.info(f"✅ Anuncio {i+1} generado exitosamente")
                logger.info(f"   - ID: {ad_data['id']}")
                logger.info(f"   - Títulos finales: {len(ad_data['headlines'])}")
                logger.info(f"   - Descripciones finales: {len(ad_data['descriptions'])}")
                
                # Mostrar longitudes máximas
                max_headline = max(len(h) for h in ad_data['headlines']) if ad_data['headlines'] else 0
                max_description = max(len(d) for d in ad_data['descriptions']) if ad_data['descriptions'] else 0
                logger.info(f"   - Máx longitud título: {max_headline}/30")
                logger.info(f"   - Máx longitud descripción: {max_description}/90")
            
            except Exception as e:
                logger.error(f"❌ EXCEPCIÓN GENERANDO ANUNCIO {i+1}")
                logger.error(f"   Tipo: {type(e).__name__}")
                logger.error(f"   Mensaje: {str(e)}")
                logger.exception("Traceback completo:")
                
                # ✅ AGREGAR ERROR A LA LISTA
                generated_ads.append({
                    'error': f'Excepción: {str(e)}',
                    'error_type': type(e).__name__,
                    'headlines': [],
                    'descriptions': []
                })
        
        # ✅ LOG FINAL
        logger.info("="*60)
        logger.info(f"🏁 GENERACIÓN COMPLETADA")
        logger.info(f"✅ Anuncios en lista: {len(generated_ads)}")
        
        if generated_ads:
            successful = len([ad for ad in generated_ads if 'error' not in ad or not ad['error']])
            failed = len(generated_ads) - successful
            logger.info(f"   - Exitosos: {successful}")
            logger.info(f"   - Fallidos: {failed}")
        else:
            logger.error("❌ Lista de anuncios vacía")
        
        logger.info("="*60)
        
        return generated_ads
    
    def _generate_ad_id(self) -> str:
        """Genera un ID único para el anuncio"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        return f"AD_{timestamp}"
    
    def _save_to_csv(self, ad_data: Dict[str, Any]):
        """Guarda el anuncio generado en CSV"""
        try:
            validation = ad_data.get('validation_result', {})
            validation_summary = validation.get('summary', {})
            
            # Recopilar errores de validación
            validation_errors = []
            if validation:
                for idx, h_data in validation.get('headlines', {}).items():
                    if not h_data.get('valid', True):
                        validation_errors.extend([f"H{idx}: {err}" for err in h_data.get('errors', [])])
                
                for idx, d_data in validation.get('descriptions', {}).items():
                    if not d_data.get('valid', True):
                        validation_errors.extend([f"D{idx}: {err}" for err in d_data.get('errors', [])])
            
            row = [
                ad_data['id'],
                ad_data['timestamp'],
                ad_data['user'],
                ad_data['provider'],
                ad_data['model'],
                json.dumps(ad_data['keywords'], ensure_ascii=False),
                ad_data['tone'],
                1,  # num_ads (siempre 1 por fila)
                ad_data['num_headlines'],
                ad_data['num_descriptions'],
                json.dumps(ad_data['headlines'], ensure_ascii=False),
                json.dumps(ad_data['descriptions'], ensure_ascii=False),
                'valid' if validation.get('valid', False) else 'invalid',
                validation_summary.get('valid_headlines', 0),
                validation_summary.get('invalid_headlines', 0),
                validation_summary.get('valid_descriptions', 0),
                validation_summary.get('invalid_descriptions', 0),
                json.dumps(validation_errors, ensure_ascii=False),
                ad_data['published'],
                ad_data['campaign_id'] or '',
                ad_data['ad_group_id'] or '',
                ''  # published_at (se llenará al publicar)
            ]
            
            with open(self.storage_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(row)
            
            logger.debug(f"💾 Anuncio guardado en CSV: {ad_data['id']}")
                
        except Exception as e:
            logger.error(f"❌ Error guardando en CSV: {e}", exc_info=True)
    
    def load_history(self, limit: int = 100, published_only: bool = False) -> List[Dict[str, Any]]:
        """
        Carga el historial de anuncios generados
        
        Args:
            limit: Número máximo de anuncios a cargar
            published_only: Si solo cargar anuncios publicados
            
        Returns:
            Lista de anuncios (más recientes primero)
        """
        history = []
        
        try:
            if not os.path.exists(self.storage_path):
                logger.warning("📂 Archivo de historial no existe")
                return history
            
            with open(self.storage_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Filtrar por publicación si se solicita
                    if published_only:
                        if row.get('published', 'False').lower() != 'true':
                            continue
                    
                    # Parsear JSON fields
                    try:
                        row['keywords'] = json.loads(row.get('keywords', '[]'))
                        row['headlines'] = json.loads(row.get('headlines', '[]'))
                        row['descriptions'] = json.loads(row.get('descriptions', '[]'))
                        row['validation_errors'] = json.loads(row.get('validation_errors', '[]'))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parseando JSON en fila: {e}")
                    
                    history.append(row)
            
            # Ordenar por timestamp (más recientes primero)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Limitar resultados
            history = history[:limit]
            
            logger.info(f"📚 Historial cargado: {len(history)} anuncios")
                        
        except Exception as e:
            logger.error(f"❌ Error cargando historial: {e}", exc_info=True)
        
        return history
    
    def get_ad_by_id(self, ad_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un anuncio específico por su ID
        
        Args:
            ad_id: ID del anuncio
            
        Returns:
            Dict con datos del anuncio o None
        """
        try:
            history = self.load_history(limit=1000)  # Cargar más para buscar
            
            for ad in history:
                if ad.get('id') == ad_id:
                    return ad
            
            logger.warning(f"⚠️ Anuncio no encontrado: {ad_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo anuncio {ad_id}: {e}")
            return None
    
    def mark_as_published(self, ad_id: str, campaign_id: str, ad_group_id: str) -> bool:
        """
        Marca un anuncio como publicado
        
        Args:
            ad_id: ID del anuncio
            campaign_id: ID de la campaña donde se publicó
            ad_group_id: ID del grupo de anuncios
            
        Returns:
            bool: True si se marcó exitosamente
        """
        try:
            # Leer todo el CSV
            rows = []
            updated = False
            
            with open(self.storage_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames
                
                for row in reader:
                    if row.get('id') == ad_id:
                        row['published'] = 'True'
                        row['campaign_id'] = campaign_id
                        row['ad_group_id'] = ad_group_id
                        row['published_at'] = datetime.utcnow().isoformat()
                        updated = True
                        logger.info(f"✅ Anuncio {ad_id} marcado como publicado")
                    
                    rows.append(row)
            
            if not updated:
                logger.warning(f"⚠️ Anuncio {ad_id} no encontrado para marcar como publicado")
                return False
            
            # Escribir de vuelta
            with open(self.storage_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            return True
                
        except Exception as e:
            logger.error(f"❌ Error marcando anuncio como publicado: {e}", exc_info=True)
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los anuncios generados
        
        Returns:
            Dict con estadísticas
        """
        try:
            history = self.load_history(limit=10000)  # Cargar todo
            
            if not history:
                return {
                    'total_ads': 0,
                    'published_ads': 0,
                    'unpublished_ads': 0,
                    'valid_ads': 0,
                    'invalid_ads': 0,
                    'providers': {},
                    'tones': {}
                }
            
            stats = {
                'total_ads': len(history),
                'published_ads': len([ad for ad in history if ad.get('published', 'False').lower() == 'true']),
                'unpublished_ads': len([ad for ad in history if ad.get('published', 'False').lower() == 'false']),
                'valid_ads': len([ad for ad in history if ad.get('validation_status') == 'valid']),
                'invalid_ads': len([ad for ad in history if ad.get('validation_status') == 'invalid']),
                'providers': {},
                'tones': {}
            }
            
            # Contar por proveedor
            for ad in history:
                provider = ad.get('provider', 'unknown')
                stats['providers'][provider] = stats['providers'].get(provider, 0) + 1
            
            # Contar por tono
            for ad in history:
                tone = ad.get('tone', 'unknown')
                stats['tones'][tone] = stats['tones'].get(tone, 0) + 1
            
            logger.info(f"📊 Estadísticas calculadas: {stats['total_ads']} anuncios totales")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error calculando estadísticas: {e}")
            return {}