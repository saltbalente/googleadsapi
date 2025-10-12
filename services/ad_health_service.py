"""
Ad Health Service - Calcula health scores para anuncios en tiempo real
Similar a KeywordHealthService pero para anuncios
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class AdHealthService:
    """Servicio para calcular health scores de anuncios en tiempo real"""
    
    def __init__(self, google_ads_client, db_service):
        """
        Args:
            google_ads_client: Cliente de Google Ads (wrapper o real)
            db_service: DatabaseService para obtener benchmarks
        """
        # Detectar si es wrapper
        if hasattr(google_ads_client, 'client'):
            self.client = google_ads_client.client
        else:
            self.client = google_ads_client
        
        self.db_service = db_service
        self.googleads_service = self.client.get_service("GoogleAdsService")
        logger.info("✅ AdHealthService inicializado")
    
    def calculate_ad_health_scores_realtime(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Calcula health scores de anuncios en tiempo real desde Google Ads API
        
        Args:
            customer_id: ID del cliente
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            
        Returns:
            DataFrame con health scores calculados
        """
        logger.info(f"Calculando ad health scores para {customer_id} del {start_date} al {end_date}")
        
        # Query para obtener datos de anuncios
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.policy_summary.approval_status,
                ad_group_ad.policy_summary.review_status,
                
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                
                ad_group_ad.ad.expanded_text_ad.headline_part1,
                ad_group_ad.ad.expanded_text_ad.headline_part2,
                ad_group_ad.ad.expanded_text_ad.description,
                
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_micros,
                metrics.ctr,
                metrics.average_cpc,
                
                segments.date
                
            FROM ad_group_ad
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND ad_group_ad.status IN ('ENABLED', 'PAUSED')
                AND ad_group.status = 'ENABLED'
                AND campaign.status = 'ENABLED'
        """
        
        try:
            response = self.googleads_service.search(customer_id=customer_id, query=query)
            
            # Procesar respuesta
            ads_data = []
            for row in response:
                ad = row.ad_group_ad.ad
                
                # Extraer headlines y descriptions según tipo de anuncio
                headlines = []
                descriptions = []
                
                if ad.type_.name == 'RESPONSIVE_SEARCH_AD' and ad.responsive_search_ad:
                    headlines = [h.text for h in ad.responsive_search_ad.headlines]
                    descriptions = [d.text for d in ad.responsive_search_ad.descriptions]
                elif ad.type_.name == 'EXPANDED_TEXT_AD' and ad.expanded_text_ad:
                    headlines = [
                        ad.expanded_text_ad.headline_part1,
                        ad.expanded_text_ad.headline_part2
                    ]
                    descriptions = [ad.expanded_text_ad.description]
                
                final_url = ad.final_urls[0] if ad.final_urls else ""
                
                ads_data.append({
                    'ad_id': ad.id,
                    'ad_type': ad.type_.name,
                    'ad_status': row.ad_group_ad.status.name,
                    'approval_status': row.ad_group_ad.policy_summary.approval_status.name,
                    'review_status': row.ad_group_ad.policy_summary.review_status.name,
                    
                    'ad_group_id': row.ad_group.id,
                    'ad_group_name': row.ad_group.name,
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    
                    'headlines': headlines,
                    'descriptions': descriptions,
                    'final_url': final_url,
                    
                    'impressions': row.metrics.impressions,
                    'clicks': row.metrics.clicks,
                    'conversions': row.metrics.conversions,
                    'conversions_value': row.metrics.conversions_value,
                    'cost_micros': row.metrics.cost_micros,
                    'ctr': row.metrics.ctr * 100,  # Convertir a porcentaje
                    'avg_cpc': row.metrics.average_cpc / 1_000_000,
                    'impression_share': 0,  # Placeholder since search_impression_share is not compatible with ad_group_ad
                    
                    'date': row.segments.date
                })
            
            if not ads_data:
                logger.warning("No se encontraron anuncios en el período especificado")
                return pd.DataFrame()
            
            # Crear DataFrame
            df = pd.DataFrame(ads_data)
            
            # Convertir listas a strings para poder hacer groupby
            df['headlines_str'] = df['headlines'].apply(lambda x: '|'.join(x) if isinstance(x, list) else str(x))
            df['descriptions_str'] = df['descriptions'].apply(lambda x: '|'.join(x) if isinstance(x, list) else str(x))
            
            # Agrupar por anuncio (sumar métricas de todos los días)
            grouped = df.groupby([
                'ad_id', 'ad_type', 'ad_status', 'approval_status', 'review_status',
                'ad_group_id', 'ad_group_name', 'campaign_id', 'campaign_name',
                'headlines_str', 'descriptions_str', 'final_url'
            ], as_index=False).agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'conversions': 'sum',
                'conversions_value': 'sum',
                'cost_micros': 'sum',
                'impression_share': 'mean'
            })
            
            # Renombrar las columnas de vuelta
            grouped['headlines'] = grouped['headlines_str']
            grouped['descriptions'] = grouped['descriptions_str']
            grouped = grouped.drop(['headlines_str', 'descriptions_str'], axis=1)
            
            # Calcular métricas derivadas
            grouped['spend'] = grouped['cost_micros'] / 1_000_000
            grouped['ctr'] = (grouped['clicks'] / grouped['impressions'].replace(0, np.nan) * 100).fillna(0).round(2)
            grouped['avg_cpc'] = (grouped['spend'] / grouped['clicks'].replace(0, np.nan)).fillna(0).round(2)
            grouped['conv_rate'] = (grouped['conversions'] / grouped['clicks'].replace(0, np.nan) * 100).fillna(0).round(2)
            grouped['cpa'] = (grouped['spend'] / grouped['conversions'].replace(0, np.nan)).fillna(0).round(2)
            grouped['roas'] = (grouped['conversions_value'] / grouped['spend'].replace(0, np.nan)).fillna(0).round(2)
            
            # Obtener benchmarks
            benchmarks = self.db_service.get_account_benchmarks(customer_id)
            
            # Calcular health score
            grouped = self._calculate_health_scores(grouped, benchmarks)
            
            logger.info(f"✅ Procesados {len(grouped)} anuncios")
            return grouped
            
        except Exception as e:
            logger.error(f"❌ Error calculando ad health scores: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _calculate_health_scores(self, df: pd.DataFrame, benchmarks) -> pd.DataFrame:
        """
        Calcula componentes de health score
        
        Formula:
        - CTR Score (0-30): Comparado con promedio de campaña
        - Conv Rate Score (0-30): Comparado con benchmark
        - Impression Share Score (0-15): % de impression share
        - Policy Score (0-15): Estado de aprobación
        - Confidence Score (0-10): Basado en volumen de datos
        """
        
        target_conv_rate = benchmarks.target_conv_rate
        benchmark_ctr = benchmarks.benchmark_ctr
        
        # 1. CTR Score (0-30)
        df['ctr_decimal'] = df['ctr'] / 100
        df['ctr_score'] = np.minimum(
            (df['ctr_decimal'] / benchmark_ctr) * 30, 30
        ).fillna(0).round(2)
        
        # 2. Conversion Rate Score (0-30)
        df['conv_rate_decimal'] = df['conv_rate'] / 100
        df['conv_rate_score'] = np.minimum(
            (df['conv_rate_decimal'] / target_conv_rate) * 30, 30
        ).fillna(0).round(2)
        
        # 3. Impression Share Score (0-15) - Using CTR as proxy since impression share not available
        df['impression_share_score'] = np.minimum(
            (df['ctr_decimal'] / benchmark_ctr) * 15, 15
        ).fillna(0).round(2)
        
        # 4. Policy Score (0-15)
        def get_policy_score(row):
            if row['approval_status'] == 'APPROVED':
                return 15.0
            elif row['approval_status'] == 'APPROVED_LIMITED':
                return 10.0
            elif row['approval_status'] == 'UNDER_REVIEW':
                return 7.5
            else:  # DISAPPROVED
                return 0.0
        
        df['policy_score'] = df.apply(get_policy_score, axis=1)
        
        # 5. Confidence Score (0-10) - Basado en clicks
        df['confidence_score'] = np.minimum(
            df['clicks'] / 50 * 10, 10
        ).fillna(0).round(2)
        
        # TOTAL HEALTH SCORE (0-100)
        df['health_score_raw'] = (
            df['ctr_score'] +
            df['conv_rate_score'] +
            df['impression_share_score'] +
            df['policy_score'] +
            df['confidence_score']
        )
        
        # Ajustar por confianza de datos
        df['data_confidence'] = np.minimum(df['clicks'] / 30, 1.0)
        df['health_score'] = (df['health_score_raw'] * df['data_confidence']).round(2)
        
        # Categoría de salud
        def get_health_category(score):
            if score >= 70:
                return 'excellent'
            elif score >= 40:
                return 'good'
            elif score > 0:
                return 'warning'
            else:
                return 'critical'
        
        df['health_category'] = df['health_score'].apply(get_health_category)
        
        # Status emoji
        def get_health_emoji(score):
            if score >= 70:
                return '🟢'
            elif score >= 40:
                return '🟡'
            else:
                return '🔴'
        
        df['status_emoji'] = df['health_score'].apply(get_health_emoji)
        
        # Recommended action
        df['recommended_action'] = df.apply(self._get_recommended_action, axis=1)
        
        return df
    
    def _get_recommended_action(self, row) -> str:
        """Determina acción recomendada para un anuncio"""
        score = row['health_score']
        clicks = row['clicks']
        conversions = row['conversions']
        spend = row['spend']
        approval = row['approval_status']
        
        # Prioridad 1: Problemas de política
        if approval == 'DISAPPROVED':
            return 'fix_policy'
        
        # Prioridad 2: Anuncios vampiro
        if clicks > 30 and conversions == 0 and spend > 50:
            return 'pause'
        
        # Prioridad 3: Poco historial
        if clicks < 20:
            return 'monitor'
        
        # Prioridad 4: Bajo rendimiento
        if score < 30 and clicks > 50:
            return 'pause'
        
        # Prioridad 5: Rendimiento medio-bajo
        if 30 <= score < 50:
            return 'optimize_copy'
        
        # Prioridad 6: Buen rendimiento
        if 70 <= score < 85:
            return 'scale'
        
        # Prioridad 7: Excelente rendimiento
        if score >= 85:
            return 'scale_aggressive'
        
        return 'monitor'
    
    def get_vampire_ads(self, df: pd.DataFrame, min_spend: float = 50) -> pd.DataFrame:
        """Detecta anuncios vampiro (alto gasto, 0 conversiones)"""
        return df[
            (df['conversions'] == 0) &
            (df['spend'] >= min_spend) &
            (df['clicks'] > 30)
        ].sort_values('spend', ascending=False)
    
    def get_winner_ads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta anuncios ganadores (alto health score)"""
        return df[
            df['health_score'] >= 80
        ].sort_values('health_score', ascending=False)
    
    def get_dormant_ads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta anuncios dormidos (baja impression share)"""
        return df[
            (df['impression_share'] < 10) &
            (df['impressions'] < 100)
        ].sort_values('impression_share')
    
    def get_policy_issues(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta anuncios con problemas de política"""
        return df[
            df['approval_status'].isin(['DISAPPROVED', 'UNDER_REVIEW'])
        ].sort_values('spend', ascending=False)