# modules/ad_group_config.py (NUEVO ARCHIVO)
"""
Ad Group Configuration Model
Maneja la configuración de múltiples grupos de anuncios
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class AdGroupConfig:
    """Configuración de un grupo de anuncios individual"""
    group_name: str
    keywords: List[str]
    landing_url: str
    business_description: str
    group_index: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'group_name': self.group_name,
            'keywords': self.keywords,
            'landing_url': self.landing_url,
            'business_description': self.business_description,
            'group_index': self.group_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdGroupConfig':
        return cls(
            group_name=data.get('group_name', ''),
            keywords=data.get('keywords', []),
            landing_url=data.get('landing_url', ''),
            business_description=data.get('business_description', ''),
            group_index=data.get('group_index', 0)
        )


@dataclass
class CampaignAdGroupsConfig:
    """Configuración completa de la campaña con múltiples grupos"""
    
    # Configuración global
    num_ad_groups: int
    provider: str  # 'openai' | 'gemini'
    model: str
    temperature: float
    tone: str
    num_headlines: int
    num_descriptions: int
    
    # Configuración por grupo
    ad_groups: List[AdGroupConfig] = field(default_factory=list)
    
    # Metadata
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    
    def add_ad_group(self, group_config: AdGroupConfig) -> None:
        """Agrega un nuevo grupo de anuncios"""
        group_config.group_index = len(self.ad_groups)
        self.ad_groups.append(group_config)
    
    def get_ad_group(self, index: int) -> Optional[AdGroupConfig]:
        """Obtiene un grupo de anuncios por índice"""
        if 0 <= index < len(self.ad_groups):
            return self.ad_groups[index]
        return None
    
    def is_complete(self) -> bool:
        """Verifica si todos los grupos están configurados"""
        return len(self.ad_groups) == self.num_ad_groups
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'num_ad_groups': self.num_ad_groups,
            'provider': self.provider,
            'model': self.model,
            'temperature': self.temperature,
            'tone': self.tone,
            'num_headlines': self.num_headlines,
            'num_descriptions': self.num_descriptions,
            'ad_groups': [ag.to_dict() for ag in self.ad_groups],
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignAdGroupsConfig':
        config = cls(
            num_ad_groups=data.get('num_ad_groups', 1),
            provider=data.get('provider', 'openai'),
            model=data.get('model', 'gpt-4'),
            temperature=data.get('temperature', 0.7),
            tone=data.get('tone', 'profesional'),
            num_headlines=data.get('num_headlines', 15),
            num_descriptions=data.get('num_descriptions', 4),
            campaign_id=data.get('campaign_id'),
            campaign_name=data.get('campaign_name')
        )
        
        for ag_data in data.get('ad_groups', []):
            config.add_ad_group(AdGroupConfig.from_dict(ag_data))
        
        return config