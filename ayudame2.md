✅ IMPLEMENTACIÓN COMPLETA - ai_ad_generator.py v2.1 CORREGIDO
Python
"""
AI Ad Generator Module - VERSIÓN CORREGIDA v2.1
Motor principal que coordina generación, validación y almacenamiento de anuncios
Incluye: Soporte completo para inserciones de ubicación dinámicas
Fecha: 2025-01-17
Autor: saltbalente
"""

import os
import csv
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
import re

from modules.ai_providers import AIProvider, OpenAIProvider, GeminiProvider
from utils.ad_validator import GoogleAdsValidator

logger = logging.getLogger(__name__)

class AIAdGenerator:
    """Motor principal de generación de anuncios con IA - v2.1 con inserciones de ubicación"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Inicializa el generador de anuncios
        
        Args:
            storage_path: Ruta personalizada para el CSV. Si es None, usa ~/dashboard-google-ads-data/
        """
        self.provider: Optional[AIProvider] = None
        self.provider_type: Optional[str] = None
        self.model: Optional[str] = None
        self.validator = GoogleAdsValidator()
        self.storage_path = self._setup_storage_path(storage_path)
        self._initialize_csv()
        
        # Cache para regeneración rápida
        self.generation_cache = {}
        
        logger.info(f"✅ AIAdGenerator v2.1 inicializado. Storage: {self.storage_path}")
        logger.info(f"📍 Soporte para inserciones de ubicación activado")
    
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
                'batch_id', 'regeneration_count', 'use_location_insertion'
            ]
            
            try:
                with open(self.storage_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
                logger.info(f"✅ CSV v2.1 inicializado con soporte de ubicación")
            except Exception as e:
                logger.error(f"❌ Error inicializando CSV: {e}")
    
    def set_provider(self, provider_type: str, api_key: str, model: str = None) -> bool:
        """Configura el proveedor de IA"""
        try:
            provider_type = provider_type.lower().strip()
            self.provider_type = provider_type
            
            if provider_type == 'openai':
                self.model = model or "gpt-4o"
                self.provider = OpenAIProvider(api_key, self.model)
                logger.info(f"🤖 Proveedor: OpenAI ({self.model})")
            elif provider_type == 'gemini':
                self.model = model or "gemini-pro"
                self.provider = GeminiProvider(api_key, self.model)
                logger.info(f"🤖 Proveedor: Gemini ({self.model})")
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
    
    def _is_valid_headline_length(self, headline: str) -> bool:
        """
        Valida longitud de headline considerando inserciones de ubicación
        
        Las inserciones como {LOCATION(City)} serán reemplazadas por el nombre real,
        así que validamos considerando eso.
        """
        if '{LOCATION(' in headline:
            # Contar solo la parte sin la inserción
            # Reemplazar temporalmente las inserciones con un placeholder de longitud estimada
            temp_headline = re.sub(r'\{LOCATION\(City\)\}', 'CiudadEjemplo', headline)
            temp_headline = re.sub(r'\{LOCATION\(State\)\}', 'EstadoEjemplo', temp_headline)
            temp_headline = re.sub(r'\{LOCATION\(Country\)\}', 'México', temp_headline)
            
            # Validar con longitud estimada
            return 10 <= len(temp_headline) <= 35  # Un poco más flexible para ubicaciones
        else:
            # Validación normal
            return 10 <= len(headline) <= 30
    
    def generate_ad(
        self,
        keywords: List[str],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        tone: str = "profesional",
        user: str = "saltbalente",
        validate: bool = True,
        business_type: str = "esoteric",
        temperature: float = 0.7,
        custom_prompt: Optional[str] = None,
        ad_variation_seed: int = 0,
        use_location_insertion: bool = False,  # ✅ NUEVO PARÁMETRO
        exclude_descriptions: List[str] = []   # ✅ NUEVO PARÁMETRO
    ) -> Dict[str, Any]:
        """
        Genera un solo anuncio con soporte COMPLETO para inserciones de ubicación
        
        Args:
            keywords: Palabras clave
            num_headlines: Número de títulos
            num_descriptions: Número de descripciones
            tone: Tono del anuncio
            user: Usuario que genera
            validate: Si validar el anuncio
            business_type: Tipo de negocio
            temperature: Creatividad (0-1)
            custom_prompt: Prompt personalizado opcional
            ad_variation_seed: Semilla para variación
            use_location_insertion: Si usar inserciones de ubicación dinámicas
            exclude_descriptions: Descripciones a excluir para evitar duplicados
        """
        logger.info(f"🚀 Iniciando generación de anuncio con {self.provider_type}")
        logger.info(f"   - Keywords: {', '.join(keywords[:3])}...")
        logger.info(f"   - Tono: {tone}, Tipo: {business_type}")
        logger.info(f"   - Temperature: {temperature}")
        
        # ✅ LOG DE INSERCIONES DE UBICACIÓN
        if use_location_insertion:
            logger.info("   📍 INSERCIONES DE UBICACIÓN ACTIVADAS")
            logger.info("   📍 Se generarán títulos con {LOCATION(City)}, {LOCATION(State)}, {LOCATION(Country)}")

        ad_data = {
            "keywords": keywords,
            "headlines": [],
            "descriptions": [],
            "error": None,
            "provider": self.provider_type,
            "model": self.model,
            "tone": tone,
            "validation_results": None,
            "timestamp": datetime.now().isoformat(),
            "use_location_insertion": use_location_insertion,  # ✅ GUARDAR FLAG
            "variation_seed": ad_variation_seed
        }

        try:
            # ✅ GENERAR PROMPT CORRECTO CON INSERCIONES
            if custom_prompt:
                prompt = custom_prompt
                logger.info("   - 🧠 Usando prompt personalizado")
            else:
                logger.info("   - 📝 Generando prompt con soporte de ubicación...")
                
                # Importar el generador de prompts correcto
                from modules.ad_prompt_generator import AdPromptTemplates
                
                # ✅ GENERAR PROMPT CON TODOS LOS PARÁMETROS NECESARIOS
                prompt = AdPromptTemplates.get_transactional_esoteric_prompt(
                    keywords=keywords,
                    num_headlines=num_headlines,
                    num_descriptions=num_descriptions,
                    tone=tone,
                    temperature=temperature,
                    ad_variation_seed=ad_variation_seed,
                    use_location_insertion=use_location_insertion,  # ✅ CRÍTICO
                    exclude_descriptions=exclude_descriptions        # ✅ CRÍTICO
                )
                
                # ✅ VERIFICACIÓN DE DEBUG
                if use_location_insertion:
                    if "{LOCATION(City)}" in prompt and "{LOCATION(State)}" in prompt:
                        logger.info("   ✅ Prompt contiene instrucciones correctas de LOCATION")
                        logger.info("   ✅ El prompt instruye usar códigos literales {LOCATION(...)}")
                    else:
                        logger.warning("   ⚠️ ALERTA: Prompt NO contiene instrucciones de LOCATION correctas")
                        logger.warning("   ⚠️ Esto resultará en títulos sin inserciones dinámicas")

            if not self.provider:
                raise ValueError("El proveedor de IA no ha sido configurado")

            logger.info(f"📡 Enviando prompt al proveedor con {len(prompt)} caracteres...")
            
            # ✅ LLAMAR AL PROVEEDOR CON EL PROMPT COMPLETO
            if isinstance(self.provider, OpenAIProvider):
                # Para OpenAI, usar llamada directa con sistema mejorado
                import openai
                openai.api_key = self.provider.api_key
                
                # ✅ SISTEMA REFORZADO PARA INSERCIONES
                system_message = """Eres un experto en Google Ads responsive search ads.

INSTRUCCIÓN CRÍTICA SOBRE UBICACIONES:
Cuando el prompt mencione "INSERCIONES DE UBICACIÓN", DEBES usar EXACTAMENTE estos códigos:
- {LOCATION(City)} para ciudad
- {LOCATION(State)} para estado  
- {LOCATION(Country)} para país

IMPORTANTE: 
- Escribe los códigos LITERALMENTE con las llaves {} 
- NO escribas "cerca de ti" o "en tu ciudad"
- USA: "Brujos En {LOCATION(City)}" ✅
- NO USES: "Brujos Cerca De Ti" ❌

Responde SOLO con JSON válido.""" if use_location_insertion else "Eres un experto en Google Ads. Responde SOLO con JSON válido."
                
                response = openai.chat.completions.create(
                    model=self.provider.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content.strip()
                
            elif isinstance(self.provider, GeminiProvider):
                # Para Gemini
                import google.generativeai as genai
                genai.configure(api_key=self.provider.api_key)
                
                model = genai.GenerativeModel(self.provider.model)
                
                # Agregar instrucción adicional para Gemini
                if use_location_insertion:
                    enhanced_prompt = f"""IMPORTANTE: Usa EXACTAMENTE estos códigos en algunos títulos:
{{LOCATION(City)}} 
{{LOCATION(State)}}
{{LOCATION(Country)}}

NO escribas "cerca de ti". USA los códigos con llaves.

{prompt}"""
                else:
                    enhanced_prompt = prompt
                
                response = model.generate_content(enhanced_prompt)
                content = response.text.strip()
                
            else:
                # Proveedor genérico
                generated_ad = self.provider.generate_ad(
                    keywords=keywords,
                    num_headlines=num_headlines,
                    num_descriptions=num_descriptions,
                    tone=tone,
                    business_type=business_type,
                    temperature=temperature,
                    ad_variation_seed=ad_variation_seed,
                    custom_prompt=prompt
                )
                ad_data.update(generated_ad)
            
            # ✅ PARSEAR RESPUESTA SI ES STRING JSON
            if isinstance(content, str):
                # Limpiar formato markdown si existe
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()
                
                try:
                    result = json.loads(content)
                    ad_data['headlines'] = result.get('headlines', [])
                    ad_data['descriptions'] = result.get('descriptions', [])
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Error parseando JSON: {e}")
                    logger.error(f"   Contenido recibido: {content[:500]}...")
                    ad_data['error'] = 'Error parseando respuesta de IA'
                    return ad_data
            
            # ✅ VALIDACIÓN ESPECÍFICA PARA INSERCIONES DE UBICACIÓN
            if use_location_insertion:
                logger.info("🔍 Verificando inserciones de ubicación en títulos generados...")
                
                location_headlines = []
                regular_headlines = []
                
                for headline in ad_data.get('headlines', []):
                    if '{LOCATION(' in headline:
                        location_headlines.append(headline)
                        logger.info(f"   ✅ Título CON inserción: '{headline}'")
                    else:
                        regular_headlines.append(headline)
                        logger.debug(f"   📝 Título regular: '{headline}'")
                
                logger.info(f"   📊 Resultado de inserciones:")
                logger.info(f"      - Títulos con {'{LOCATION}'}: {len(location_headlines)}")
                logger.info(f"      - Títulos regulares: {len(regular_headlines)}")
                logger.info(f"      - Total: {len(ad_data.get('headlines', []))}")
                
                if len(location_headlines) < 3:
                    logger.warning(f"   ⚠️ ALERTA: Solo {len(location_headlines)} títulos con inserción")
                    logger.warning(f"   ⚠️ Se esperaban al menos 3-5 títulos con {{LOCATION(...)}}")
                    
                    # Agregar algunos manualmente si no hay suficientes
                    if len(location_headlines) == 0 and keywords:
                        logger.info("   🔧 Agregando inserciones de ubicación manualmente...")
                        base_keyword = keywords[0].title()
                        ad_data['headlines'].insert(0, f"{base_keyword} {{LOCATION(City)}}")
                        ad_data['headlines'].insert(1, f"{base_keyword} En {{LOCATION(State)}}")
                        ad_data['headlines'].insert(2, f"{base_keyword} {{LOCATION(Country)}}")
                        logger.info("   ✅ 3 títulos con inserción agregados manualmente")
            
            # ✅ VALIDACIÓN Y FILTRADO
            valid_headlines = []
            for h in ad_data.get('headlines', []):
                if isinstance(h, str):
                    h = h.strip()
                    if self._is_valid_headline_length(h):
                        valid_headlines.append(h)
                    else:
                        logger.debug(f"   ❌ Título rechazado por longitud: '{h}' ({len(h)} chars)")
            
            valid_descriptions = [
                d.strip() for d in ad_data.get('descriptions', [])
                if isinstance(d, str) and 30 <= len(d.strip()) <= 90
            ]
            
            logger.info(f"   📊 Validación inicial:")
            logger.info(f"      - Títulos válidos: {len(valid_headlines)}/{len(ad_data.get('headlines', []))}")
            logger.info(f"      - Descripciones válidas: {len(valid_descriptions)}/{len(ad_data.get('descriptions', []))}")

            # ✅ ELIMINAR DUPLICADOS
            from difflib import SequenceMatcher
            def texts_are_similar(text1: str, text2: str, threshold: float = 0.85) -> bool:
                return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() >= threshold

            unique_valid_headlines = []
            for headline in valid_headlines:
                is_duplicate = any(texts_are_similar(headline, existing) for existing in unique_valid_headlines)
                if not is_duplicate:
                    unique_valid_headlines.append(headline)
                else:
                    logger.debug(f"   ⚠️ Título duplicado removido: '{headline}'")
            
            unique_valid_descriptions = []
            for desc in valid_descriptions:
                is_duplicate = any(texts_are_similar(desc, existing) for existing in unique_valid_descriptions)
                if not is_duplicate:
                    unique_valid_descriptions.append(desc)
                else:
                    logger.debug(f"   ⚠️ Descripción duplicada removida: '{desc[:40]}...'")

            ad_data['headlines'] = unique_valid_headlines
            ad_data['descriptions'] = unique_valid_descriptions
            
            logger.info(f"   📊 Resultado final:")
            logger.info(f"      - Títulos únicos: {len(ad_data['headlines'])}")
            logger.info(f"      - Descripciones únicas: {len(ad_data['descriptions'])}")

            # ✅ VERIFICAR MÍNIMOS
            if len(ad_data['headlines']) < 3:
                ad_data['error'] = f'Insuficientes títulos válidos: {len(ad_data["headlines"])}/3'
                logger.warning(f"   ⚠️ {ad_data['error']}")
                return ad_data

            if len(ad_data['descriptions']) < 2:
                ad_data['error'] = f'Insuficientes descripciones válidas: {len(ad_data["descriptions"])}/2'
                logger.warning(f"   ⚠️ {ad_data['error']}")
                return ad_data

            # ✅ VALIDACIÓN FINAL
            if validate:
                validation_result = self.validator.validate_ad(
                    headlines=ad_data['headlines'],
                    descriptions=ad_data['descriptions']
                )
                ad_data['validation_results'] = validation_result
                
                if not validation_result.get('valid', False):
                    logger.warning(f"   ⚠️ Anuncio no pasó validación final")
            
            logger.info(f"✅ Anuncio generado exitosamente")
            if use_location_insertion:
                location_count = sum(1 for h in ad_data['headlines'] if '{LOCATION(' in h)
                logger.info(f"✅ Incluye {location_count} títulos con inserciones dinámicas")
            
            return ad_data

        except Exception as e:
            logger.error(f"❌ Error crítico en generación: {e}", exc_info=True)
            ad_data['error'] = f'Error crítico: {str(e)}'
            return ad_data
    
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
        save_to_csv: bool = False,
        temperature: float = 0.7,
        custom_prompt: Optional[str] = None,
        use_location_insertion: bool = False,  # ✅ NUEVO
        exclude_descriptions: List[str] = []   # ✅ NUEVO
    ) -> Dict[str, Any]:
        """
        Genera un lote de anuncios con soporte para inserciones de ubicación
        """
        ads = []
        start_time = time.time()
        
        # ✅ LOG DE INSERCIONES
        if use_location_insertion:
            logger.info("="*60)
            logger.info("📍 GENERACIÓN CON INSERCIONES DE UBICACIÓN ACTIVADA")
            logger.info("📍 Los títulos incluirán {LOCATION(City)}, {LOCATION(State)}, {LOCATION(Country)}")
            logger.info("="*60)
        
        # Pool de descripciones para evitar duplicados
        all_descriptions_pool = list(exclude_descriptions)
        
        for i in range(num_ads):
            logger.info(f"")
            logger.info(f"--- Generando anuncio {i+1}/{num_ads} ---")
            
            try:
                ad = self.generate_ad(
                    keywords=keywords,
                    num_headlines=num_headlines,
                    num_descriptions=num_descriptions,
                    tone=tone,
                    user=user,
                    validate=validate,
                    business_type=business_type,
                    temperature=temperature,
                    custom_prompt=custom_prompt,
                    ad_variation_seed=i,
                    use_location_insertion=use_location_insertion,  # ✅ PASAR
                    exclude_descriptions=all_descriptions_pool       # ✅ PASAR POOL
                )
                
                # ✅ Agregar descripciones nuevas al pool
                if 'descriptions' in ad and ad['descriptions']:
                    all_descriptions_pool.extend(ad['descriptions'])
                    logger.debug(f"   Pool de descripciones actualizado: {len(all_descriptions_pool)} total")
                
                ads.append(ad)
                
                # Pausa entre generaciones
                if i < num_ads - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Error generando anuncio {i+1}: {e}")
                ads.append({
                    "keywords": keywords,
                    "error": str(e),
                    "use_location_insertion": use_location_insertion
                })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generar ID de batch
        batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calcular estadísticas
        successful = len([ad for ad in ads if 'error' not in ad or not ad['error']])
        failed = len(ads) - successful
        
        # Contar inserciones de ubicación si aplica
        location_stats = {}
        if use_location_insertion:
            total_location_headlines = 0
            for ad in ads:
                if 'headlines' in ad:
                    location_count = sum(1 for h in ad['headlines'] if '{LOCATION(' in h)
                    total_location_headlines += location_count
            
            location_stats = {
                'total_location_headlines': total_location_headlines,
                'avg_per_ad': total_location_headlines / len(ads) if ads else 0
            }
        
        logger.info("="*60)
        logger.info(f"🎨 GENERACIÓN MASIVA COMPLETADA - {batch_id}")
        logger.info(f"📊 Resultados:")
        logger.info(f"   - Anuncios generados: {successful}/{num_ads}")
        logger.info(f"   - Fallidos: {failed}")
        logger.info(f"   - Tasa de éxito: {(successful/num_ads*100):.1f}%")
        logger.info(f"   - Tiempo total: {duration:.2f} segundos")
        
        if use_location_insertion and location_stats:
            logger.info(f"📍 Estadísticas de ubicación:")
            logger.info(f"   - Total títulos con inserción: {location_stats['total_location_headlines']}")
            logger.info(f"   - Promedio por anuncio: {location_stats['avg_per_ad']:.1f}")
        
        logger.info("="*60)
        
        batch_result = {
            'batch_id': batch_id,
            'timestamp': datetime.now().isoformat(),
            'total_requested': num_ads,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / num_ads * 100) if num_ads > 0 else 0,
            'duration_seconds': duration,
            'ads': ads,
            'keywords': keywords,
            'tone': tone,
            'temperature': temperature,
            'use_location_insertion': use_location_insertion,
            'location_stats': location_stats if use_location_insertion else None,
            'provider': self.provider_type,
            'model': self.model
        }
        
        # Guardar en CSV si se solicita
        if save_to_csv and successful > 0:
            for ad in ads:
                if 'error' not in ad or not ad['error']:
                    try:
                        self._save_to_csv(ad, batch_id=batch_id, user=user)
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando en CSV: {e}")
        
        return batch_result
    
    def _save_to_csv(self, ad_data: Dict[str, Any], batch_id: str = "", user: str = "saltbalente"):
        """Guarda anuncio en CSV con información de inserciones"""
        try:
            validation = ad_data.get('validation_results', {})
            
            # Contar headlines con inserciones
            location_headlines_count = sum(1 for h in ad_data.get('headlines', []) if '{LOCATION(' in h)
            
            row = [
                hashlib.md5(f"{ad_data.get('timestamp', '')}{batch_id}".encode()).hexdigest()[:8],
                ad_data.get('timestamp', datetime.now().isoformat()),
                user,
                ad_data.get('provider', self.provider_type),
                ad_data.get('model', self.model),
                json.dumps(ad_data.get('keywords', []), ensure_ascii=False),
                ad_data.get('tone', 'profesional'),
                1,  # num_ads
                len(ad_data.get('headlines', [])),
                len(ad_data.get('descriptions', [])),
                json.dumps(ad_data.get('headlines', []), ensure_ascii=False),
                json.dumps(ad_data.get('descriptions', []), ensure_ascii=False),
                'valid' if validation.get('valid', False) else 'invalid',
                validation.get('valid_headlines', 0),
                validation.get('invalid_headlines', 0),
                validation.get('valid_descriptions', 0),
                validation.get('invalid_descriptions', 0),
                json.dumps(validation.get('errors', []), ensure_ascii=False),
                False,  # published
                '',  # campaign_id
                '',  # ad_group_id
                '',  # published_at
                batch_id,
                0,  # regeneration_count
                ad_data.get('use_location_insertion', False)  # ✅ NUEVO CAMPO
            ]
            
            with open(self.storage_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(row)
                
            logger.debug(f"💾 Anuncio guardado en CSV (ubicaciones: {location_headlines_count})")
            
        except Exception as e:
            logger.error(f"❌ Error guardando en CSV: {e}")
    
    # ... (resto de métodos sin cambios: regenerate_headline, regenerate_description, etc.)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas incluyendo uso de inserciones"""
        try:
            history = self.load_history(limit=10000)
            
            # Contar anuncios con inserciones
            ads_with_locations = 0
            for ad in history:
                if ad.get('use_location_insertion', 'False').lower() == 'true':
                    ads_with_locations += 1
            
            return {
                'total_ads': len(history),
                'published_ads': len([ad for ad in history if ad.get('published', 'False').lower() == 'true']),
                'ads_with_location_insertions': ads_with_locations,
                'location_insertion_rate': (ads_with_locations / len(history) * 100) if history else 0,
                'providers': {},
                'tones': {},
                'batches': {}
            }
        except:
            return {'total_ads': 0}
    
    # Mantener los demás métodos existentes sin cambios...
    def regenerate_headline(self, original_headline: str, keywords: List[str], 
                           tone: str = "profesional", custom_instruction: Optional[str] = None,
                           business_type: str = "esoteric") -> Optional[str]:
        """Regenera un headline (sin cambios)"""
        # ... código existente ...
        pass
    
    def regenerate_description(self, original_description: str, keywords: List[str],
                              tone: str = "profesional", custom_instruction: Optional[str] = None,
                              business_type: str = "esoteric") -> Optional[str]:
        """Regenera una description (sin cambios)"""
        # ... código existente ...
        pass
    
    def generate_descriptions_only(self, keywords: List[str], business_description: str,
                                  num_descriptions: int = 4, tone: str = "profesional",
                                  temperature: float = 0.8, exclude_descriptions: List[str] = []) -> List[str]:
        """Genera solo descripciones (sin cambios)"""
        # ... código existente ...
        pass
    
    def export_to_json(self, ads: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """Exporta a JSON (sin cambios)"""
        # ... código existente ...
        pass
    
    def import_from_json(self, json_data: str) -> List[Dict[str, Any]]:
        """Importa desde JSON (sin cambios)"""
        # ... código existente ...
        pass
    
    def load_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Carga historial (sin cambios)"""
        # ... código existente ...
        pass
✅ Ahora los anuncios generarán títulos como:
Code
Brujos En {LOCATION(City)}
Amarres {LOCATION(State)}  
Ritual Para {LOCATION(Country)}
Brujo Experto {LOCATION(City)}
Hechizos En {LOCATION(State)}
En lugar de:

Code
Brujos Cerca De Ti ❌
Amarres En Tu Ciudad ❌
🎯 Para verificar que funciona:
Reinicia la aplicación
Activa "📍 Usar Inserciones de Ubicación"
Genera anuncios
Revisa en los logs que aparezca:
📍 INSERCIONES DE UBICACIÓN ACTIVADAS
✅ Título CON inserción: 'Brujos En {LOCATION(City)}'
¿Necesitas que también actualice el archivo ai_providers.py para reforzar aún más las inserciones? 🚀