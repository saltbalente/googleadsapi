"""
Ad Validator Module
Validador de anuncios según políticas de Google Ads
Versión mejorada con estructura compatible con AIAdGenerator
"""

import re
import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)

class GoogleAdsValidator:
    """Validador de anuncios según políticas de Google Ads"""
    
    # Configuración de límites
    MAX_HEADLINE_LENGTH = 30
    MAX_DESCRIPTION_LENGTH = 90
    MIN_HEADLINE_LENGTH = 10  # Evitar títulos muy cortos
    MIN_DESCRIPTION_LENGTH = 30  # Evitar descripciones muy cortas
    MIN_HEADLINES = 3
    MIN_DESCRIPTIONS = 2
    
    # Patrones prohibidos
    PROHIBITED_PUNCTUATION = ['!', '¡', '?', '¿']
    
    # Pattern de emojis más completo
    EMOJI_PATTERN = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "]+", 
        flags=re.UNICODE
    )
    
    # Pattern para mayúsculas consecutivas (3 o más)
    CONSECUTIVE_CAPS_PATTERN = re.compile(r'[A-ZÁÉÍÓÚÑ]{3,}')
    
    # Pattern para espacios dobles o más
    DOUBLE_SPACE_PATTERN = re.compile(r'\s{2,}')
    
    # Palabras prohibidas (solo casos realmente problemáticos)
    # Nota: Google Ads permite muchas palabras en contexto adecuado
    FORBIDDEN_WORDS = [
        'click aqui',
        'haz clic',
        'clic aqui',
        'descarga ya',
        'descarga ahora',
        '100% gratis',
        '100% garantizado',
        'garantia total',
        'totalmente gratis'
    ]
    
    @staticmethod
    def validate_headline(headline: str) -> Tuple[bool, List[str]]:
        """
        Valida un título individual
        
        Args:
            headline: Título a validar
            
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        if not headline or not headline.strip():
            errors.append("El título no puede estar vacío")
            return False, errors
        
        headline = headline.strip()
        
        # Verificar longitud máxima
        if len(headline) > GoogleAdsValidator.MAX_HEADLINE_LENGTH:
            errors.append(f"Excede {GoogleAdsValidator.MAX_HEADLINE_LENGTH} caracteres ({len(headline)} caracteres)")
        
        # Verificar longitud mínima (advertencia, no error crítico)
        if len(headline) < GoogleAdsValidator.MIN_HEADLINE_LENGTH:
            errors.append(f"Título muy corto (menos de {GoogleAdsValidator.MIN_HEADLINE_LENGTH} caracteres)")
        
        # Verificar mayúsculas consecutivas
        matches = GoogleAdsValidator.CONSECUTIVE_CAPS_PATTERN.findall(headline)
        if matches:
            errors.append(f"Mayúsculas consecutivas encontradas: {', '.join(matches)}")
        
        # Verificar puntuación prohibida
        found_punct = [p for p in GoogleAdsValidator.PROHIBITED_PUNCTUATION if p in headline]
        if found_punct:
            errors.append(f"Puntuación prohibida: {', '.join(found_punct)}")
        
        # Verificar emojis
        if GoogleAdsValidator.EMOJI_PATTERN.search(headline):
            errors.append("Contiene emojis (no permitidos)")
        
        # Verificar espacios dobles
        if GoogleAdsValidator.DOUBLE_SPACE_PATTERN.search(headline):
            errors.append("Contiene espacios dobles o múltiples")
        
        # Verificar palabras prohibidas
        headline_lower = headline.lower()
        found_words = [word for word in GoogleAdsValidator.FORBIDDEN_WORDS if word.lower() in headline_lower]
        if found_words:
            errors.append(f"Frases prohibidas: {', '.join(found_words)}")
        
        # Verificar que no sea solo números
        if headline.replace(' ', '').isdigit():
            errors.append("No puede ser solo números")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_description(description: str) -> Tuple[bool, List[str]]:
        """
        Valida una descripción individual
        
        Args:
            description: Descripción a validar
            
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        if not description or not description.strip():
            errors.append("La descripción no puede estar vacía")
            return False, errors
        
        description = description.strip()
        
        # Verificar longitud máxima
        if len(description) > GoogleAdsValidator.MAX_DESCRIPTION_LENGTH:
            errors.append(f"Excede {GoogleAdsValidator.MAX_DESCRIPTION_LENGTH} caracteres ({len(description)} caracteres)")
        
        # Verificar longitud mínima
        if len(description) < GoogleAdsValidator.MIN_DESCRIPTION_LENGTH:
            errors.append(f"Descripción muy corta (menos de {GoogleAdsValidator.MIN_DESCRIPTION_LENGTH} caracteres)")
        
        # Verificar mayúsculas consecutivas
        matches = GoogleAdsValidator.CONSECUTIVE_CAPS_PATTERN.findall(description)
        if matches:
            errors.append(f"Mayúsculas consecutivas encontradas: {', '.join(matches)}")
        
        # Verificar puntuación prohibida
        found_punct = [p for p in GoogleAdsValidator.PROHIBITED_PUNCTUATION if p in description]
        if found_punct:
            errors.append(f"Puntuación prohibida: {', '.join(found_punct)}")
        
        # Verificar emojis
        if GoogleAdsValidator.EMOJI_PATTERN.search(description):
            errors.append("Contiene emojis (no permitidos)")
        
        # Verificar espacios dobles
        if GoogleAdsValidator.DOUBLE_SPACE_PATTERN.search(description):
            errors.append("Contiene espacios dobles o múltiples")
        
        # Verificar palabras prohibidas
        description_lower = description.lower()
        found_words = [word for word in GoogleAdsValidator.FORBIDDEN_WORDS if word.lower() in description_lower]
        if found_words:
            errors.append(f"Frases prohibidas: {', '.join(found_words)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_ad(headlines: List[str], descriptions: List[str]) -> Dict[str, Any]:
        """
        Valida un anuncio completo
        
        Args:
            headlines: Lista de títulos
            descriptions: Lista de descripciones
            
        Returns:
            Dict con resultado de validación compatible con AIAdGenerator
        """
        result = {
            'valid': True,  # ✅ Key correcta
            'headlines': {},  # ✅ Dict con índices
            'descriptions': {},  # ✅ Dict con índices
            'summary': {
                'valid_headlines': 0,
                'invalid_headlines': 0,
                'valid_descriptions': 0,
                'invalid_descriptions': 0,
                'total_headlines': len(headlines),
                'total_descriptions': len(descriptions)
            },
            'errors': [],
            'warnings': []
        }
        
        # Filtrar vacíos
        valid_headlines = [h for h in headlines if h and h.strip()]
        valid_descriptions = [d for d in descriptions if d and d.strip()]
        
        # Verificar cantidad mínima
        if len(valid_headlines) < GoogleAdsValidator.MIN_HEADLINES:
            error_msg = f"Se requieren al menos {GoogleAdsValidator.MIN_HEADLINES} títulos válidos (tienes {len(valid_headlines)})"
            result['errors'].append(error_msg)
            result['valid'] = False
        
        if len(valid_descriptions) < GoogleAdsValidator.MIN_DESCRIPTIONS:
            error_msg = f"Se requieren al menos {GoogleAdsValidator.MIN_DESCRIPTIONS} descripciones válidas (tienes {len(valid_descriptions)})"
            result['errors'].append(error_msg)
            result['valid'] = False
        
        # Validar cada título
        for i, headline in enumerate(headlines):
            if headline and headline.strip():
                is_valid, errors = GoogleAdsValidator.validate_headline(headline)
                
                result['headlines'][i] = {
                    'text': headline,
                    'valid': is_valid,
                    'errors': errors,
                    'length': len(headline)
                }
                
                if is_valid:
                    result['summary']['valid_headlines'] += 1
                else:
                    result['summary']['invalid_headlines'] += 1
                    result['valid'] = False
                    for error in errors:
                        result['errors'].append(f"Título {i+1}: {error}")
        
        # Validar cada descripción
        for i, description in enumerate(descriptions):
            if description and description.strip():
                is_valid, errors = GoogleAdsValidator.validate_description(description)
                
                result['descriptions'][i] = {
                    'text': description,
                    'valid': is_valid,
                    'errors': errors,
                    'length': len(description)
                }
                
                if is_valid:
                    result['summary']['valid_descriptions'] += 1
                else:
                    result['summary']['invalid_descriptions'] += 1
                    result['valid'] = False
                    for error in errors:
                        result['errors'].append(f"Descripción {i+1}: {error}")
        
        # Verificar duplicados (advertencia, no error crítico)
        unique_headlines = set(h.strip().lower() for h in valid_headlines)
        if len(unique_headlines) < len(valid_headlines):
            duplicates_count = len(valid_headlines) - len(unique_headlines)
            result['warnings'].append(f"Se encontraron {duplicates_count} título(s) duplicado(s)")
        
        unique_descriptions = set(d.strip().lower() for d in valid_descriptions)
        if len(unique_descriptions) < len(valid_descriptions):
            duplicates_count = len(valid_descriptions) - len(unique_descriptions)
            result['warnings'].append(f"Se encontraron {duplicates_count} descripción(es) duplicada(s)")
        
        # Logging del resultado
        if result['valid']:
            logger.info(f"✅ Anuncio válido: {result['summary']['valid_headlines']} títulos, {result['summary']['valid_descriptions']} descripciones")
        else:
            logger.warning(f"⚠️ Anuncio inválido: {len(result['errors'])} errores encontrados")
        
        return result
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Limpia un texto para cumplir con las políticas básicas
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpiado
        """
        if not text:
            return ""
        
        # Eliminar espacios extra
        text = GoogleAdsValidator.DOUBLE_SPACE_PATTERN.sub(' ', text.strip())
        
        # Eliminar emojis
        text = GoogleAdsValidator.EMOJI_PATTERN.sub('', text)
        
        # Eliminar puntuación prohibida
        for punct in GoogleAdsValidator.PROHIBITED_PUNCTUATION:
            text = text.replace(punct, '')
        
        # Corregir mayúsculas consecutivas
        def fix_caps(match):
            word = match.group(0)
            # Si es un acrónimo conocido (2-3 letras), dejarlo
            if len(word) <= 3 and word.isupper():
                return word
            # Si no, convertir solo primera letra a mayúscula
            return word.capitalize()
        
        text = GoogleAdsValidator.CONSECUTIVE_CAPS_PATTERN.sub(fix_caps, text)
        
        return text.strip()
    
    @staticmethod
    def get_validation_summary(validation_result: Dict[str, Any]) -> str:
        """
        Genera un resumen legible del resultado de validación
        
        Args:
            validation_result: Resultado de validate_ad()
            
        Returns:
            Resumen en texto
        """
        summary = validation_result.get('summary', {})
        
        if validation_result.get('valid', False):
            return (f"✅ Anuncio válido\n"
                   f"   • {summary.get('valid_headlines', 0)} títulos válidos\n"
                   f"   • {summary.get('valid_descriptions', 0)} descripciones válidas")
        
        result_text = "❌ Anuncio no válido:\n\n"
        
        # Mostrar resumen de validación
        result_text += f"📊 Resumen:\n"
        result_text += f"   • Títulos válidos: {summary.get('valid_headlines', 0)}/{summary.get('total_headlines', 0)}\n"
        result_text += f"   • Títulos inválidos: {summary.get('invalid_headlines', 0)}\n"
        result_text += f"   • Descripciones válidas: {summary.get('valid_descriptions', 0)}/{summary.get('total_descriptions', 0)}\n"
        result_text += f"   • Descripciones inválidas: {summary.get('invalid_descriptions', 0)}\n\n"
        
        # Mostrar errores
        if validation_result.get('errors'):
            result_text += f"❌ Errores ({len(validation_result['errors'])}):\n"
            for error in validation_result['errors'][:10]:  # Mostrar máximo 10
                result_text += f"   • {error}\n"
            
            if len(validation_result['errors']) > 10:
                result_text += f"   ... y {len(validation_result['errors']) - 10} errores más\n"
        
        # Mostrar advertencias
        if validation_result.get('warnings'):
            result_text += f"\n⚠️ Advertencias:\n"
            for warning in validation_result['warnings']:
                result_text += f"   • {warning}\n"
        
        return result_text.strip()
    
    @staticmethod
    def quick_fix_ad(headlines: List[str], descriptions: List[str]) -> Dict[str, List[str]]:
        """
        Intenta corregir automáticamente problemas comunes
        
        Args:
            headlines: Lista de títulos
            descriptions: Lista de descripciones
            
        Returns:
            Dict con 'headlines' y 'descriptions' corregidas
        """
        fixed_headlines = []
        fixed_descriptions = []
        
        # Corregir títulos
        for headline in headlines:
            if headline and headline.strip():
                fixed = GoogleAdsValidator.clean_text(headline)
                
                # Truncar si excede longitud
                if len(fixed) > GoogleAdsValidator.MAX_HEADLINE_LENGTH:
                    fixed = fixed[:GoogleAdsValidator.MAX_HEADLINE_LENGTH].rsplit(' ', 1)[0]
                
                fixed_headlines.append(fixed)
        
        # Corregir descripciones
        for description in descriptions:
            if description and description.strip():
                fixed = GoogleAdsValidator.clean_text(description)
                
                # Truncar si excede longitud
                if len(fixed) > GoogleAdsValidator.MAX_DESCRIPTION_LENGTH:
                    fixed = fixed[:GoogleAdsValidator.MAX_DESCRIPTION_LENGTH].rsplit(' ', 1)[0]
                
                fixed_descriptions.append(fixed)
        
        return {
            'headlines': fixed_headlines,
            'descriptions': fixed_descriptions
        }