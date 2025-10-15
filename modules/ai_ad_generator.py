"""
AI Ad Generator Module - VERSIÓN MEJORADA v2.0
Motor principal que coordina generación, validación y almacenamiento de anuncios
Incluye: Generación masiva, regeneración individual, guardado de APIs, exportación
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
    """Motor principal de generación de anuncios con IA - MEJORADO"""
    def generate_for_multiple_ad_groups(
        self,
        campaign_config: 'CampaignAdGroupsConfig',  # Usar el nuevo modelo
        user: str = "saltbalente"
    ) -> Dict[str, Any]:
        """
        ✨ NUEVO: Genera anuncios para múltiples grupos con keywords únicas
        
        Args:
            campaign_config: Configuración completa de la campaña
            user: Usuario que genera
            
        Returns:
            Dict con resultados por cada grupo de anuncios
        """
        from modules.ad_group_config import CampaignAdGroupsConfig
        
        logger.info("="*70)
        logger.info("🚀 GENERACIÓN MULTI-GRUPO INICIADA")
        logger.info(f"📦 Total de grupos: {campaign_config.num_ad_groups}")
        logger.info(f"🤖 Proveedor: {campaign_config.provider}")
        logger.info(f"🎨 Temperatura: {campaign_config.temperature}")
        logger.info("="*70)
        
        if not campaign_config.is_complete():
            error_msg = f"Configuración incompleta: {len(campaign_config.ad_groups)}/{campaign_config.num_ad_groups} grupos"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'ad_groups_results': []
            }
        
        # Configurar proveedor una sola vez
        if not self.set_provider(
            provider_type=campaign_config.provider,
            api_key=os.getenv(f"{campaign_config.provider.upper()}_API_KEY"),
            model=campaign_config.model
        ):
            return {
                'success': False,
                'error': 'No se pudo configurar el proveedor de IA',
                'ad_groups_results': []
            }
        
        # Generar anuncios para cada grupo
        ad_groups_results = []
        total_successful = 0
        total_failed = 0
        
        for group_config in campaign_config.ad_groups:
            logger.info("")
            logger.info("─"*70)
            logger.info(f"📋 GRUPO #{group_config.group_index + 1}: {group_config.group_name}")
            logger.info(f"🔑 Keywords: {', '.join(group_config.keywords[:5])}{'...' if len(group_config.keywords) > 5 else ''}")
            logger.info(f"🌐 URL: {group_config.landing_url}")
            logger.info("─"*70)
            
            try:
                # Generar anuncios para este grupo específico
                batch_result = self.generate_batch(
                    keywords=group_config.keywords,
                    num_ads=1,  # Un anuncio por grupo (puedes ajustar)
                    num_headlines=campaign_config.num_headlines,
                    num_descriptions=campaign_config.num_descriptions,
                    tone=campaign_config.tone,
                    user=user,
                    validate=True,
                    business_type="esoteric",
                    save_to_csv=True,
                    temperature=campaign_config.temperature
                )
                
                # Agregar metadata del grupo
                batch_result['ad_group_config'] = group_config.to_dict()
                batch_result['group_index'] = group_config.group_index
                batch_result['group_name'] = group_config.group_name
                
                ad_groups_results.append(batch_result)
                
                if batch_result['successful'] > 0:
                    total_successful += batch_result['successful']
                    logger.info(f"✅ Grupo #{group_config.group_index + 1} completado: {batch_result['successful']} anuncios")
                else:
                    total_failed += 1
                    logger.warning(f"⚠️ Grupo #{group_config.group_index + 1} falló")
                
            except Exception as e:
                logger.error(f"❌ Error en grupo #{group_config.group_index + 1}: {e}")
                ad_groups_results.append({
                    'success': False,
                    'error': str(e),
                    'ad_group_config': group_config.to_dict(),
                    'group_index': group_config.group_index,
                    'group_name': group_config.group_name
                })
                total_failed += 1
        
        # Resultado final
        final_result = {
            'success': total_successful > 0,
            'campaign_config': campaign_config.to_dict(),
            'total_groups': campaign_config.num_ad_groups,
            'successful_groups': total_successful,
            'failed_groups': total_failed,
            'success_rate': (total_successful / campaign_config.num_ad_groups * 100) if campaign_config.num_ad_groups > 0 else 0,
            'ad_groups_results': ad_groups_results,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("="*70)
        logger.info("🏁 GENERACIÓN MULTI-GRUPO COMPLETADA")
        logger.info(f"   ✅ Exitosos: {total_successful}/{campaign_config.num_ad_groups}")
        logger.info(f"   ❌ Fallidos: {total_failed}/{campaign_config.num_ad_groups}")
        logger.info(f"   📊 Tasa de éxito: {final_result['success_rate']:.1f}%")
        logger.info("="*70)
        
        return final_result
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
        
        # Cache para regeneración rápida
        self.generation_cache = {}
        
        logger.info(f"✅ AIAdGenerator v2.0 inicializado. Storage: {self.storage_path}")
    
    def _setup_storage_path(self, custom_path: Optional[str]) -> str:
        """Configura la ruta de almacenamiento"""
        if custom_path:
            return custom_path
        
        home_dir = Path.home()
        data_dir = home_dir / "dashboard-google-ads-data"
        
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directorio de datos: {data_dir}")
        except Exception as e:
            logger.error(f"❌ Error creando directorio: {e}")
            data_dir = Path.cwd() / "data"
            data_dir.mkdir(exist_ok=True)
        
        return str(data_dir / "generated_ads.csv")
    
    def _initialize_csv(self):
        """Inicializa el archivo CSV si no existe"""
        if not os.path.exists(self.storage_path):
            headers = [
                'id', 'timestamp', 'user', 'provider', 'model', 'keywords',
                'tone', 'num_ads', 'num_headlines', 'num_descriptions',
                'headlines', 'descriptions', 'validation_status',
                'valid_headlines', 'invalid_headlines', 'valid_descriptions',
                'invalid_descriptions', 'validation_errors', 'published',
                'campaign_id', 'ad_group_id', 'published_at',
                'batch_id', 'regeneration_count'
            ]
            
            try:
                with open(self.storage_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
                logger.info(f"✅ CSV v2.0 inicializado: {self.storage_path}")
            except Exception as e:
                logger.error(f"❌ Error inicializando CSV: {e}")
    
    def set_provider(self, provider_type: str, api_key: str, model: str = None) -> bool:
        """Configura el proveedor de IA"""
        try:
            provider_type = provider_type.lower().strip()
            
            if provider_type == 'openai':
                self.provider = OpenAIProvider(api_key, model or "gpt-4")
                logger.info(f"🤖 Proveedor: OpenAI ({model or 'gpt-4'})")
            elif provider_type == 'gemini':
                self.provider = GeminiProvider(api_key, model or "gemini-pro")
                logger.info(f"🤖 Proveedor: Gemini ({model or 'gemini-pro'})")
            else:
                raise ValueError(f"Proveedor no soportado: {provider_type}")
            
            if not self.provider.test_connection():
                raise ConnectionError("No se pudo conectar con el proveedor")
            
            logger.info("✅ Conexión con proveedor exitosa")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando proveedor: {e}")
            self.provider = None
            return False
    
    def generate_batch(
        self,
        keywords: List[str],
        num_ads: int = 1,
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        user: str = "saltbalente",
        validate: bool = True,
        business_type: str = "esoteric",
        save_to_csv: bool = True,
        temperature: float = 0.7,  # ✅ NUEVO
        use_magnetic: bool = False,  # ✅ FLAG MAGNÉTICO
        use_location_insertion: bool = False  # ✅ INSERCIONES DE UBICACIÓN
    ) -> Dict[str, Any]:
        """
        ✨ Genera múltiples anuncios en batch con soporte de temperatura, modo magnético e inserciones de ubicación
        """
        batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("="*60)
        logger.info(f"🎨 GENERACIÓN MASIVA - BATCH: {batch_id}")
        logger.info(f"📊 Cantidad de anuncios: {num_ads}")
        logger.info(f"🎨 Creatividad (temperature): {temperature}")
        logger.info(f"🔴 Modo magnético: {use_magnetic}")
        logger.info(f"📍 Inserciones de ubicación: {use_location_insertion}")
        logger.info("="*60)
        
        generated_ads = self.generate_ad(
            keywords=keywords,
            num_ads=num_ads,
            num_headlines=num_headlines,
            num_descriptions=num_descriptions,
            tone=tone,
            user=user,
            validate=validate,
            business_type=business_type,
            temperature=temperature,  # ✅ Pasar temperatura
            use_magnetic=use_magnetic,  # ✅ Pasar modo magnético
            use_location_insertion=use_location_insertion  # ✅ Pasar inserciones de ubicación
        )
        
        for idx, ad in enumerate(generated_ads):
            ad['batch_id'] = batch_id
            ad['index_in_batch'] = idx + 1
        
        successful = len([ad for ad in generated_ads if 'error' not in ad or not ad['error']])
        failed = len(generated_ads) - successful
        
        batch_result = {
            'batch_id': batch_id,
            'timestamp': datetime.now().isoformat(),
            'total_requested': num_ads,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / num_ads * 100) if num_ads > 0 else 0,
            'ads': generated_ads,
            'keywords': keywords,
            'tone': tone,
            'temperature': temperature,
            'provider': self.provider.__class__.__name__.replace('Provider', '') if self.provider else None
        }
        
        if save_to_csv and successful > 0:
            for ad in generated_ads:
                if 'error' not in ad or not ad['error']:
                    try:
                        self._save_to_csv(ad)
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando en CSV: {e}")
        
        logger.info(f"✅ BATCH COMPLETADO: {successful}/{num_ads} exitosos ({batch_result['success_rate']:.1f}%)")
        return batch_result
    
    def regenerate_headline(
        self,
        original_headline: str,
        keywords: List[str],
        tone: str = "profesional",
        custom_instruction: Optional[str] = None,
        business_type: str = "esoteric"
    ) -> Optional[str]:
        """
        ✨ NUEVO: Regenera un headline con instrucciones personalizadas
        """
        if not self.provider:
            logger.error("❌ No hay proveedor configurado")
            return None
        
        logger.info(f"🔄 Regenerando headline: '{original_headline}'")
        
        try:
            instruction = custom_instruction or "Crea una variación diferente pero igualmente efectiva"
            
            prompt = f"""Regenera este titular de Google Ads:

TITULAR ORIGINAL: "{original_headline}"

CONTEXTO:
- Keywords: {', '.join(keywords)}
- Tono: {tone}
- Tipo de negocio: {business_type}
- Instrucción especial: {instruction}

REQUISITOS ESTRICTOS:
- Máximo 30 caracteres (OBLIGATORIO)
- Incluir keywords relevantes
- Mantener tono {tone}
- Diferente al original pero igual de efectivo

RESPONDE SOLO CON EL NUEVO TITULAR, SIN COMILLAS NI EXPLICACIONES."""

            if isinstance(self.provider, OpenAIProvider):
                import openai
                openai.api_key = self.provider.api_key
                
                response = openai.ChatCompletion.create(
                    model=self.provider.model,
                    messages=[
                        {"role": "system", "content": "Eres un experto en copywriting para Google Ads. Respondes SOLO con el titular."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=60,
                    temperature=0.9
                )
                
                new_headline = response.choices[0].message.content.strip()
            
            elif isinstance(self.provider, GeminiProvider):
                import google.generativeai as genai
                genai.configure(api_key=self.provider.api_key)
                
                model = genai.GenerativeModel(self.provider.model)
                response = model.generate_content(prompt)
                
                new_headline = response.text.strip()
            
            else:
                return None
            
            new_headline = new_headline.strip('"\'').strip()
            
            if len(new_headline) > 30:
                new_headline = new_headline[:30]
            
            if len(new_headline) < 10:
                return None
            
            logger.info(f"✅ Headline regenerado: '{new_headline}'")
            return new_headline
        
        except Exception as e:
            logger.error(f"❌ Error regenerando: {e}")
            return None
    
    def regenerate_description(
        self,
        original_description: str,
        keywords: List[str],
        tone: str = "profesional",
        custom_instruction: Optional[str] = None,
        business_type: str = "esoteric"
    ) -> Optional[str]:
        """✨ NUEVO: Regenera una description"""
        if not self.provider:
            return None
        
        try:
            instruction = custom_instruction or "Crea una variación diferente"
            
            prompt = f"""Regenera esta descripción de Google Ads:

DESCRIPCIÓN ORIGINAL: "{original_description}"

CONTEXTO:
- Keywords: {', '.join(keywords)}
- Tono: {tone}
- Instrucción: {instruction}

REQUISITOS:
- Máximo 90 caracteres
- Incluir CTA
- Tono {tone}

RESPONDE SOLO CON LA NUEVA DESCRIPCIÓN."""

            if isinstance(self.provider, OpenAIProvider):
                import openai
                openai.api_key = self.provider.api_key
                
                response = openai.ChatCompletion.create(
                    model=self.provider.model,
                    messages=[
                        {"role": "system", "content": "Experto en Google Ads."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=100,
                    temperature=0.9
                )
                
                new_desc = response.choices[0].message.content.strip()
            
            elif isinstance(self.provider, GeminiProvider):
                import google.generativeai as genai
                genai.configure(api_key=self.provider.api_key)
                
                model = genai.GenerativeModel(self.provider.model)
                response = model.generate_content(prompt)
                
                new_desc = response.text.strip()
            
            else:
                return None
            
            new_desc = new_desc.strip('"\'').strip()
            
            if len(new_desc) > 90:
                new_desc = new_desc[:90]
            
            if len(new_desc) < 30:
                return None
            
            return new_desc
        
        except Exception as e:
            logger.error(f"❌ Error regenerando description: {e}")
            return None
    
    def generate_ad(
        self,
        keywords: List[str],
        num_ads: int = 1,
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        user: str = "saltbalente",
        validate: bool = True,
        business_type: str = "esoteric",
        temperature: float = 0.7,  # ✅ NUEVO: Parámetro de creatividad
        use_magnetic: bool = False,  # ✅ FLAG MAGNÉTICO
        use_location_insertion: bool = False  # ✅ INSERCIONES DE UBICACIÓN
    ) -> List[Dict[str, Any]]:
        """
        Genera múltiples anuncios con variación garantizada
        Versión 3.0 - Usa generate_multiple_ads() del provider con soporte para inserciones de ubicación
        """
        
        logger.info("="*60)
        logger.info("🚀 GENERACIÓN DE ANUNCIOS v3.0")
        logger.info(f"📋 Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
        logger.info(f"🔢 Cantidad solicitada: {num_ads}")
        logger.info(f"🎨 Temperatura/Creatividad: {temperature}")
        logger.info(f"🏢 Business type: {business_type}")
        logger.info(f"🔴 Modo magnético: {use_magnetic}")
        logger.info(f"📍 Inserciones de ubicación: {use_location_insertion}")
        logger.info("="*60)
        
        if not self.provider:
            logger.error("❌ No hay proveedor configurado")
            return [{'error': 'No hay proveedor configurado', 'headlines': [], 'descriptions': []}]
        
        try:
            # ✅ USAR EL NUEVO MÉTODO generate_multiple_ads() DEL PROVIDER
            logger.info(f"📡 Llamando a provider.generate_multiple_ads()...")
            
            generated_ads_raw = self.provider.generate_multiple_ads(
                keywords=keywords,
                num_ads=num_ads,
                num_headlines=num_headlines,
                num_descriptions=num_descriptions,
                tone=tone,
                business_type=business_type,
                temperature=temperature,  # ✅ Pasar temperatura
                use_magnetic=use_magnetic,  # ✅ Pasar modo magnético
                use_location_insertion=use_location_insertion  # ✅ Pasar inserciones de ubicación
            )
            
            logger.info(f"📥 Provider retornó {len(generated_ads_raw)} anuncios")
            
            # Procesar y validar cada anuncio
            processed_ads = []
            
            for i, ad_data in enumerate(generated_ads_raw):
                try:
                    ad_index = i + 1
                    logger.info(f"🔍 Procesando anuncio {ad_index}/{len(generated_ads_raw)}...")
                    
                    # Validar estructura básica
                    if not isinstance(ad_data, dict):
                        logger.warning(f"⚠️ Anuncio {ad_index}: Estructura inválida")
                        processed_ads.append({
                            'error': 'Estructura de datos inválida',
                            'headlines': [],
                            'descriptions': [],
                            'ad_number': ad_index
                        })
                        continue
                    
                    # Si hay error en el anuncio
                    if 'error' in ad_data and ad_data['error']:
                        logger.warning(f"⚠️ Anuncio {ad_index}: Error reportado - {ad_data['error']}")
                        processed_ads.append({
                            **ad_data,
                            'ad_number': ad_index
                        })
                        continue
                    
                    # Validar que tenga headlines y descriptions
                    if 'headlines' not in ad_data or not ad_data['headlines']:
                        logger.warning(f"⚠️ Anuncio {ad_index}: Sin títulos")
                        processed_ads.append({
                            'error': 'No se generaron títulos',
                            'headlines': [],
                            'descriptions': ad_data.get('descriptions', []),
                            'ad_number': ad_index
                        })
                        continue
                    
                    if 'descriptions' not in ad_data or not ad_data['descriptions']:
                        logger.warning(f"⚠️ Anuncio {ad_index}: Sin descripciones")
                        processed_ads.append({
                            'error': 'No se generaron descripciones',
                            'headlines': ad_data.get('headlines', []),
                            'descriptions': [],
                            'ad_number': ad_index
                        })
                        continue
                    
                    # Filtrar y validar longitudes
                    valid_headlines = [
                        h.strip() for h in ad_data['headlines'] 
                        if isinstance(h, str) and 10 <= len(h.strip()) <= 30
                    ]
                    
                    valid_descriptions = [
                        d.strip() for d in ad_data['descriptions']
                        if isinstance(d, str) and 30 <= len(d.strip()) <= 90
                    ]
                    
                    logger.info(f"   📊 Títulos válidos: {len(valid_headlines)}/{len(ad_data['headlines'])}")
                    logger.info(f"   📊 Descripciones válidas: {len(valid_descriptions)}/{len(ad_data['descriptions'])}")
                    
                    # Verificar mínimos requeridos
                    if len(valid_headlines) < 3:
                        logger.warning(f"⚠️ Anuncio {ad_index}: Solo {len(valid_headlines)} títulos válidos (mínimo 3)")
                        processed_ads.append({
                            'error': f'Insuficientes títulos válidos: {len(valid_headlines)}/3',
                            'headlines': valid_headlines,
                            'descriptions': valid_descriptions,
                            'ad_number': ad_index
                        })
                        continue
                    
                    if len(valid_descriptions) < 2:
                        logger.warning(f"⚠️ Anuncio {ad_index}: Solo {len(valid_descriptions)} descripciones válidas (mínimo 2)")
                        processed_ads.append({
                            'error': f'Insuficientes descripciones válidas: {len(valid_descriptions)}/2',
                            'headlines': valid_headlines,
                            'descriptions': valid_descriptions,
                            'ad_number': ad_index
                        })
                        continue
                    
                    # Actualizar el ad_data con elementos validados
                    ad_data['headlines'] = valid_headlines
                    ad_data['descriptions'] = valid_descriptions
                    
                    # Validar con GoogleAdsValidator si está habilitado
                    if validate:
                        try:
                            validation_result = self.validator.validate_ad(
                                headlines=valid_headlines,
                                descriptions=valid_descriptions
                            )
                            ad_data['validation_result'] = validation_result
                            logger.info(f"   ✅ Validación Google Ads: {validation_result.get('valid', False)}")
                        except Exception as val_error:
                            logger.warning(f"   ⚠️ Error en validación: {val_error}")
                            ad_data['validation_result'] = {'valid': False, 'error': str(val_error)}
                    
                    # Agregar metadatos
                    ad_data['id'] = f"AD_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{ad_index}"
                    ad_data['timestamp'] = datetime.now().isoformat()
                    ad_data['keywords'] = keywords
                    ad_data['tone'] = tone
                    ad_data['user'] = user
                    ad_data['business_type'] = business_type
                    ad_data['temperature'] = temperature
                    ad_data['ad_number'] = ad_index
                    ad_data['total_ads_in_batch'] = num_ads
                    
                    # Metadatos del provider (si no existen)
                    if 'provider' not in ad_data:
                        ad_data['provider'] = self.provider.__class__.__name__.replace('Provider', '')
                    if 'model' not in ad_data:
                        ad_data['model'] = getattr(self.provider, 'model', 'unknown')
                    
                    ad_data['num_headlines'] = len(valid_headlines)
                    ad_data['num_descriptions'] = len(valid_descriptions)
                    ad_data['regeneration_count'] = 0
                    ad_data['published'] = False
                    ad_data['campaign_id'] = None
                    ad_data['ad_group_id'] = None
                    
                    processed_ads.append(ad_data)
                    logger.info(f"✅ Anuncio {ad_index} procesado correctamente")
                
                except Exception as e:
                    logger.error(f"❌ Error procesando anuncio {i+1}: {e}", exc_info=True)
                    processed_ads.append({
                        'error': f'Error procesando anuncio: {str(e)}',
                        'headlines': [],
                        'descriptions': [],
                        'ad_number': i + 1
                    })
            
            # Estadísticas finales
            successful = len([ad for ad in processed_ads if 'error' not in ad or not ad['error']])
            failed = len(processed_ads) - successful
            
            logger.info("="*60)
            logger.info(f"🏁 GENERACIÓN COMPLETADA")
            logger.info(f"   ✅ Exitosos: {successful}/{num_ads}")
            logger.info(f"   ❌ Fallidos: {failed}/{num_ads}")
            logger.info(f"   📊 Tasa de éxito: {(successful/num_ads*100):.1f}%")
            logger.info("="*60)
            
            return processed_ads
        
        except Exception as e:
            logger.error(f"❌ Error crítico en generación: {e}", exc_info=True)
            return [{
                'error': f'Error crítico: {str(e)}',
                'headlines': [],
                'descriptions': []
            }]
    
    def _save_to_csv(self, ad_data: Dict[str, Any]):
        """Guarda en CSV"""
        try:
            validation = ad_data.get('validation_result', {})
            
            row = [
                ad_data.get('id', ''),
                ad_data.get('timestamp', ''),
                ad_data.get('user', 'saltbalente'),
                ad_data.get('provider', ''),
                ad_data.get('model', ''),
                json.dumps(ad_data.get('keywords', []), ensure_ascii=False),
                ad_data.get('tone', ''),
                1,
                ad_data.get('num_headlines', 0),
                ad_data.get('num_descriptions', 0),
                json.dumps(ad_data.get('headlines', []), ensure_ascii=False),
                json.dumps(ad_data.get('descriptions', []), ensure_ascii=False),
                'valid' if validation.get('valid', False) else 'invalid',
                0, 0, 0, 0, '',
                ad_data.get('published', False),
                ad_data.get('campaign_id', ''),
                ad_data.get('ad_group_id', ''),
                '',
                ad_data.get('batch_id', ''),
                ad_data.get('regeneration_count', 0)
            ]
            
            with open(self.storage_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(row)
        except:
            pass
    
    def export_to_json(self, ads: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """Exporta a JSON"""
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_ads': len(ads),
            'ads': ads
        }
        
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                return filepath
            except:
                pass
        
        return json_str
    
    def import_from_json(self, json_data: str) -> List[Dict[str, Any]]:
        """Importa desde JSON"""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            return data.get('ads', [])
        except:
            return []
    
    def load_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Carga historial"""
        history = []
        
        try:
            if not os.path.exists(self.storage_path):
                return history
            
            with open(self.storage_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    try:
                        row['keywords'] = json.loads(row.get('keywords', '[]'))
                        row['headlines'] = json.loads(row.get('headlines', '[]'))
                        row['descriptions'] = json.loads(row.get('descriptions', '[]'))
                    except:
                        pass
                    
                    history.append(row)
            
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return history[:limit]
        except:
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas"""
        try:
            history = self.load_history(limit=10000)
            
            return {
                'total_ads': len(history),
                'published_ads': len([ad for ad in history if ad.get('published', 'False').lower() == 'true']),
                'providers': {},
                'tones': {},
                'batches': {}
            }
        except:
            return {'total_ads': 0}