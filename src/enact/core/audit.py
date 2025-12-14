from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Protocol, Any, Dict, Optional
import json

@dataclass
class AuditLog:
    """Represents a single audit entry."""
    timestamp: datetime
    agent_id: str
    tool: str
    function: str
    arguments: Dict[str, Any]
    allow: bool
    reason: str
    duration_ms: float
    correlation_id: Optional[str] = None

class Auditor(Protocol):
    """Protocol for audit loggers."""
    def log(self, entry: AuditLog) -> None:
        ...

class JsonLineAuditor:
    """
    Appends audit logs to a file in JSON Lines format.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath

    def log(self, entry: AuditLog) -> None:
        # Convert dataclass to dict
        data = asdict(entry)
        
        # Serialize datetime
        data['timestamp'] = entry.timestamp.isoformat()
        
        # Write to file
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')

class HTTPAuditor:
    """
    Sends audit logs to an HTTP endpoint.
    Useful for integrating with external logging services, webhooks, or monitoring platforms.
    """
    def __init__(self, url: str, headers: Dict[str, str] = None, timeout: int = 5):
        """
        Args:
            url: The HTTP endpoint to send logs to
            headers: Optional HTTP headers (e.g., for authentication)
            timeout: Request timeout in seconds
        """
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout

    def log(self, entry: AuditLog) -> None:
        import requests
        
        # Convert dataclass to dict
        data = asdict(entry)
        
        # Serialize datetime
        data['timestamp'] = entry.timestamp.isoformat()
        
        try:
            response = requests.post(
                self.url,
                json=data,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            # Log the error but don't crash the governance flow
            # In production, you might want to use a proper logger here
            print(f"HTTPAuditor failed to send log: {e}")

class SyslogAuditor:
    """
    Sends audit logs to a syslog server.
    Compatible with standard syslog daemons (rsyslog, syslog-ng, etc.)
    """
    def __init__(self, host: str = 'localhost', port: int = 514, facility: int = 16):
        """
        Args:
            host: Syslog server hostname
            port: Syslog server port (default 514 for UDP)
            facility: Syslog facility code (default 16 = local0)
        """
        import logging
        import logging.handlers
        
        self.logger = logging.getLogger('enact.audit')
        self.logger.setLevel(logging.INFO)
        
        # Create syslog handler
        handler = logging.handlers.SysLogHandler(
            address=(host, port),
            facility=facility
        )
        
        # Format: structured for easy parsing
        formatter = logging.Formatter('enact-audit: %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, entry: AuditLog) -> None:
        # Convert to dict
        data = asdict(entry)
        data['timestamp'] = entry.timestamp.isoformat()
        
        # Log as JSON for structured logging
        self.logger.info(json.dumps(data))

class CloudWatchAuditor:
    """
    Sends audit logs to AWS CloudWatch Logs.
    Requires boto3 and AWS credentials configured.
    """
    def __init__(self, log_group: str, log_stream: str, region: str = 'us-east-1'):
        """
        Args:
            log_group: CloudWatch log group name
            log_stream: CloudWatch log stream name
            region: AWS region
        """
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 is required for CloudWatchAuditor. Install with: pip install boto3")
        
        self.log_group = log_group
        self.log_stream = log_stream
        self.client = boto3.client('logs', region_name=region)
        self.sequence_token = None
        
        # Ensure log group and stream exist
        self._ensure_log_stream()

    def _ensure_log_stream(self):
        """Create log group and stream if they don't exist."""
        try:
            self.client.create_log_group(logGroupName=self.log_group)
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass
        
        try:
            self.client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

    def log(self, entry: AuditLog) -> None:
        # Convert to dict
        data = asdict(entry)
        data['timestamp'] = entry.timestamp.isoformat()
        
        # CloudWatch expects timestamp in milliseconds
        timestamp_ms = int(entry.timestamp.timestamp() * 1000)
        
        log_event = {
            'timestamp': timestamp_ms,
            'message': json.dumps(data)
        }
        
        try:
            kwargs = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [log_event]
            }
            
            if self.sequence_token:
                kwargs['sequenceToken'] = self.sequence_token
            
            response = self.client.put_log_events(**kwargs)
            self.sequence_token = response.get('nextSequenceToken')
            
        except Exception as e:
            print(f"CloudWatchAuditor failed to send log: {e}")
