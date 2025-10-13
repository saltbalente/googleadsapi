"""
Script para crear todos los componentes UI
"""

from pathlib import Path

# Componentes a crear
components = [
    'performance_predictor_ui',
    'competitive_analyzer_ui',
    'keyword_extractor_ui',
    'landing_page_analyzer_ui',
    'conversational_assistant_ui',
    'export_manager_ui',
    'template_batch_ui',
    'settings_ui'
]

template = '''"""
{title} UI - Interfaz de {functionality}
"""

import streamlit as st

def show():
    """Muestra la interfaz"""
    
    st.markdown("## {emoji} {title}")
    
    st.info("⏳ **Funcionalidad en desarrollo**")
    
    st.markdown("""
    Esta funcionalidad estará disponible próximamente.
    """)
'''

titles = {
    'performance_predictor_ui': ('📈 Predicción de Rendimiento', 'Predicción de Rendimiento', '📈'),
    'competitive_analyzer_ui': ('🔍 Análisis de Competencia', 'Análisis Competitivo', '🔍'),
    'keyword_extractor_ui': ('🔑 Extractor de Keywords', 'Extracción de Keywords', '🔑'),
    'landing_page_analyzer_ui': ('🌐 Análisis de Landing Pages', 'Análisis de Landing Pages', '🌐'),
    'conversational_assistant_ui': ('💬 Asistente Conversacional', 'Asistente Conversacional', '💬'),
    'export_manager_ui': ('📦 Exportación', 'Exportación de Anuncios', '📦'),
    'template_batch_ui': ('🎨 Templates y Batch', 'Templates y Generación Masiva', '🎨'),
    'settings_ui': ('⚙️ Configuración', 'Configuración del Sistema', '⚙️')
}

# Crear directorio
components_dir = Path('components')
components_dir.mkdir(exist_ok=True)

# Crear archivos
for component in components:
    file_path = components_dir / f'{component}.py'
    
    if not file_path.exists():
        title_info = titles.get(component, ('Component', 'Funcionalidad', '🔧'))
        
        content = template.format(
            title=title_info[0],
            functionality=title_info[1],
            emoji=title_info[2]
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✅ Creado: {file_path}')
    else:
        print(f'⏭️  Ya existe: {file_path}')

print('\n✅ Todos los componentes creados!')