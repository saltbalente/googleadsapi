#!/usr/bin/env python3
"""
Script para aplicar traducciones i18n al código fuente
Reemplaza strings hardcodeados con llamadas a la función de traducción
"""

import os
import re
import json
import ast
import astor
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse

class I18nApplicator:
    def __init__(self, context_map_path: str = "locales/context_map.json"):
        """Inicializa el aplicador de traducciones"""
        self.context_map_path = context_map_path
        self.context_map = self._load_context_map()
        self.processed_files = set()
        
    def _load_context_map(self) -> Dict:
        """Carga el mapa de contexto generado por extract_strings.py"""
        try:
            with open(self.context_map_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: No se encontró {self.context_map_path}")
            print("   Ejecuta primero: python scripts/extract_strings.py")
            return {}
    
    def _get_translation_key(self, text: str, file_path: str, line_num: int) -> str:
        """Busca la clave de traducción para un texto específico"""
        # Buscar en el mapa de contexto
        for key, info in self.context_map.items():
            if info['original'] == text:
                # Verificar si coincide el archivo y línea (aproximadamente)
                for location in info['locations']:
                    if file_path.endswith(location['file']) and abs(location['line'] - line_num) <= 2:
                        return key
        
        # Si no se encuentra, generar clave basada en el texto
        return self._generate_key(text, info.get('category', 'general'))
    
    def _generate_key(self, text: str, category: str = 'general') -> str:
        """Genera una clave de traducción basada en el texto"""
        # Limpiar el texto para crear una clave
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        clean_text = re.sub(r'\s+', '_', clean_text.strip())
        clean_text = clean_text[:50]  # Limitar longitud
        
        return f"{category}.{clean_text}"
    
    def _should_translate_string(self, text: str) -> bool:
        """Determina si un string debe ser traducido"""
        # Ignorar strings muy cortos
        if len(text.strip()) < 3:
            return False
            
        # Ignorar strings que son solo números o símbolos
        if re.match(r'^[\d\s\-\+\.\,\%\$\€\£\¥]+$', text):
            return False
            
        # Ignorar URLs, emails, paths
        if re.match(r'^(https?://|mailto:|/|\\|[a-zA-Z]:\\)', text):
            return False
            
        # Ignorar strings de configuración
        if text.lower() in ['true', 'false', 'none', 'null', 'undefined']:
            return False
            
        # Ignorar strings que parecen ser código
        if re.match(r'^[a-z_]+\.[a-z_]+', text):
            return False
            
        return True
    
    def _add_i18n_import(self, tree: ast.AST) -> ast.AST:
        """Añade la importación del sistema i18n al AST"""
        # Buscar si ya existe la importación
        has_i18n_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'utils.i18n' and any(alias.name == 't' for alias in node.names):
                    has_i18n_import = True
                    break
        
        if not has_i18n_import:
            # Crear la importación: from utils.i18n import t
            import_node = ast.ImportFrom(
                module='utils.i18n',
                names=[ast.alias(name='t', asname=None)],
                level=0
            )
            
            # Insertar al principio del archivo (después de otros imports)
            if hasattr(tree, 'body') and tree.body:
                # Encontrar el lugar correcto para insertar
                insert_pos = 0
                for i, node in enumerate(tree.body):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        insert_pos = i + 1
                    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                        # Docstring del módulo
                        insert_pos = i + 1
                    else:
                        break
                
                tree.body.insert(insert_pos, import_node)
        
        return tree
    
    def _replace_strings_in_ast(self, tree: ast.AST, file_path: str) -> Tuple[ast.AST, int]:
        """Reemplaza strings en el AST con llamadas a t()"""
        replacements = 0
        
        class StringReplacer(ast.NodeTransformer):
            def __init__(self, applicator, file_path):
                self.applicator = applicator
                self.file_path = file_path
                self.replacements = 0
            
            def visit_Constant(self, node):
                # Solo procesar strings
                if isinstance(node.value, str):
                    text = node.value
                    
                    if self.applicator._should_translate_string(text):
                        # Obtener la clave de traducción
                        key = self.applicator._get_translation_key(text, self.file_path, node.lineno)
                        
                        # Crear llamada a t(key)
                        new_node = ast.Call(
                            func=ast.Name(id='t', ctx=ast.Load()),
                            args=[ast.Constant(value=key)],
                            keywords=[]
                        )
                        
                        # Copiar información de línea
                        ast.copy_location(new_node, node)
                        self.replacements += 1
                        return new_node
                
                return node
            
            def visit_Str(self, node):
                # Para compatibilidad con Python < 3.8
                text = node.s
                
                if self.applicator._should_translate_string(text):
                    key = self.applicator._get_translation_key(text, self.file_path, node.lineno)
                    
                    new_node = ast.Call(
                        func=ast.Name(id='t', ctx=ast.Load()),
                        args=[ast.Constant(value=key)],
                        keywords=[]
                    )
                    
                    ast.copy_location(new_node, node)
                    self.replacements += 1
                    return new_node
                
                return node
        
        replacer = StringReplacer(self, file_path)
        new_tree = replacer.visit(tree)
        
        return new_tree, replacer.replacements
    
    def apply_to_file(self, file_path: str, dry_run: bool = False) -> Dict:
        """Aplica traducciones a un archivo específico"""
        result = {
            'file': file_path,
            'success': False,
            'replacements': 0,
            'error': None
        }
        
        try:
            # Leer el archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parsear el AST
            tree = ast.parse(content, filename=file_path)
            
            # Añadir importación i18n
            tree = self._add_i18n_import(tree)
            
            # Reemplazar strings
            new_tree, replacements = self._replace_strings_in_ast(tree, file_path)
            
            result['replacements'] = replacements
            
            if replacements > 0 and not dry_run:
                # Generar el código modificado
                new_content = astor.to_source(new_tree)
                
                # Crear backup
                backup_path = f"{file_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Escribir el archivo modificado
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ {file_path}: {replacements} strings reemplazados")
                print(f"   💾 Backup guardado en: {backup_path}")
            elif replacements > 0:
                print(f"🔍 {file_path}: {replacements} strings serían reemplazados (dry-run)")
            else:
                print(f"⏭️  {file_path}: No hay strings para traducir")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error procesando {file_path}: {e}")
        
        return result
    
    def apply_to_directory(self, directory: str, dry_run: bool = False, 
                          exclude_patterns: List[str] = None) -> Dict:
        """Aplica traducciones a todos los archivos Python en un directorio"""
        if exclude_patterns is None:
            exclude_patterns = [
                '*/venv/*', '*/env/*', '*/__pycache__/*', 
                '*/node_modules/*', '*/locales/*', '*/scripts/extract_strings.py',
                '*/scripts/translate_auto.py', '*/scripts/apply_i18n.py',
                '*/utils/i18n.py'
            ]
        
        results = {
            'total_files': 0,
            'processed_files': 0,
            'total_replacements': 0,
            'errors': [],
            'files': []
        }
        
        # Buscar archivos Python
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Verificar patrones de exclusión
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if re.search(pattern.replace('*', '.*'), file_path):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        python_files.append(file_path)
        
        results['total_files'] = len(python_files)
        
        print(f"🔍 Encontrados {len(python_files)} archivos Python para procesar")
        
        # Procesar cada archivo
        for file_path in python_files:
            result = self.apply_to_file(file_path, dry_run)
            results['files'].append(result)
            
            if result['success']:
                results['processed_files'] += 1
                results['total_replacements'] += result['replacements']
            else:
                results['errors'].append({
                    'file': file_path,
                    'error': result['error']
                })
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Aplicar traducciones i18n al código')
    parser.add_argument('--directory', '-d', default='.', 
                       help='Directorio a procesar (default: .)')
    parser.add_argument('--file', '-f', 
                       help='Archivo específico a procesar')
    parser.add_argument('--dry-run', action='store_true',
                       help='Solo mostrar qué cambios se harían sin aplicarlos')
    parser.add_argument('--context-map', default='locales/context_map.json',
                       help='Ruta al mapa de contexto')
    
    args = parser.parse_args()
    
    print("🌍 Aplicador de Traducciones i18n")
    print("=" * 60)
    
    applicator = I18nApplicator(args.context_map)
    
    if not applicator.context_map:
        print("❌ No se pudo cargar el mapa de contexto. Saliendo...")
        return
    
    if args.dry_run:
        print("🔍 Modo DRY-RUN: Solo se mostrarán los cambios propuestos")
        print()
    
    if args.file:
        # Procesar archivo específico
        result = applicator.apply_to_file(args.file, args.dry_run)
        print(f"\n📊 Resultado: {result['replacements']} reemplazos en {args.file}")
    else:
        # Procesar directorio
        results = applicator.apply_to_directory(args.directory, args.dry_run)
        
        print(f"\n📊 Resumen de Procesamiento:")
        print(f"  • Archivos encontrados: {results['total_files']}")
        print(f"  • Archivos procesados: {results['processed_files']}")
        print(f"  • Total de reemplazos: {results['total_replacements']}")
        print(f"  • Errores: {len(results['errors'])}")
        
        if results['errors']:
            print(f"\n❌ Errores encontrados:")
            for error in results['errors']:
                print(f"  • {error['file']}: {error['error']}")
        
        if not args.dry_run and results['total_replacements'] > 0:
            print(f"\n✅ Aplicación completada!")
            print(f"📁 Se crearon backups con extensión .backup")
            print(f"🔄 Reinicia la aplicación para ver los cambios")

if __name__ == "__main__":
    main()