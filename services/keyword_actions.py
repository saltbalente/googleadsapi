"""
Keyword Actions Service for Google Ads Dashboard
Handles keyword management actions like pause/resume, bid changes, etc.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from modules.google_ads_client import GoogleAdsClientWrapper
from google.ads.googleads.errors import GoogleAdsException
from utils.logger import get_logger, log_api_call
from utils.rate_limit import rate_limited

logger = get_logger(__name__)

class KeywordActionsService:
    """Service for performing actions on keywords"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        """
        Initialize keyword actions service
        
        Args:
            google_ads_client: Google Ads API client wrapper
        """
        self.client = google_ads_client
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "pause_keyword")
    def pause_keyword(self, customer_id: str, ad_group_criterion_id: str) -> Dict[str, Any]:
        """
        Pause a keyword
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_criterion_id: Ad group criterion ID (keyword ID) to pause
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_criterion_service = client.get_service("AdGroupCriterionService")
            
            # Create ad group criterion operation
            criterion_operation = client.get_type("AdGroupCriterionOperation")
            criterion = criterion_operation.update
            criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
                customer_id, ad_group_criterion_id.split('~')[0], ad_group_criterion_id.split('~')[1]
            )
            criterion.status = client.enums.AdGroupCriterionStatusEnum.PAUSED
            
            # Set field mask
            client.copy_from(
                criterion_operation.update_mask,
                client.field_mask.FieldMask(paths=["status"])
            )
            
            # Execute the operation
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=[criterion_operation]
            )
            
            logger.info(f"Keyword {ad_group_criterion_id} paused successfully for customer {customer_id}")
            return {
                "success": True,
                "message": f"Keyword paused successfully",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error pausing keyword: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error pausing keyword: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "resume_keyword")
    def resume_keyword(self, customer_id: str, ad_group_criterion_id: str) -> Dict[str, Any]:
        """
        Resume (enable) a keyword
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_criterion_id: Ad group criterion ID (keyword ID) to resume
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_criterion_service = client.get_service("AdGroupCriterionService")
            
            # Create ad group criterion operation
            criterion_operation = client.get_type("AdGroupCriterionOperation")
            criterion = criterion_operation.update
            criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
                customer_id, ad_group_criterion_id.split('~')[0], ad_group_criterion_id.split('~')[1]
            )
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            
            # Set field mask
            client.copy_from(
                criterion_operation.update_mask,
                client.field_mask.FieldMask(paths=["status"])
            )
            
            # Execute the operation
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=[criterion_operation]
            )
            
            logger.info(f"Keyword {ad_group_criterion_id} resumed successfully for customer {customer_id}")
            return {
                "success": True,
                "message": f"Keyword resumed successfully",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error resuming keyword: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error resuming keyword: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "update_keyword_bid")
    def update_keyword_bid(self, customer_id: str, ad_group_criterion_id: str, 
                          new_bid_micros: int) -> Dict[str, Any]:
        """
        Update keyword bid
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_criterion_id: Ad group criterion ID (keyword ID) to update
            new_bid_micros: New bid amount in micros (1 USD = 1,000,000 micros)
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_criterion_service = client.get_service("AdGroupCriterionService")
            
            # Create ad group criterion operation
            criterion_operation = client.get_type("AdGroupCriterionOperation")
            criterion = criterion_operation.update
            criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
                customer_id, ad_group_criterion_id.split('~')[0], ad_group_criterion_id.split('~')[1]
            )
            criterion.cpc_bid_micros = new_bid_micros
            
            # Set field mask
            client.copy_from(
                criterion_operation.update_mask,
                client.field_mask.FieldMask(paths=["cpc_bid_micros"])
            )
            
            # Execute the operation
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=[criterion_operation]
            )
            
            logger.info(f"Keyword {ad_group_criterion_id} bid updated to {new_bid_micros} micros for customer {customer_id}")
            return {
                "success": True,
                "message": f"Keyword bid updated successfully to ${new_bid_micros / 1_000_000:.2f}",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error updating keyword bid: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error updating keyword bid: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=3)
    @log_api_call("", "bulk_pause_keywords")
    def bulk_pause_keywords(self, customer_id: str, ad_group_criterion_ids: List[str]) -> Dict[str, Any]:
        """
        Pause multiple keywords in bulk
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_criterion_ids: List of ad group criterion IDs (keyword IDs) to pause
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_criterion_service = client.get_service("AdGroupCriterionService")
            operations = []
            
            for criterion_id in ad_group_criterion_ids:
                criterion_operation = client.get_type("AdGroupCriterionOperation")
                criterion = criterion_operation.update
                criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
                    customer_id, criterion_id.split('~')[0], criterion_id.split('~')[1]
                )
                criterion.status = client.enums.AdGroupCriterionStatusEnum.PAUSED
                
                client.copy_from(
                    criterion_operation.update_mask,
                    client.field_mask.FieldMask(paths=["status"])
                )
                operations.append(criterion_operation)
            
            # Execute bulk operation
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=operations
            )
            
            logger.info(f"Bulk paused {len(ad_group_criterion_ids)} keywords for customer {customer_id}")
            return {
                "success": True,
                "message": f"Successfully paused {len(ad_group_criterion_ids)} keywords",
                "results": [result.resource_name for result in response.results]
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error in bulk pause keywords: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error in bulk pause keywords: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=3)
    @log_api_call("", "bulk_resume_keywords")
    def bulk_resume_keywords(self, customer_id: str, ad_group_criterion_ids: List[str]) -> Dict[str, Any]:
        """
        Resume multiple keywords in bulk
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_criterion_ids: List of ad group criterion IDs (keyword IDs) to resume
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_criterion_service = client.get_service("AdGroupCriterionService")
            operations = []
            
            for criterion_id in ad_group_criterion_ids:
                criterion_operation = client.get_type("AdGroupCriterionOperation")
                criterion = criterion_operation.update
                criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
                    customer_id, criterion_id.split('~')[0], criterion_id.split('~')[1]
                )
                criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                
                client.copy_from(
                    criterion_operation.update_mask,
                    client.field_mask.FieldMask(paths=["status"])
                )
                operations.append(criterion_operation)
            
            # Execute bulk operation
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=operations
            )
            
            logger.info(f"Bulk resumed {len(ad_group_criterion_ids)} keywords for customer {customer_id}")
            return {
                "success": True,
                "message": f"Successfully resumed {len(ad_group_criterion_ids)} keywords",
                "results": [result.resource_name for result in response.results]
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error in bulk resume keywords: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error in bulk resume keywords: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def get_keyword_status(self, customer_id: str, ad_group_criterion_id: str) -> Dict[str, Any]:
        """
        Get current status of a keyword
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_criterion_id: Ad group criterion ID (keyword ID) to check
            
        Returns:
            Dictionary with keyword status information
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            # Parse the criterion ID to get ad group and criterion parts
            parts = ad_group_criterion_id.split('~')
            if len(parts) != 2:
                return {"success": False, "message": "Invalid criterion ID format"}
            
            ad_group_id, criterion_id = parts
            
            query = f"""
                SELECT 
                    ad_group_criterion.criterion_id,
                    ad_group_criterion.status,
                    ad_group_criterion.cpc_bid_micros,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group.name,
                    campaign.name
                FROM ad_group_criterion 
                WHERE ad_group_criterion.criterion_id = {criterion_id}
                AND ad_group.id = {ad_group_id}
                AND ad_group_criterion.type = 'KEYWORD'
            """
            
            ga_service = client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)
            
            for row in response:
                return {
                    "success": True,
                    "criterion_id": str(row.ad_group_criterion.criterion_id),
                    "status": row.ad_group_criterion.status.name,
                    "cpc_bid_micros": row.ad_group_criterion.cpc_bid_micros,
                    "keyword_text": row.ad_group_criterion.keyword.text,
                    "match_type": row.ad_group_criterion.keyword.match_type.name,
                    "ad_group_name": row.ad_group.name,
                    "campaign_name": row.campaign.name
                }
            
            return {"success": False, "message": "Keyword not found"}
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error getting keyword status: {ex}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error getting keyword status: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}