"""
Webhook Service for managing webhook endpoints and processing.
"""
import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import re

from ..models.schemas import (
    WebhookPayload, WebhookEndpoint, WebhookStatus,
    WebhookLog, WebhookFilter
)

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for webhook endpoint management and processing."""
    
    def __init__(self):
        self.endpoints = {}  # In production, use database
        self.webhook_logs = {}
        
    async def initialize(self):
        """Initialize webhook service."""
        logger.info("Initializing Webhook Service...")
        
        # Create some default endpoints for demo
        demo_endpoint = WebhookEndpoint(
            id="demo-endpoint",
            name="Demo Endpoint",
            description="Demo webhook endpoint for testing",
            path="/demo",
            allowed_methods=["POST", "GET"],
            is_active=True
        )
        self.endpoints["demo-endpoint"] = demo_endpoint
        
    async def cleanup(self):
        """Cleanup webhook service resources."""
        logger.info("Cleaning up Webhook Service...")
        
    async def health_check(self) -> Dict[str, Any]:
        """Check webhook service health."""
        try:
            return {
                "status": "healthy",
                "endpoints_count": len(self.endpoints),
                "active_endpoints": len([e for e in self.endpoints.values() if e.is_active])
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def create_endpoint(
        self, 
        user_id: str, 
        endpoint: WebhookEndpoint
    ) -> str:
        """Create a new webhook endpoint."""
        try:
            # Generate endpoint ID if not provided
            if not endpoint.id:
                endpoint.id = f"ep_{uuid.uuid4().hex[:12]}"
            
            # Generate path if not provided
            if not endpoint.path:
                endpoint.path = f"/{endpoint.name.lower().replace(' ', '-')}"
            
            # Set metadata
            endpoint.user_id = user_id
            endpoint.created_at = datetime.utcnow()
            
            # Validate path uniqueness
            existing_paths = [e.path for e in self.endpoints.values()]
            if endpoint.path in existing_paths:
                endpoint.path = f"{endpoint.path}-{uuid.uuid4().hex[:6]}"
            
            # Store endpoint
            self.endpoints[endpoint.id] = endpoint
            
            logger.info(f"Created endpoint {endpoint.id} for user {user_id}")
            return endpoint.id
            
        except Exception as e:
            logger.error(f"Failed to create endpoint: {e}")
            raise
    
    async def list_endpoints(self, user_id: str) -> List[WebhookEndpoint]:
        """List all webhook endpoints for a user."""
        try:
            user_endpoints = [
                endpoint for endpoint in self.endpoints.values()
                if endpoint.user_id == user_id
            ]
            return user_endpoints
        except Exception as e:
            logger.error(f"Failed to list endpoints: {e}")
            raise
    
    async def get_endpoint(self, user_id: str, endpoint_id: str) -> Optional[WebhookEndpoint]:
        """Get specific webhook endpoint."""
        try:
            endpoint = self.endpoints.get(endpoint_id)
            if endpoint and endpoint.user_id == user_id:
                return endpoint
            return None
        except Exception as e:
            logger.error(f"Failed to get endpoint: {e}")
            raise
    
    async def update_endpoint(
        self, 
        user_id: str, 
        endpoint_id: str, 
        endpoint_data: WebhookEndpoint
    ):
        """Update webhook endpoint."""
        try:
            existing_endpoint = await self.get_endpoint(user_id, endpoint_id)
            if not existing_endpoint:
                raise ValueError("Endpoint not found")
            
            # Update fields
            for field, value in endpoint_data.dict(exclude_unset=True).items():
                if field not in ['id', 'user_id', 'created_at']:
                    setattr(existing_endpoint, field, value)
            
            logger.info(f"Updated endpoint {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to update endpoint: {e}")
            raise
    
    async def delete_endpoint(self, user_id: str, endpoint_id: str):
        """Delete webhook endpoint."""
        try:
            endpoint = await self.get_endpoint(user_id, endpoint_id)
            if not endpoint:
                raise ValueError("Endpoint not found")
            
            del self.endpoints[endpoint_id]
            logger.info(f"Deleted endpoint {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete endpoint: {e}")
            raise
    
    async def process_webhook(self, webhook_data: WebhookPayload):
        """Process received webhook."""
        try:
            start_time = datetime.utcnow()
            
            # Validate endpoint exists and is active
            endpoint = self.endpoints.get(webhook_data.endpoint_id)
            if not endpoint or not endpoint.is_active:
                webhook_data.status = WebhookStatus.FAILED
                logger.warning(f"Webhook for inactive/missing endpoint: {webhook_data.endpoint_id}")
                return
            
            # Check method is allowed
            if webhook_data.method not in endpoint.allowed_methods:
                webhook_data.status = WebhookStatus.FAILED
                logger.warning(f"Method {webhook_data.method} not allowed for endpoint {webhook_data.endpoint_id}")
                return
            
            # Process the webhook
            await self._execute_webhook_processing(webhook_data, endpoint)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            webhook_data.processing_time_ms = processing_time
            webhook_data.status = WebhookStatus.PROCESSED
            
            # Create log entry
            log_entry = WebhookLog(
                id=str(uuid.uuid4()),
                webhook_id=webhook_data.id,
                endpoint_id=webhook_data.endpoint_id,
                method=webhook_data.method,
                status=webhook_data.status,
                timestamp=webhook_data.timestamp,
                processing_time_ms=processing_time
            )
            
            self.webhook_logs[log_entry.id] = log_entry
            
            logger.info(f"Processed webhook {webhook_data.id} in {processing_time:.2f}ms")
            
        except Exception as e:
            webhook_data.status = WebhookStatus.FAILED
            logger.error(f"Webhook processing failed: {e}")
    
    async def _execute_webhook_processing(self, webhook_data: WebhookPayload, endpoint: WebhookEndpoint):
        """Execute webhook-specific processing logic."""
        try:
            # Extract and analyze payload
            await self._analyze_payload(webhook_data)
            
            # Apply any endpoint-specific processing
            if endpoint.custom_response:
                await self._apply_custom_processing(webhook_data, endpoint.custom_response)
            
            # Trigger relay rules (handled by RelayService)
            from .relay_service import RelayService
            relay_service = RelayService()
            await relay_service.process_webhook_for_relay(webhook_data)
            
        except Exception as e:
            logger.error(f"Webhook execution failed: {e}")
            raise
    
    async def _analyze_payload(self, webhook_data: WebhookPayload):
        """Analyze webhook payload for insights."""
        try:
            analysis = {
                "content_type": webhook_data.headers.get("content-type", "unknown"),
                "payload_size": len(str(webhook_data.body)) if webhook_data.body else 0,
                "has_signature": any("signature" in key.lower() for key in webhook_data.headers.keys()),
                "json_payload": isinstance(webhook_data.body, dict),
                "timestamp_analyzed": datetime.utcnow().isoformat()
            }
            
            # Store analysis in webhook data
            if not hasattr(webhook_data, 'analysis'):
                webhook_data.analysis = analysis
                
        except Exception as e:
            logger.warning(f"Payload analysis failed: {e}")
    
    async def _apply_custom_processing(self, webhook_data: WebhookPayload, custom_config: Dict[str, Any]):
        """Apply custom processing logic based on endpoint configuration."""
        try:
            # Extract fields if specified
            if "extract_fields" in custom_config:
                extracted = {}
                for field_path in custom_config["extract_fields"]:
                    value = self._extract_field_value(webhook_data.body, field_path)
                    if value is not None:
                        extracted[field_path] = value
                webhook_data.extracted_fields = extracted
            
            # Apply transformations
            if "transformations" in custom_config:
                for transform in custom_config["transformations"]:
                    await self._apply_transformation(webhook_data, transform)
            
            logger.debug(f"Applied custom processing for webhook {webhook_data.id}")
            
        except Exception as e:
            logger.error(f"Custom processing failed: {e}")
    
    def _extract_field_value(self, data: Any, field_path: str) -> Any:
        """Extract value from nested data using dot notation."""
        try:
            if not data or not field_path:
                return None
            
            parts = field_path.split('.')
            current = data
            
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    current = current[index] if 0 <= index < len(current) else None
                else:
                    return None
                
                if current is None:
                    break
            
            return current
            
        except Exception:
            return None
    
    async def _apply_transformation(self, webhook_data: WebhookPayload, transform_config: Dict[str, Any]):
        """Apply a single transformation to webhook data."""
        try:
            transform_type = transform_config.get("type")
            
            if transform_type == "add_header":
                new_headers = transform_config.get("headers", {})
                webhook_data.headers.update(new_headers)
            
            elif transform_type == "filter_body":
                fields = transform_config.get("fields", [])
                if isinstance(webhook_data.body, dict) and fields:
                    filtered_body = {k: v for k, v in webhook_data.body.items() if k in fields}
                    webhook_data.body = filtered_body
            
            elif transform_type == "add_timestamp":
                if isinstance(webhook_data.body, dict):
                    webhook_data.body["processed_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.warning(f"Transformation failed: {e}")
    
    async def get_webhook_logs(
        self, 
        user_id: str, 
        filters: WebhookFilter, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[WebhookLog]:
        """Get webhook logs with filtering."""
        try:
            # Get user's endpoint IDs
            user_endpoints = await self.list_endpoints(user_id)
            user_endpoint_ids = {ep.id for ep in user_endpoints}
            
            # Filter logs
            filtered_logs = []
            for log in self.webhook_logs.values():
                # Check if log belongs to user's endpoints
                if log.endpoint_id not in user_endpoint_ids:
                    continue
                
                # Apply filters
                if filters.endpoint_id and log.endpoint_id != filters.endpoint_id:
                    continue
                
                if filters.method and log.method != filters.method:
                    continue
                
                if filters.status and log.status != filters.status:
                    continue
                
                if filters.start_date and log.timestamp < filters.start_date:
                    continue
                
                if filters.end_date and log.timestamp > filters.end_date:
                    continue
                
                filtered_logs.append(log)
            
            # Sort by timestamp (newest first)
            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            return filtered_logs[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to get webhook logs: {e}")
            raise
    
    async def get_endpoint_statistics(self, user_id: str, endpoint_id: str, days: int = 7) -> Dict[str, Any]:
        """Get statistics for a specific endpoint."""
        try:
            # Verify endpoint ownership
            endpoint = await self.get_endpoint(user_id, endpoint_id)
            if not endpoint:
                raise ValueError("Endpoint not found")
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Filter logs for this endpoint
            endpoint_logs = [
                log for log in self.webhook_logs.values()
                if log.endpoint_id == endpoint_id and start_date <= log.timestamp <= end_date
            ]
            
            # Calculate statistics
            total_requests = len(endpoint_logs)
            successful_requests = len([log for log in endpoint_logs if log.status == WebhookStatus.PROCESSED])
            failed_requests = total_requests - successful_requests
            
            # Method breakdown
            method_counts = {}
            for log in endpoint_logs:
                method_counts[log.method] = method_counts.get(log.method, 0) + 1
            
            # Average processing time
            processing_times = [log.processing_time_ms for log in endpoint_logs if log.processing_time_ms]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            return {
                "endpoint_id": endpoint_id,
                "period_days": days,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "average_processing_time_ms": round(avg_processing_time, 2),
                "requests_by_method": method_counts,
                "recent_activity": endpoint_logs[:10]  # Last 10 requests
            }
            
        except Exception as e:
            logger.error(f"Failed to get endpoint statistics: {e}")
            raise