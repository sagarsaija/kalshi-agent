import base64
import time
from typing import Any, Optional
import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, ec
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from app.config import get_settings


class KalshiClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.kalshi_base_url
        self.api_key_id = settings.api_key_id
        self.private_key = self._load_private_key(settings.private_key)
        self.client = httpx.AsyncClient(timeout=30.0)

    def _load_private_key(self, key_string: str):
        """Load the private key from string (handles both RSA and EC keys)."""
        # Normalize the key - handle case where headers exist but no newlines
        key_string = key_string.strip()
        
        # Extract the base64 content if headers are present but malformed
        if "-----BEGIN" in key_string and "-----END" in key_string:
            # Check if it's properly formatted (has newlines after header)
            if "-----BEGIN RSA PRIVATE KEY-----\n" not in key_string and "-----BEGIN EC PRIVATE KEY-----\n" not in key_string and "-----BEGIN PRIVATE KEY-----\n" not in key_string:
                # Headers exist but no newlines - extract and reformat
                import re
                match = re.search(r'-----BEGIN ([A-Z ]+)-----(.+)-----END \1-----', key_string)
                if match:
                    key_type = match.group(1)
                    key_body = match.group(2)
                    # Reformat with proper newlines
                    key_string = f"-----BEGIN {key_type}-----\n{key_body}\n-----END {key_type}-----"
        
        key_bytes = key_string.encode()
        
        # Try loading as PEM format
        try:
            private_key = serialization.load_pem_private_key(
                key_bytes,
                password=None,
                backend=default_backend()
            )
            return private_key
        except Exception:
            pass
        
        # If the key doesn't have headers, add them and try again
        if "-----BEGIN" not in key_string:
            # Try RSA format first (most common for Kalshi)
            pem_key = f"-----BEGIN RSA PRIVATE KEY-----\n{key_string}\n-----END RSA PRIVATE KEY-----"
            try:
                return serialization.load_pem_private_key(
                    pem_key.encode(),
                    password=None,
                    backend=default_backend()
                )
            except Exception:
                pass
            
            # Try EC key format
            pem_key = f"-----BEGIN EC PRIVATE KEY-----\n{key_string}\n-----END EC PRIVATE KEY-----"
            try:
                return serialization.load_pem_private_key(
                    pem_key.encode(),
                    password=None,
                    backend=default_backend()
                )
            except Exception:
                pass
            
            # Try PKCS8 format
            pem_key = f"-----BEGIN PRIVATE KEY-----\n{key_string}\n-----END PRIVATE KEY-----"
            try:
                return serialization.load_pem_private_key(
                    pem_key.encode(),
                    password=None,
                    backend=default_backend()
                )
            except Exception:
                pass
        
        raise ValueError("Could not load private key")

    def _sign_request(self, timestamp: str, method: str, path: str) -> str:
        """Sign the request using the private key with RSA-PSS."""
        message = f"{timestamp}{method}{path}".encode()
        
        # Check if EC or RSA key
        if isinstance(self.private_key, ec.EllipticCurvePrivateKey):
            signature = self.private_key.sign(
                message,
                ec.ECDSA(hashes.SHA256())
            )
        else:
            # RSA key - Kalshi requires RSA-PSS padding
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        
        return base64.b64encode(signature).decode()

    def _get_headers(self, method: str, path: str) -> dict:
        """Generate authentication headers for a request."""
        timestamp = str(int(time.time() * 1000))
        # Kalshi expects the full path including /trade-api/v2 prefix in signature
        full_path = f"/trade-api/v2{path}"
        signature = self._sign_request(timestamp, method, full_path)
        
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
        }

    async def _request(
        self, 
        method: str, 
        path: str, 
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> dict[str, Any]:
        """Make an authenticated request to the Kalshi API."""
        url = f"{self.base_url}{path}"
        headers = self._get_headers(method.upper(), path)
        
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
        )
        response.raise_for_status()
        return response.json()

    async def get_balance(self) -> dict[str, Any]:
        """Get current portfolio balance."""
        return await self._request("GET", "/portfolio/balance")

    async def get_positions(self, limit: int = 100, cursor: Optional[str] = None) -> dict[str, Any]:
        """Get current open positions."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", "/portfolio/positions", params=params)

    async def get_fills(
        self, 
        limit: int = 100, 
        cursor: Optional[str] = None,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None,
    ) -> dict[str, Any]:
        """Get trade fills (executed orders)."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts
        return await self._request("GET", "/portfolio/fills", params=params)

    async def get_settlements(
        self, 
        limit: int = 100, 
        cursor: Optional[str] = None
    ) -> dict[str, Any]:
        """Get settled positions."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", "/portfolio/settlements", params=params)

    async def get_portfolio_history(
        self,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None,
    ) -> dict[str, Any]:
        """Get historical portfolio values."""
        params = {}
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts
        return await self._request("GET", "/portfolio/history", params=params)

    async def get_market(self, ticker: str) -> dict[str, Any]:
        """Get market details by ticker."""
        return await self._request("GET", f"/markets/{ticker}")

    async def get_markets(
        self, 
        tickers: Optional[list[str]] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get multiple markets."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if tickers:
            params["tickers"] = ",".join(tickers)
        return await self._request("GET", "/markets", params=params)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_client: Optional[KalshiClient] = None


def get_kalshi_client() -> KalshiClient:
    global _client
    if _client is None:
        _client = KalshiClient()
    return _client
