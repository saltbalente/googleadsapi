"""
Campaign Actions Service for Google Ads Dashboard
Handles campaign management actions like pause/resume, budget changes, etc.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from modules.google_ads_client import GoogleAdsClientWrapper
from google.ads.googleads.errors import GoogleAdsException
from utils.logger import get_logger, log_api_call
from utils.rate_limit import rate_limited

logger = get_logger(__name__)

class CampaignActionsService:
    """Service for performing actions on campaigns"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        """
        Initialize campaign actions service
        
        Args:
            google_ads_client: Google Ads API client wrapper
        """
        self.client = google_ads_client
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "pause_campaign")
    def pause_campaign(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """
        Pause a campaign
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID to pause
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            campaign_service = client.get_service("CampaignService")
            
            # Create campaign operation
            campaign_operation = client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
            campaign.status = client.enums.CampaignStatusEnum.PAUSED
            
            # Set field mask
            client.copy_from(
                campaign_operation.update_mask,
                client.field_mask.FieldMask(paths=["status"])
            )
            
            # Execute the operation
            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=[campaign_operation]
            )
            
            logger.info(f"Campaign {campaign_id} paused successfully for customer {customer_id}")
            return {
                "success": True,
                "message": f"Campaign paused successfully",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error pausing campaign: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error pausing campaign: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "resume_campaign")
    def resume_campaign(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """
        Resume (enable) a campaign
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID to resume
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            campaign_service = client.get_service("CampaignService")
            
            # Create campaign operation
            campaign_operation = client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
            campaign.status = client.enums.CampaignStatusEnum.ENABLED
            
            # Set field mask
            client.copy_from(
                campaign_operation.update_mask,
                client.field_mask.FieldMask(paths=["status"])
            )
            
            # Execute the operation
            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=[campaign_operation]
            )
            
            logger.info(f"Campaign {campaign_id} resumed successfully for customer {customer_id}")
            return {
                "success": True,
                "message": f"Campaign resumed successfully",
                "resource_name": response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error resuming campaign: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error resuming campaign: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=5)
    @log_api_call("", "update_campaign_budget")
    def update_campaign_budget(self, customer_id: str, campaign_id: str, 
                             new_budget_micros: int) -> Dict[str, Any]:
        """
        Update campaign budget
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID to update
            new_budget_micros: New budget amount in micros (1 USD = 1,000,000 micros)
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            # First, get the campaign to find its budget
            campaign_service = client.get_service("CampaignService")
            campaign_resource = campaign_service.campaign_path(customer_id, campaign_id)
            
            # Get campaign details
            query = f"""
                SELECT 
                    campaign.id,
                    campaign.name,
                    campaign.campaign_budget
                FROM campaign 
                WHERE campaign.id = {campaign_id}
            """
            
            ga_service = client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)
            
            campaign_budget_resource = None
            for row in response:
                campaign_budget_resource = row.campaign.campaign_budget
                break
            
            if not campaign_budget_resource:
                return {"success": False, "message": "Campaign budget not found"}
            
            # Update the budget
            budget_service = client.get_service("CampaignBudgetService")
            budget_operation = client.get_type("CampaignBudgetOperation")
            budget = budget_operation.update
            budget.resource_name = campaign_budget_resource
            budget.amount_micros = new_budget_micros
            
            # Set field mask
            client.copy_from(
                budget_operation.update_mask,
                client.field_mask.FieldMask(paths=["amount_micros"])
            )
            
            # Execute the operation
            budget_response = budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_operation]
            )
            
            logger.info(f"Campaign {campaign_id} budget updated to {new_budget_micros} micros for customer {customer_id}")
            return {
                "success": True,
                "message": f"Campaign budget updated successfully to ${new_budget_micros / 1_000_000:.2f}",
                "resource_name": budget_response.results[0].resource_name
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error updating campaign budget: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error updating campaign budget: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=3)
    @log_api_call("", "bulk_pause_campaigns")
    def bulk_pause_campaigns(self, customer_id: str, campaign_ids: List[str]) -> Dict[str, Any]:
        """
        Pause multiple campaigns in bulk
        
        Args:
            customer_id: Google Ads customer ID
            campaign_ids: List of campaign IDs to pause
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            campaign_service = client.get_service("CampaignService")
            operations = []
            
            for campaign_id in campaign_ids:
                campaign_operation = client.get_type("CampaignOperation")
                campaign = campaign_operation.update
                campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
                campaign.status = client.enums.CampaignStatusEnum.PAUSED
                
                client.copy_from(
                    campaign_operation.update_mask,
                    client.field_mask.FieldMask(paths=["status"])
                )
                operations.append(campaign_operation)
            
            # Execute bulk operation
            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=operations
            )
            
            logger.info(f"Bulk paused {len(campaign_ids)} campaigns for customer {customer_id}")
            return {
                "success": True,
                "message": f"Successfully paused {len(campaign_ids)} campaigns",
                "results": [result.resource_name for result in response.results]
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error in bulk pause: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error in bulk pause: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    @rate_limited('mutate', tokens=3)
    @log_api_call("", "bulk_resume_campaigns")
    def bulk_resume_campaigns(self, customer_id: str, campaign_ids: List[str]) -> Dict[str, Any]:
        """
        Resume multiple campaigns in bulk
        
        Args:
            customer_id: Google Ads customer ID
            campaign_ids: List of campaign IDs to resume
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            campaign_service = client.get_service("CampaignService")
            operations = []
            
            for campaign_id in campaign_ids:
                campaign_operation = client.get_type("CampaignOperation")
                campaign = campaign_operation.update
                campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
                campaign.status = client.enums.CampaignStatusEnum.ENABLED
                
                client.copy_from(
                    campaign_operation.update_mask,
                    client.field_mask.FieldMask(paths=["status"])
                )
                operations.append(campaign_operation)
            
            # Execute bulk operation
            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=operations
            )
            
            logger.info(f"Bulk resumed {len(campaign_ids)} campaigns for customer {customer_id}")
            return {
                "success": True,
                "message": f"Successfully resumed {len(campaign_ids)} campaigns",
                "results": [result.resource_name for result in response.results]
            }
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error in bulk resume: {ex}"
            logger.error(error_msg)
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error in bulk resume: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def get_campaign_status(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """
        Get current status of a campaign
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID to check
            
        Returns:
            Dictionary with campaign status information
        """
        try:
            client = self.client.get_client()
            if not client:
                return {"success": False, "message": "Google Ads client not initialized"}
            
            query = f"""
                SELECT 
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.serving_status
                FROM campaign 
                WHERE campaign.id = {campaign_id}
            """
            
            ga_service = client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)
            
            for row in response:
                return {
                    "success": True,
                    "campaign_id": str(row.campaign.id),
                    "name": row.campaign.name,
                    "status": row.campaign.status.name,
                    "serving_status": row.campaign.serving_status.name
                }
            
            return {"success": False, "message": "Campaign not found"}
            
        except GoogleAdsException as ex:
            error_msg = f"Google Ads API error getting campaign status: {ex}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error getting campaign status: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}