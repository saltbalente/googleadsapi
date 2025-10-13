"""
🎨 TEMPLATE MANAGER - Gestor de Plantillas Esotéricas
Sistema completo de gestión de plantillas para generación de anuncios
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import yaml
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import random
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Gestor centralizado de plantillas esotéricas para generación de anuncios.
    
    Características:
    - Carga y gestión de templates desde YAML
    - Aplicación de templates a generación de anuncios
    - Combinación de múltiples templates
    - Validación de contenido contra reglas
    - Generación de variaciones dinámicas
    - Sistema de recomendaciones inteligentes
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el gestor de plantillas.
        
        Args:
            config_path: Ruta al archivo esoteric_templates.yaml
        """
        self.config_path = config_path or self._get_default_config_path()
        self.templates: Dict[str, Any] = {}
        self.global_settings: Dict[str, Any] = {}
        self.dynamic_variations: Dict[str, List[str]] = {}
        self.validation_rules: Dict[str, Any] = {}
        self.export_settings: Dict[str, Any] = {}
        
        # Cargar configuración
        self._load_config()
        
        logger.info(f"✅ TemplateManager inicializado con {len(self.templates)} templates")
    
    def _get_default_config_path(self) -> str:
        """Obtiene la ruta por defecto del archivo de configuración."""
        current_dir = Path(__file__).parent.parent
        config_path = current_dir / "config" / "esoteric_templates.yaml"
        return str(config_path)
    
    def _load_config(self) -> None:
        """Carga la configuración desde el archivo YAML."""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"❌ Archivo de configuración no encontrado: {self.config_path}")
                raise FileNotFoundError(f"No se encontró el archivo: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            # Cargar secciones
            self.global_settings = config.get('global_settings', {})
            self.templates = config.get('templates', {})
            self.dynamic_variations = config.get('dynamic_variations', {})
            self.validation_rules = config.get('validation_rules', {})
            self.export_settings = config.get('export_settings', {})
            
            logger.info(f"✅ Configuración cargada exitosamente")
            logger.info(f"   - Templates: {len(self.templates)}")
            logger.info(f"   - Variaciones dinámicas: {len(self.dynamic_variations)}")
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            raise
    
    # =========================================================================
    # MÉTODOS DE CONSULTA DE TEMPLATES
    # =========================================================================
    
    def get_all_templates(self) -> Dict[str, Any]:
        """
        Obtiene todos los templates disponibles.
        
        Returns:
            Diccionario con todos los templates
        """
        return self.templates
    
    def get_template_names(self) -> List[str]:
        """
        Obtiene una lista de nombres de templates disponibles.
        
        Returns:
            Lista de nombres de templates
        """
        return list(self.templates.keys())
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un template específico por nombre.
        
        Args:
            template_name: Nombre del template (ej: 'brujeria_pareja')
        
        Returns:
            Diccionario con datos del template o None si no existe
        """
        template = self.templates.get(template_name)
        
        if not template:
            logger.warning(f"⚠️ Template '{template_name}' no encontrado")
            return None
        
        logger.info(f"✅ Template '{template_name}' obtenido")
        return template
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, str]]:
        """
        Obtiene información básica de un template (nombre, descripción, icono, color).
        
        Args:
            template_name: Nombre del template
        
        Returns:
            Diccionario con info básica del template
        """
        template = self.get_template(template_name)
        
        if not template:
            return None
        
        return {
            'key': template_name,
            'name': template.get('name', template_name),
            'description': template.get('description', ''),
            'icon': template.get('icon', '🔮'),
            'color': template.get('color', '#9C27B0')
        }
    
    def get_all_templates_info(self) -> List[Dict[str, str]]:
        """
        Obtiene información básica de todos los templates.
        
        Returns:
            Lista de diccionarios con info de cada template
        """
        templates_info = []
        
        for template_name in self.get_template_names():
            info = self.get_template_info(template_name)
            if info:
                templates_info.append(info)
        
        return templates_info
    
    # =========================================================================
    # MÉTODOS DE KEYWORDS
    # =========================================================================
    
    def get_keywords(
        self, 
        template_name: str, 
        include_primary: bool = True,
        include_secondary: bool = True,
        include_long_tail: bool = True,
        max_keywords: Optional[int] = None
    ) -> List[str]:
        """
        Obtiene keywords de un template con opciones de filtrado.
        
        Args:
            template_name: Nombre del template
            include_primary: Incluir keywords primarias
            include_secondary: Incluir keywords secundarias
            include_long_tail: Incluir keywords long tail
            max_keywords: Número máximo de keywords a retornar
        
        Returns:
            Lista de keywords
        """
        template = self.get_template(template_name)
        
        if not template:
            return []
        
        keywords_sugeridas = template.get('keywords_sugeridas', {})
        keywords = []
        
        if include_primary:
            keywords.extend(keywords_sugeridas.get('primarias', []))
        
        if include_secondary:
            keywords.extend(keywords_sugeridas.get('secundarias', []))
        
        if include_long_tail:
            keywords.extend(keywords_sugeridas.get('long_tail', []))
        
        # Limitar cantidad si se especifica
        if max_keywords and len(keywords) > max_keywords:
            keywords = keywords[:max_keywords]
        
        logger.info(f"✅ Obtenidas {len(keywords)} keywords del template '{template_name}'")
        return keywords
    
    def get_random_keywords(
        self, 
        template_name: str, 
        count: int = 10,
        include_all_types: bool = True
    ) -> List[str]:
        """
        Obtiene keywords aleatorias de un template.
        
        Args:
            template_name: Nombre del template
            count: Número de keywords a obtener
            include_all_types: Si True, incluye todos los tipos de keywords
        
        Returns:
            Lista de keywords aleatorias
        """
        all_keywords = self.get_keywords(
            template_name,
            include_primary=include_all_types,
            include_secondary=include_all_types,
            include_long_tail=include_all_types
        )
        
        if not all_keywords:
            return []
        
        # Seleccionar aleatoriamente
        count = min(count, len(all_keywords))
        random_keywords = random.sample(all_keywords, count)
        
        logger.info(f"✅ Obtenidas {len(random_keywords)} keywords aleatorias")
        return random_keywords
    
    # =========================================================================
    # MÉTODOS DE TONOS Y CTAS
    # =========================================================================
    
    def get_recommended_tones(self, template_name: str) -> List[str]:
        """
        Obtiene los tonos recomendados para un template.
        
        Args:
            template_name: Nombre del template
        
        Returns:
            Lista de tonos recomendados
        """
        template = self.get_template(template_name)
        
        if not template:
            return []
        
        return template.get('tonos_recomendados', [])
    
    def get_suggested_ctas(self, template_name: str, count: Optional[int] = None) -> List[str]:
        """
        Obtiene CTAs sugeridos de un template.
        
        Args:
            template_name: Nombre del template
            count: Número máximo de CTAs a retornar
        
        Returns:
            Lista de CTAs sugeridos
        """
        template = self.get_template(template_name)
        
        if not template:
            return []
        
        ctas = template.get('ctas_sugeridos', [])
        
        if count and len(ctas) > count:
            ctas = ctas[:count]
        
        return ctas
    
    def get_base_descriptions(self, template_name: str) -> List[str]:
        """
        Obtiene descripciones base de un template.
        
        Args:
            template_name: Nombre del template
        
        Returns:
            Lista de descripciones base
        """
        template = self.get_template(template_name)
        
        if not template:
            return []
        
        return template.get('descripciones_base', [])
    
    # =========================================================================
    # MÉTODOS DE APLICACIÓN DE TEMPLATES
    # =========================================================================
    
    def apply_template(
        self, 
        template_name: str,
        num_keywords: int = 10,
        tone: Optional[str] = None,
        custom_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Aplica un template para generar datos de entrada para el generador de anuncios.
        
        Args:
            template_name: Nombre del template a aplicar
            num_keywords: Número de keywords a usar
            tone: Tono específico (si no se proporciona, usa el primero recomendado)
            custom_keywords: Keywords personalizadas (si se proporcionan, reemplazan las del template)
        
        Returns:
            Diccionario con datos preparados para generación
        """
        template = self.get_template(template_name)
        
        if not template:
            logger.error(f"❌ No se puede aplicar template '{template_name}': no existe")
            return {}
        
        # Obtener keywords
        if custom_keywords:
            keywords = custom_keywords[:num_keywords]
        else:
            keywords = self.get_keywords(template_name, max_keywords=num_keywords)
        
        # Obtener tono
        recommended_tones = self.get_recommended_tones(template_name)
        if tone and tone in recommended_tones:
            selected_tone = tone
        elif recommended_tones:
            selected_tone = recommended_tones[0]
        else:
            selected_tone = self.global_settings.get('default_tone', 'profesional')
        
        # Obtener CTAs y descripciones base
        ctas = self.get_suggested_ctas(template_name)
        descriptions = self.get_base_descriptions(template_name)
        
        # Construir datos de aplicación
        applied_data = {
            'template_name': template_name,
            'template_display_name': template.get('name', template_name),
            'keywords': keywords,
            'tone': selected_tone,
            'recommended_tones': recommended_tones,
            'suggested_ctas': ctas,
            'base_descriptions': descriptions,
            'num_headlines': self.global_settings.get('default_num_headlines', 15),
            'num_descriptions': self.global_settings.get('default_num_descriptions', 4),
            'targeting_suggestions': template.get('targeting_suggestions', {}),
            'url_patterns': template.get('url_patterns', []),
            'applied_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Template '{template_name}' aplicado exitosamente")
        logger.info(f"   - Keywords: {len(keywords)}")
        logger.info(f"   - Tono: {selected_tone}")
        
        return applied_data
    
    def combine_templates(
        self, 
        template_names: List[str],
        num_keywords_per_template: int = 5,
        tone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Combina múltiples templates para crear un conjunto híbrido de datos.
        
        Args:
            template_names: Lista de nombres de templates a combinar
            num_keywords_per_template: Keywords a tomar de cada template
            tone: Tono específico a usar
        
        Returns:
            Diccionario con datos combinados
        """
        if not template_names:
            logger.warning("⚠️ No se proporcionaron templates para combinar")
            return {}
        
        combined_keywords = []
        combined_ctas = []
        combined_descriptions = []
        all_tones = []
        
        for template_name in template_names:
            template = self.get_template(template_name)
            
            if not template:
                logger.warning(f"⚠️ Template '{template_name}' no encontrado, omitiendo")
                continue
            
            # Combinar keywords
            keywords = self.get_keywords(template_name, max_keywords=num_keywords_per_template)
            combined_keywords.extend(keywords)
            
            # Combinar CTAs
            ctas = self.get_suggested_ctas(template_name, count=3)
            combined_ctas.extend(ctas)
            
            # Combinar descripciones
            descriptions = self.get_base_descriptions(template_name)
            combined_descriptions.extend(descriptions[:2])  # 2 de cada template
            
            # Combinar tonos
            tones = self.get_recommended_tones(template_name)
            all_tones.extend(tones)
        
        # Eliminar duplicados manteniendo orden
        combined_keywords = list(dict.fromkeys(combined_keywords))
        combined_ctas = list(dict.fromkeys(combined_ctas))
        combined_descriptions = list(dict.fromkeys(combined_descriptions))
        all_tones = list(dict.fromkeys(all_tones))
        
        # Seleccionar tono
        if tone and tone in all_tones:
            selected_tone = tone
        elif all_tones:
            selected_tone = all_tones[0]
        else:
            selected_tone = self.global_settings.get('default_tone', 'profesional')
        
        combined_data = {
            'template_name': 'combined',
            'template_display_name': f"Combinación de {len(template_names)} templates",
            'combined_templates': template_names,
            'keywords': combined_keywords,
            'tone': selected_tone,
            'recommended_tones': all_tones,
            'suggested_ctas': combined_ctas,
            'base_descriptions': combined_descriptions,
            'num_headlines': self.global_settings.get('default_num_headlines', 15),
            'num_descriptions': self.global_settings.get('default_num_descriptions', 4),
            'applied_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Combinados {len(template_names)} templates exitosamente")
        logger.info(f"   - Keywords totales: {len(combined_keywords)}")
        logger.info(f"   - CTAs totales: {len(combined_ctas)}")
        
        return combined_data
    
    # =========================================================================
    # MÉTODOS DE VARIACIONES DINÁMICAS
    # =========================================================================
    
    def get_dynamic_variations(self, variation_type: str) -> List[str]:
        """
        Obtiene variaciones dinámicas por tipo.
        
        Args:
            variation_type: Tipo de variación ('urgency_modifiers', 'quality_modifiers', 'benefit_modifiers')
        
        Returns:
            Lista de variaciones
        """
        return self.dynamic_variations.get(variation_type, [])
    
    def apply_dynamic_variation(
        self, 
        base_text: str, 
        variation_type: str,
        position: str = 'prefix'
    ) -> List[str]:
        """
        Aplica variaciones dinámicas a un texto base.
        
        Args:
            base_text: Texto base al que aplicar variaciones
            variation_type: Tipo de variación a aplicar
            position: 'prefix' o 'suffix' (dónde colocar la variación)
        
        Returns:
            Lista de textos con variaciones aplicadas
        """
        variations = self.get_dynamic_variations(variation_type)
        
        if not variations:
            return [base_text]
        
        varied_texts = []
        
        for variation in variations:
            if position == 'prefix':
                varied_text = f"{variation} {base_text}"
            else:  # suffix
                varied_text = f"{base_text} {variation}"
            
            varied_texts.append(varied_text)
        
        return varied_texts
    
    def generate_headline_variations(
        self, 
        base_headline: str,
        include_urgency: bool = True,
        include_quality: bool = True,
        max_variations: int = 5
    ) -> List[str]:
        """
        Genera variaciones de un titular base usando modificadores dinámicos.
        
        Args:
            base_headline: Titular base
            include_urgency: Incluir modificadores de urgencia
            include_quality: Incluir modificadores de calidad
            max_variations: Número máximo de variaciones
        
        Returns:
            Lista de variaciones del titular
        """
        variations = [base_headline]  # Incluir el original
        
        if include_urgency:
            urgency_variations = self.apply_dynamic_variation(
                base_headline, 
                'urgency_modifiers', 
                position='suffix'
            )
            variations.extend(urgency_variations[:2])  # Agregar 2 variaciones de urgencia
        
        if include_quality:
            quality_variations = self.apply_dynamic_variation(
                base_headline, 
                'quality_modifiers', 
                position='prefix'
            )
            variations.extend(quality_variations[:2])  # Agregar 2 variaciones de calidad
        
        # Limitar a max_variations
        variations = variations[:max_variations]
        
        logger.info(f"✅ Generadas {len(variations)} variaciones del titular")
        return variations
    
    # =========================================================================
    # MÉTODOS DE VALIDACIÓN
    # =========================================================================
    
    def validate_headline(self, headline: str) -> Tuple[bool, List[str]]:
        """
        Valida un titular contra las reglas definidas.
        
        Args:
            headline: Titular a validar
        
        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        rules = self.validation_rules.get('headlines', {})
        errors = []
        
        # Validar longitud
        max_length = rules.get('max_length', 30)
        min_length = rules.get('min_length', 10)
        
        if len(headline) > max_length:
            errors.append(f"Excede longitud máxima ({len(headline)}/{max_length} caracteres)")
        
        if len(headline) < min_length:
            errors.append(f"Por debajo de longitud mínima ({len(headline)}/{min_length} caracteres)")
        
        # Validar palabras prohibidas
        forbidden_words = rules.get('forbidden_words', [])
        headline_lower = headline.lower()
        
        for forbidden in forbidden_words:
            if forbidden.lower() in headline_lower:
                errors.append(f"Contiene palabra prohibida: '{forbidden}'")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors
    
    def validate_description(self, description: str) -> Tuple[bool, List[str]]:
        """
        Valida una descripción contra las reglas definidas.
        
        Args:
            description: Descripción a validar
        
        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        rules = self.validation_rules.get('descriptions', {})
        errors = []
        
        # Validar longitud
        max_length = rules.get('max_length', 90)
        min_length = rules.get('min_length', 30)
        
        if len(description) > max_length:
            errors.append(f"Excede longitud máxima ({len(description)}/{max_length} caracteres)")
        
        if len(description) < min_length:
            errors.append(f"Por debajo de longitud mínima ({len(description)}/{min_length} caracteres)")
        
        # Validar palabras prohibidas
        forbidden_words = rules.get('forbidden_words', [])
        description_lower = description.lower()
        
        for forbidden in forbidden_words:
            if forbidden.lower() in description_lower:
                errors.append(f"Contiene palabra prohibida: '{forbidden}'")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors
    
    def validate_ad(
        self, 
        headlines: List[str], 
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Valida un anuncio completo (todos los titulares y descripciones).
        
        Args:
            headlines: Lista de titulares
            descriptions: Lista de descripciones
        
        Returns:
            Diccionario con resultados de validación
        """
        validation_result = {
            'valid': True,
            'headlines': {},
            'descriptions': {},
            'summary': {
                'total_headlines': len(headlines),
                'valid_headlines': 0,
                'invalid_headlines': 0,
                'total_descriptions': len(descriptions),
                'valid_descriptions': 0,
                'invalid_descriptions': 0
            },
            'errors': [],
            'warnings': []
        }
        
        # Validar titulares
        for i, headline in enumerate(headlines):
            is_valid, errors = self.validate_headline(headline)
            
            validation_result['headlines'][i] = {
                'text': headline,
                'valid': is_valid,
                'errors': errors
            }
            
            if is_valid:
                validation_result['summary']['valid_headlines'] += 1
            else:
                validation_result['summary']['invalid_headlines'] += 1
                validation_result['valid'] = False
                validation_result['errors'].extend([f"Titular {i+1}: {e}" for e in errors])
        
        # Validar descripciones
        for i, description in enumerate(descriptions):
            is_valid, errors = self.validate_description(description)
            
            validation_result['descriptions'][i] = {
                'text': description,
                'valid': is_valid,
                'errors': errors
            }
            
            if is_valid:
                validation_result['summary']['valid_descriptions'] += 1
            else:
                validation_result['summary']['invalid_descriptions'] += 1
                validation_result['valid'] = False
                validation_result['errors'].extend([f"Descripción {i+1}: {e}" for e in errors])
        
        logger.info(f"✅ Validación completada")
        logger.info(f"   - Titulares válidos: {validation_result['summary']['valid_headlines']}/{len(headlines)}")
        logger.info(f"   - Descripciones válidas: {validation_result['summary']['valid_descriptions']}/{len(descriptions)}")
        
        return validation_result
    
    # =========================================================================
    # MÉTODOS DE RECOMENDACIONES
    # =========================================================================
    
    def get_template_recommendations(
        self, 
        keywords: List[str],
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recomienda templates basándose en keywords proporcionadas.
        
        Args:
            keywords: Lista de keywords del usuario
            top_n: Número de recomendaciones a retornar
        
        Returns:
            Lista de templates recomendados con scores
        """
        recommendations = []
        
        for template_name, template_data in self.templates.items():
            # Obtener todas las keywords del template
            template_keywords = self.get_keywords(template_name)
            
            # Calcular coincidencia
            matches = 0
            for user_kw in keywords:
                user_kw_lower = user_kw.lower()
                for template_kw in template_keywords:
                    if user_kw_lower in template_kw.lower() or template_kw.lower() in user_kw_lower:
                        matches += 1
                        break
            
            # Calcular score (porcentaje de coincidencia)
            score = (matches / len(keywords) * 100) if keywords else 0
            
            if score > 0:
                recommendations.append({
                    'template_name': template_name,
                    'display_name': template_data.get('name', template_name),
                    'description': template_data.get('description', ''),
                    'icon': template_data.get('icon', '🔮'),
                    'score': round(score, 2),
                    'matches': matches
                })
        
        # Ordenar por score descendente
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Retornar top N
        top_recommendations = recommendations[:top_n]
        
        logger.info(f"✅ Generadas {len(top_recommendations)} recomendaciones de templates")
        
        return top_recommendations
    
    # =========================================================================
    # MÉTODOS DE CONFIGURACIÓN
    # =========================================================================
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Obtiene la configuración global."""
        return self.global_settings
    
    def get_export_settings(self) -> Dict[str, Any]:
        """Obtiene la configuración de exportación."""
        return self.export_settings
    
    def reload_config(self) -> bool:
        """
        Recarga la configuración desde el archivo YAML.
        
        Returns:
            True si se recargó exitosamente, False en caso contrario
        """
        try:
            self._load_config()
            logger.info("✅ Configuración recargada exitosamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error recargando configuración: {e}")
            return False
    
    # =========================================================================
    # MÉTODOS DE ESTADÍSTICAS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del gestor de templates.
        
        Returns:
            Diccionario con estadísticas
        """
        total_keywords = sum(
            len(self.get_keywords(template_name)) 
            for template_name in self.get_template_names()
        )
        
        total_ctas = sum(
            len(self.get_suggested_ctas(template_name)) 
            for template_name in self.get_template_names()
        )
        
        stats = {
            'total_templates': len(self.templates),
            'template_names': self.get_template_names(),
            'total_keywords': total_keywords,
            'total_ctas': total_ctas,
            'dynamic_variation_types': len(self.dynamic_variations),
            'config_path': self.config_path,
            'last_loaded': datetime.now().isoformat()
        }
        
        return stats


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_template_manager(config_path: Optional[str] = None) -> TemplateManager:
    """
    Factory function para crear una instancia de TemplateManager.
    
    Args:
        config_path: Ruta opcional al archivo de configuración
    
    Returns:
        Instancia de TemplateManager
    """
    return TemplateManager(config_path)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Crear instancia del gestor
    manager = TemplateManager()
    
    # Obtener todos los templates
    print("\n" + "="*60)
    print("📋 TEMPLATES DISPONIBLES")
    print("="*60)
    
    templates_info = manager.get_all_templates_info()
    for info in templates_info:
        print(f"\n{info['icon']} {info['name']}")
        print(f"   Key: {info['key']}")
        print(f"   Descripción: {info['description']}")
    
    # Aplicar un template
    print("\n" + "="*60)
    print("🎯 APLICANDO TEMPLATE: brujeria_pareja")
    print("="*60)
    
    applied = manager.apply_template('brujeria_pareja', num_keywords=10, tone='emocional')
    
    print(f"\n✅ Template aplicado: {applied['template_display_name']}")
    print(f"   Keywords ({len(applied['keywords'])}):")
    for kw in applied['keywords'][:5]:
        print(f"      - {kw}")
    print(f"   Tono: {applied['tone']}")
    print(f"   CTAs sugeridos: {len(applied['suggested_ctas'])}")
    
    # Validar un anuncio
    print("\n" + "="*60)
    print("✅ VALIDACIÓN DE ANUNCIO")
    print("="*60)
    
    test_headlines = [
        "Amarres de Amor Efectivos",
        "Recupera a Tu Pareja Ya",
        "ESTE ES UN TITULO DEMASIADO LARGO QUE EXCEDE EL LIMITE PERMITIDO"
    ]
    
    test_descriptions = [
        "Amarres de amor con resultados garantizados en 24 horas",
        "Desc corta"
    ]
    
    validation = manager.validate_ad(test_headlines, test_descriptions)
    
    print(f"\n¿Válido?: {validation['valid']}")
    print(f"Titulares válidos: {validation['summary']['valid_headlines']}/{validation['summary']['total_headlines']}")
    print(f"Descripciones válidas: {validation['summary']['valid_descriptions']}/{validation['summary']['total_descriptions']}")
    
    if validation['errors']:
        print("\n⚠️ Errores encontrados:")
        for error in validation['errors']:
            print(f"   - {error}")
    
    # Obtener estadísticas
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS")
    print("="*60)
    
    stats = manager.get_statistics()
    print(f"\n✅ Total de templates: {stats['total_templates']}")
    print(f"✅ Total de keywords: {stats['total_keywords']}")
    print(f"✅ Total de CTAs: {stats['total_ctas']}")
    print(f"✅ Tipos de variaciones: {stats['dynamic_variation_types']}")