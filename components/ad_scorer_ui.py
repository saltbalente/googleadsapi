"""
📊 AD SCORER UI - Interfaz de Análisis y Scoring
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def show():
    """Muestra la interfaz de scoring"""
    
    st.markdown("## 📊 Análisis y Scoring de Anuncios")
    
    st.info("""
    **🎯 Evalúa la calidad de tus anuncios**
    
    Obtén un score de 0-100 y recomendaciones detalladas de mejora.
    """)
    
    # Tabs
    tab1, tab2 = st.tabs(["📊 Analizar Anuncio", "📈 Comparar Anuncios"])
    
    # ========== TAB 1: ANALIZAR ==========
    with tab1:
        st.markdown("### Ingresa tu Anuncio")
        
        # Headlines
        st.markdown("#### 📝 Headlines")
        headlines_input = st.text_area(
            "Una por línea:",
            placeholder="Amarres de Amor Efectivos\nRecupera a Tu Pareja Ya\nBrujería Profesional",
            height=150,
            key="scorer_headlines"
        )
        
        # Descriptions
        st.markdown("#### 📄 Descriptions")
        descriptions_input = st.text_area(
            "Una por línea:",
            placeholder="Amarres de amor con resultados garantizados.\nBruja profesional con experiencia.",
            height=100,
            key="scorer_descriptions"
        )
        
        # Keywords opcionales
        st.markdown("#### 🔑 Keywords (opcional)")
        keywords_input = st.text_input(
            "Separadas por comas:",
            placeholder="amarres de amor, hechizos, brujería",
            key="scorer_keywords"
        )
        
        # Botón de analizar
        if st.button("📊 Analizar Anuncio", type="primary", use_container_width=True):
            headlines = [h.strip() for h in headlines_input.split('\n') if h.strip()]
            descriptions = [d.strip() for d in descriptions_input.split('\n') if d.strip()]
            keywords = [k.strip() for k in keywords_input.split(',') if k.strip()] if keywords_input else None
            
            if not headlines and not descriptions:
                st.error("❌ Ingresa al menos headlines o descriptions")
            else:
                with st.spinner("📊 Analizando..."):
                    try:
                        if st.session_state.get('ad_scorer'):
                            from utils.ad_scorer import AdScorer
                            
                            scorer = st.session_state.ad_scorer
                            
                            # Analizar
                            result = scorer.score_ad(
                                headlines=headlines,
                                descriptions=descriptions,
                                keywords=keywords,
                                compare_to_benchmark=True
                            )
                            
                            # Mostrar score general
                            st.markdown("### 🎯 Score General")
                            
                            score = result['overall_score']
                            grade = result['grade']
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Score", f"{score:.1f}/100")
                            
                            with col2:
                                st.metric("Calificación", grade)
                            
                            with col3:
                                st.metric("Nivel", result['performance_level'])
                            
                            # Barra de progreso
                            st.progress(score / 100)
                            
                            # Scores por categoría
                            st.markdown("### 📊 Scores por Categoría")
                            
                            categories = result['category_scores']
                            
                            for category, data in categories.items():
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**{category.title()}**")
                                    st.progress(data['percentage'] / 100)
                                
                                with col2:
                                    st.metric("", f"{data['score']:.1f}/{data['max']}")
                            
                            # Fortalezas
                            if result['strengths']:
                                st.markdown("### ✅ Fortalezas")
                                for strength in result['strengths']:
                                    st.success(f"✓ {strength['description']}")
                            
                            # Debilidades
                            if result['weaknesses']:
                                st.markdown("### ⚠️ Áreas de Mejora")
                                for weakness in result['weaknesses']:
                                    st.warning(f"⚠ {weakness['description']}")
                            
                            # Recomendaciones
                            st.markdown("### 💡 Recomendaciones")
                            for i, rec in enumerate(result['recommendations'], 1):
                                st.info(f"""
                                **{i}. [{rec['priority'].upper()}] {rec['category']}**
                                
                                {rec['recommendation']}
                                
                                *Impacto esperado: {rec['expected_impact']}*
                                """)
                            
                            # Comparación con benchmark
                            if result.get('benchmark_comparison'):
                                st.markdown("### 📈 Comparación con Industria")
                                bench = result['benchmark_comparison']
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric(
                                        "Tu Score",
                                        f"{bench['your_score']:.1f}",
                                        f"{bench['difference']:+.1f}"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "Promedio Industria",
                                        f"{bench['industry_average']:.1f}"
                                    )
                                
                                with col3:
                                    st.metric(
                                        "Percentil",
                                        f"Top {100 - bench['percentile']}%"
                                    )
                                
                                st.info(bench['description'])
                            
                            # Actualizar estadísticas
                            st.session_state.stats['analisis_realizados'] += 1
                        
                        else:
                            st.warning("⚠️ Ad Scorer no disponible. Mostrando análisis básico...")
                            
                            st.metric("Score Estimado", "75/100")
                            st.success("✅ Anuncio analizado (modo demo)")
                            st.info("💡 Configura los módulos para análisis completo")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    # ========== TAB 2: COMPARAR ==========
    with tab2:
        st.markdown("### 📊 Comparar Dos Anuncios")
        
        st.info("Compara dos versiones de anuncios lado a lado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Anuncio A")
            headlines_a = st.text_area("Headlines A:", height=100, key="headlines_a")
            descriptions_a = st.text_area("Descriptions A:", height=80, key="descriptions_a")
        
        with col2:
            st.markdown("#### Anuncio B")
            headlines_b = st.text_area("Headlines B:", height=100, key="headlines_b")
            descriptions_b = st.text_area("Descriptions B:", height=80, key="descriptions_b")
        
        if st.button("🔄 Comparar", type="primary", use_container_width=True):
            st.info("⏳ Funcionalidad de comparación en desarrollo...")