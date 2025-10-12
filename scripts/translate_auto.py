"""
Traductor Automático con Google Translate (Gratis)
Traduce catálogo de strings preservando formato y variables
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from deep_translator import GoogleTranslator
from tqdm import tqdm

class SmartTranslator:
    """Traduce strings preservando formato especial"""
    
    def __init__(self, source_lang: str = 'en', target_lang: str = 'es'):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Cache de traducciones para evitar duplicados
        self.translation_cache = {}
        
        # Estadísticas
        self.stats = {
            'total': 0,
            'translated': 0,
            'cached': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def translate_text(self, text: str, preserve_format: bool = True) -> str:
        """Traduce texto preservando formato especial"""
        
        # Check cache
        if text in self.translation_cache:
            self.stats['cached'] += 1
            return self.translation_cache[text]
        
        try:
            # Preservar emojis y variables
            if preserve_format:
                text_to_translate, placeholders = self._extract_special_tokens(text)
            else:
                text_to_translate = text
                placeholders = {}
            
            # Traducir
            translated = self.translator.translate(text_to_translate)
            
            # Restaurar tokens especiales
            if preserve_format and placeholders:
                translated = self._restore_special_tokens(translated, placeholders)
            
            # Cache
            self.translation_cache[text] = translated
            self.stats['translated'] += 1
            
            # Rate limiting (Google Translate gratis tiene límite)
            time.sleep(0.1)
            
            return translated
        
        except Exception as e:
            print(f"\n❌ Error traduciendo '{text[:50]}...': {e}")
            self.stats['errors'] += 1
            return text  # Return original on error
    
    def _extract_special_tokens(self, text: str) -> tuple:
        """Extrae emojis, variables y otros tokens especiales"""
        placeholders = {}
        counter = 0
        
        # Preservar emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # símbolos & pictogramas
            "\U0001F680-\U0001F6FF"  # transporte & símbolos de mapa
            "\U0001F1E0-\U0001F1FF"  # banderas (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        
        def replace_emoji(match):
            nonlocal counter
            placeholder = f"__EMOJI{counter}__"
            placeholders[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        text = emoji_pattern.sub(replace_emoji, text)
        
        # Preservar variables en llaves {}
        var_pattern = re.compile(r'\{([^}]*)\}')
        
        def replace_var(match):
            nonlocal counter
            placeholder = f"__VAR{counter}__"
            placeholders[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        text = var_pattern.sub(replace_var, text)
        
        # Preservar URLs
        url_pattern = re.compile(r'https?://[^\s]+')
        
        def replace_url(match):
            nonlocal counter
            placeholder = f"__URL{counter}__"
            placeholders[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        text = url_pattern.sub(replace_url, text)
        
        # Preservar formato markdown
        markdown_patterns = [
            (r'\*\*([^*]+)\*\*', '__BOLD'),  # **bold**
            (r'\*([^*]+)\*', '__ITALIC'),    # *italic*
            (r'`([^`]+)`', '__CODE'),        # `code`
        ]
        
        for pattern, prefix in markdown_patterns:
            def replace_md(match):
                nonlocal counter
                placeholder = f"{prefix}{counter}__"
                placeholders[placeholder] = match.group(0)
                counter += 1
                return placeholder
            
            text = re.sub(pattern, replace_md, text)
        
        return text, placeholders
    
    def _restore_special_tokens(self, text: str, placeholders: Dict[str, str]) -> str:
        """Restaura tokens especiales después de traducción"""
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)
        
        return text
    
    def translate_catalog(self, catalog: Dict, custom_translations: Dict = None) -> Dict:
        """Traduce catálogo completo de strings"""
        
        # Load custom translations (overrides)
        custom = custom_translations or {}
        
        translated = {}
        
        # Count total strings
        total_strings = self._count_nested_strings(catalog)
        self.stats['total'] = total_strings
        
        print(f"\n🌐 Traduciendo {total_strings} strings de {self.source_lang} a {self.target_lang}...")
        
        # Translate recursively
        with tqdm(total=total_strings, desc="Traduciendo") as pbar:
            translated = self._translate_recursive(catalog, custom, pbar)
        
        return translated
    
    def _count_nested_strings(self, d: Dict) -> int:
        """Cuenta strings en diccionario anidado"""
        count = 0
        for value in d.values():
            if isinstance(value, dict):
                count += self._count_nested_strings(value)
            elif isinstance(value, str):
                count += 1
        return count
    
    def _translate_recursive(self, data: Dict, custom: Dict, pbar: tqdm) -> Dict:
        """Traduce diccionario recursivamente"""
        result = {}
        
        for key, value in data.items():
            # Check for custom override
            custom_path = f"{key}"
            
            if isinstance(value, dict):
                result[key] = self._translate_recursive(value, custom.get(key, {}), pbar)
            elif isinstance(value, str):
                # Use custom translation if available
                if custom_path in custom:
                    result[key] = custom[custom_path]
                    self.stats['skipped'] += 1
                else:
                    result[key] = self.translate_text(value)
                
                pbar.update(1)
            else:
                result[key] = value
        
        return result
    
    def save_translation(self, translated: Dict, output_path: Path):
        """Guarda traducción"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translated, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Traducción guardada en: {output_path}")
    
    def print_stats(self):
        """Imprime estadísticas de traducción"""
        print("\n📊 Estadísticas de Traducción:")
        print(f"  • Total de strings: {self.stats['total']}")
        print(f"  • Traducidos: {self.stats['translated']}")
        print(f"  • Desde cache: {self.stats['cached']}")
        print(f"  • Custom overrides: {self.stats['skipped']}")
        print(f"  • Errores: {self.stats['errors']}")


def main():
    """Ejecuta traducción automática"""
    print("🌍 Sistema de Traducción Automática")
    print("=" * 60)
    
    # Paths
    locales_dir = Path("locales")
    en_path = locales_dir / "en.json"
    es_path = locales_dir / "es.json"
    es_custom_path = locales_dir / "es_custom.json"
    
    # Verificar que existe catálogo en inglés
    if not en_path.exists():
        print(f"❌ No se encontró {en_path}")
        print("   Primero ejecuta: python scripts/extract_strings.py")
        return
    
    # Cargar catálogo en inglés
    with open(en_path, 'r', encoding='utf-8') as f:
        en_catalog = json.load(f)
    
    # Cargar custom translations si existen
    custom_translations = {}
    if es_custom_path.exists():
        with open(es_custom_path, 'r', encoding='utf-8') as f:
            custom_translations = json.load(f)
        print(f"📝 Cargadas {len(custom_translations)} traducciones personalizadas")
    
    # Inicializar traductor
    translator = SmartTranslator(source_lang='en', target_lang='es')
    
    # Traducir catálogo
    es_catalog = translator.translate_catalog(en_catalog, custom_translations)
    
    # Guardar traducción
    translator.save_translation(es_catalog, es_path)
    
    # Estadísticas
    translator.print_stats()
    
    print("\n✅ Traducción completada!")
    print(f"📁 Archivo generado: {es_path}")


if __name__ == "__main__":
    main()