import requests
import logging 
from .bolt_schemas import FleetOrder, Vehicle, PortalStatus, Driver, FleetStateLog
from typing import List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Client:
    """Client for interacting with Bolt Fleet Integration API.
    
    This client handles authentication, token management, and provides methods
    to retrieve fleet orders, vehicles, drivers, and fleet state logs from
    the Bolt API. It automatically manages access token refresh when tokens
    expire or become invalid.
    
    Attributes:
        base_url: Base URL for the Bolt API
        client_id: OAuth client ID for authentication
        client_secret: OAuth client secret for authentication
        access_token: Current access token (automatically refreshed when needed)
    """
    
    def __init__(self):
        self.client_id = os.getenv("BOLT_CLIENT_ID")
        self.client_secret = os.getenv("BOLT_CLIENT_SECRET")
        self.base_url = os.getenv("BOLT_API_URL")
        self.access_token = None
        self._ensure_token()

    def get_access_token(self) -> str:
        """Get a new access token from Bolt OIDC.
        
        Requests a new access token using client credentials grant type.
        The token is used for authenticating subsequent API requests.
        
        Returns:
            str: The access token string
            
        Raises:
            Exception: If the token request fails or no token is received
        """
        logger.info("Requesting new access token from Bolt OIDC")
        response = requests.post(
            "https://oidc.bolt.eu/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "fleet-integration:api"
            }
        )
        if response.status_code != 200:
            logger.error(f"Failed to get access token: {response.status_code} {response.text}")
            raise Exception(f"Failed to get access token: {response.status_code} {response.text}")
        token = response.json().get("access_token")
        if not token:
            raise Exception("No access token received in response")
        logger.info("Successfully obtained access token")
        return token
    
    def _ensure_token(self):
        """Ensure access token is set. Refresh if not configured.
        
        Private method that checks if an access token exists. If not,
        it automatically fetches a new token. This is called during
        initialization and before API requests.
        """
        if not self.access_token:
            self.access_token = self.get_access_token()
    
    def _refresh_token_if_needed(self, response) -> bool:
        """Check if token needs refresh based on response and refresh if needed.
        
        Analyzes the API response to determine if the access token has expired
        or is invalid. If so, automatically refreshes the token.
        
        Args:
            response: The HTTP response object from the API request
            
        Returns:
            bool: True if token was refreshed, False otherwise
            
        Note:
            Checks for HTTP 401 status code or response code 503 to detect
            token expiration or invalidity.
        """
        try:
            response_data = response.json()
            # Check for 503 or token-related errors
            if response.status_code == 401 or response_data.get('code') == 503:
                logger.warning("Access token expired or invalid, refreshing...")
                self.access_token = self.get_access_token()
                return True
        except Exception:
            # If response is not JSON or parsing fails, check status code
            if response.status_code == 401:
                logger.warning("Unauthorized response, refreshing token...")
                self.access_token = self.get_access_token()
                return True
        return False
    
    def get_fleet_orders(self, offset: int, limit: int, company_ids: List[int], start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[FleetOrder]:
        """Get fleet orders from Bolt API with automatic token refresh.
        
        Retrieves fleet orders for the specified companies within a time range.
        Automatically handles token refresh if the current token is expired.
        
        Args:
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            company_ids: List of company IDs to filter orders
            start_ts: Start timestamp (Unix timestamp in seconds). Defaults to
                24 hours ago if not provided.
            end_ts: End timestamp (Unix timestamp in seconds). Defaults to
                current time if not provided.
                
        Returns:
            List[FleetOrder]: List of FleetOrder objects representing the orders
            
        Raises:
            Exception: If the API request fails or returns an error status code
            
        Note:
            If start_ts or end_ts is None, defaults to a one-day interval
            (last 24 hours). Automatically retries the request once if token
            refresh is needed.
        """
        self._ensure_token()
        
        # Use default one-day interval if timestamps not provided
        if start_ts is None:
            start_ts = int((datetime.now() - timedelta(days=1)).timestamp())
        if end_ts is None:
            end_ts = int(datetime.now().timestamp())
        
        # First attempt
        response = requests.post(
            f"{self.base_url}/getFleetOrders",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
            json={
                "offset": offset,
                "limit": limit,
                "company_ids": company_ids,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "time_range_filter_type": "price_review"
            }
        )
        
        # Refresh token if needed and retry once
        if self._refresh_token_if_needed(response):
            logger.info("Retrying request with new token...")
            response = requests.post(
                f"{self.base_url}/getFleetOrders",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
                json={
                    "offset": offset,
                    "limit": limit,
                    "company_ids": company_ids,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "time_range_filter_type": "price_review"
                }
            )
            
        if response.status_code != 200:
            logger.error(f"Failed to get fleet orders: {response.status_code} {response.text}")
            raise Exception(f"Failed to get fleet orders: {response.status_code} {response.text}")
        return [FleetOrder(**order) for order in response.json().get("data", {}).get("orders", [])]

    def get_vehicles(self, offset: int, limit: int, company_id: int, portal_status: PortalStatus, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[Vehicle]:
        """Get vehicles from Bolt API with automatic token refresh.
        
        Retrieves vehicles for the specified company filtered by portal status
        within a time range. Automatically handles token refresh if the current
        token is expired.
        
        Args:
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            company_id: Company ID to filter vehicles
            portal_status: Portal status filter (e.g., active, inactive)
            start_ts: Start timestamp (Unix timestamp in seconds). Defaults to
                24 hours ago if not provided.
            end_ts: End timestamp (Unix timestamp in seconds). Defaults to
                current time if not provided.
                
        Returns:
            List[Vehicle]: List of Vehicle objects representing the vehicles
            
        Raises:
            Exception: If the API request fails or returns an error status code
            
        Note:
            If start_ts or end_ts is None, defaults to a one-day interval
            (last 24 hours). Automatically retries the request once if token
            refresh is needed.
        """
        self._ensure_token()
        
        # Use default one-day interval if timestamps not provided
        if start_ts is None:
            start_ts = int((datetime.now() - timedelta(days=1)).timestamp())
        if end_ts is None:
            end_ts = int(datetime.now().timestamp())
        
        # Handle portal_status - support both enum and direct values
        portal_status_value = portal_status.value if hasattr(portal_status, 'value') else portal_status
        
        # First attempt
        response = requests.post(
            f"{self.base_url}/getVehicles",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
            json={
                "offset": offset,
                "limit": limit,
                "company_id": company_id,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "portal_status": portal_status_value
            }
        )
        
        # Refresh token if needed and retry once
        if self._refresh_token_if_needed(response):
            logger.info("Retrying request with new token...")
            response = requests.post(
                f"{self.base_url}/getVehicles",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
                json={
                    "offset": offset,
                    "limit": limit,
                    "company_id": company_id,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "portal_status": portal_status_value
                }
            )
        
        if response.status_code != 200:
            logger.error(f"Failed to get vehicles: {response.status_code} {response.text}")
            raise Exception(f"Failed to get vehicles: {response.status_code} {response.text}")
        return [Vehicle(**vehicle) for vehicle in response.json().get("data", {}).get("vehicles", [])]

    def get_drivers(self, offset: int, limit: int, company_id: int, portal_status: PortalStatus, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[Driver]:
        """Get drivers from Bolt API with automatic token refresh.
        
        Retrieves drivers for the specified company filtered by portal status
        within a time range. Automatically handles token refresh if the current
        token is expired.
        
        Args:
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            company_id: Company ID to filter drivers
            portal_status: Portal status filter (e.g., active, inactive)
            start_ts: Start timestamp (Unix timestamp in seconds). Defaults to
                24 hours ago if not provided.
            end_ts: End timestamp (Unix timestamp in seconds). Defaults to
                current time if not provided.
                
        Returns:
            List[Driver]: List of Driver objects representing the drivers
            
        Raises:
            Exception: If the API request fails or returns an error status code
            
        Note:
            If start_ts or end_ts is None, defaults to a one-day interval
            (last 24 hours). Automatically retries the request once if token
            refresh is needed.
        """
        self._ensure_token()
        
        # Use default one-day interval if timestamps not provided
        if start_ts is None:
            start_ts = int((datetime.now() - timedelta(days=1)).timestamp())
        if end_ts is None:
            end_ts = int(datetime.now().timestamp())
        
        # Handle portal_status - support both enum and direct values
        portal_status_value = portal_status.value if hasattr(portal_status, 'value') else portal_status
        
        # First attempt
        response = requests.post(
            f"{self.base_url}/getDrivers",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
            json={
                "offset": offset,
                "limit": limit,
                "company_id": company_id,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "portal_status": portal_status_value
            }
        )
        
        # Refresh token if needed and retry once
        if self._refresh_token_if_needed(response):
            logger.info("Retrying request with new token...")
            response = requests.post(
                f"{self.base_url}/getDrivers",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
                json={
                    "offset": offset,
                    "limit": limit,
                    "company_id": company_id,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "portal_status": portal_status_value
                }
            )
        
        if response.status_code != 200:
            logger.error(f"Failed to get drivers: {response.status_code} {response.text}")
            raise Exception(f"Failed to get drivers: {response.status_code} {response.text}")
        return [Driver(**driver) for driver in response.json().get("data", {}).get("drivers", [])]


    def get_fleet_state_logs(self, offset: int, limit: int, company_id: int, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[FleetStateLog]:
        """Get fleet state logs from Bolt API with automatic token refresh.
        
        Retrieves fleet state logs for the specified company within a time range.
        Fleet state logs track changes in fleet status over time. Automatically
        handles token refresh if the current token is expired.
        
        Args:
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            company_id: Company ID to filter state logs
            start_ts: Start timestamp (Unix timestamp in seconds). Defaults to
                24 hours ago if not provided.
            end_ts: End timestamp (Unix timestamp in seconds). Defaults to
                current time if not provided.
                
        Returns:
            List[FleetStateLog]: List of FleetStateLog objects representing
                the state log entries
            
        Raises:
            Exception: If the API request fails or returns an error status code
            
        Note:
            If start_ts or end_ts is None, defaults to a one-day interval
            (last 24 hours). Automatically retries the request once if token
            refresh is needed.
        """
        self._ensure_token()
        
        # Use default one-day interval if timestamps not provided
        if start_ts is None:
            start_ts = int((datetime.now() - timedelta(days=1)).timestamp())
        if end_ts is None:
            end_ts = int(datetime.now().timestamp())
        
        # First attempt
        response = requests.post(
            f"{self.base_url}/getFleetStateLogs",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
            json={
                "offset": offset,
                "limit": limit,
                "company_id": company_id,
                "start_ts": start_ts,
                "end_ts": end_ts
            }
        )
        
        # Refresh token if needed and retry once
        if self._refresh_token_if_needed(response):
            logger.info("Retrying request with new token...")
            response = requests.post(
                f"{self.base_url}/getFleetStateLogs",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.access_token}"},
                json={
                    "offset": offset,
                    "limit": limit,
                    "company_id": company_id,
                    "start_ts": start_ts,
                    "end_ts": end_ts
                }
            )
        
        if response.status_code != 200:
            logger.error(f"Failed to get fleet state logs: {response.status_code} {response.text}")
            raise Exception(f"Failed to get fleet state logs: {response.status_code} {response.text}")
        return [FleetStateLog(**log) for log in response.json().get("data", {}).get("state_logs", [])]


def create_client() -> Client:
    """Create a new Client instance.
    
    Returns:
        Client: A new Client instance
    """
    return Client()
