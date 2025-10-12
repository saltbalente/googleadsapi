"""
Sistema i18n Robusto con Soporte de Fallback y Variables
"""

import json
import streamlit as st
from pathlib import Path
from typing import Any, Dict, Optional

class I18n:
    """Motor de internacionalización con fallback y validación"""
    
    def __init__(self, locale: str = "es", fallback_locale: str = "en"):
        self.locale = locale
        self.fallback_locale = fallback_locale
        
        # Cargar traducciones
        self.translations = self._load_translations(locale)
        self.fallback_translations = self._load_translations(fallback_locale) if fallback_locale != locale else {}
        
        # Cache de accesos para debugging
        self.access_log = []
    
    def _load_translations(self, locale: str) -> Dict[str, Any]:
        """Carga archivo de traducciones"""
        try:
            locale_path = Path(f"locales/{locale}.json")
            if locale_path.exists():
                with open(locale_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️ Archivo de traducción no encontrado: {locale_path}")
                return {}
        except Exception as e:
            print(f"❌ Error cargando traducciones {locale}: {e}")
            return {}
    
    def t(self, key: str, **kwargs) -> str:
        """
        Traduce una clave con soporte de variables
        
        Args:
            key: Clave de traducción (ej: 'buttons.save')
            **kwargs: Variables para interpolación
        
        Returns:
            String traducido con variables interpoladas
        """
        # Log access para debugging
        self.access_log.append(key)
        
        # Buscar traducción
        translation = self._get_nested_value(self.translations, key)
        
        # Fallback si no se encuentra
        if translation is None and self.fallback_translations:
            translation = self._get_nested_value(self.fallback_translations, key)
        
        # Si aún no se encuentra, devolver la clave
        if translation is None:
            print(f"⚠️ Traducción no encontrada: {key}")
            return key
        
        # Interpolar variables
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError as e:
                print(f"⚠️ Variable no encontrada en '{key}': {e}")
                return translation
        
        return translation
    
    def _get_nested_value(self, data: Dict, key: str) -> Optional[str]:
        """Obtiene valor de diccionario anidado usando notación de puntos"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def get_available_locales(self) -> list:
        """Obtiene lista de locales disponibles"""
        locales_dir = Path("locales")
        if not locales_dir.exists():
            return []
        
        locales = []
        for file in locales_dir.glob("*.json"):
            if file.stem not in ['context_map', 'template']:
                locales.append(file.stem)
        
        return sorted(locales)
    
    def switch_locale(self, new_locale: str):
        """Cambia el idioma activo"""
        self.locale = new_locale
        self.translations = self._load_translations(new_locale)
        
        # Actualizar en session state si está disponible
        if hasattr(st, 'session_state'):
            st.session_state.locale = new_locale
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso"""
        return {
            'locale': self.locale,
            'fallback_locale': self.fallback_locale,
            'translations_loaded': len(self.translations),
            'fallback_loaded': len(self.fallback_translations),
            'access_count': len(self.access_log),
            'unique_keys': len(set(self.access_log))
        }


# Global instance
_i18n_instance = None

def init_i18n(default_locale: str = "es", fallback_locale: str = "en"):
    """Inicializa el sistema i18n global"""
    global _i18n_instance
    _i18n_instance = I18n(locale=default_locale, fallback_locale=fallback_locale)
    return _i18n_instance

def get_i18n(locale: str = None) -> I18n:
    """Obtiene la instancia i18n global o crea una nueva"""
    global _i18n_instance
    
    if _i18n_instance is None:
        _i18n_instance = I18n(locale=locale or "es")
    elif locale and locale != _i18n_instance.locale:
        _i18n_instance.switch_locale(locale)
    
    return _i18n_instance

def t(key: str, **kwargs) -> str:
    """Función de conveniencia para traducir"""
    return get_i18n().t(key, **kwargs)

def switch_locale(locale: str):
    """Función de conveniencia para cambiar idioma"""
    get_i18n().switch_locale(locale)
    
    # Actualizar session state
    if hasattr(st, 'session_state'):
        st.session_state.locale = locale

def create_locale_selector():
    """Crea selector de idioma para Streamlit"""
    i18n = get_i18n()
    available_locales = i18n.get_available_locales()
    
    if len(available_locales) <= 1:
        return None
    
    # Mapeo de códigos a nombres
    locale_names = {
        'en': '🇺🇸 English',
        'es': '🇪🇸 Español',
        'fr': '🇫🇷 Français',
        'de': '🇩🇪 Deutsch',
        'it': '🇮🇹 Italiano',
        'pt': '🇵🇹 Português'
    }
    
    # Crear opciones
    options = []
    for locale in available_locales:
        name = locale_names.get(locale, f"🌍 {locale.upper()}")
        options.append((locale, name))
    
    # Encontrar índice actual
    current_index = 0
    for i, (locale, _) in enumerate(options):
        if locale == i18n.locale:
            current_index = i
            break
    
    # Crear selectbox
    selected = st.selectbox(
        "🌍 Idioma / Language",
        options=options,
        index=current_index,
        format_func=lambda x: x[1],
        key="locale_selector"
    )
    
    # Cambiar idioma si es diferente
    if selected[0] != i18n.locale:
        switch_locale(selected[0])
        st.rerun()
    
    return selected[0]


# Decorador para componentes traducibles
def translatable(func):
    """Decorador que inyecta función t en componentes"""
    def wrapper(*args, **kwargs):
        # Inyectar función t
        kwargs['t'] = t
        return func(*args, **kwargs)
    return wrapper


# Utilidades para desarrollo
def validate_translations():
    """Valida integridad de traducciones"""
    i18n = get_i18n()
    available_locales = i18n.get_available_locales()
    
    if len(available_locales) < 2:
        print("⚠️ Se necesitan al menos 2 idiomas para validar")
        return
    
    # Cargar todas las traducciones
    all_translations = {}
    for locale in available_locales:
        all_translations[locale] = i18n._load_translations(locale)
    
    # Obtener todas las claves del idioma base (inglés)
    base_locale = 'en' if 'en' in available_locales else available_locales[0]
    base_keys = set(_get_all_keys(all_translations[base_locale]))
    
    print(f"🔍 Validando traducciones (base: {base_locale})")
    print(f"📊 Claves base: {len(base_keys)}")
    
    # Validar cada idioma
    for locale in available_locales:
        if locale == base_locale:
            continue
        
        locale_keys = set(_get_all_keys(all_translations[locale]))
        missing = base_keys - locale_keys
        extra = locale_keys - base_keys
        
        print(f"\n🌍 {locale}:")
        print(f"  ✅ Completas: {len(locale_keys & base_keys)}")
        if missing:
            print(f"  ❌ Faltantes: {len(missing)}")
            for key in sorted(missing)[:5]:  # Mostrar solo primeras 5
                print(f"    - {key}")
            if len(missing) > 5:
                print(f"    ... y {len(missing) - 5} más")
        
        if extra:
            print(f"  ⚠️ Extras: {len(extra)}")

def _get_all_keys(data: Dict, prefix: str = "") -> list:
    """Obtiene todas las claves de un diccionario anidado"""
    keys = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.extend(_get_all_keys(value, full_key))
        else:
            keys.append(full_key)
    return keys


if __name__ == "__main__":
    # Test básico
    print("🧪 Probando sistema i18n...")
    
    # Crear instancia
    i18n = I18n(locale="es")
    
    # Probar traducción
    test_key = "buttons.save"
    result = i18n.t(test_key)
    print(f"t('{test_key}') = '{result}'")
    
    # Estadísticas
    stats = i18n.get_stats()
    print(f"\n📊 Estadísticas: {stats}")
    
    # Validar traducciones si existen
    validate_translations()