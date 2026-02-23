"""
Autonomous Cross-Domain Integration Engine Core
MISSION: Enable seamless AI module integration across diverse domains for autonomous ecosystem evolution
ARCHITECTURE: Registry-based discovery with standardized communication protocols and orchestration
"""

import json
import logging
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Callable, Type, Union
from enum import Enum
import inspect
from datetime import datetime
import uuid
import traceback

# Core Firestore dependency - CRITICAL for state management
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud import firestore as google_firestore
    FIREBASE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Firebase dependencies not available: {e}")
    FIREBASE_AVAILABLE = False

# Configure logging for ecosystem tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # stdout for ecosystem tracking
        logging.FileHandler('integration_engine.log')
    ]
)
logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Module lifecycle states with clear transitions"""
    REGISTERED = "registered"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    DEPRECATED = "deprecated"
    ERROR = "error"


class DomainCategory(Enum):
    """Core domain categories for module classification"""
    DATA_PROCESSING = "data_processing"
    NLP = "natural_language_processing"
    COMPUTER_VISION = "computer_vision"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    AUTONOMOUS_PLANNING = "autonomous_planning"
    API_INTEGRATION = "api_integration"
    STORAGE = "storage"
    MONITORING = "monitoring"
    UNKNOWN = "unknown"


@dataclass
class CapabilitySignature:
    """Structured definition of a module's capability with type hints"""
    name: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    description: str
    version: str = "1.0.0"
    requires_context: bool = False
    timeout_seconds: int = 30
    is_async: bool = False


@dataclass
class ModuleMetadata:
    """Comprehensive metadata for AI module registration"""
    module_id: str
    module_name: str
    domain: DomainCategory
    version: str
    capabilities: List[CapabilitySignature]
    dependencies: List[str] = field(default_factory=list)
    status: ModuleStatus = ModuleStatus.REGISTERED
    health_score: float = 1.0
    last_heartbeat: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    endpoint: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-serializable dictionary"""
        data = asdict(self)
        data['domain'] = self.domain.value
        data['status'] = self.status.value
        data['capabilities'] = [asdict(cap) for cap in self.capabilities]
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_heartbeat:
            data['last_heartbeat'] = self.last_heartbeat.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleMetadata':
        """Reconstruct from Firestore dictionary"""
        data = data.copy()
        data['domain'] = DomainCategory(data['domain'])
        data['status'] = ModuleStatus(data['status'])
        data['capabilities'] = [
            CapabilitySignature(**cap) for cap in data['capabilities']
        ]
        for date_field in ['created_at', 'updated_at', 'last_heartbeat']:
            if date_field in data and data[date_field]:
                data[date_field] = datetime.fromisoformat(data[date_field])
        return cls(**data)


class IntegrationMessage:
    """
    Standardized communication protocol between modules
    Enables cross-domain interoperability
    """
    
    def __init__(
        self,
        message_id: Optional[str] = None,
        source_module: Optional[str] = None,
        target_module: Optional[str] = None,
        capability: Optional[str] = None,
        payload: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message_id = message_id or str(uuid.uuid4())
        self.source_module = source_module
        self.target_module = target_module
        self.capability = capability
        self.payload = payload or {}
        self.context = context or {}
        self.metadata = metadata or {
            'created_at': datetime.utcnow().isoformat(),
            'priority': 'normal',
            'retry_count': 0
        }
        self.errors: List[str] = []
    
    def validate(self) -> bool:
        """Validate message structure and required fields"""
        if not self.source_module:
            self.errors.append("Missing source_module")
        if not self.capability:
            self.errors.append("Missing capability")
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize message for transmission"""
        return {
            'message