"""
Relay Service for forwarding and replaying webhooks.
"""
import asyncio
import logging
import uuid
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
import ipaddress
import socket
from urllib.parse import urlsplit

from ..models.schemas import (
    RelayRule, WebhookPayload, RelayResult, RelayCondition,
    WebhookTransformation, FilterOperator, TransformationType
)

logger = logging.getLogger(__name__)
SENSITIVE_RELAY_HEADERS = {
    "authorization",
    "cookie",
    "host",
    "content-length",
    "connection",
    "proxy-authorization",
}


async def validate_public_target_url(value: str) -> str:
    """Allow only HTTPS targets whose complete DNS answer is public."""
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("relay target must be an HTTPS URL without credentials or fragments")
    loop = asyncio.get_running_loop()
    try:
        answers = await loop.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("relay target hostname could not be resolved") from exc
    if not answers:
        raise ValueError("relay target hostname has no DNS answers")
    for answer in answers:
        address = ipaddress.ip_address(answer[4][0])
        if not address.is_global:
            raise ValueError("relay target resolves to a non-public address")
    return value

class RelayService:
    """Service for webhook relaying and replay functionality."""
    
    def __init__(self):
        self.relay_rules = {}  # In production, use database
        self.relay_results = {}
        self.session = None
        
    async def initialize(self):
        """Initialize relay service."""
        logger.info("Initializing Relay Service...")
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Create demo relay rule
        demo_rule = RelayRule(
            id="demo-relay",
            name="Demo Relay Rule",
            description="Demo rule for webhook relaying",
            source_endpoint_id="demo-endpoint",
            target_urls=["https://httpbin.org/post"],
            is_active=True
        )
        self.relay_rules["demo-relay"] = demo_rule
        
    async def cleanup(self):
        """Cleanup relay service resources."""
        logger.info("Cleaning up Relay Service...")
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check relay service health."""
        try:
            return {
                "status": "healthy",
                "active_rules": len([r for r in self.relay_rules.values() if r.is_active]),
                "total_rules": len(self.relay_rules),
                "session_active": self.session is not None and not self.session.closed
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def create_rule(self, user_id: str, relay_rule: RelayRule) -> str:
        """Create a new relay rule."""
        try:
            # Generate rule ID if not provided
            if not relay_rule.id:
                relay_rule.id = f"rule_{uuid.uuid4().hex[:12]}"
            
            # Set metadata
            relay_rule.user_id = user_id
            relay_rule.created_at = datetime.utcnow()
            
            # Validate rule
            await self._validate_relay_rule(relay_rule)
            
            # Store rule
            self.relay_rules[relay_rule.id] = relay_rule
            
            logger.info(f"Created relay rule {relay_rule.id} for user {user_id}")
            return relay_rule.id
            
        except Exception as e:
            logger.error(f"Failed to create relay rule: {e}")
            raise
    
    async def list_rules(self, user_id: str) -> List[RelayRule]:
        """List all relay rules for a user."""
        try:
            user_rules = [
                rule for rule in self.relay_rules.values()
                if rule.user_id == user_id
            ]
            return user_rules
        except Exception as e:
            logger.error(f"Failed to list relay rules: {e}")
            raise
    
    async def get_rule(self, user_id: str, rule_id: str) -> Optional[RelayRule]:
        """Get specific relay rule."""
        try:
            rule = self.relay_rules.get(rule_id)
            if rule and rule.user_id == user_id:
                return rule
            return None
        except Exception as e:
            logger.error(f"Failed to get relay rule: {e}")
            raise
    
    async def update_rule(self, user_id: str, rule_id: str, rule_data: RelayRule):
        """Update relay rule."""
        try:
            existing_rule = await self.get_rule(user_id, rule_id)
            if not existing_rule:
                raise ValueError("Relay rule not found")
            
            # Validate updated rule
            rule_data.id = rule_id
            rule_data.user_id = user_id
            await self._validate_relay_rule(rule_data)
            
            # Update fields
            for field, value in rule_data.dict(exclude_unset=True).items():
                if field not in ['id', 'user_id', 'created_at']:
                    setattr(existing_rule, field, value)
            
            logger.info(f"Updated relay rule {rule_id}")
            
        except Exception as e:
            logger.error(f"Failed to update relay rule: {e}")
            raise
    
    async def delete_rule(self, user_id: str, rule_id: str):
        """Delete relay rule."""
        try:
            rule = await self.get_rule(user_id, rule_id)
            if not rule:
                raise ValueError("Relay rule not found")
            
            del self.relay_rules[rule_id]
            logger.info(f"Deleted relay rule {rule_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete relay rule: {e}")
            raise
    
    async def _validate_relay_rule(self, rule: RelayRule):
        """Validate relay rule configuration."""
        try:
            # Check target URLs are valid
            if not rule.target_urls:
                raise ValueError("At least one target URL is required")
            for target_url in rule.target_urls:
                await validate_public_target_url(str(target_url))
            
            # Validate conditions
            for condition in rule.conditions:
                if not condition.field or not condition.value:
                    raise ValueError("Condition field and value are required")
                
                # Validate field format
                if not re.match(r'^(header|body|query)\..+$', condition.field):
                    raise ValueError("Invalid condition field format. Use header.*, body.*, or query.*")
            
            # Validate transformations
            for transform in rule.transformations:
                if not transform.config:
                    raise ValueError("Transformation config is required")
            
            # Check timeout and retry settings
            if rule.timeout_seconds <= 0 or rule.timeout_seconds > 300:
                raise ValueError("Timeout must be between 1 and 300 seconds")
            
            if rule.retry_attempts < 0 or rule.retry_attempts > 10:
                raise ValueError("Retry attempts must be between 0 and 10")
            
        except Exception as e:
            logger.error(f"Relay rule validation failed: {e}")
            raise
    
    async def process_webhook_for_relay(self, webhook_data: WebhookPayload):
        """Process webhook for potential relaying."""
        try:
            # Find matching relay rules
            matching_rules = await self._find_matching_rules(webhook_data)
            
            if not matching_rules:
                logger.debug(f"No matching relay rules for webhook {webhook_data.id}")
                return
            
            # Process each matching rule
            relay_tasks = []
            for rule in matching_rules:
                if rule.is_active:
                    task = asyncio.create_task(
                        self._execute_relay_rule(webhook_data, rule)
                    )
                    relay_tasks.append(task)
            
            # Execute all relays concurrently
            if relay_tasks:
                relay_results = await asyncio.gather(*relay_tasks, return_exceptions=True)
                
                # Store results
                webhook_data.relay_results = []
                for i, result in enumerate(relay_results):
                    if isinstance(result, Exception):
                        logger.error(f"Relay task failed: {result}")
                        webhook_data.relay_results.append({
                            "rule_id": matching_rules[i].id,
                            "status": "error",
                            "error": str(result)
                        })
                    else:
                        webhook_data.relay_results.extend(result)
            
        except Exception as e:
            logger.error(f"Webhook relay processing failed: {e}")
    
    async def _find_matching_rules(self, webhook_data: WebhookPayload) -> List[RelayRule]:
        """Find relay rules that match the webhook."""
        try:
            matching_rules = []
            
            for rule in self.relay_rules.values():
                if rule.source_endpoint_id != webhook_data.endpoint_id:
                    continue
                
                # Check conditions
                if await self._check_conditions(webhook_data, rule.conditions):
                    matching_rules.append(rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"Failed to find matching rules: {e}")
            return []
    
    async def _check_conditions(self, webhook_data: WebhookPayload, conditions: List[RelayCondition]) -> bool:
        """Check if webhook matches all conditions."""
        try:
            if not conditions:
                return True  # No conditions means match all
            
            for condition in conditions:
                if not await self._evaluate_condition(webhook_data, condition):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Condition checking failed: {e}")
            return False
    
    async def _evaluate_condition(self, webhook_data: WebhookPayload, condition: RelayCondition) -> bool:
        """Evaluate a single condition."""
        try:
            # Extract field value
            field_parts = condition.field.split('.', 1)
            if len(field_parts) != 2:
                return False
            
            field_type, field_name = field_parts
            actual_value = None
            
            if field_type == "header":
                actual_value = webhook_data.headers.get(field_name, "")
            elif field_type == "query":
                actual_value = webhook_data.query_params.get(field_name, "")
            elif field_type == "body":
                if isinstance(webhook_data.body, dict):
                    actual_value = self._get_nested_value(webhook_data.body, field_name)
                else:
                    actual_value = str(webhook_data.body) if webhook_data.body else ""
            
            if actual_value is None:
                return False
            
            # Convert to string for comparison
            actual_str = str(actual_value).lower()
            expected_str = condition.value.lower()
            
            # Apply operator
            if condition.operator == FilterOperator.EQUALS:
                return actual_str == expected_str
            elif condition.operator == FilterOperator.CONTAINS:
                return expected_str in actual_str
            elif condition.operator == FilterOperator.STARTS_WITH:
                return actual_str.startswith(expected_str)
            elif condition.operator == FilterOperator.ENDS_WITH:
                return actual_str.endswith(expected_str)
            elif condition.operator == FilterOperator.REGEX:
                return bool(re.search(condition.value, actual_str, re.IGNORECASE))
            
            return False
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        try:
            parts = path.split('.')
            current = data
            
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
                
                if current is None:
                    break
            
            return current
            
        except Exception:
            return None
    
    async def _execute_relay_rule(self, webhook_data: WebhookPayload, rule: RelayRule) -> List[Dict[str, Any]]:
        """Execute a relay rule for a webhook."""
        try:
            # Apply transformations
            transformed_data = await self._apply_transformations(webhook_data, rule.transformations)
            
            # Relay to all target URLs
            relay_tasks = []
            for target_url in rule.target_urls:
                task = asyncio.create_task(
                    self._relay_to_target(transformed_data, str(target_url), rule)
                )
                relay_tasks.append(task)
            
            # Execute all relays
            results = await asyncio.gather(*relay_tasks, return_exceptions=True)
            
            # Process results
            relay_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    relay_results.append({
                        "rule_id": rule.id,
                        "target_url": str(rule.target_urls[i]),
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    relay_results.append(result)
            
            return relay_results
            
        except Exception as e:
            logger.error(f"Relay rule execution failed: {e}")
            raise
    
    async def _apply_transformations(self, webhook_data: WebhookPayload, transformations: List[WebhookTransformation]) -> WebhookPayload:
        """Apply transformations to webhook data."""
        try:
            # Create a copy of the webhook data
            transformed_data = webhook_data.copy(deep=True)
            
            for transform in transformations:
                await self._apply_single_transformation(transformed_data, transform)
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return webhook_data
    
    async def _apply_single_transformation(self, webhook_data: WebhookPayload, transform: WebhookTransformation):
        """Apply a single transformation."""
        try:
            if transform.type == TransformationType.ADD_HEADER:
                headers_to_add = transform.config.get("headers", {})
                webhook_data.headers.update(headers_to_add)
            
            elif transform.type == TransformationType.REMOVE_HEADER:
                headers_to_remove = transform.config.get("headers", [])
                for header in headers_to_remove:
                    webhook_data.headers.pop(header, None)
            
            elif transform.type == TransformationType.MODIFY_BODY:
                if isinstance(webhook_data.body, dict):
                    modifications = transform.config.get("modifications", {})
                    webhook_data.body.update(modifications)
            
            elif transform.type == TransformationType.ADD_QUERY_PARAM:
                params_to_add = transform.config.get("params", {})
                webhook_data.query_params.update(params_to_add)
            
            elif transform.type == TransformationType.JSON_PATH:
                # Extract specific fields from JSON body
                if isinstance(webhook_data.body, dict):
                    paths = transform.config.get("paths", [])
                    extracted = {}
                    for path in paths:
                        value = self._get_nested_value(webhook_data.body, path)
                        if value is not None:
                            extracted[path.replace('.', '_')] = value
                    webhook_data.body = extracted
            
        except Exception as e:
            logger.warning(f"Single transformation failed: {e}")
    
    async def _relay_to_target(self, webhook_data: WebhookPayload, target_url: str, rule: RelayRule) -> Dict[str, Any]:
        """Relay webhook to a single target URL."""
        start_time = datetime.utcnow()
        
        try:
            # Prepare request data
            headers = {
                key: value
                for key, value in webhook_data.headers.items()
                if key.lower() not in SENSITIVE_RELAY_HEADERS
            }
            headers['Content-Type'] = 'application/json'
            headers['X-Webhook-Relay-Id'] = webhook_data.id
            headers['X-Webhook-Source'] = webhook_data.endpoint_id
            
            # Prepare body
            if isinstance(webhook_data.body, (dict, list)):
                body_data = json.dumps(webhook_data.body)
            else:
                body_data = webhook_data.body or ""
            
            # Make request with retries
            for attempt in range(rule.retry_attempts + 1):
                try:
                    safe_target_url = await validate_public_target_url(target_url)
                    timeout = aiohttp.ClientTimeout(total=rule.timeout_seconds)
                    async with self.session.request(
                        method=webhook_data.method,
                        url=safe_target_url,
                        headers=headers,
                        data=body_data,
                        timeout=timeout,
                        allow_redirects=False,
                    ) as response:
                        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                        response_text = await response.text()
                        
                        result = RelayResult(
                            target_url=target_url,
                            status_code=response.status,
                            success=200 <= response.status < 300,
                            response_time_ms=response_time,
                            response_headers=dict(response.headers),
                            response_body=response_text[:1000],  # Limit response body
                            timestamp=datetime.utcnow()
                        )
                        
                        if result.success:
                            logger.info(f"Relay successful: {target_url} (attempt {attempt + 1})")
                            return result.dict()
                        else:
                            logger.warning(f"Relay failed: {target_url} - {response.status}")
                            if attempt == rule.retry_attempts:
                                result.error_message = f"HTTP {response.status}: {response_text[:200]}"
                                return result.dict()
                            
                except asyncio.TimeoutError:
                    if attempt == rule.retry_attempts:
                        return RelayResult(
                            target_url=target_url,
                            success=False,
                            response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                            error_message="Request timeout",
                            timestamp=datetime.utcnow()
                        ).dict()
                    await asyncio.sleep(1)  # Wait before retry
                    
                except Exception as e:
                    if attempt == rule.retry_attempts:
                        return RelayResult(
                            target_url=target_url,
                            success=False,
                            response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                            error_message=str(e),
                            timestamp=datetime.utcnow()
                        ).dict()
                    await asyncio.sleep(1)  # Wait before retry
            
        except Exception as e:
            logger.error(f"Relay to {target_url} failed: {e}")
            return RelayResult(
                target_url=target_url,
                success=False,
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                error_message=str(e),
                timestamp=datetime.utcnow()
            ).dict()
    
    async def replay_webhook(self, webhook_data: WebhookPayload, target_urls: List[str]):
        """Replay a webhook to specified URLs."""
        try:
            logger.info(f"Starting webhook replay for {webhook_data.id} to {len(target_urls)} targets")
            
            # Create temporary relay rule for replay
            temp_rule = RelayRule(
                id=f"replay_{uuid.uuid4().hex[:8]}",
                name="Temporary Replay Rule",
                source_endpoint_id=webhook_data.endpoint_id,
                target_urls=target_urls,
                retry_attempts=1,
                timeout_seconds=30
            )
            
            # Execute relay
            results = await self._execute_relay_rule(webhook_data, temp_rule)
            
            # Store replay results
            replay_id = str(uuid.uuid4())
            self.relay_results[replay_id] = {
                "replay_id": replay_id,
                "webhook_id": webhook_data.id,
                "targets": target_urls,
                "results": results,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Webhook replay completed: {replay_id}")
            return replay_id
            
        except Exception as e:
            logger.error(f"Webhook replay failed: {e}")
            raise
