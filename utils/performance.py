"""
Utilidades de Performance para Streamlit - ULTRA OPTIMIZADO
Versión: 2.0
"""

import streamlit as st
from functools import wraps
import time
from typing import Callable, Any, Dict, List
import logging

logger = logging.getLogger(__name__)

# Storage para métricas
_performance_metrics: Dict[str, List[float]] = {}


# ============================================================================
# DECORADOR DE CACHE ULTRA-RÁPIDO CON ERROR HANDLING
# ============================================================================

def ultra_cache(ttl: int = 3600, show_spinner: bool = False):
    """
    Decorador de cache ultra-optimizado con manejo de errores
    
    Args:
        ttl: Tiempo de vida en segundos (default: 1 hora)
        show_spinner: Mostrar spinner durante carga
    """
    def decorator(func: Callable) -> Callable:
        cached_func = st.cache_data(ttl=ttl, show_spinner=show_spinner)(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return cached_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error en cache de {func.__name__}: {e}")
                # Fallback: ejecutar sin cache
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def ultra_cache_resource(ttl: int = 7200, show_spinner: bool = False):
    """
    Decorador de cache para recursos con error handling
    
    Args:
        ttl: Tiempo de vida en segundos (default: 2 horas)
        show_spinner: Mostrar spinner durante carga
    """
    def decorator(func: Callable) -> Callable:
        cached_func = st.cache_resource(ttl=ttl, show_spinner=show_spinner)(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return cached_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error en cache resource de {func.__name__}: {e}")
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# LAZY LOADING
# ============================================================================

def lazy_load(component_func: Callable) -> Callable:
    """
    Carga lazy de componentes pesados
    Solo se cargan cuando son necesarios
    """
    @wraps(component_func)
    def wrapper(*args, **kwargs):
        placeholder = st.empty()
        cache_key = f"lazy_{component_func.__name__}"
        
        if cache_key not in st.session_state:
            with placeholder:
                with st.spinner(f"Cargando {component_func.__name__}..."):
                    result = component_func(*args, **kwargs)
                    st.session_state[cache_key] = result
        
        return st.session_state[cache_key]
    
    return wrapper


# ============================================================================
# COMPRESIÓN DE DATOS MEJORADA
# ============================================================================

def compress_dataframe(df):
    """
    Comprime un DataFrame para usar menos memoria
    
    Args:
        df: DataFrame a comprimir
        
    Returns:
        DataFrame comprimido
    """
    import pandas as pd
    
    if df is None or df.empty:
        return df
    
    df_compressed = df.copy()
    
    for col in df_compressed.columns:
        col_type = df_compressed[col].dtype
        
        try:
            if col_type == 'int64':
                df_compressed[col] = pd.to_numeric(df_compressed[col], downcast='integer')
            
            elif col_type == 'float64':
                df_compressed[col] = pd.to_numeric(df_compressed[col], downcast='float')
            
            elif col_type == 'object':
                num_unique = df_compressed[col].nunique()
                num_total = len(df_compressed[col])
                
                if num_unique / num_total < 0.5:
                    df_compressed[col] = df_compressed[col].astype('category')
        
        except Exception as e:
            logger.warning(f"⚠️ No se pudo optimizar columna {col}: {e}")
            continue
    
    # Log reducción
    original_size = df.memory_usage(deep=True).sum() / 1024**2
    compressed_size = df_compressed.memory_usage(deep=True).sum() / 1024**2
    reduction = (1 - compressed_size / original_size) * 100
    
    logger.info(f"💾 DataFrame: {original_size:.2f}MB → {compressed_size:.2f}MB ({reduction:.1f}% ↓)")
    
    return df_compressed


# ============================================================================
# PERFORMANCE TIMER
# ============================================================================

class PerformanceTimer:
    """Context manager para medir tiempos de ejecución"""
    
    def __init__(self, name: str, show_in_ui: bool = False):
        self.name = name
        self.show_in_ui = show_in_ui
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        
        logger.info(f"⚡ {self.name}: {elapsed:.3f}s")
        
        if self.show_in_ui:
            st.caption(f"⏱️ {self.name}: {elapsed:.2f}s")


# ============================================================================
# PROFILING
# ============================================================================

def profile(func: Callable) -> Callable:
    """Decorador para perfilar funciones"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        
        func_name = func.__name__
        if func_name not in _performance_metrics:
            _performance_metrics[func_name] = []
        
        _performance_metrics[func_name].append(elapsed)
        
        if elapsed > 1.0:
            logger.warning(f"⚠️ Función lenta: {func_name} tomó {elapsed:.2f}s")
        
        return result
    
    return wrapper


def get_performance_report() -> Dict[str, Dict[str, float]]:
    """Genera reporte de performance"""
    report = {}
    
    for func_name, times in _performance_metrics.items():
        if times:
            report[func_name] = {
                'calls': len(times),
                'total': sum(times),
                'avg': sum(times) / len(times),
                'min': min(times),
                'max': max(times),
            }
    
    return report


# ============================================================================
# BATCH LOADING
# ============================================================================

def batch_load(items: list, batch_size: int = 10):
    """Carga items en batches"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


# ============================================================================
# PRELOAD
# ============================================================================

def preload_common_data():
    """Precarga datos comunes"""
    if 'preload_done' not in st.session_state:
        with PerformanceTimer("Preload común"):
            st.session_state['preload_done'] = True
            st.session_state['app_start_time'] = time.time()


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def clear_all_caches():
    """Limpia todos los caches"""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
        logger.info("🧹 Caches limpiados")
        return True
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


# ============================================================================
# MEMORY PROFILING
# ============================================================================

def get_memory_usage() -> Dict[str, float]:
    """Obtiene uso de memoria"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024**2,
            'vms_mb': memory_info.vms / 1024**2,
            'percent': process.memory_percent(),
        }
    except:
        return {}


# ============================================================================
# UI WIDGETS
# ============================================================================

def show_performance_sidebar():
    """Muestra métricas en sidebar"""
    with st.sidebar:
        st.markdown("### ⚡ Performance")
        
        # Memory
        memory = get_memory_usage()
        if memory:
            st.metric("💾 RAM", f"{memory['rss_mb']:.0f} MB")
        
        # Cache stats
        if st.button("🧹 Clear Cache", use_container_width=True):
            if clear_all_caches():
                st.success("✅ Limpiado")
                time.sleep(0.5)
                st.rerun()