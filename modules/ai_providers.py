"""
AI Providers Module
Conectores funcionales para OpenAI y Google Gemini
Versión 2.0 - Soporte para múltiples anuncios con variación
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json
import logging
from modules.ad_prompts import AdPromptTemplates, MagneticAdPrompts 

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Clase abstracta para proveedores de IA"""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model
        self.client = None
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Verifica la conexión con la API"""
        pass
    
    @abstractmethod
    def generate_ad(self, keywords: List[str], num_headlines: int = 15, 
                   num_descriptions: int = 4, tone: str = "profesional",
                   business_type: str = "auto", temperature: float = 0.7,
                   ad_variation_seed: int = 0) -> Dict[str, Any]:
        """Genera anuncios basados en palabras clave"""
        pass
    
    def generate_multiple_ads(self, keywords: List[str], num_ads: int = 3,
                            num_headlines: int = 15, num_descriptions: int = 4,
                            tone: str = "profesional", business_type: str = "auto",
                            temperature: float = 0.7) -> List[Dict[str, Any]]:
        """
        Genera múltiples anuncios con variación garantizada
        
        Args:
            keywords: Lista de keywords para generar anuncios
            num_ads: Cantidad de anuncios a generar (default: 3)
            num_headlines: Títulos por anuncio (default: 15)
            num_descriptions: Descripciones por anuncio (default: 4)
            tone: Tono del anuncio (default: "profesional")
            business_type: Tipo de negocio (default: "auto")
            temperature: Creatividad de la IA (default: 0.7)
        
        Returns:
            Lista de diccionarios con anuncios generados
        """
        ads = []
        
        for ad_index in range(num_ads):
            logger.info(f"🔄 Generando anuncio {ad_index + 1}/{num_ads}...")
            
            try:
                # Generar anuncio con seed de variación
                ad = self.generate_ad(
                    keywords=keywords,
                    num_headlines=num_headlines,
                    num_descriptions=num_descriptions,
                    tone=tone,
                    business_type=business_type,
                    temperature=temperature,
                    ad_variation_seed=ad_index
                )
                
                # Validar que el anuncio tenga contenido
                if ad and ad.get('headlines') and ad.get('descriptions'):
                    ad['ad_number'] = ad_index + 1
                    ad['total_ads'] = num_ads
                    ads.append(ad)
                    logger.info(f"✅ Anuncio {ad_index + 1}/{num_ads} generado: {len(ad['headlines'])} títulos, {len(ad['descriptions'])} descripciones")
                else:
                    logger.warning(f"⚠️ Anuncio {ad_index + 1} vacío o incompleto, saltando...")
                    
            except Exception as e:
                logger.error(f"❌ Error generando anuncio {ad_index + 1}/{num_ads}: {e}")
                continue
        
        if not ads:
            logger.error("❌ No se pudo generar ningún anuncio válido")
            return []
        
        # Validar que los anuncios sean diferentes
        if len(ads) > 1:
            self._validate_ads_are_different(ads)
        
        logger.info(f"✅ Total generado: {len(ads)}/{num_ads} anuncios exitosos")
        return ads
    
    def _validate_ads_are_different(self, ads: List[Dict[str, Any]]) -> None:
        """Valida que los anuncios generados sean suficientemente diferentes"""
        for i in range(len(ads) - 1):
            for j in range(i + 1, len(ads)):
                ad1_headlines = set(ads[i].get('headlines', []))
                ad2_headlines = set(ads[j].get('headlines', []))
                
                # Calcular similitud
                if ad1_headlines and ad2_headlines:
                    intersection = ad1_headlines & ad2_headlines
                    similarity = len(intersection) / max(len(ad1_headlines), len(ad2_headlines))
                    
                    if similarity > 0.3:  # Más del 30% de similitud
                        logger.warning(f"⚠️ Anuncios {i+1} y {j+1} tienen {similarity*100:.1f}% de similitud")
                        logger.warning(f"   Títulos duplicados: {list(intersection)[:3]}")
                    else:
                        logger.info(f"✅ Anuncios {i+1} y {j+1} son suficientemente diferentes ({similarity*100:.1f}% similitud)")


class OpenAIProvider(AIProvider):
    """Proveedor para OpenAI GPT"""
    
    def __init__(self, api_key: str, model: str = "gpt-5-pro"):
        super().__init__(api_key, model)
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            logger.info(f"✅ OpenAI client inicializado con modelo {model}")
        except ImportError:
            logger.error("❌ openai no está instalado. Ejecuta: pip install openai")
            raise ImportError("Paquete 'openai' no encontrado. Instala con: pip install openai")
        except Exception as e:
            logger.error(f"❌ Error inicializando OpenAI: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Verifica la conexión con OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=5,
                temperature=0.1
            )
            
            if response and response.choices:
                logger.info("✅ Conexión exitosa con OpenAI")
                return True
            else:
                logger.error("❌ Respuesta vacía de OpenAI")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando con OpenAI: {e}")
            return False
    
    def generate_ad(self, keywords: List[str], num_headlines: int = 15, 
                   num_descriptions: int = 4, tone: str = "profesional",
                   business_type: str = "auto", temperature: float = 0.7,
                   ad_variation_seed: int = 0, custom_prompt: str = None,
                   use_location_insertion: bool = False) -> Dict[str, Any]:
        """Genera anuncios usando OpenAI GPT con soporte de variación"""
        try:
            # Validación de entrada
            if not keywords or len(keywords) == 0:
                raise ValueError("Se requieren palabras clave para generar anuncios")
            
            if not self.api_key:
                raise ValueError("API key de OpenAI no configurada")
            
            # Si hay prompt personalizado, usarlo
            if custom_prompt:
                prompt = custom_prompt
            else:
                # Generar prompt estándar
                from modules.ad_prompt_generator import AdPromptTemplates
                prompt = AdPromptTemplates.get_prompt_for_keywords(
                    keywords=keywords,
                    num_headlines=num_headlines,
                    num_descriptions=num_descriptions,
                    tone=tone,
                    business_type=business_type,
                    temperature=temperature,
                    ad_variation_seed=ad_variation_seed,
                    use_location_insertion=use_location_insertion  # ✅ CRÍTICO
                )
                logger.info("🔄 Usando prompt generado automáticamente")
            
            logger.info(f"🤖 OpenAI - Anuncio #{ad_variation_seed + 1} - {self.model}")
            logger.info(f"📋 Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
            logger.info(f"🎨 Temperature: {temperature} | Seed: {ad_variation_seed}")
            
            # Verificar conexión solo en el primer anuncio
            if ad_variation_seed == 0 and not self.test_connection():
                raise ConnectionError("No se pudo conectar con OpenAI. Verifica tu API key.")
            
            # ✅ INSTRUCCIÓN ADICIONAL PARA REFORZAR INSERCIONES
            if use_location_insertion:
                system_message = """Eres un experto en Google Ads. 
IMPORTANTE: Cuando veas instrucciones de INSERCIONES DE UBICACIÓN, debes usar EXACTAMENTE los códigos:
- {LOCATION(City)} para ciudad
- {LOCATION(State)} para estado  
- {LOCATION(Country)} para país

NO escribas "cerca de ti" o "en tu ciudad". USA LOS CÓDIGOS LITERALES con llaves."""
            else:
                system_message = """Eres un experto copywriter de Google Ads especializado en crear contenido único y original.

REGLAS CRÍTICAS Y NO NEGOCIABLES:
1. ❌ NUNCA copies ejemplos literalmente del prompt
2. ✅ SIEMPRE genera contenido 100% ÚNICO y DIFERENTE
3. ✅ Cada descripción debe ser COMPLETAMENTE DISTINTA a las anteriores
4. ✅ Cada título debe ser ÚNICO y NO REPETIR conceptos
5. ✅ Usa sinónimos, estructuras diferentes y enfoques variados
6. ✅ Respetas límites de caracteres estrictamente (Títulos: 10-30, Descripciones: 30-90)
7. ✅ Respondes SOLO en JSON válido sin markdown

⚠️ IMPORTANTE: Si ves ejemplos en el prompt (como "Ej: ..."), úsalos SOLO como inspiración conceptual.
NUNCA copies el texto exacto. Genera versiones completamente diferentes adaptadas a las keywords específicas.

VALIDACIÓN: Antes de responder, verifica que:
- Ninguna descripción sea similar a otra (< 85% de similitud)
- Ningún título sea similar a otro (< 85% de similitud)
- Todo el contenido es original y no copia ejemplos"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,  # ⚠️ CRÍTICO: Usar temperature del parámetro
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            # Validar respuesta de la API
            if not response or not response.choices:
                raise ValueError("Respuesta vacía de OpenAI")
            
            if not response.choices[0].message.content:
                raise ValueError("Contenido vacío en la respuesta de OpenAI")
            
            content = response.choices[0].message.content.strip()
            
            # Limpiar markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            # Parsear JSON
            result = json.loads(content)
            
            # ✅ VERIFICACIÓN DE INSERCIONES
            if use_location_insertion:
                location_count = sum(1 for h in result.get('headlines', []) if '{LOCATION(' in h)
                logger.info(f"   📍 Títulos con inserción generados: {location_count}")
            
            # ✅ VALIDACIÓN Y TRUNCADO FORZADO
            if "headlines" not in result or "descriptions" not in result:
                raise ValueError("Respuesta no tiene formato esperado")
            
            # Validar y truncar títulos
            validated_headlines = []
            for h in result["headlines"]:
                h = h.strip()
                if len(h) > 30:
                    logger.warning(f"⚠️ Título excede 30 chars ({len(h)}): '{h[:40]}...' - Truncando")
                    h = h[:30].rsplit(' ', 1)[0] if ' ' in h[:30] else h[:30]
                
                if 10 <= len(h) <= 30:
                    validated_headlines.append(h)
            
            # Validar y truncar descripciones
            validated_descriptions = []
            for d in result["descriptions"]:
                d = d.strip()
                if len(d) > 90:
                    logger.warning(f"⚠️ Descripción excede 90 chars ({len(d)}): '{d[:50]}...' - Truncando")
                    d = d[:90].rsplit(' ', 1)[0] if ' ' in d[:90] else d[:90]
                
                if 30 <= len(d) <= 90:
                    validated_descriptions.append(d)
            
            # Verificar suficientes elementos
            if len(validated_headlines) < 3:
                raise ValueError(f"Solo {len(validated_headlines)} títulos válidos (mínimo 3)")
            
            if len(validated_descriptions) < 2:
                raise ValueError(f"Solo {len(validated_descriptions)} descripciones válidas (mínimo 2)")
            
            # Agregar metadatos
            final_result = {
                "headlines": validated_headlines,
                "descriptions": validated_descriptions,
                "provider": "OpenAI",
                "model": self.model,
                "variation_seed": ad_variation_seed
            }
            
            logger.info(f"✅ Anuncio #{ad_variation_seed + 1} OK: {len(validated_headlines)} títulos, {len(validated_descriptions)} descripciones")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Error generando anuncio #{ad_variation_seed + 1} con OpenAI: {e}")
            return {
                "headlines": [],
                "descriptions": [],
                "error": str(e),
                "provider": "OpenAI",
                "model": self.model,
                "variation_seed": ad_variation_seed
            }


class GeminiProvider(AIProvider):
    """Proveedor para Google Gemini"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-pro"):
        super().__init__(api_key, model)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
            logger.info(f"✅ Gemini client inicializado con modelo {model}")
        except ImportError:
            logger.error("❌ google-generativeai no está instalado. Ejecuta: pip install google-generativeai")
            raise ImportError("Paquete 'google-generativeai' no encontrado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Gemini: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Verifica la conexión con Gemini"""
        try:
            response = self.client.generate_content("Test connection")
            
            if response and response.text:
                logger.info("✅ Conexión exitosa con Gemini")
                return True
            else:
                logger.error("❌ Respuesta vacía de Gemini")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando con Gemini: {e}")
            return False
    
    def generate_ad(self, keywords: List[str], num_headlines: int = 15, 
                   num_descriptions: int = 4, tone: str = "profesional",
                   business_type: str = "auto", temperature: float = 0.7,
                   ad_variation_seed: int = 0, custom_prompt: str = None,
                   use_location_insertion: bool = False) -> Dict[str, Any]:
        """Genera anuncios usando Google Gemini con soporte de variación"""
        try:
            # Validación de entrada
            if not keywords or len(keywords) == 0:
                raise ValueError("Se requieren palabras clave para generar anuncios")
            
            if not self.api_key:
                raise ValueError("API key de Gemini no configurada")
            
            # Si hay prompt personalizado, usarlo
            if custom_prompt:
                prompt = custom_prompt
            else:
                # Generar prompt estándar
                from modules.ad_prompt_generator import AdPromptTemplates
                prompt = AdPromptTemplates.get_prompt_for_keywords(
                    keywords=keywords,
                    num_headlines=num_headlines,
                    num_descriptions=num_descriptions,
                    tone=tone,
                    business_type=business_type,
                    temperature=temperature,
                    ad_variation_seed=ad_variation_seed,
                    use_location_insertion=use_location_insertion  # ✅ CRÍTICO
                )
                logger.info("🔄 Usando prompt generado automáticamente")
            
            logger.info(f"🤖 Gemini - Anuncio #{ad_variation_seed + 1} - {self.model}")
            logger.info(f"📋 Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
            logger.info(f"🎨 Temperature: {temperature} | Seed: {ad_variation_seed}")
            
            # Verificar conexión solo en el primer anuncio
            if ad_variation_seed == 0 and not self.test_connection():
                raise ConnectionError("No se pudo conectar con Gemini. Verifica tu API key.")
            
            # ✅ INSTRUCCIÓN ADICIONAL PARA REFORZAR INSERCIONES
            if use_location_insertion:
                enhanced_prompt = f"""IMPORTANTE: Cuando veas instrucciones de INSERCIONES DE UBICACIÓN, debes usar EXACTAMENTE los códigos:
- {{LOCATION(City)}} para ciudad
- {{LOCATION(State)}} para estado  
- {{LOCATION(Country)}} para país

NO escribas "cerca de ti" o "en tu ciudad". USA LOS CÓDIGOS LITERALES con llaves.

{prompt}"""
            else:
                enhanced_prompt = f"""INSTRUCCIONES CRÍTICAS:
- NUNCA copies ejemplos literalmente
- SIEMPRE genera contenido 100% ÚNICO
- Cada descripción debe ser COMPLETAMENTE DISTINTA
- Usa sinónimos y estructuras variadas
- Respeta límites: Títulos 10-30 chars, Descripciones 30-90 chars
- Responde SOLO en JSON válido

Los ejemplos en el prompt son SOLO inspiración. NO copies el texto exacto.

{prompt}"""

            response = self.client.generate_content(enhanced_prompt)
            
            # Validar respuesta de la API
            if not response or not response.text:
                raise ValueError("Respuesta vacía de Gemini")
            
            content = response.text.strip()
            
            # Limpiar markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            # Parsear JSON
            result = json.loads(content)
            
            # ✅ VERIFICACIÓN DE INSERCIONES
            if use_location_insertion:
                location_count = sum(1 for h in result.get('headlines', []) if '{LOCATION(' in h)
                logger.info(f"   📍 Títulos con inserción generados: {location_count}")
            
            # Validar estructura
            if not isinstance(result, dict) or "headlines" not in result or "descriptions" not in result:
                raise ValueError("Respuesta no tiene el formato JSON esperado")
            
            # VALIDACIÓN Y TRUNCADO
            validated_headlines = []
            for headline in result["headlines"]:
                if isinstance(headline, str):
                    headline = headline.strip()
                    if len(headline) > 30:
                        headline = headline[:30].rsplit(' ', 1)[0] if ' ' in headline[:30] else headline[:30]
                    
                    if 10 <= len(headline) <= 30:
                        validated_headlines.append(headline)
            
            validated_descriptions = []
            for description in result["descriptions"]:
                if isinstance(description, str):
                    description = description.strip()
                    if len(description) > 90:
                        description = description[:90].rsplit(' ', 1)[0] if ' ' in description[:90] else description[:90]
                    
                    if 30 <= len(description) <= 90:
                        validated_descriptions.append(description)
            
            # Verificar suficientes elementos
            if len(validated_headlines) < 3:
                raise ValueError(f"Solo {len(validated_headlines)} títulos válidos (mínimo 3)")
            
            if len(validated_descriptions) < 2:
                raise ValueError(f"Solo {len(validated_descriptions)} descripciones válidas (mínimo 2)")
            
            # Resultado final
            final_result = {
                "headlines": validated_headlines,
                "descriptions": validated_descriptions,
                "provider": "Gemini",
                "model": self.model,
                "variation_seed": ad_variation_seed
            }
            
            logger.info(f"✅ Anuncio #{ad_variation_seed + 1} OK: {len(validated_headlines)} títulos, {len(validated_descriptions)} descripciones")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Error generando anuncio #{ad_variation_seed + 1} con Gemini: {e}")
            return {
                "headlines": [],
                "descriptions": [],
                "error": str(e),
                "provider": "Gemini",
                "model": self.model,
                "variation_seed": ad_variation_seed
            }