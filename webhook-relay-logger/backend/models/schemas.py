"""
Pydantic models for Webhook Relay & Logger API.
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class HttpMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class WebhookStatus(str, Enum):
    """Webhook processing status."""
    RECEIVED = "received"
    PROCESSED = "processed"
    RELAYED = "relayed"
    FAILED = "failed"

class FilterOperator(str, Enum):
    """Filter operators."""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"

class TransformationType(str, Enum):
    """Transformation types."""
    ADD_HEADER = "add_header"
    REMOVE_HEADER = "remove_header"
    MODIFY_BODY = "modify_body"
    ADD_QUERY_PARAM = "add_query_param"
    JSON_PATH = "json_path"

class WebhookPayload(BaseModel):
    """Webhook payload model."""
    id: str = Field(..., description="Unique webhook ID")
    endpoint_id: str = Field(..., description="Endpoint identifier")
    method: str = Field(..., description="HTTP method")
    url: str = Field(..., description="Request URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    query_params: Dict[str, str] = Field(default_factory=dict, description="Query parameters")
    body: Optional[Union[Dict, List, str]] = Field(None, description="Request body")
    timestamp: datetime = Field(..., description="Webhook received timestamp")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    status: WebhookStatus = Field(default=WebhookStatus.RECEIVED, description="Processing status")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    relay_results: List[Dict[str, Any]] = Field(default_factory=list, description="Relay results")

class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration."""
    id: Optional[str] = Field(None, description="Endpoint ID")
    name: str = Field(..., description="Endpoint name")
    description: Optional[str] = Field(None, description="Endpoint description")
    path: str = Field(..., description="Endpoint path (auto-generated if not provided)")
    allowed_methods: List[HttpMethod] = Field(default=[HttpMethod.POST], description="Allowed HTTP methods")
    is_active: bool = Field(default=True, description="Whether endpoint is active")
    require_auth: bool = Field(default=False, description="Whether endpoint requires authentication")
    custom_response: Optional[Dict[str, Any]] = Field(None, description="Custom response configuration")
    rate_limit: Optional[int] = Field(None, description="Rate limit per minute")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    user_id: Optional[str] = Field(None, description="Owner user ID")

    @field_validator("path", mode="before")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.startswith('/'):
            value = f'/{value}'
        import re
        return re.sub(r'[^a-zA-Z0-9\-_/]', '', value)

class WebhookFilter(BaseModel):
    """Webhook filtering criteria."""
    endpoint_id: Optional[str] = Field(None, description="Filter by endpoint")
    method: Optional[str] = Field(None, description="Filter by HTTP method")
    status: Optional[WebhookStatus] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    header_filters: Dict[str, str] = Field(default_factory=dict, description="Header-based filters")
    body_contains: Optional[str] = Field(None, description="Body content filter")

class RelayCondition(BaseModel):
    """Relay condition model."""
    field: str = Field(..., description="Field to check (header.*, body.*, query.*)")
    operator: FilterOperator = Field(..., description="Comparison operator")
    value: str = Field(..., description="Value to compare against")

class WebhookTransformation(BaseModel):
    """Webhook transformation model."""
    type: TransformationType = Field(..., description="Transformation type")
    config: Dict[str, Any] = Field(..., description="Transformation configuration")

class RelayRule(BaseModel):
    """Webhook relay rule model."""
    id: Optional[str] = Field(None, description="Rule ID")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    source_endpoint_id: str = Field(..., description="Source endpoint ID")
    target_urls: List[HttpUrl] = Field(..., description="Target URLs to relay to")
    conditions: List[RelayCondition] = Field(default_factory=list, description="Relay conditions")
    transformations: List[WebhookTransformation] = Field(default_factory=list, description="Webhook transformations")
    is_active: bool = Field(default=True, description="Whether rule is active")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    user_id: Optional[str] = Field(None, description="Owner user ID")

class WebhookLog(BaseModel):
    """Webhook log entry model."""
    id: str = Field(..., description="Log entry ID")
    webhook_id: str = Field(..., description="Associated webhook ID")
    endpoint_id: str = Field(..., description="Endpoint ID")
    method: str = Field(..., description="HTTP method")
    status: WebhookStatus = Field(..., description="Processing status")
    timestamp: datetime = Field(..., description="Log timestamp")
    processing_time_ms: Optional[float] = Field(None, description="Processing time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    relay_count: int = Field(default=0, description="Number of relays triggered")

class ReplayRequest(BaseModel):
    """Webhook replay request model."""
    target_urls: List[HttpUrl] = Field(..., description="URLs to replay webhook to")
    modify_headers: Dict[str, str] = Field(default_factory=dict, description="Headers to add/modify")
    modify_body: Optional[Dict[str, Any]] = Field(None, description="Body modifications")
    
class RelayResult(BaseModel):
    """Result of a webhook relay attempt."""
    target_url: str = Field(..., description="Target URL")
    status_code: Optional[int] = Field(None, description="Response status code")
    success: bool = Field(..., description="Whether relay was successful")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    response_headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    response_body: Optional[str] = Field(None, description="Response body")
    timestamp: datetime = Field(..., description="Relay timestamp")

class WebhookAnalytics(BaseModel):
    """Webhook analytics model."""
    total_webhooks: int = Field(..., description="Total webhook count")
    successful_webhooks: int = Field(..., description="Successful webhook count")
    failed_webhooks: int = Field(..., description="Failed webhook count")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    webhooks_by_method: Dict[str, int] = Field(..., description="Breakdown by HTTP method")
    webhooks_by_endpoint: Dict[str, int] = Field(..., description="Breakdown by endpoint")
    webhooks_by_status: Dict[str, int] = Field(..., description="Breakdown by status")
    hourly_volume: List[Dict[str, Any]] = Field(..., description="Hourly webhook volume")
    top_sources: List[Dict[str, Any]] = Field(..., description="Top source IPs/hosts")

class EndpointAnalytics(BaseModel):
    """Endpoint-specific analytics."""
    endpoint_id: str = Field(..., description="Endpoint ID")
    total_requests: int = Field(..., description="Total requests")
    success_rate: float = Field(..., description="Success rate percentage")
    average_response_time_ms: float = Field(..., description="Average response time")
    requests_by_method: Dict[str, int] = Field(..., description="Requests by HTTP method")
    recent_activity: List[Dict[str, Any]] = Field(..., description="Recent activity")
    
class UserSettings(BaseModel):
    """User settings for webhook handling."""
    auto_relay: bool = Field(default=True, description="Enable automatic relaying")
    log_retention_days: int = Field(default=30, description="Log retention period")
    max_payload_size_mb: int = Field(default=10, description="Maximum payload size")
    notification_webhooks: List[HttpUrl] = Field(default_factory=list, description="Notification webhook URLs")
    default_timeout: int = Field(default=30, description="Default relay timeout")

class AuthToken(BaseModel):
    """Authentication token model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

class UserRegistration(BaseModel):
    """User registration model."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=8)
    name: str = Field(..., description="User name")

class UserLogin(BaseModel):
    """User login model."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class APIError(BaseModel):
    """API error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    webhook_id: Optional[str] = Field(None, description="Related webhook ID if applicable")
