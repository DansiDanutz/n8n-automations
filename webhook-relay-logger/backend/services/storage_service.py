"""
Storage Service for webhook data persistence and analytics.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from collections import defaultdict

from ..models.schemas import (
    WebhookPayload, WebhookLog, WebhookFilter,
    WebhookAnalytics, EndpointAnalytics
)

logger = logging.getLogger(__name__)

class StorageService:
    """Service for webhook data storage and analytics."""
    
    def __init__(self):
        self.webhooks = {}  # In production, use database
        self.webhook_logs = {}
        self.analytics_cache = {}
        
    async def initialize(self):
        """Initialize storage service."""
        logger.info("Initializing Storage Service...")
        
    async def cleanup(self):
        """Cleanup storage service resources."""
        logger.info("Cleaning up Storage Service...")
        
    async def health_check(self) -> Dict[str, Any]:
        """Check storage service health."""
        try:
            return {
                "status": "healthy",
                "stored_webhooks": len(self.webhooks),
                "log_entries": len(self.webhook_logs)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def store_webhook(self, webhook_data: WebhookPayload):
        """Store webhook data."""
        try:
            # Store main webhook data
            self.webhooks[webhook_data.id] = webhook_data
            
            # Create log entry
            log_entry = WebhookLog(
                id=f"log_{webhook_data.id}",
                webhook_id=webhook_data.id,
                endpoint_id=webhook_data.endpoint_id,
                method=webhook_data.method,
                status=webhook_data.status,
                timestamp=webhook_data.timestamp,
                processing_time_ms=webhook_data.processing_time_ms
            )
            
            self.webhook_logs[log_entry.id] = log_entry
            
            # Clear analytics cache for affected user/endpoint
            if webhook_data.user_id:
                cache_key = f"analytics_{webhook_data.user_id}"
                self.analytics_cache.pop(cache_key, None)
            
            logger.debug(f"Stored webhook {webhook_data.id}")
            
        except Exception as e:
            logger.error(f"Failed to store webhook: {e}")
            raise
    
    async def get_webhook(self, user_id: str, webhook_id: str) -> Optional[WebhookPayload]:
        """Get specific webhook by ID."""
        try:
            webhook = self.webhooks.get(webhook_id)
            if webhook and webhook.user_id == user_id:
                return webhook
            return None
        except Exception as e:
            logger.error(f"Failed to get webhook: {e}")
            return None
    
    async def get_webhooks(
        self, 
        user_id: str, 
        filters: WebhookFilter, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[WebhookLog]:
        """Get webhook logs with filtering."""
        try:
            # Get all logs for user's webhooks
            user_webhook_ids = {
                wh.id for wh in self.webhooks.values() 
                if wh.user_id == user_id
            }
            
            filtered_logs = []
            for log in self.webhook_logs.values():
                # Check if log belongs to user's webhooks
                if log.webhook_id not in user_webhook_ids:
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
                
                # Additional filtering based on webhook data
                webhook = self.webhooks.get(log.webhook_id)
                if webhook:
                    # Header filters
                    if filters.header_filters:
                        header_match = True
                        for header_key, header_value in filters.header_filters.items():
                            if header_key not in webhook.headers:
                                header_match = False
                                break
                            if header_value not in webhook.headers[header_key]:
                                header_match = False
                                break
                        if not header_match:
                            continue
                    
                    # Body content filter
                    if filters.body_contains:
                        body_str = json.dumps(webhook.body) if webhook.body else ""
                        if filters.body_contains.lower() not in body_str.lower():
                            continue
                
                filtered_logs.append(log)
            
            # Sort by timestamp (newest first)
            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            return filtered_logs[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to get webhooks: {e}")
            raise
    
    async def get_analytics(self, user_id: str, days: int = 7) -> WebhookAnalytics:
        """Get webhook analytics for user."""
        try:
            # Check cache
            cache_key = f"analytics_{user_id}_{days}"
            if cache_key in self.analytics_cache:
                cache_entry = self.analytics_cache[cache_key]
                if (datetime.utcnow() - cache_entry['timestamp']).seconds < 300:  # 5 min cache
                    return cache_entry['data']
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get user's webhooks
            user_webhooks = [
                wh for wh in self.webhooks.values()
                if wh.user_id == user_id and start_date <= wh.timestamp <= end_date
            ]
            
            # Calculate analytics
            total_webhooks = len(user_webhooks)
            successful_webhooks = len([wh for wh in user_webhooks if wh.status == "processed"])
            failed_webhooks = total_webhooks - successful_webhooks
            
            # Processing times
            processing_times = [wh.processing_time_ms for wh in user_webhooks if wh.processing_time_ms]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Method breakdown
            method_counts = defaultdict(int)
            for wh in user_webhooks:
                method_counts[wh.method] += 1
            
            # Endpoint breakdown
            endpoint_counts = defaultdict(int)
            for wh in user_webhooks:
                endpoint_counts[wh.endpoint_id] += 1
            
            # Status breakdown
            status_counts = defaultdict(int)
            for wh in user_webhooks:
                status_counts[wh.status] += 1
            
            # Hourly volume
            hourly_volume = self._calculate_hourly_volume(user_webhooks, days)
            
            # Top sources
            source_counts = defaultdict(int)
            for wh in user_webhooks:
                source_ip = wh.headers.get('x-forwarded-for', wh.headers.get('remote-addr', 'unknown'))
                source_counts[source_ip] += 1
            
            top_sources = [
                {"source": source, "count": count}
                for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            analytics = WebhookAnalytics(
                total_webhooks=total_webhooks,
                successful_webhooks=successful_webhooks,
                failed_webhooks=failed_webhooks,
                average_processing_time_ms=round(avg_processing_time, 2),
                webhooks_by_method=dict(method_counts),
                webhooks_by_endpoint=dict(endpoint_counts),
                webhooks_by_status=dict(status_counts),
                hourly_volume=hourly_volume,
                top_sources=top_sources
            )
            
            # Cache result
            self.analytics_cache[cache_key] = {
                'data': analytics,
                'timestamp': datetime.utcnow()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            raise
    
    async def get_endpoint_analytics(self, user_id: str, endpoint_id: str, days: int = 7) -> EndpointAnalytics:
        """Get analytics for specific endpoint."""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get endpoint webhooks
            endpoint_webhooks = [
                wh for wh in self.webhooks.values()
                if (wh.user_id == user_id and 
                    wh.endpoint_id == endpoint_id and 
                    start_date <= wh.timestamp <= end_date)
            ]
            
            if not endpoint_webhooks:
                return EndpointAnalytics(
                    endpoint_id=endpoint_id,
                    total_requests=0,
                    success_rate=0,
                    average_response_time_ms=0,
                    requests_by_method={},
                    recent_activity=[]
                )
            
            # Calculate metrics
            total_requests = len(endpoint_webhooks)
            successful_requests = len([wh for wh in endpoint_webhooks if wh.status == "processed"])
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Processing times
            processing_times = [wh.processing_time_ms for wh in endpoint_webhooks if wh.processing_time_ms]
            avg_response_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Method breakdown
            method_counts = defaultdict(int)
            for wh in endpoint_webhooks:
                method_counts[wh.method] += 1
            
            # Recent activity
            recent_webhooks = sorted(endpoint_webhooks, key=lambda x: x.timestamp, reverse=True)[:10]
            recent_activity = [
                {
                    "timestamp": wh.timestamp.isoformat(),
                    "method": wh.method,
                    "status": wh.status,
                    "processing_time_ms": wh.processing_time_ms
                }
                for wh in recent_webhooks
            ]
            
            return EndpointAnalytics(
                endpoint_id=endpoint_id,
                total_requests=total_requests,
                success_rate=round(success_rate, 2),
                average_response_time_ms=round(avg_response_time, 2),
                requests_by_method=dict(method_counts),
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"Failed to get endpoint analytics: {e}")
            raise
    
    def _calculate_hourly_volume(self, webhooks: List[WebhookPayload], days: int) -> List[Dict[str, Any]]:
        """Calculate hourly webhook volume."""
        try:
            # Create hourly buckets
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            hourly_counts = defaultdict(int)
            
            for webhook in webhooks:
                # Round to nearest hour
                hour_key = webhook.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour_key] += 1
            
            # Create continuous hourly data
            hourly_data = []
            current_hour = start_time.replace(minute=0, second=0, microsecond=0)
            
            while current_hour <= end_time:
                hourly_data.append({
                    "hour": current_hour.isoformat(),
                    "count": hourly_counts.get(current_hour, 0)
                })
                current_hour += timedelta(hours=1)
            
            return hourly_data
            
        except Exception as e:
            logger.error(f"Failed to calculate hourly volume: {e}")
            return []
    
    async def cleanup_old_data(self, retention_days: int = 30):
        """Clean up old webhook data."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Remove old webhooks
            old_webhook_ids = [
                wh_id for wh_id, wh in self.webhooks.items()
                if wh.timestamp < cutoff_date
            ]
            
            for wh_id in old_webhook_ids:
                del self.webhooks[wh_id]
            
            # Remove old logs
            old_log_ids = [
                log_id for log_id, log in self.webhook_logs.items()
                if log.timestamp < cutoff_date
            ]
            
            for log_id in old_log_ids:
                del self.webhook_logs[log_id]
            
            # Clear analytics cache
            self.analytics_cache.clear()
            
            logger.info(f"Cleaned up {len(old_webhook_ids)} webhooks and {len(old_log_ids)} logs")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def export_webhook_data(self, user_id: str, format: str = "json") -> Dict[str, Any]:
        """Export webhook data for user."""
        try:
            # Get all user webhooks
            user_webhooks = [
                wh for wh in self.webhooks.values()
                if wh.user_id == user_id
            ]
            
            if format.lower() == "json":
                return {
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "webhook_count": len(user_webhooks),
                    "webhooks": [wh.dict() for wh in user_webhooks]
                }
            else:
                raise ValueError("Unsupported export format")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise