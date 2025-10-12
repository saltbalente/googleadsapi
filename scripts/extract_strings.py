"""
Extractor Inteligente de Strings Traducibles
Escanea toda la app y genera catálogo de strings en inglés
"""

import os
import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class SmartStringExtractor:
    """Extrae strings traducibles de código Python/Streamlit"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.strings_catalog = defaultdict(dict)
        self.context_map = {}  # Mapea string → contexto de uso
        
        # Patrones de extracción por tipo
        self.patterns = {
            'streamlit': [
                # Streamlit UI
                (r'st\.title\(["\'](.+?)["\']\)', 'page_titles'),
                (r'st\.header\(["\'](.+?)["\']\)', 'headers'),
                (r'st\.subheader\(["\'](.+?)["\']\)', 'subheaders'),
                (r'st\.markdown\(["\'](.+?)["\']\)', 'markdown'),
                (r'st\.info\(["\'](.+?)["\']\)', 'messages.info'),
                (r'st\.warning\(["\'](.+?)["\']\)', 'messages.warning'),
                (r'st\.error\(["\'](.+?)["\']\)', 'messages.error'),
                (r'st\.success\(["\'](.+?)["\']\)', 'messages.success'),
                (r'st\.caption\(["\'](.+?)["\']\)', 'captions'),
                
                # Metrics
                (r'st\.metric\(\s*["\'](.+?)["\']\s*,', 'metrics'),
                
                # Buttons
                (r'st\.button\(["\'](.+?)["\']\)', 'buttons'),
                
                # Inputs
                (r'st\.text_input\(["\'](.+?)["\']\)', 'inputs'),
                (r'st\.selectbox\(["\'](.+?)["\']\)', 'selects'),
                (r'st\.multiselect\(["\'](.+?)["\']\)', 'selects'),
                (r'st\.slider\(["\'](.+?)["\']\)', 'inputs'),
                (r'st\.checkbox\(["\'](.+?)["\']\)', 'inputs'),
                
                # Dataframe columns
                (r'st\.dataframe\(["\'](.+?)["\']\)', 'tables'),
            ],
            
            'python': [
                # Logging
                (r'logger\.info\(["\'](.+?)["\']\)', 'logs.info'),
                (r'logger\.warning\(["\'](.+?)["\']\)', 'logs.warning'),
                (r'logger\.error\(["\'](.+?)["\']\)', 'logs.error'),
                
                # Format strings
                (r'format_currency\(["\'](.+?)["\']\)', 'formats'),
                
                # Messages
                (r'help=["\'](.+?)["\']\)', 'help_texts'),
            ],
            
            'dataframes': [
                # Column names in rename/columns
                (r'columns=\{["\'](.+?)["\']\s*:', 'columns'),
                (r'rename\(columns=\{["\'](.+?)["\']\s*:', 'columns'),
            ]
        }
    
    def extract_from_file(self, filepath: Path) -> Dict[str, str]:
        """Extrae strings de un archivo Python"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            extracted = {}
            
            # Extraer usando patrones
            for pattern_type, patterns in self.patterns.items():
                for pattern, category in patterns:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    for match in matches:
                        # Limpiar string
                        clean_match = self._clean_string(match)
                        if self._is_translatable(clean_match):
                            key = self._generate_key(clean_match, category)
                            extracted[key] = clean_match
                            
                            # Guardar contexto
                            self.context_map[key] = {
                                'file': str(filepath),
                                'category': category,
                                'original': match
                            }
            
            return extracted
        
        except Exception as e:
            print(f"❌ Error procesando {filepath}: {e}")
            return {}
    
    def _clean_string(self, s: str) -> str:
        """Limpia string para traducción"""
        # Remover f-strings variables pero preservar estructura
        s = re.sub(r'\{[^}]+\}', '{}', s)
        
        # Remover saltos de línea excesivos
        s = re.sub(r'\n+', '\n', s)
        
        # Trim
        s = s.strip()
        
        return s
    
    def _is_translatable(self, s: str) -> bool:
        """Verifica si un string es traducible"""
        # No traducir si es muy corto
        if len(s) < 2:
            return False
        
        # No traducir si es solo código
        if re.match(r'^[A-Z_]+$', s):  # CONSTANTES
            return False
        
        # No traducir URLs
        if s.startswith('http'):
            return False
        
        # No traducir si es solo números/símbolos
        if re.match(r'^[\d\s\-\+\*\/\(\)\.]+$', s):
            return False
        
        return True
    
    def _generate_key(self, text: str, category: str) -> str:
        """Genera clave única para el string"""
        # Usar primeras palabras + hash para unicidad
        words = re.findall(r'\w+', text.lower())
        prefix = '_'.join(words[:3]) if words else 'unknown'
        
        # Truncar a 50 chars
        prefix = prefix[:50]
        
        # Agregar hash corto para evitar colisiones
        hash_suffix = abs(hash(text)) % 10000
        
        return f"{category}.{prefix}_{hash_suffix}"
    
    def extract_from_directory(self, directory: Path = None) -> Dict[str, Dict[str, str]]:
        """Extrae strings de todos los archivos .py en directorio"""
        if directory is None:
            directory = self.root_dir
        
        all_strings = {}
        
        # Escanear archivos .py
        python_files = list(directory.rglob("*.py"))
        
        print(f"📁 Escaneando {len(python_files)} archivos Python...")
        
        for filepath in python_files:
            # Skip virtual env y cache
            if any(skip in str(filepath) for skip in ['.venv', '__pycache__', '.git', 'venv']):
                continue
            
            print(f"  📄 {filepath.relative_to(self.root_dir)}")
            file_strings = self.extract_from_file(filepath)
            all_strings.update(file_strings)
        
        print(f"\n✅ Extraídos {len(all_strings)} strings únicos\n")
        
        return all_strings
    
    def organize_by_category(self, strings: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Organiza strings por categoría jerárquica"""
        organized = defaultdict(dict)
        
        for key, value in strings.items():
            # Separar categoría del key
            parts = key.split('.')
            if len(parts) >= 2:
                category = '.'.join(parts[:-1])
                sub_key = parts[-1]
                
                # Crear estructura jerárquica
                self._set_nested_dict(organized, category, sub_key, value)
            else:
                organized['misc'][key] = value
        
        return dict(organized)
    
    def _set_nested_dict(self, d: dict, category: str, key: str, value: str):
        """Establece valor en dict anidado"""
        parts = category.split('.')
        current = d
        
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[key] = value
    
    def save_catalog(self, catalog: Dict, output_path: Path):
        """Guarda catálogo de strings"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Catálogo guardado en: {output_path}")
    
    def save_context_map(self, output_path: Path):
        """Guarda mapa de contexto"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.context_map, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Mapa de contexto guardado en: {output_path}")


def main():
    """Ejecuta extracción de strings"""
    print("🌍 Sistema de Extracción de Strings para Traducción")
    print("=" * 60)
    
    # Inicializar extractor
    extractor = SmartStringExtractor(root_dir=".")
    
    # Extraer strings de toda la app
    strings = extractor.extract_from_directory()
    
    # Organizar por categoría
    organized = extractor.organize_by_category(strings)
    
    # Crear directorio locales si no existe
    locales_dir = Path("locales")
    locales_dir.mkdir(exist_ok=True)
    
    # Guardar catálogo en inglés (base)
    extractor.save_catalog(organized, locales_dir / "en.json")
    
    # Guardar mapa de contexto para referencia
    extractor.save_context_map(locales_dir / "context_map.json")
    
    # Estadísticas
    print("\n📊 Estadísticas de Extracción:")
    print(f"  • Total de strings: {len(strings)}")
    print(f"  • Categorías: {len(organized)}")
    
    for category, items in organized.items():
        count = len(items) if isinstance(items, dict) else 1
        print(f"    - {category}: {count} strings")
    
    print("\n✅ Extracción completada!")
    print(f"📁 Archivos generados en: {locales_dir}")


if __name__ == "__main__":
    main()