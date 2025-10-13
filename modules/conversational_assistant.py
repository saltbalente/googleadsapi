"""
🤖 CONVERSATIONAL ASSISTANT - Asistente Conversacional para Anuncios
Sistema de chat inteligente para refinar y mejorar anuncios mediante conversación natural
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from collections import deque

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationalAssistant:
    """
    Asistente conversacional que proporciona:
    - Chat interactivo para refinar anuncios
    - Comandos naturales en español
    - Contexto de conversación
    - Historial de cambios
    - Sugerencias inteligentes
    - Regeneración con IA
    - Análisis de intención
    - Respuestas contextuales
    """
    
    # =========================================================================
    # PATRONES DE COMANDOS
    # =========================================================================
    
    COMMAND_PATTERNS = {
        # Modificadores de tono
        'more_urgent': [
            r'(?:hazlo|haz|pon|hazme|ponlo)\s+(?:más\s+)?urgente',
            r'añade\s+urgencia',
            r'más\s+urgencia',
            r'urgente'
        ],
        'more_emotional': [
            r'(?:hazlo|haz|pon|hazme|ponlo)\s+(?:más\s+)?emocional',
            r'añade\s+emoción',
            r'más\s+emoción',
            r'emocional'
        ],
        'more_professional': [
            r'(?:hazlo|haz|pon|hazme|ponlo)\s+(?:más\s+)?profesional',
            r'más\s+formal',
            r'profesional',
            r'formal'
        ],
        'more_powerful': [
            r'(?:hazlo|haz|pon|hazme|ponlo)\s+(?:más\s+)?poderoso',
            r'más\s+impactante',
            r'poderoso',
            r'impactante'
        ],
        
        # Modificadores de longitud
        'make_shorter': [
            r'(?:hazlo|haz|pon|hazme|ponlo)\s+(?:más\s+)?corto',
            r'acorta(?:lo)?',
            r'más\s+corto',
            r'reduce\s+(?:la\s+)?longitud'
        ],
        'make_longer': [
            r'(?:hazlo|haz|pon|hazme|ponlo)\s+(?:más\s+)?largo',
            r'alarga(?:lo)?',
            r'más\s+largo',
            r'añade\s+(?:más\s+)?(?:texto|contenido|palabras)'
        ],
        
        # Modificadores de contenido
        'add_benefits': [
            r'agrega\s+beneficios?',
            r'añade\s+beneficios?',
            r'incluye\s+beneficios?',
            r'menciona\s+beneficios?',
            r'beneficios?'
        ],
        'add_cta': [
            r'agrega\s+(?:un\s+)?(?:cta|llamada?\s+a\s+la\s+acción)',
            r'añade\s+(?:un\s+)?(?:cta|llamada?\s+a\s+la\s+acción)',
            r'incluye\s+(?:un\s+)?(?:cta|llamada?\s+a\s+la\s+acción)',
            r'pon\s+(?:un\s+)?(?:cta|llamada?\s+a\s+la\s+acción)'
        ],
        'add_numbers': [
            r'agrega\s+números?',
            r'añade\s+números?',
            r'incluye\s+números?',
            r'pon\s+números?'
        ],
        'add_keywords': [
            r'agrega\s+(?:las\s+)?keywords?',
            r'añade\s+(?:las\s+)?palabras?\s+clave',
            r'incluye\s+(?:más\s+)?keywords?',
            r'usa\s+(?:más\s+)?keywords?'
        ],
        
        # Acciones específicas
        'remove_word': [
            r'elimina\s+(?:la\s+palabra\s+)?["\']?(\w+)["\']?',
            r'quita\s+(?:la\s+palabra\s+)?["\']?(\w+)["\']?',
            r'remueve\s+(?:la\s+palabra\s+)?["\']?(\w+)["\']?'
        ],
        'replace_word': [
            r'reemplaza\s+["\']?(\w+)["\']?\s+(?:con|por)\s+["\']?(\w+)["\']?',
            r'cambia\s+["\']?(\w+)["\']?\s+(?:con|por)\s+["\']?(\w+)["\']?',
            r'sustituye\s+["\']?(\w+)["\']?\s+(?:con|por)\s+["\']?(\w+)["\']?'
        ],
        
        # Regeneración
        'regenerate': [
            r'regener[aá](?:lo)?',
            r'genera\s+(?:de\s+)?nuevo',
            r'crea\s+(?:otro|nueva?\s+versión)',
            r'otra?\s+(?:versión|opción)'
        ],
        'regenerate_all': [
            r'regener[aá]\s+todo',
            r'genera\s+todo\s+(?:de\s+)?nuevo',
            r'empieza\s+de\s+nuevo'
        ],
        
        # Consultas
        'show_changes': [
            r'(?:mu[ée]strame|ver|mostrar)\s+(?:los\s+)?cambios',
            r'qu[ée]\s+(?:ha\s+)?cambiado',
            r'historial'
        ],
        'show_stats': [
            r'(?:mu[ée]strame|ver|mostrar)\s+(?:las\s+)?estad[ií]sticas',
            r'(?:mu[ée]strame|ver|mostrar)\s+m[ée]tricas',
            r'estad[ií]sticas',
            r'an[aá]lisis'
        ],
        'help': [
            r'ayuda',
            r'qu[ée]\s+puedo\s+(?:hacer|decir)',
            r'comandos',
            r'opciones'
        ]
    }
    
    # Tonos disponibles
    AVAILABLE_TONES = {
        'urgente': 'Tono urgente con llamados a la acción inmediatos',
        'emocional': 'Tono emotivo que conecta con sentimientos',
        'profesional': 'Tono formal y confiable',
        'poderoso': 'Tono impactante y persuasivo',
        'místico': 'Tono misterioso y espiritual',
        'esperanzador': 'Tono positivo y optimista',
        'tranquilizador': 'Tono calmado y reconfortante'
    }
    
    # Palabras para modificar contenido
    URGENCY_WORDS = ['ahora', 'ya', 'hoy', 'inmediato', 'urgente', 'rápido']
    BENEFIT_WORDS = ['garantizado', 'efectivo', 'resultado', 'éxito', 'profesional']
    CTA_PHRASES = ['Consulta ahora', 'Solicita ya', 'Contacta hoy', 'Pide información', 'Llama ya']
    
    def __init__(
        self,
        ai_generator=None,
        max_history: int = 50,
        context_window: int = 5
    ):
        """
        Inicializa el asistente conversacional.
        
        Args:
            ai_generator: Generador de IA para regeneración
            max_history: Máximo de mensajes en historial
            context_window: Ventana de contexto para decisiones
        """
        self.ai_generator = ai_generator
        self.max_history = max_history
        self.context_window = context_window
        
        # Estado de la conversación
        self.conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history: deque = deque(maxlen=max_history)
        self.current_ad: Optional[Dict[str, Any]] = None
        self.change_history: List[Dict[str, Any]] = []
        
        # Estadísticas
        self.stats = {
            'total_messages': 0,
            'commands_executed': 0,
            'regenerations': 0,
            'successful_changes': 0
        }
        
        logger.info(f"✅ ConversationalAssistant inicializado")
        logger.info(f"   - Conversation ID: {self.conversation_id}")
    
    # =========================================================================
    # INICIALIZACIÓN DE CONVERSACIÓN
    # =========================================================================
    
    def start_conversation(
        self,
        initial_ad: Dict[str, Any],
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Inicia una nueva conversación con un anuncio.
        
        Args:
            initial_ad: Anuncio inicial (headlines, descriptions)
            keywords: Keywords opcionales para contexto
        
        Returns:
            Mensaje de bienvenida
        """
        self.current_ad = {
            'headlines': initial_ad.get('headlines', []),
            'descriptions': initial_ad.get('descriptions', []),
            'keywords': keywords or [],
            'tone': initial_ad.get('tone', 'profesional'),
            'version': 1,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
        
        # Mensaje de bienvenida
        welcome_message = self._create_message(
            role='assistant',
            content=self._generate_welcome_message(),
            metadata={'type': 'welcome'}
        )
        
        self.conversation_history.append(welcome_message)
        
        logger.info(f"🎬 Conversación iniciada: {self.conversation_id}")
        
        return welcome_message
    
    def _generate_welcome_message(self) -> str:
        """Genera mensaje de bienvenida personalizado."""
        ad_preview = self._get_ad_preview()
        
        message = f"""¡Hola! 👋 Soy tu asistente para optimizar anuncios.

📊 **Anuncio actual:**
{ad_preview}

💡 **¿Cómo te puedo ayudar?**

Puedes pedirme cosas como:
• "Hazlo más urgente"
• "Agrega beneficios"
• "Acórtalo"
• "Añade una llamada a la acción"
• "Reemplaza 'garantizado' por 'efectivo'"
• "Regenera todo"

¿Qué te gustaría cambiar?"""
        
        return message
    
    # =========================================================================
    # PROCESAMIENTO DE MENSAJES
    # =========================================================================
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y ejecuta acciones.
        
        Args:
            user_message: Mensaje del usuario
        
        Returns:
            Respuesta del asistente con cambios aplicados
        """
        if not self.current_ad:
            return self._create_error_message(
                "No hay anuncio activo. Inicia una conversación primero."
            )
        
        # Agregar mensaje del usuario al historial
        user_msg = self._create_message(
            role='user',
            content=user_message
        )
        self.conversation_history.append(user_msg)
        self.stats['total_messages'] += 1
        
        logger.info(f"💬 Mensaje del usuario: {user_message[:50]}...")
        
        # Analizar intención
        intent = self._analyze_intent(user_message)
        
        logger.info(f"🎯 Intención detectada: {intent['type']}")
        
        # Ejecutar acción según intención
        response = self._execute_intent(intent, user_message)
        
        # Agregar respuesta al historial
        self.conversation_history.append(response)
        
        return response
    
    # =========================================================================
    # ANÁLISIS DE INTENCIÓN
    # =========================================================================
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """
        Analiza la intención del mensaje del usuario.
        
        Args:
            message: Mensaje a analizar
        
        Returns:
            Diccionario con tipo de intención y parámetros
        """
        message_lower = message.lower().strip()
        
        # Buscar coincidencias con patrones
        for intent_type, patterns in self.COMMAND_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    # Extraer parámetros del match
                    params = list(match.groups()) if match.groups() else []
                    
                    return {
                        'type': intent_type,
                        'confidence': 0.9,
                        'params': params,
                        'original_message': message
                    }
        
        # Si no coincide con ningún patrón, intención genérica
        return {
            'type': 'general_request',
            'confidence': 0.5,
            'params': [],
            'original_message': message
        }
    
    # =========================================================================
    # EJECUCIÓN DE INTENCIONES
    # =========================================================================
    
    def _execute_intent(
        self,
        intent: Dict[str, Any],
        original_message: str
    ) -> Dict[str, Any]:
        """
        Ejecuta la acción correspondiente a la intención.
        
        Args:
            intent: Intención detectada
            original_message: Mensaje original
        
        Returns:
            Respuesta del asistente
        """
        intent_type = intent['type']
        params = intent['params']
        
        try:
            # Mapeo de intenciones a métodos
            intent_handlers = {
                'more_urgent': lambda: self._apply_tone_change('urgente'),
                'more_emotional': lambda: self._apply_tone_change('emocional'),
                'more_professional': lambda: self._apply_tone_change('profesional'),
                'more_powerful': lambda: self._apply_tone_change('poderoso'),
                'make_shorter': lambda: self._make_shorter(),
                'make_longer': lambda: self._make_longer(),
                'add_benefits': lambda: self._add_benefits(),
                'add_cta': lambda: self._add_cta(),
                'add_numbers': lambda: self._add_numbers(),
                'add_keywords': lambda: self._add_keywords(),
                'remove_word': lambda: self._remove_word(params[0]) if params else self._create_error_message("¿Qué palabra quieres eliminar?"),
                'replace_word': lambda: self._replace_word(params[0], params[1]) if len(params) >= 2 else self._create_error_message("Usa formato: reemplaza 'palabra1' por 'palabra2'"),
                'regenerate': lambda: self._regenerate(),
                'regenerate_all': lambda: self._regenerate_all(),
                'show_changes': lambda: self._show_changes(),
                'show_stats': lambda: self._show_stats(),
                'help': lambda: self._show_help(),
                'general_request': lambda: self._handle_general_request(original_message)
            }
            
            # Ejecutar handler
            handler = intent_handlers.get(intent_type)
            
            if handler:
                response = handler()
                self.stats['commands_executed'] += 1
                return response
            else:
                return self._create_error_message(
                    f"No sé cómo procesar '{original_message}'. Escribe 'ayuda' para ver comandos."
                )
        
        except Exception as e:
            logger.error(f"❌ Error ejecutando intención {intent_type}: {e}")
            return self._create_error_message(
                f"Ocurrió un error: {str(e)}. Intenta de nuevo."
            )
    
    # =========================================================================
    # APLICACIÓN DE CAMBIOS
    # =========================================================================
    
    def _apply_tone_change(self, new_tone: str) -> Dict[str, Any]:
        """Cambia el tono del anuncio."""
        old_tone = self.current_ad['tone']
        self.current_ad['tone'] = new_tone
        
        # Registrar cambio
        self._record_change(
            change_type='tone_change',
            description=f"Tono cambiado de '{old_tone}' a '{new_tone}'",
            before={'tone': old_tone},
            after={'tone': new_tone}
        )
        
        # Si hay IA, regenerar con nuevo tono
        if self.ai_generator:
            regenerate_result = self._regenerate_with_tone(new_tone)
            
            if regenerate_result['success']:
                return self._create_success_message(
                    f"✅ Tono cambiado a **{new_tone}**. He regenerado el anuncio:\n\n{self._get_ad_preview()}\n\n¿Algo más que quieras cambiar?"
                )
        
        # Sin IA, solo cambiar el tono
        return self._create_success_message(
            f"✅ Tono establecido en **{new_tone}**.\n\n💡 Conecta un proveedor de IA para regenerar automáticamente el contenido.\n\n¿Qué más quieres cambiar?"
        )
    
    def _make_shorter(self) -> Dict[str, Any]:
        """Acorta los textos del anuncio."""
        changes_made = 0
        
        # Acortar headlines (quitar últimas palabras)
        for i, headline in enumerate(self.current_ad['headlines']):
            if len(headline) > 20:
                words = headline.split()
                if len(words) > 3:
                    shortened = ' '.join(words[:-1])
                    self.current_ad['headlines'][i] = shortened
                    changes_made += 1
        
        # Acortar descriptions
        for i, desc in enumerate(self.current_ad['descriptions']):
            if len(desc) > 60:
                # Truncar en punto o coma
                if '.' in desc:
                    shortened = desc.split('.')[0] + '.'
                elif ',' in desc:
                    shortened = desc.split(',')[0]
                else:
                    shortened = desc[:60].rsplit(' ', 1)[0]
                
                self.current_ad['descriptions'][i] = shortened
                changes_made += 1
        
        self._record_change(
            change_type='make_shorter',
            description=f"Acortados {changes_made} elementos"
        )
        
        if changes_made > 0:
            return self._create_success_message(
                f"✅ Anuncio acortado ({changes_made} cambios):\n\n{self._get_ad_preview()}\n\n¿Algo más?"
            )
        else:
            return self._create_info_message(
                "ℹ️ El anuncio ya está bastante corto. ¿Quieres hacer otra modificación?"
            )
    
    def _make_longer(self) -> Dict[str, Any]:
        """Alarga los textos del anuncio."""
        changes_made = 0
        
        # Alargar headlines (agregar palabras de poder)
        for i, headline in enumerate(self.current_ad['headlines']):
            if len(headline) < 25:
                # Agregar palabra de beneficio
                power_word = self.BENEFIT_WORDS[i % len(self.BENEFIT_WORDS)]
                if power_word.lower() not in headline.lower():
                    self.current_ad['headlines'][i] = f"{headline} {power_word.capitalize()}"
                    changes_made += 1
        
        # Alargar descriptions (agregar frases)
        for i, desc in enumerate(self.current_ad['descriptions']):
            if len(desc) < 70 and not desc.endswith('.'):
                extension = " Consulta disponible."
                if len(desc + extension) <= 90:
                    self.current_ad['descriptions'][i] = desc + extension
                    changes_made += 1
        
        self._record_change(
            change_type='make_longer',
            description=f"Alargados {changes_made} elementos"
        )
        
        if changes_made > 0:
            return self._create_success_message(
                f"✅ Anuncio ampliado ({changes_made} cambios):\n\n{self._get_ad_preview()}\n\n¿Algo más?"
            )
        else:
            return self._create_info_message(
                "ℹ️ Los textos ya están bastante completos. ¿Otra cosa?"
            )
    
    def _add_benefits(self) -> Dict[str, Any]:
        """Agrega palabras de beneficios al anuncio."""
        changes_made = 0
        
        # Agregar a headlines
        for i in range(min(3, len(self.current_ad['headlines']))):
            headline = self.current_ad['headlines'][i]
            benefit = self.BENEFIT_WORDS[i % len(self.BENEFIT_WORDS)]
            
            if benefit.lower() not in headline.lower() and len(headline) < 25:
                self.current_ad['headlines'][i] = f"{headline} {benefit.capitalize()}"
                changes_made += 1
        
        self._record_change(
            change_type='add_benefits',
            description=f"Agregados {changes_made} beneficios"
        )
        
        return self._create_success_message(
            f"✅ Beneficios agregados ({changes_made} cambios):\n\n{self._get_ad_preview()}\n\n¿Qué más?"
        )
    
    def _add_cta(self) -> Dict[str, Any]:
        """Agrega llamadas a la acción."""
        changes_made = 0
        
        # Agregar CTA a descriptions
        for i, desc in enumerate(self.current_ad['descriptions']):
            # Verificar si ya tiene CTA
            has_cta = any(
                word in desc.lower() 
                for word in ['consulta', 'solicita', 'contacta', 'llama', 'pide']
            )
            
            if not has_cta and len(desc) < 75:
                cta = self.CTA_PHRASES[i % len(self.CTA_PHRASES)]
                if len(desc + ' ' + cta) <= 90:
                    self.current_ad['descriptions'][i] = f"{desc} {cta}."
                    changes_made += 1
        
        self._record_change(
            change_type='add_cta',
            description=f"Agregados {changes_made} CTAs"
        )
        
        return self._create_success_message(
            f"✅ Llamadas a la acción agregadas ({changes_made}):\n\n{self._get_ad_preview()}\n\n¿Algo más?"
        )
    
    def _add_numbers(self) -> Dict[str, Any]:
        """Agrega números al anuncio."""
        changes_made = 0
        numbers_to_add = ['24h', '100%', '7 días', '48 horas']
        
        for i in range(min(2, len(self.current_ad['headlines']))):
            headline = self.current_ad['headlines'][i]
            
            if not any(char.isdigit() for char in headline) and len(headline) < 25:
                number = numbers_to_add[i % len(numbers_to_add)]
                self.current_ad['headlines'][i] = f"{headline} {number}"
                changes_made += 1
        
        self._record_change(
            change_type='add_numbers',
            description=f"Agregados {changes_made} números"
        )
        
        return self._create_success_message(
            f"✅ Números agregados ({changes_made}):\n\n{self._get_ad_preview()}\n\n¿Qué más?"
        )
    
    def _add_keywords(self) -> Dict[str, Any]:
        """Agrega keywords al anuncio."""
        if not self.current_ad.get('keywords'):
            return self._create_info_message(
                "ℹ️ No tengo keywords para agregar. ¿Puedes proporcionarme algunas?"
            )
        
        changes_made = 0
        keywords = self.current_ad['keywords']
        
        # Agregar keywords que falten en headlines
        for i in range(min(3, len(self.current_ad['headlines']))):
            headline = self.current_ad['headlines'][i]
            
            for keyword in keywords[:3]:
                if keyword.lower() not in headline.lower() and len(headline) < 25:
                    # Capitalizar primera letra
                    kw_capitalized = keyword.capitalize()
                    self.current_ad['headlines'][i] = f"{headline} {kw_capitalized}"
                    changes_made += 1
                    break
        
        self._record_change(
            change_type='add_keywords',
            description=f"Agregadas {changes_made} keywords"
        )
        
        return self._create_success_message(
            f"✅ Keywords agregadas ({changes_made}):\n\n{self._get_ad_preview()}\n\n¿Algo más?"
        )
    
    def _remove_word(self, word: str) -> Dict[str, Any]:
        """Elimina una palabra del anuncio."""
        changes_made = 0
        word_lower = word.lower()
        
        # Eliminar de headlines
        for i, headline in enumerate(self.current_ad['headlines']):
            if word_lower in headline.lower():
                # Eliminar palabra (case-insensitive)
                new_headline = re.sub(
                    rf'\b{re.escape(word)}\b',
                    '',
                    headline,
                    flags=re.IGNORECASE
                )
                # Limpiar espacios múltiples
                new_headline = ' '.join(new_headline.split())
                self.current_ad['headlines'][i] = new_headline
                changes_made += 1
        
        # Eliminar de descriptions
        for i, desc in enumerate(self.current_ad['descriptions']):
            if word_lower in desc.lower():
                new_desc = re.sub(
                    rf'\b{re.escape(word)}\b',
                    '',
                    desc,
                    flags=re.IGNORECASE
                )
                new_desc = ' '.join(new_desc.split())
                self.current_ad['descriptions'][i] = new_desc
                changes_made += 1
        
        self._record_change(
            change_type='remove_word',
            description=f"Eliminada palabra '{word}' ({changes_made} veces)"
        )
        
        if changes_made > 0:
            return self._create_success_message(
                f"✅ Palabra '{word}' eliminada ({changes_made} veces):\n\n{self._get_ad_preview()}\n\n¿Algo más?"
            )
        else:
            return self._create_info_message(
                f"ℹ️ No encontré la palabra '{word}' en el anuncio. ¿Otra cosa?"
            )
    
    def _replace_word(self, old_word: str, new_word: str) -> Dict[str, Any]:
        """Reemplaza una palabra por otra."""
        changes_made = 0
        
        # Reemplazar en headlines
        for i, headline in enumerate(self.current_ad['headlines']):
            if old_word.lower() in headline.lower():
                new_headline = re.sub(
                    rf'\b{re.escape(old_word)}\b',
                    new_word,
                    headline,
                    flags=re.IGNORECASE
                )
                self.current_ad['headlines'][i] = new_headline
                changes_made += 1
        
        # Reemplazar en descriptions
        for i, desc in enumerate(self.current_ad['descriptions']):
            if old_word.lower() in desc.lower():
                new_desc = re.sub(
                    rf'\b{re.escape(old_word)}\b',
                    new_word,
                    desc,
                    flags=re.IGNORECASE
                )
                self.current_ad['descriptions'][i] = new_desc
                changes_made += 1
        
        self._record_change(
            change_type='replace_word',
            description=f"Reemplazada '{old_word}' por '{new_word}' ({changes_made} veces)"
        )
        
        if changes_made > 0:
            return self._create_success_message(
                f"✅ '{old_word}' → '{new_word}' ({changes_made} cambios):\n\n{self._get_ad_preview()}\n\n¿Algo más?"
            )
        else:
            return self._create_info_message(
                f"ℹ️ No encontré '{old_word}' en el anuncio. ¿Otra cosa?"
            )
    
    # =========================================================================
    # REGENERACIÓN CON IA
    # =========================================================================
    
    def _regenerate(self) -> Dict[str, Any]:
        """Regenera el anuncio actual."""
        if not self.ai_generator:
            return self._create_info_message(
                "ℹ️ Necesitas conectar un proveedor de IA para regenerar. ¿Puedo ayudarte de otra forma?"
            )
        
        try:
            # Regenerar con configuración actual
            generated = self.ai_generator.generate_ad(
                keywords=self.current_ad.get('keywords', []),
                num_ads=1,
                num_headlines=len(self.current_ad['headlines']),
                num_descriptions=len(self.current_ad['descriptions']),
                tone=self.current_ad['tone'],
                user='saltbalente',
                validate=True
            )
            
            if generated and len(generated) > 0:
                new_ad = generated[0]
                
                # Actualizar anuncio actual
                self.current_ad['headlines'] = new_ad.get('headlines', [])
                self.current_ad['descriptions'] = new_ad.get('descriptions', [])
                self.current_ad['version'] += 1
                
                self._record_change(
                    change_type='regenerate',
                    description=f"Regenerado con IA (versión {self.current_ad['version']})"
                )
                
                self.stats['regenerations'] += 1
                
                return self._create_success_message(
                    f"✅ Anuncio regenerado con IA:\n\n{self._get_ad_preview()}\n\n¿Te gusta o quieres más cambios?"
                )
            else:
                return self._create_error_message(
                    "❌ No pude regenerar el anuncio. Intenta de nuevo."
                )
        
        except Exception as e:
            logger.error(f"Error regenerando: {e}")
            return self._create_error_message(
                f"❌ Error al regenerar: {str(e)}"
            )
    
    def _regenerate_all(self) -> Dict[str, Any]:
        """Regenera todo el anuncio desde cero."""
        # Simplemente llamar a regenerate
        return self._regenerate()
    
    def _regenerate_with_tone(self, tone: str) -> Dict[str, bool]:
        """Regenera con un tono específico."""
        if not self.ai_generator:
            return {'success': False}
        
        try:
            generated = self.ai_generator.generate_ad(
                keywords=self.current_ad.get('keywords', []),
                num_ads=1,
                num_headlines=len(self.current_ad['headlines']),
                num_descriptions=len(self.current_ad['descriptions']),
                tone=tone,
                user='saltbalente',
                validate=True
            )
            
            if generated and len(generated) > 0:
                new_ad = generated[0]
                self.current_ad['headlines'] = new_ad.get('headlines', [])
                self.current_ad['descriptions'] = new_ad.get('descriptions', [])
                self.current_ad['version'] += 1
                self.stats['regenerations'] += 1
                return {'success': True}
            
            return {'success': False}
        
        except Exception as e:
            logger.error(f"Error regenerando con tono: {e}")
            return {'success': False}
    
    # =========================================================================
    # CONSULTAS
    # =========================================================================
    
    def _show_changes(self) -> Dict[str, Any]:
        """Muestra historial de cambios."""
        if not self.change_history:
            return self._create_info_message(
                "ℹ️ Aún no has hecho cambios. ¿Qué te gustaría modificar?"
            )
        
        changes_text = "📜 **Historial de cambios:**\n\n"
        
        for i, change in enumerate(self.change_history[-10:], 1):
            timestamp = change['timestamp']
            description = change['description']
            changes_text += f"{i}. {description} ({timestamp})\n"
        
        changes_text += f"\n**Total de cambios:** {len(self.change_history)}\n"
        changes_text += f"**Versión actual:** {self.current_ad['version']}\n\n"
        changes_text += "¿Quieres hacer más cambios?"
        
        return self._create_info_message(changes_text)
    
    def _show_stats(self) -> Dict[str, Any]:
        """Muestra estadísticas de la conversación."""
        stats_text = f"""📊 **Estadísticas de la conversación:**

• **Mensajes totales:** {self.stats['total_messages']}
• **Comandos ejecutados:** {self.stats['commands_executed']}
• **Regeneraciones:** {self.stats['regenerations']}
• **Cambios exitosos:** {self.stats['successful_changes']}
• **Versión del anuncio:** {self.current_ad['version']}

🎯 **Anuncio actual:**
• **Tono:** {self.current_ad['tone']}
• **Headlines:** {len(self.current_ad['headlines'])}
• **Descriptions:** {len(self.current_ad['descriptions'])}
• **Keywords:** {len(self.current_ad.get('keywords', []))}

¿Algo más en lo que pueda ayudarte?"""
        
        return self._create_info_message(stats_text)
    
    def _show_help(self) -> Dict[str, Any]:
        """Muestra ayuda con comandos disponibles."""
        help_text = """📚 **Comandos disponibles:**

🎨 **Cambiar tono:**
• "Hazlo más urgente"
• "Hazlo más emocional"
• "Hazlo más profesional"
• "Hazlo más poderoso"

✂️ **Modificar longitud:**
• "Acórtalo" / "Hazlo más corto"
• "Alágalo" / "Hazlo más largo"

➕ **Agregar contenido:**
• "Agrega beneficios"
• "Añade una llamada a la acción"
• "Incluye números"
• "Usa más keywords"

✏️ **Editar texto:**
• "Elimina 'palabra'"
• "Reemplaza 'palabra1' por 'palabra2'"

🔄 **Regenerar:**
• "Regenera" (regenerar actual)
• "Genera todo de nuevo" (desde cero)

📊 **Consultas:**
• "Muéstrame los cambios"
• "Estadísticas"
• "Ayuda"

¿Qué quieres hacer?"""
        
        return self._create_info_message(help_text)
    
    def _handle_general_request(self, message: str) -> Dict[str, Any]:
        """Maneja solicitudes generales sin patrón específico."""
        # Intentar interpretar el mensaje
        message_lower = message.lower()
        
        # Buscar palabras clave
        if any(word in message_lower for word in ['mejor', 'optimiza', 'mejora']):
            return self._create_info_message(
                "💡 Puedo mejorar el anuncio de varias formas:\n\n• Cambiar el tono\n• Agregar beneficios\n• Incluir CTAs\n• Regenerar con IA\n\n¿Qué prefieres?"
            )
        
        if any(word in message_lower for word in ['qué', 'como', 'puedo']):
            return self._show_help()
        
        # Respuesta genérica
        return self._create_info_message(
            f"🤔 Entiendo que quieres: \"{message}\"\n\nPero no estoy seguro de cómo ayudarte. Escribe 'ayuda' para ver los comandos disponibles."
        )
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _get_ad_preview(self, max_items: int = 3) -> str:
        """Genera preview del anuncio actual."""
        preview = "**📝 Headlines:**\n"
        for i, h in enumerate(self.current_ad['headlines'][:max_items], 1):
            preview += f"{i}. {h}\n"
        
        if len(self.current_ad['headlines']) > max_items:
            preview += f"   ... y {len(self.current_ad['headlines']) - max_items} más\n"
        
        preview += "\n**📄 Descriptions:**\n"
        for i, d in enumerate(self.current_ad['descriptions'][:max_items], 1):
            preview += f"{i}. {d}\n"
        
        if len(self.current_ad['descriptions']) > max_items:
            preview += f"   ... y {len(self.current_ad['descriptions']) - max_items} más\n"
        
        return preview
    
    def _record_change(
        self,
        change_type: str,
        description: str,
        before: Optional[Dict] = None,
        after: Optional[Dict] = None
    ) -> None:
        """Registra un cambio en el historial."""
        change = {
            'type': change_type,
            'description': description,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'version': self.current_ad['version'],
            'before': before,
            'after': after
        }
        
        self.change_history.append(change)
        self.stats['successful_changes'] += 1
        self.current_ad['last_modified'] = datetime.now().isoformat()
    
    def _create_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Crea un mensaje estructurado."""
        return {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
    
    def _create_success_message(self, content: str) -> Dict[str, Any]:
        """Crea mensaje de éxito."""
        return self._create_message(
            role='assistant',
            content=content,
            metadata={'type': 'success'}
        )
    
    def _create_error_message(self, content: str) -> Dict[str, Any]:
        """Crea mensaje de error."""
        return self._create_message(
            role='assistant',
            content=f"❌ {content}",
            metadata={'type': 'error'}
        )
    
    def _create_info_message(self, content: str) -> Dict[str, Any]:
        """Crea mensaje informativo."""
        return self._create_message(
            role='assistant',
            content=content,
            metadata={'type': 'info'}
        )
    
    def get_current_ad(self) -> Dict[str, Any]:
        """Obtiene el anuncio actual."""
        return self.current_ad
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtiene historial de conversación."""
        history = list(self.conversation_history)
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas."""
        return {
            **self.stats,
            'conversation_id': self.conversation_id,
            'ad_version': self.current_ad['version'] if self.current_ad else 0,
            'total_changes': len(self.change_history)
        }
    
    def export_conversation(self, format: str = 'json') -> str:
        """Exporta la conversación."""
        data = {
            'conversation_id': self.conversation_id,
            'history': list(self.conversation_history),
            'current_ad': self.current_ad,
            'changes': self.change_history,
            'stats': self.stats
        }
        
        if format == 'json':
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        return str(data)


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_conversational_assistant(
    ai_generator=None,
    max_history: int = 50
) -> ConversationalAssistant:
    """
    Factory function para crear asistente.
    
    Args:
        ai_generator: Generador de IA
        max_history: Historial máximo
    
    Returns:
        Instancia de ConversationalAssistant
    """
    return ConversationalAssistant(
        ai_generator=ai_generator,
        max_history=max_history
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🤖 CONVERSATIONAL ASSISTANT - Ejemplo de Uso")
    print("="*60)
    
    # Crear asistente
    assistant = ConversationalAssistant()
    
    # Anuncio inicial
    initial_ad = {
        'headlines': [
            'Amarres de Amor Profesionales',
            'Recupera a Tu Pareja',
            'Brujería Efectiva'
        ],
        'descriptions': [
            'Amarres de amor con resultados garantizados.',
            'Bruja profesional con experiencia.'
        ],
        'tone': 'profesional'
    }
    
    keywords = ['amarres de amor', 'hechizos', 'brujería']
    
    # Iniciar conversación
    print("\n🎬 Iniciando conversación...")
    welcome = assistant.start_conversation(initial_ad, keywords)
    print(f"\n{welcome['content']}")
    
    # Simular conversación
    test_messages = [
        "Hazlo más urgente",
        "Agrega beneficios",
        "Acórtalo un poco",
        "Reemplaza 'profesional' por 'experto'",
        "Muéstrame los cambios",
        "Estadísticas"
    ]
    
    for msg in test_messages:
        print("\n" + "-"*60)
        print(f"👤 Usuario: {msg}")
        
        response = assistant.process_message(msg)
        print(f"\n🤖 Asistente:\n{response['content']}")
        
        time.sleep(0.5)
    
    # Estadísticas finales
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS FINALES")
    print("="*60)
    
    stats = assistant.get_statistics()
    print(f"\n✅ Conversación ID: {stats['conversation_id']}")
    print(f"✅ Mensajes: {stats['total_messages']}")
    print(f"✅ Comandos ejecutados: {stats['commands_executed']}")
    print(f"✅ Cambios realizados: {stats['successful_changes']}")
    print(f"✅ Versión del anuncio: {stats['ad_version']}")
    
    print("\n" + "="*60)