"""Conduit Base Connector Interface"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class SyncResult:
    status: str
    rows_read: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_deleted: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    new_state: Optional[Dict[str, Any]] = None

    def to_dict(self):
        return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in self.__dict__.items()}

@dataclass
class SchemaField:
    name: str
    data_type: str
    nullable: bool = True
    description: str = ""
    is_primary_key: bool = False

@dataclass
class SchemaTable:
    name: str
    fields: List[SchemaField]
    description: str = ""

class BaseConnector(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", self.__class__.__name__)

    @abstractmethod
    def discover_schema(self) -> List[SchemaTable]: pass

    @abstractmethod
    def sync_full(self, table: str) -> SyncResult: pass

    @abstractmethod
    def sync_incremental(self, table: str, last_state: Dict[str, Any]) -> SyncResult: pass

    @abstractmethod
    def test_connection(self) -> bool: pass

    def get_merge_key(self, table: str) -> List[str]:
        return ["id"]
