"""
Ad Group Actions Service for Google Ads Dashboard
Handles ad group management actions like pause/resume, bid changes, etc.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from modules.google_ads_client import GoogleAdsClientWrapper
from google.ads.googleads.errors import GoogleAdsException
from utils.logger import get_logger, log_api_call
from utils.rate_limit import rate_limited

logger = get_logger(__name__)

class AdGroupActionsService:
    """Service for performing actions on ad groups"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        """
        Initialize ad group actions service
        
        Args:
            google_ads_client: Google Ads API client wrapper
        """
        self.client = google_ads_client
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "pause_ad_group")
    def pause_ad_group(self, customer_id: str, ad_group_id: str) -> Dict[str, Any]:
        """
        Pause an ad group
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID to pause
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_service = client.get_service("AdGroupService")
            
            # Create ad group operation
            ad_group_operation = client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update
            ad_group.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
            ad_group.status = client.enums.AdGroupStatusEnum.PAUSED
            
            # Set field mask
            client.copy_from(
                ad_group_operation.update_mask,
                client.field_mask.FieldMask(paths=["status"])
            )
            
            # Execute the operation
            response = ad_group_service.mutate_ad_groups(
                customer_id=customer_id,
                operations=[ad_group_operation]
            )
            
            logger.info(f"Ad group {ad_group_id} paused successfully for customer {customer_id}")
            return {
                "success": True,
                "message": f"Ad group paused successfully",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error pausing ad group: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error pausing ad group: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "resume_ad_group")
    def resume_ad_group(self, customer_id: str, ad_group_id: str) -> Dict[str, Any]:
        """
        Resume (enable) an ad group
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID to resume
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_service = client.get_service("AdGroupService")
            
            # Create ad group operation
            ad_group_operation = client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update
            ad_group.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
            ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
            
            # Set field mask
            client.copy_from(
                ad_group_operation.update_mask,
                client.field_mask.FieldMask(paths=["status"])
            )
            
            # Execute the operation
            response = ad_group_service.mutate_ad_groups(
                customer_id=customer_id,
                operations=[ad_group_operation]
            )
            
            logger.info(f"Ad group {ad_group_id} resumed successfully for customer {customer_id}")
            return {
                "success": True,
                "message": f"Ad group resumed successfully",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error resuming ad group: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error resuming ad group: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "update_ad_group_bid")
    def update_ad_group_bid(self, customer_id: str, ad_group_id: str, 
                           new_bid_micros: int) -> Dict[str, Any]:
        """
        Update ad group default bid
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID to update
            new_bid_micros: New bid amount in micros (1 USD = 1,000,000 micros)
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_service = client.get_service("AdGroupService")
            
            # Create ad group operation
            ad_group_operation = client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update
            ad_group.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
            ad_group.cpc_bid_micros = new_bid_micros
            
            # Set field mask
            client.copy_from(
                ad_group_operation.update_mask,
                client.field_mask.FieldMask(paths=["cpc_bid_micros"])
            )
            
            # Execute the operation
            response = ad_group_service.mutate_ad_groups(
                customer_id=customer_id,
                operations=[ad_group_operation]
            )
            
            logger.info(f"Ad group {ad_group_id} bid updated to {new_bid_micros} micros for customer {customer_id}")
            return {
                "success": True,
                "message": f"Ad group bid updated successfully to ${new_bid_micros / 1_000_000:.2f}",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error updating ad group bid: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error updating ad group bid: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=3)
    @log_api_call("", "bulk_pause_ad_groups")
    def bulk_pause_ad_groups(self, customer_id: str, ad_group_ids: List[str]) -> Dict[str, Any]:
        """
        Pause multiple ad groups in bulk
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_ids: List of ad group IDs to pause
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_service = client.get_service("AdGroupService")
            operations = []
            
            for ad_group_id in ad_group_ids:
                ad_group_operation = client.get_type("AdGroupOperation")
                ad_group = ad_group_operation.update
                ad_group.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
                ad_group.status = client.enums.AdGroupStatusEnum.PAUSED
                
                client.copy_from(
                    ad_group_operation.update_mask,
                    client.field_mask.FieldMask(paths=["status"])
                )
                operations.append(ad_group_operation)
            
            # Execute bulk operation
            response = ad_group_service.mutate_ad_groups(
                customer_id=customer_id,
                operations=operations
            )
            
            logger.info(f"Bulk paused {len(ad_group_ids)} ad groups for customer {customer_id}")
            return {
                "success": True,
                "message": f"Successfully paused {len(ad_group_ids)} ad groups",
                "results": [result.resource_name for result in response.results]
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error in bulk pause ad groups: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error in bulk pause ad groups: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=3)
    @log_api_call("", "bulk_resume_ad_groups")
    def bulk_resume_ad_groups(self, customer_id: str, ad_group_ids: List[str]) -> Dict[str, Any]:
        """
        Resume multiple ad groups in bulk
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_ids: List of ad group IDs to resume
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            ad_group_service = client.get_service("AdGroupService")
            operations = []
            
            for ad_group_id in ad_group_ids:
                ad_group_operation = client.get_type("AdGroupOperation")
                ad_group = ad_group_operation.update
                ad_group.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
                ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
                
                client.copy_from(
                    ad_group_operation.update_mask,
                    client.field_mask.FieldMask(paths=["status"])
                )
                operations.append(ad_group_operation)
            
            # Execute bulk operation
            response = ad_group_service.mutate_ad_groups(
                customer_id=customer_id,
                operations=operations
            )
            
            logger.info(f"Bulk resumed {len(ad_group_ids)} ad groups for customer {customer_id}")
            return {
                "success": True,
                "message": f"Successfully resumed {len(ad_group_ids)} ad groups",
                "results": [result.resource_name for result in response.results]
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error in bulk resume ad groups: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error in bulk resume ad groups: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def get_ad_group_status(self, customer_id: str, ad_group_id: str) -> Dict[str, Any]:
        """
        Get current status of an ad group
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID to check
            
        Returns:
            Dictionary with ad group status information
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            query = f"""
                SELECT 
                    ad_group.id,
                    ad_group.name,
                    ad_group.status,
                    ad_group.cpc_bid_micros,
                    campaign.name
                FROM ad_group 
                WHERE ad_group.id = {ad_group_id}
            """
            
            ga_service = client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)
            
            for row in response:
                return {
                    "success": True,
                    "ad_group_id": str(row.ad_group.id),
                    "name": row.ad_group.name,
                    "status": row.ad_group.status.name,
                    "cpc_bid_micros": row.ad_group.cpc_bid_micros,
                    "campaign_name": row.campaign.name
                }
            
            return {"success": False, "message": "Ad group not found"}
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error getting ad group status: {ex}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error getting ad group status: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}