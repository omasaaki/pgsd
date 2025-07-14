"""Schema data models for PGSD application."""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ObjectType(Enum):
    """Database object type enumeration."""

    TABLE = "table"
    VIEW = "view"
    SEQUENCE = "sequence"
    FUNCTION = "function"
    PROCEDURE = "procedure"
    TRIGGER = "trigger"
    INDEX = "index"
    CONSTRAINT = "constraint"


class ConstraintType(Enum):
    """Constraint type enumeration."""

    PRIMARY_KEY = "PRIMARY KEY"
    FOREIGN_KEY = "FOREIGN KEY"
    UNIQUE = "UNIQUE"
    CHECK = "CHECK"
    NOT_NULL = "NOT NULL"


class IndexType(Enum):
    """Index type enumeration."""

    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    SPGIST = "spgist"
    BRIN = "brin"


@dataclass(frozen=True)
class ColumnInfo:
    """Column information data model."""

    column_name: str
    ordinal_position: int
    column_default: Optional[str] = None
    is_nullable: bool = True
    data_type: str = ""
    character_maximum_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    udt_name: Optional[str] = None
    column_comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColumnInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass(frozen=True)
class ConstraintInfo:
    """Constraint information data model."""

    constraint_name: str
    table_name: str
    constraint_type: str
    column_name: Optional[str] = None
    foreign_table_name: Optional[str] = None
    foreign_column_name: Optional[str] = None
    check_clause: Optional[str] = None
    constraint_comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstraintInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass(frozen=True)
class IndexInfo:
    """Index information data model."""

    index_name: str
    table_name: str
    index_type: str
    is_unique: bool
    is_primary: bool
    column_names: List[str] = field(default_factory=list)
    index_definition: Optional[str] = None
    condition: Optional[str] = None
    index_comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass(frozen=True)
class TriggerInfo:
    """Trigger information data model."""

    trigger_name: str
    table_name: str
    trigger_event: str
    trigger_timing: str
    function_name: str
    trigger_definition: Optional[str] = None
    trigger_comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass(frozen=True)
class TableInfo:
    """Table information data model."""

    table_name: str
    table_type: str
    table_schema: str
    table_comment: Optional[str] = None
    estimated_rows: int = 0
    table_size: str = "0 bytes"
    columns: List[ColumnInfo] = field(default_factory=list)
    constraints: List[ConstraintInfo] = field(default_factory=list)
    indexes: List[IndexInfo] = field(default_factory=list)
    triggers: List[TriggerInfo] = field(default_factory=list)

    def get_column(self, column_name: str) -> Optional[ColumnInfo]:
        """Get column by name."""
        for column in self.columns:
            if column.column_name == column_name:
                return column
        return None

    def get_primary_key_columns(self) -> List[str]:
        """Get primary key column names."""
        pk_columns = []
        for constraint in self.constraints:
            if constraint.constraint_type == ConstraintType.PRIMARY_KEY.value:
                if constraint.column_name:
                    pk_columns.append(constraint.column_name)
        return pk_columns

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "table_name": self.table_name,
            "table_type": self.table_type,
            "table_schema": self.table_schema,
            "table_comment": self.table_comment,
            "estimated_rows": self.estimated_rows,
            "table_size": self.table_size,
            "columns": [col.to_dict() for col in self.columns],
            "constraints": [cons.to_dict() for cons in self.constraints],
            "indexes": [idx.to_dict() for idx in self.indexes],
            "triggers": [trig.to_dict() for trig in self.triggers],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TableInfo":
        """Create from dictionary."""
        return cls(
            table_name=data["table_name"],
            table_type=data["table_type"],
            table_schema=data["table_schema"],
            table_comment=data.get("table_comment"),
            estimated_rows=data.get("estimated_rows", 0),
            table_size=data.get("table_size", "0 bytes"),
            columns=[ColumnInfo.from_dict(col) for col in data.get("columns", [])],
            constraints=[
                ConstraintInfo.from_dict(cons) for cons in data.get("constraints", [])
            ],
            indexes=[IndexInfo.from_dict(idx) for idx in data.get("indexes", [])],
            triggers=[TriggerInfo.from_dict(trig) for trig in data.get("triggers", [])],
        )


@dataclass(frozen=True)
class ViewInfo:
    """View information data model."""

    view_name: str
    view_definition: str
    is_updatable: bool
    is_insertable_into: bool
    view_comment: Optional[str] = None
    columns: List[ColumnInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "view_name": self.view_name,
            "view_definition": self.view_definition,
            "is_updatable": self.is_updatable,
            "is_insertable_into": self.is_insertable_into,
            "view_comment": self.view_comment,
            "columns": [col.to_dict() for col in self.columns],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ViewInfo":
        """Create from dictionary."""
        return cls(
            view_name=data["view_name"],
            view_definition=data["view_definition"],
            is_updatable=data["is_updatable"],
            is_insertable_into=data["is_insertable_into"],
            view_comment=data.get("view_comment"),
            columns=[ColumnInfo.from_dict(col) for col in data.get("columns", [])],
        )


@dataclass(frozen=True)
class SequenceInfo:
    """Sequence information data model."""

    sequence_name: str
    data_type: str
    start_value: str
    minimum_value: str
    maximum_value: str
    increment: str
    cycle_option: bool
    sequence_comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SequenceInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass(frozen=True)
class FunctionInfo:
    """Function information data model."""

    function_name: str
    function_type: str
    return_type: str
    function_definition: str
    argument_types: List[str] = field(default_factory=list)
    argument_names: List[str] = field(default_factory=list)
    function_comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FunctionInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass(frozen=True)
class SchemaInfo:
    """Complete schema information data model."""

    schema_name: str
    database_type: str
    collection_time: datetime
    tables: List[TableInfo] = field(default_factory=list)
    views: List[ViewInfo] = field(default_factory=list)
    sequences: List[SequenceInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    constraints: List[ConstraintInfo] = field(default_factory=list)
    indexes: List[IndexInfo] = field(default_factory=list)
    triggers: List[TriggerInfo] = field(default_factory=list)

    def get_table(self, table_name: str) -> Optional[TableInfo]:
        """Get table by name."""
        for table in self.tables:
            if table.table_name == table_name:
                return table
        return None

    def get_view(self, view_name: str) -> Optional[ViewInfo]:
        """Get view by name."""
        for view in self.views:
            if view.view_name == view_name:
                return view
        return None

    def get_sequence(self, sequence_name: str) -> Optional[SequenceInfo]:
        """Get sequence by name."""
        for sequence in self.sequences:
            if sequence.sequence_name == sequence_name:
                return sequence
        return None

    def get_function(self, function_name: str) -> Optional[FunctionInfo]:
        """Get function by name."""
        for function in self.functions:
            if function.function_name == function_name:
                return function
        return None

    def get_object_count(self) -> Dict[str, int]:
        """Get object count statistics."""
        return {
            "tables": len(self.tables),
            "views": len(self.views),
            "sequences": len(self.sequences),
            "functions": len(self.functions),
            "constraints": len(self.constraints),
            "indexes": len(self.indexes),
            "triggers": len(self.triggers),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema_name": self.schema_name,
            "database_type": self.database_type,
            "collection_time": self.collection_time.isoformat(),
            "tables": [table.to_dict() for table in self.tables],
            "views": [view.to_dict() for view in self.views],
            "sequences": [seq.to_dict() for seq in self.sequences],
            "functions": [func.to_dict() for func in self.functions],
            "constraints": [cons.to_dict() for cons in self.constraints],
            "indexes": [idx.to_dict() for idx in self.indexes],
            "triggers": [trig.to_dict() for trig in self.triggers],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaInfo":
        """Create from dictionary."""
        return cls(
            schema_name=data["schema_name"],
            database_type=data["database_type"],
            collection_time=datetime.fromisoformat(data["collection_time"]),
            tables=[TableInfo.from_dict(table) for table in data.get("tables", [])],
            views=[ViewInfo.from_dict(view) for view in data.get("views", [])],
            sequences=[
                SequenceInfo.from_dict(seq) for seq in data.get("sequences", [])
            ],
            functions=[
                FunctionInfo.from_dict(func) for func in data.get("functions", [])
            ],
            constraints=[
                ConstraintInfo.from_dict(cons) for cons in data.get("constraints", [])
            ],
            indexes=[IndexInfo.from_dict(idx) for idx in data.get("indexes", [])],
            triggers=[TriggerInfo.from_dict(trig) for trig in data.get("triggers", [])],
        )

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "SchemaInfo":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass(frozen=True)
class SchemaComparison:
    """Schema comparison result data model."""

    source_schema: SchemaInfo
    target_schema: SchemaInfo
    comparison_time: datetime
    differences: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_schema": self.source_schema.to_dict(),
            "target_schema": self.target_schema.to_dict(),
            "comparison_time": self.comparison_time.isoformat(),
            "differences": self.differences,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaComparison":
        """Create from dictionary."""
        return cls(
            source_schema=SchemaInfo.from_dict(data["source_schema"]),
            target_schema=SchemaInfo.from_dict(data["target_schema"]),
            comparison_time=datetime.fromisoformat(data["comparison_time"]),
            differences=data.get("differences", []),
        )

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "SchemaComparison":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
