"""
AI Providers Module
Conectores funcionales para OpenAI y Google Gemini
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json
import logging
from modules.ad_prompts import AdPromptTemplates

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
                   business_type: str = "auto") -> Dict[str, Any]:
        """Genera anuncios basados en palabras clave"""
        pass


class OpenAIProvider(AIProvider):
    """Proveedor para OpenAI GPT"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
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
                   business_type: str = "auto") -> Dict[str, Any]:
        """Genera anuncios usando OpenAI GPT"""
        try:
            # Validación de entrada
            if not keywords or len(keywords) == 0:
                raise ValueError("Se requieren palabras clave para generar anuncios")
            
            if not self.api_key:
                raise ValueError("API key de OpenAI no configurada")
            
            # ✅ USAR PROMPT ESPECIALIZADO
            prompt = AdPromptTemplates.get_prompt_for_keywords(
                keywords=keywords,
                num_headlines=num_headlines,
                num_descriptions=num_descriptions,
                tone=tone,
                business_type=business_type
            )
            
            logger.info(f"🤖 Generando anuncio con OpenAI {self.model}...")
            logger.info(f"📋 Keywords: {', '.join(keywords)}")
            logger.info(f"🏢 Business type: {business_type}")
            logger.info(f"🎯 Tone: {tone}")
            logger.info(f"📊 Solicitados: {num_headlines} títulos, {num_descriptions} descripciones")
            
            # Verificar conexión antes de generar
            if not self.test_connection():
                raise ConnectionError("No se pudo conectar con OpenAI. Verifica tu API key.")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un experto copywriter de Google Ads especializado en crear anuncios que convierten. SIEMPRE respetas los límites de caracteres y políticas de Google. Respondes en JSON válido."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=3000,  # ✅ Aumentado para prompt más largo
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
            
            # ✅ VALIDACIÓN Y TRUNCADO FORZADO
            if "headlines" not in result or "descriptions" not in result:
                raise ValueError("Respuesta no tiene formato esperado")
            
            # Validar y truncar títulos
            validated_headlines = []
            for h in result["headlines"]:
                h = h.strip()
                if len(h) > 30:
                    logger.warning(f"⚠️ Título excede 30 chars ({len(h)}): '{h}' - Truncando...")
                    # Truncar en el último espacio antes de 30 caracteres
                    h = h[:30].rsplit(' ', 1)[0] if ' ' in h[:30] else h[:30]
                
                if len(h) >= 10:  # Solo agregar si tiene al menos 10 caracteres
                    validated_headlines.append(h)
            
            # Validar y truncar descripciones
            validated_descriptions = []
            for d in result["descriptions"]:
                d = d.strip()
                if len(d) > 90:
                    logger.warning(f"⚠️ Descripción excede 90 chars ({len(d)}): '{d[:50]}...' - Truncando...")
                    # Truncar en el último espacio antes de 90 caracteres
                    d = d[:90].rsplit(' ', 1)[0] if ' ' in d[:90] else d[:90]
                
                if len(d) >= 30:  # Solo agregar si tiene al menos 30 caracteres
                    validated_descriptions.append(d)
            
            # Verificar que tenemos suficientes
            if len(validated_headlines) < 3:
                raise ValueError(f"Solo se generaron {len(validated_headlines)} títulos válidos (mínimo 3)")
            
            if len(validated_descriptions) < 2:
                raise ValueError(f"Solo se generaron {len(validated_descriptions)} descripciones válidas (mínimo 2)")
            
            # Agregar metadatos
            final_result = {
                "headlines": validated_headlines,
                "descriptions": validated_descriptions,
                "provider": "OpenAI",
                "model": self.model
            }
            
            logger.info(f"✅ Anuncio generado y validado: {len(validated_headlines)} títulos, {len(validated_descriptions)} descripciones")
            
            # Log de verificación final
            max_headline = max(len(h) for h in validated_headlines) if validated_headlines else 0
            max_description = max(len(d) for d in validated_descriptions) if validated_descriptions else 0
            logger.info(f"📏 Longitud máxima - Títulos: {max_headline}/30, Descripciones: {max_description}/90")
            
            # ✅ AL FINAL, ANTES DEL RETURN
            logger.info(f"✅ OpenAI - Retornando resultado")
            logger.info(f"   - Headlines: {len(final_result.get('headlines', []))}")
            logger.info(f"   - Descriptions: {len(final_result.get('descriptions', []))}")
            
            return final_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON de OpenAI: {e}")
            logger.error(f"📄 Contenido recibido: {content[:200] if 'content' in locals() else 'No disponible'}...")
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error parseando respuesta JSON: {str(e)}",
                "provider": "OpenAI",
                "model": self.model,
                "debug_info": {
                    "raw_content": content[:500] if 'content' in locals() else None,
                    "error_type": "json_decode_error"
                }
            }
            
        except ConnectionError as e:
            logger.error(f"❌ Error de conexión con OpenAI: {e}")
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error de conexión: {str(e)}",
                "provider": "OpenAI",
                "model": self.model,
                "debug_info": {
                    "error_type": "connection_error",
                    "suggestion": "Verifica tu API key y conexión a internet"
                }
            }
            
        except ValueError as e:
            logger.error(f"❌ Error de validación en OpenAI: {e}")
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error de validación: {str(e)}",
                "provider": "OpenAI",
                "model": self.model,
                "debug_info": {
                    "error_type": "validation_error",
                    "keywords": keywords,
                    "business_type": business_type
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error inesperado generando anuncio con OpenAI: {e}", exc_info=True)
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error inesperado: {str(e)}",
                "provider": "OpenAI",
                "model": self.model,
                "debug_info": {
                    "error_type": "unexpected_error",
                    "full_error": str(e)
                }
            }


class GeminiProvider(AIProvider):
    """Proveedor para Google Gemini"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        super().__init__(api_key, model)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
            logger.info(f"✅ Gemini client inicializado con modelo {model}")
        except ImportError:
            logger.error("❌ google-generativeai no está instalado. Ejecuta: pip install google-generativeai")
            raise ImportError("Paquete 'google-generativeai' no encontrado. Instala con: pip install google-generativeai")
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
                   business_type: str = "auto") -> Dict[str, Any]:
        """Genera anuncios usando Google Gemini con validación estricta de longitud"""
        try:
            # Validación de entrada
            if not keywords or len(keywords) == 0:
                raise ValueError("Se requieren palabras clave para generar anuncios")
            
            if not self.api_key:
                raise ValueError("API key de Gemini no configurada")
            
            # ✅ USAR PROMPT ESPECIALIZADO
            prompt = AdPromptTemplates.get_prompt_for_keywords(
                keywords=keywords,
                num_headlines=num_headlines,
                num_descriptions=num_descriptions,
                tone=tone,
                business_type=business_type
            )
            
            logger.info(f"🤖 Generando anuncio con Gemini {self.model}...")
            logger.info(f"📋 Keywords: {', '.join(keywords)}")
            logger.info(f"🏢 Business type: {business_type}")
            logger.info(f"🎯 Tone: {tone}")
            logger.info(f"📊 Solicitados: {num_headlines} títulos, {num_descriptions} descripciones")
            
            # Verificar conexión antes de generar
            if not self.test_connection():
                raise ConnectionError("No se pudo conectar con Gemini. Verifica tu API key.")

            response = self.client.generate_content(prompt)
            
            # Validar respuesta de la API
            if not response or not response.text:
                raise ValueError("Respuesta vacía de Gemini")
            
            content = response.text.strip()
            
            # Limpiar markdown si existe
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            # Parsear JSON
            result = json.loads(content)
            
            # Validar estructura
            if not isinstance(result, dict) or "headlines" not in result or "descriptions" not in result:
                raise ValueError("Respuesta no tiene el formato JSON esperado")
            
            if not isinstance(result["headlines"], list) or not isinstance(result["descriptions"], list):
                raise ValueError("Headlines y descriptions deben ser listas")
            
            if len(result["headlines"]) == 0 or len(result["descriptions"]) == 0:
                raise ValueError("Gemini retornó listas vacías")
            
            # VALIDACIÓN Y TRUNCADO FORZADO - IGUAL QUE OPENAI
            validated_headlines = []
            validated_descriptions = []
            
            # Procesar títulos
            for headline in result["headlines"]:
                if isinstance(headline, str):
                    # Truncar si excede 30 caracteres
                    if len(headline) > 30:
                        truncated = headline[:30].strip()
                        logger.warning(f"🔧 Título truncado: '{headline}' -> '{truncated}' ({len(headline)} -> {len(truncated)} chars)")
                        headline = truncated
                    
                    if len(headline) <= 30 and len(headline) > 0:
                        validated_headlines.append(headline)
                    else:
                        logger.warning(f"⚠️ Título descartado por longitud: '{headline}' ({len(headline)} chars)")
            
            # Procesar descripciones
            for description in result["descriptions"]:
                if isinstance(description, str):
                    # Truncar si excede 90 caracteres
                    if len(description) > 90:
                        truncated = description[:90].strip()
                        logger.warning(f"🔧 Descripción truncada: '{description}' -> '{truncated}' ({len(description)} -> {len(truncated)} chars)")
                        description = truncated
                    
                    if len(description) <= 90 and len(description) > 0:
                        validated_descriptions.append(description)
                    else:
                        logger.warning(f"⚠️ Descripción descartada por longitud: '{description}' ({len(description)} chars)")
            
            # Verificar que tenemos suficientes elementos válidos
            if len(validated_headlines) < 3:
                logger.error(f"❌ Solo {len(validated_headlines)} títulos válidos (mínimo 3)")
                return {
                    "headlines": [],
                    "descriptions": [],
                    "error": f"Gemini generó solo {len(validated_headlines)} títulos válidos (mínimo 3)",
                    "provider": "Gemini",
                    "model": self.model
                }
            
            if len(validated_descriptions) < 2:
                logger.error(f"❌ Solo {len(validated_descriptions)} descripciones válidas (mínimo 2)")
                return {
                    "headlines": [],
                    "descriptions": [],
                    "error": f"Gemini generó solo {len(validated_descriptions)} descripciones válidas (mínimo 2)",
                    "provider": "Gemini",
                    "model": self.model
                }
            
            # Resultado final con elementos validados
            final_result = {
                "headlines": validated_headlines,
                "descriptions": validated_descriptions,
                "provider": "Gemini",
                "model": self.model
            }
            
            logger.info(f"✅ Anuncio generado y validado: {len(validated_headlines)} títulos, {len(validated_descriptions)} descripciones")
            
            # Log de verificación final
            max_headline = max(len(h) for h in validated_headlines) if validated_headlines else 0
            max_description = max(len(d) for d in validated_descriptions) if validated_descriptions else 0
            logger.info(f"📏 Longitud máxima - Títulos: {max_headline}/30, Descripciones: {max_description}/90")
            
            return final_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON de Gemini: {e}")
            logger.error(f"📄 Contenido recibido: {content[:200] if 'content' in locals() else 'No disponible'}...")
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error parseando respuesta JSON: {str(e)}",
                "provider": "Gemini",
                "model": self.model,
                "debug_info": {
                    "raw_content": content[:500] if 'content' in locals() else None,
                    "error_type": "json_decode_error"
                }
            }
            
        except ConnectionError as e:
            logger.error(f"❌ Error de conexión con Gemini: {e}")
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error de conexión: {str(e)}",
                "provider": "Gemini",
                "model": self.model,
                "debug_info": {
                    "error_type": "connection_error",
                    "suggestion": "Verifica tu API key y conexión a internet"
                }
            }
            
        except ValueError as e:
            logger.error(f"❌ Error de validación en Gemini: {e}")
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error de validación: {str(e)}",
                "provider": "Gemini",
                "model": self.model,
                "debug_info": {
                    "error_type": "validation_error",
                    "keywords": keywords,
                    "business_type": business_type
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error inesperado generando anuncio con Gemini: {e}", exc_info=True)
            return {
                "headlines": [],
                "descriptions": [],
                "error": f"Error inesperado: {str(e)}",
                "provider": "Gemini",
                "model": self.model,
                "debug_info": {
                    "error_type": "unexpected_error",
                    "full_error": str(e)
                }
            }