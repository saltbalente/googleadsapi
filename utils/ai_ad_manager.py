"""
Gestor de Anuncios de IA
Utilidades para gestionar anuncios generados por IA
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIAdManager:
    """Gestor de anuncios generados por IA"""
    @staticmethod
    def mark_ad_as_used(ad_id: str, campaign_id: str = None, ad_group_id: str = None) -> bool:
        """
        Marca un anuncio como usado en una campaña
        
        Args:
            ad_id: ID del anuncio
            campaign_id: ID de la campaña (opcional)
            ad_group_id: ID del grupo de anuncios (opcional)
        
        Returns:
            bool: True si se marcó exitosamente
        """
        if 'pending_ai_ads' not in st.session_state:
            logger.warning("⚠️ No hay anuncios pendientes")
            return False
        
        for ad in st.session_state.pending_ai_ads:
            if ad['id'] == ad_id:
                ad['used'] = True
                ad['campaign_id'] = campaign_id
                ad['ad_group_id'] = ad_group_id
                ad['used_at'] = datetime.now().isoformat()
                logger.info(f"✅ Anuncio {ad_id} marcado como usado")
                return True
        
        logger.warning(f"⚠️ Anuncio {ad_id} no encontrado")
        return False
    @staticmethod
    def get_available_ads() -> List[Dict[str, Any]]:
        """Obtiene anuncios disponibles (no usados)"""
        if 'pending_ai_ads' not in st.session_state:
            return []
        
        return [ad for ad in st.session_state.pending_ai_ads if not ad.get('used', False)]
    
    @staticmethod
    def get_used_ads() -> List[Dict[str, Any]]:
        """Obtiene anuncios ya usados"""
        if 'pending_ai_ads' not in st.session_state:
            return []
        
        return [ad for ad in st.session_state.pending_ai_ads if ad.get('used', False)]
    
    @staticmethod
    def get_ad_by_id(ad_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un anuncio específico por ID"""
        if 'pending_ai_ads' not in st.session_state:
            return None
        
        for ad in st.session_state.pending_ai_ads:
            if ad['id'] == ad_id:
                return ad
        
        return None
    
    @staticmethod
    def delete_ad(ad_id: str) -> bool:
        """Elimina un anuncio de la lista"""
        if 'pending_ai_ads' not in st.session_state:
            return False
        
        st.session_state.pending_ai_ads = [
            ad for ad in st.session_state.pending_ai_ads 
            if ad['id'] != ad_id
        ]
        
        logger.info(f"✅ Anuncio {ad_id} eliminado")
        return True
    
    @staticmethod
    def clear_used_ads():
        """Limpia anuncios ya usados"""
        if 'pending_ai_ads' not in st.session_state:
            return
        
        before = len(st.session_state.pending_ai_ads)
        st.session_state.pending_ai_ads = [
            ad for ad in st.session_state.pending_ai_ads 
            if not ad.get('used', False)
        ]
        after = len(st.session_state.pending_ai_ads)
        
        logger.info(f"✅ {before - after} anuncios usados eliminados")
    
    @staticmethod
    def get_statistics() -> Dict[str, int]:
        """Obtiene estadísticas de anuncios"""
        if 'pending_ai_ads' not in st.session_state:
            return {'total': 0, 'available': 0, 'used': 0}
        
        ads = st.session_state.pending_ai_ads
        
        return {
            'total': len(ads),
            'available': len([ad for ad in ads if not ad.get('used', False)]),
            'used': len([ad for ad in ads if ad.get('used', False)])
        }