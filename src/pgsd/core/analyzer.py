"""Diff analyzer for PostgreSQL schemas."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from ..models.schema import (
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ConstraintInfo,
    IndexInfo,
    ViewInfo,
    FunctionInfo,
    SequenceInfo,
    TriggerInfo,
)


# Compatibility wrappers
class TableInfoCompat:
    """Compatibility wrapper for TableInfo."""

    def __init__(self, table_info):
        self._table = table_info
        self.name = table_info.table_name

    def __getattr__(self, name):
        return getattr(self._table, name)


class ColumnInfoCompat:
    """Compatibility wrapper for ColumnInfo."""

    def __init__(self, column_info):
        self._column = column_info
        self.name = column_info.column_name

    def __getattr__(self, name):
        return getattr(self._column, name)


class ConstraintInfoCompat:
    """Compatibility wrapper for ConstraintInfo."""

    def __init__(self, constraint_info):
        self._constraint = constraint_info
        self.name = constraint_info.constraint_name

    def __getattr__(self, name):
        return getattr(self._constraint, name)


class IndexInfoCompat:
    """Compatibility wrapper for IndexInfo."""

    def __init__(self, index_info):
        self._index = index_info
        self.name = index_info.index_name

    def __getattr__(self, name):
        return getattr(self._index, name)


def make_schema_info_compat(info):
    """Create compatibility wrappers."""
    # Create new lists with wrapped objects
    tables = []
    for table in info.tables:
        wrapped_table = TableInfoCompat(table)
        wrapped_table.columns = [ColumnInfoCompat(col) for col in table.columns]
        wrapped_table.constraints = [ConstraintInfoCompat(c) for c in table.constraints]
        wrapped_table.indexes = [IndexInfoCompat(idx) for idx in table.indexes]
        wrapped_table.triggers = [TriggerInfoCompat(t) for t in table.triggers]
        tables.append(wrapped_table)

    # Create wrapped schema
    wrapped_info = type("SchemaInfoCompat", (), {})()
    wrapped_info.schema_name = info.schema_name
    wrapped_info.database_type = info.database_type
    wrapped_info.collection_time = info.collection_time
    wrapped_info.tables = tables
    wrapped_info.views = [ViewInfoCompat(v) for v in info.views]
    wrapped_info.functions = [FunctionInfoCompat(f) for f in info.functions]
    wrapped_info.sequences = [SequenceInfoCompat(s) for s in info.sequences]

    return wrapped_info


class TriggerInfoCompat:
    """Compatibility wrapper for TriggerInfo."""

    def __init__(self, trigger_info):
        self._trigger = trigger_info
        self.name = trigger_info.trigger_name

    def __getattr__(self, name):
        return getattr(self._trigger, name)


class ViewInfoCompat:
    """Compatibility wrapper for ViewInfo."""

    def __init__(self, view_info):
        self._view = view_info
        self.name = view_info.view_name

    def __getattr__(self, name):
        return getattr(self._view, name)


class FunctionInfoCompat:
    """Compatibility wrapper for FunctionInfo."""

    def __init__(self, function_info):
        self._function = function_info
        self.name = function_info.function_name
        self.signature = (
            f"{function_info.function_name}({','.join(function_info.argument_types)})"
        )

    def __getattr__(self, name):
        return getattr(self._function, name)


class SequenceInfoCompat:
    """Compatibility wrapper for SequenceInfo."""

    def __init__(self, sequence_info):
        self._sequence = sequence_info
        self.name = sequence_info.sequence_name

    def __getattr__(self, name):
        return getattr(self._sequence, name)


logger = logging.getLogger(__name__)


@dataclass
class TableDiff:
    """Represents differences in a table."""

    name: str
    columns: Dict[str, List[Any]] = field(default_factory=dict)
    constraints: Dict[str, List[Any]] = field(default_factory=dict)
    indexes: Dict[str, List[Any]] = field(default_factory=dict)
    triggers: Dict[str, List[Any]] = field(default_factory=dict)

    def has_changes(self) -> bool:
        """Check if table has any changes."""
        return bool(self.columns or self.constraints or self.indexes or self.triggers)


@dataclass
class DiffResult:
    """Result of schema comparison."""

    tables: Dict[str, List[Any]] = field(default_factory=dict)
    columns: Dict[str, List[Any]] = field(default_factory=dict)
    constraints: Dict[str, List[Any]] = field(default_factory=dict)
    indexes: Dict[str, List[Any]] = field(default_factory=dict)
    views: Dict[str, List[Any]] = field(default_factory=dict)
    functions: Dict[str, List[Any]] = field(default_factory=dict)
    sequences: Dict[str, List[Any]] = field(default_factory=dict)
    triggers: Dict[str, List[Any]] = field(default_factory=dict)
    summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize result dictionaries."""
        for attr in [
            "tables",
            "columns",
            "constraints",
            "indexes",
            "views",
            "functions",
            "sequences",
            "triggers",
        ]:
            if not getattr(self, attr):
                setattr(self, attr, {"added": [], "removed": [], "modified": []})

    def update_summary(self):
        """Update summary statistics."""
        self.summary = {
            "total_changes": 0,
            "tables_added": len(self.tables.get("added", [])),
            "tables_removed": len(self.tables.get("removed", [])),
            "tables_modified": len(self.tables.get("modified", [])),
            "columns_added": len(self.columns.get("added", [])),
            "columns_removed": len(self.columns.get("removed", [])),
            "columns_modified": len(self.columns.get("modified", [])),
            "constraints_added": len(self.constraints.get("added", [])),
            "constraints_removed": len(self.constraints.get("removed", [])),
            "constraints_modified": len(self.constraints.get("modified", [])),
            "indexes_added": len(self.indexes.get("added", [])),
            "indexes_removed": len(self.indexes.get("removed", [])),
            "indexes_modified": len(self.indexes.get("modified", [])),
            "views_added": len(self.views.get("added", [])),
            "views_removed": len(self.views.get("removed", [])),
            "views_modified": len(self.views.get("modified", [])),
            "functions_added": len(self.functions.get("added", [])),
            "functions_removed": len(self.functions.get("removed", [])),
            "functions_modified": len(self.functions.get("modified", [])),
            "sequences_added": len(self.sequences.get("added", [])),
            "sequences_removed": len(self.sequences.get("removed", [])),
            "sequences_modified": len(self.sequences.get("modified", [])),
            "triggers_added": len(self.triggers.get("added", [])),
            "triggers_removed": len(self.triggers.get("removed", [])),
            "triggers_modified": len(self.triggers.get("modified", [])),
        }
        self.summary["total_changes"] = sum(
            v for k, v in self.summary.items() if k != "total_changes"
        )


class DiffAnalyzer:
    """Analyzer for detecting differences between PostgreSQL schemas."""

    def __init__(self):
        """Initialize the diff analyzer."""
        self.result = DiffResult()

    def analyze(self, schema_a: SchemaInfo, schema_b: SchemaInfo) -> DiffResult:
        """
        Analyze differences between two schemas.

        Args:
            schema_a: Source schema information
            schema_b: Target schema information

        Returns:
            DiffResult object containing all detected differences
        """
        logger.info(
            f"Starting schema comparison: "
            f"{schema_a.schema_name} -> {schema_b.schema_name}"
        )

        # Make schemas compatible
        schema_a = make_schema_info_compat(schema_a)
        schema_b = make_schema_info_compat(schema_b)

        # Reset result
        self.result = DiffResult()

        # Compare tables
        self._compare_tables(schema_a, schema_b)

        # Compare views
        self._compare_views(schema_a, schema_b)

        # Compare functions
        self._compare_functions(schema_a, schema_b)

        # Compare sequences
        self._compare_sequences(schema_a, schema_b)

        # Update summary
        self.result.update_summary()

        logger.info(
            f"Schema comparison completed. "
            f"Total changes: {self.result.summary['total_changes']}"
        )

        return self.result

    def _compare_tables(self, schema_a: SchemaInfo, schema_b: SchemaInfo):
        """Compare tables between schemas."""
        tables_a = {t.name: t for t in schema_a.tables}
        tables_b = {t.name: t for t in schema_b.tables}

        table_names_a = set(tables_a.keys())
        table_names_b = set(tables_b.keys())

        # Added tables
        added = table_names_b - table_names_a
        for table_name in added:
            self.result.tables["added"].append(tables_b[table_name])
            # Add all columns as added
            for column in tables_b[table_name].columns:
                self.result.columns["added"].append(
                    {"table": table_name, "column": column}
                )
            # Add all constraints as added
            for constraint in tables_b[table_name].constraints:
                self.result.constraints["added"].append(
                    {"table": table_name, "constraint": constraint}
                )

        # Removed tables
        removed = table_names_a - table_names_b
        for table_name in removed:
            self.result.tables["removed"].append(tables_a[table_name])
            # Add all columns as removed
            for column in tables_a[table_name].columns:
                self.result.columns["removed"].append(
                    {"table": table_name, "column": column}
                )

        # Common tables - check for modifications
        common = table_names_a & table_names_b
        for table_name in common:
            table_diff = self._compare_table_details(
                tables_a[table_name], tables_b[table_name]
            )
            if table_diff.has_changes():
                self.result.tables["modified"].append(table_diff)

    def _compare_table_details(
        self, table_a: TableInfo, table_b: TableInfo
    ) -> TableDiff:
        """Compare details of two tables."""
        table_diff = TableDiff(name=table_a.name)

        # Compare columns
        self._compare_columns(table_a, table_b, table_diff)

        # Compare constraints
        self._compare_constraints(table_a, table_b, table_diff)

        # Compare indexes
        self._compare_indexes(table_a, table_b, table_diff)

        # Compare triggers
        self._compare_triggers(table_a, table_b, table_diff)

        return table_diff

    def _compare_columns(
        self, table_a: TableInfo, table_b: TableInfo, table_diff: TableDiff
    ):
        """Compare columns between two tables."""
        columns_a = {c.name: c for c in table_a.columns}
        columns_b = {c.name: c for c in table_b.columns}

        col_names_a = set(columns_a.keys())
        col_names_b = set(columns_b.keys())

        # Added columns
        added = col_names_b - col_names_a
        for col_name in added:
            column = columns_b[col_name]
            table_diff.columns.setdefault("added", []).append(column)
            self.result.columns["added"].append(
                {"table": table_a.name, "column": column}
            )

        # Removed columns
        removed = col_names_a - col_names_b
        for col_name in removed:
            column = columns_a[col_name]
            table_diff.columns.setdefault("removed", []).append(column)
            self.result.columns["removed"].append(
                {"table": table_a.name, "column": column}
            )

        # Modified columns
        common = col_names_a & col_names_b
        for col_name in common:
            col_changes = self._compare_column_details(
                columns_a[col_name], columns_b[col_name]
            )
            if col_changes:
                table_diff.columns.setdefault("modified", []).append(
                    {"column": columns_b[col_name], "changes": col_changes}
                )
                self.result.columns["modified"].append(
                    {
                        "table": table_a.name,
                        "column": columns_b[col_name],
                        "changes": col_changes,
                    }
                )

    def _compare_column_details(
        self, col_a: ColumnInfo, col_b: ColumnInfo
    ) -> Optional[Dict[str, Any]]:
        """Compare detailed attributes of two columns."""
        changes = {}

        # Data type
        if col_a.data_type != col_b.data_type:
            changes["data_type"] = {"from": col_a.data_type, "to": col_b.data_type}

        # NULL constraint
        if col_a.is_nullable != col_b.is_nullable:
            changes["is_nullable"] = {
                "from": col_a.is_nullable,
                "to": col_b.is_nullable,
            }

        # Default value
        if col_a.column_default != col_b.column_default:
            changes["column_default"] = {
                "from": col_a.column_default,
                "to": col_b.column_default,
            }

        # Character maximum length
        if col_a.character_maximum_length != col_b.character_maximum_length:
            changes["character_maximum_length"] = {
                "from": col_a.character_maximum_length,
                "to": col_b.character_maximum_length,
            }

        # Numeric precision
        if col_a.numeric_precision != col_b.numeric_precision:
            changes["numeric_precision"] = {
                "from": col_a.numeric_precision,
                "to": col_b.numeric_precision,
            }

        # Numeric scale
        if col_a.numeric_scale != col_b.numeric_scale:
            changes["numeric_scale"] = {
                "from": col_a.numeric_scale,
                "to": col_b.numeric_scale,
            }

        # Ordinal position (only include if significant structural change)
        # Skip ordinal position changes unless it's a major reordering
        if col_a.ordinal_position != col_b.ordinal_position:
            # Only report if the position difference is significant
            position_diff = abs(col_a.ordinal_position - col_b.ordinal_position)
            if position_diff > 1:  # More than just adjacent position change
                changes["ordinal_position"] = {
                    "from": col_a.ordinal_position,
                    "to": col_b.ordinal_position,
                }

        return changes if changes else None

    def _compare_constraints(
        self, table_a: TableInfo, table_b: TableInfo, table_diff: TableDiff
    ):
        """Compare constraints between two tables."""
        constraints_a = {c.name: c for c in table_a.constraints}
        constraints_b = {c.name: c for c in table_b.constraints}

        const_names_a = set(constraints_a.keys())
        const_names_b = set(constraints_b.keys())

        # Added constraints
        added = const_names_b - const_names_a
        for const_name in added:
            constraint = constraints_b[const_name]
            table_diff.constraints.setdefault("added", []).append(constraint)
            self.result.constraints["added"].append(
                {"table": table_a.name, "constraint": constraint}
            )

        # Removed constraints
        removed = const_names_a - const_names_b
        for const_name in removed:
            constraint = constraints_a[const_name]
            table_diff.constraints.setdefault("removed", []).append(constraint)
            self.result.constraints["removed"].append(
                {"table": table_a.name, "constraint": constraint}
            )

        # Modified constraints
        common = const_names_a & const_names_b
        for const_name in common:
            const_changes = self._compare_constraint_details(
                constraints_a[const_name], constraints_b[const_name]
            )
            if const_changes:
                table_diff.constraints.setdefault("modified", []).append(
                    {"constraint": constraints_b[const_name], "changes": const_changes}
                )
                self.result.constraints["modified"].append(
                    {
                        "table": table_a.name,
                        "constraint": constraints_b[const_name],
                        "changes": const_changes,
                    }
                )

    def _compare_constraint_details(
        self, const_a: ConstraintInfo, const_b: ConstraintInfo
    ) -> Optional[Dict[str, Any]]:
        """Compare detailed attributes of two constraints."""
        changes = {}

        # Constraint type
        if const_a.constraint_type != const_b.constraint_type:
            changes["constraint_type"] = {
                "from": const_a.constraint_type,
                "to": const_b.constraint_type,
            }

        # Column comparison (handle single column vs multiple columns)
        cols_a = [const_a.column_name] if const_a.column_name else []
        cols_b = [const_b.column_name] if const_b.column_name else []
        if cols_a != cols_b:
            changes["columns"] = {
                "from": cols_a,
                "to": cols_b,
            }

        # Check constraint definition
        if hasattr(const_a, "check_clause") and hasattr(const_b, "check_clause"):
            if const_a.check_clause != const_b.check_clause:
                changes["check_clause"] = {
                    "from": const_a.check_clause,
                    "to": const_b.check_clause,
                }

        # Foreign key details
        if (
            const_a.constraint_type == "FOREIGN KEY"
            and const_b.constraint_type == "FOREIGN KEY"
        ):
            if hasattr(const_a, "foreign_table_name") and hasattr(
                const_b, "foreign_table_name"
            ):
                if const_a.foreign_table_name != const_b.foreign_table_name:
                    changes["foreign_table_name"] = {
                        "from": const_a.foreign_table_name,
                        "to": const_b.foreign_table_name,
                    }
                if const_a.foreign_column_name != const_b.foreign_column_name:
                    changes["foreign_column_name"] = {
                        "from": const_a.foreign_column_name,
                        "to": const_b.foreign_column_name,
                    }

        return changes if changes else None

    def _compare_indexes(
        self, table_a: TableInfo, table_b: TableInfo, table_diff: TableDiff
    ):
        """Compare indexes between two tables."""
        indexes_a = {i.name: i for i in table_a.indexes}
        indexes_b = {i.name: i for i in table_b.indexes}

        idx_names_a = set(indexes_a.keys())
        idx_names_b = set(indexes_b.keys())

        # Added indexes
        added = idx_names_b - idx_names_a
        for idx_name in added:
            index = indexes_b[idx_name]
            table_diff.indexes.setdefault("added", []).append(index)
            self.result.indexes["added"].append({"table": table_a.name, "index": index})

        # Removed indexes
        removed = idx_names_a - idx_names_b
        for idx_name in removed:
            index = indexes_a[idx_name]
            table_diff.indexes.setdefault("removed", []).append(index)
            self.result.indexes["removed"].append(
                {"table": table_a.name, "index": index}
            )

        # Modified indexes
        common = idx_names_a & idx_names_b
        for idx_name in common:
            idx_changes = self._compare_index_details(
                indexes_a[idx_name], indexes_b[idx_name]
            )
            if idx_changes:
                table_diff.indexes.setdefault("modified", []).append(
                    {"index": indexes_b[idx_name], "changes": idx_changes}
                )
                self.result.indexes["modified"].append(
                    {
                        "table": table_a.name,
                        "index": indexes_b[idx_name],
                        "changes": idx_changes,
                    }
                )

    def _compare_index_details(
        self, idx_a: IndexInfo, idx_b: IndexInfo
    ) -> Optional[Dict[str, Any]]:
        """Compare detailed attributes of two indexes."""
        changes = {}

        # Index type
        if idx_a.index_type != idx_b.index_type:
            changes["index_type"] = {"from": idx_a.index_type, "to": idx_b.index_type}

        # Unique flag
        if idx_a.is_unique != idx_b.is_unique:
            changes["is_unique"] = {"from": idx_a.is_unique, "to": idx_b.is_unique}

        # Primary flag
        if idx_a.is_primary != idx_b.is_primary:
            changes["is_primary"] = {"from": idx_a.is_primary, "to": idx_b.is_primary}

        # Column list
        cols_a = idx_a.column_names
        cols_b = idx_b.column_names
        if cols_a != cols_b:
            changes["columns"] = {"from": cols_a, "to": cols_b}

        # Index definition
        if idx_a.index_definition != idx_b.index_definition:
            changes["definition"] = {
                "from": idx_a.index_definition,
                "to": idx_b.index_definition,
            }

        return changes if changes else None

    def _compare_triggers(
        self, table_a: TableInfo, table_b: TableInfo, table_diff: TableDiff
    ):
        """Compare triggers between two tables."""
        triggers_a = {t.name: t for t in table_a.triggers}
        triggers_b = {t.name: t for t in table_b.triggers}

        trig_names_a = set(triggers_a.keys())
        trig_names_b = set(triggers_b.keys())

        # Added triggers
        added = trig_names_b - trig_names_a
        for trig_name in added:
            trigger = triggers_b[trig_name]
            table_diff.triggers.setdefault("added", []).append(trigger)
            self.result.triggers["added"].append(
                {"table": table_a.name, "trigger": trigger}
            )

        # Removed triggers
        removed = trig_names_a - trig_names_b
        for trig_name in removed:
            trigger = triggers_a[trig_name]
            table_diff.triggers.setdefault("removed", []).append(trigger)
            self.result.triggers["removed"].append(
                {"table": table_a.name, "trigger": trigger}
            )

        # Modified triggers
        common = trig_names_a & trig_names_b
        for trig_name in common:
            trig_changes = self._compare_trigger_details(
                triggers_a[trig_name], triggers_b[trig_name]
            )
            if trig_changes:
                table_diff.triggers.setdefault("modified", []).append(
                    {"trigger": triggers_b[trig_name], "changes": trig_changes}
                )
                self.result.triggers["modified"].append(
                    {
                        "table": table_a.name,
                        "trigger": triggers_b[trig_name],
                        "changes": trig_changes,
                    }
                )

    def _compare_trigger_details(
        self, trig_a: TriggerInfo, trig_b: TriggerInfo
    ) -> Optional[Dict[str, Any]]:
        """Compare detailed attributes of two triggers."""
        changes = {}

        # Trigger timing
        if trig_a.trigger_timing != trig_b.trigger_timing:
            changes["timing"] = {
                "from": trig_a.trigger_timing,
                "to": trig_b.trigger_timing,
            }

        # Trigger events
        events_a = [trig_a.trigger_event] if trig_a.trigger_event else []
        events_b = [trig_b.trigger_event] if trig_b.trigger_event else []
        if events_a != events_b:
            changes["events"] = {
                "from": events_a,
                "to": events_b,
            }

        # Trigger function
        if trig_a.function_name != trig_b.function_name:
            changes["function_name"] = {
                "from": trig_a.function_name,
                "to": trig_b.function_name,
            }

        # Trigger definition
        if trig_a.trigger_definition != trig_b.trigger_definition:
            changes["definition"] = {
                "from": trig_a.trigger_definition,
                "to": trig_b.trigger_definition,
            }

        return changes if changes else None

    def _compare_views(self, schema_a: SchemaInfo, schema_b: SchemaInfo):
        """Compare views between schemas."""
        views_a = {v.name: v for v in schema_a.views}
        views_b = {v.name: v for v in schema_b.views}

        view_names_a = set(views_a.keys())
        view_names_b = set(views_b.keys())

        # Added views
        added = view_names_b - view_names_a
        for view_name in added:
            self.result.views["added"].append(views_b[view_name])

        # Removed views
        removed = view_names_a - view_names_b
        for view_name in removed:
            self.result.views["removed"].append(views_a[view_name])

        # Modified views
        common = view_names_a & view_names_b
        for view_name in common:
            view_changes = self._compare_view_details(
                views_a[view_name], views_b[view_name]
            )
            if view_changes:
                self.result.views["modified"].append(
                    {"view": views_b[view_name], "changes": view_changes}
                )

    def _compare_view_details(
        self, view_a: ViewInfo, view_b: ViewInfo
    ) -> Optional[Dict[str, Any]]:
        """Compare detailed attributes of two views."""
        changes = {}

        # View definition
        if view_a.view_definition != view_b.view_definition:
            changes["definition"] = {
                "from": view_a.view_definition,
                "to": view_b.view_definition,
            }

        # Updatable flag
        if view_a.is_updatable != view_b.is_updatable:
            changes["is_updatable"] = {
                "from": view_a.is_updatable,
                "to": view_b.is_updatable,
            }

        # Insertable flag
        if view_a.is_insertable_into != view_b.is_insertable_into:
            changes["is_insertable_into"] = {
                "from": view_a.is_insertable_into,
                "to": view_b.is_insertable_into,
            }

        # Column changes
        cols_a = {c.column_name: c for c in view_a.columns}
        cols_b = {c.column_name: c for c in view_b.columns}
        col_names_a = set(cols_a.keys())
        col_names_b = set(cols_b.keys())

        if col_names_a != col_names_b:
            changes["columns"] = {
                "added": list(col_names_b - col_names_a),
                "removed": list(col_names_a - col_names_b),
            }

        return changes if changes else None

    def _compare_functions(self, schema_a: SchemaInfo, schema_b: SchemaInfo):
        """Compare functions between schemas."""
        funcs_a = {f.signature: f for f in schema_a.functions}
        funcs_b = {f.signature: f for f in schema_b.functions}

        func_sigs_a = set(funcs_a.keys())
        func_sigs_b = set(funcs_b.keys())

        # Added functions
        added = func_sigs_b - func_sigs_a
        for func_sig in added:
            self.result.functions["added"].append(funcs_b[func_sig])

        # Removed functions
        removed = func_sigs_a - func_sigs_b
        for func_sig in removed:
            self.result.functions["removed"].append(funcs_a[func_sig])

        # Modified functions
        common = func_sigs_a & func_sigs_b
        for func_sig in common:
            func_changes = self._compare_function_details(
                funcs_a[func_sig], funcs_b[func_sig]
            )
            if func_changes:
                self.result.functions["modified"].append(
                    {"function": funcs_b[func_sig], "changes": func_changes}
                )

    def _compare_function_details(
        self, func_a: FunctionInfo, func_b: FunctionInfo
    ) -> Optional[Dict[str, Any]]:
        """Compare detailed attributes of two functions."""
        changes = {}

        # Return type
        if func_a.return_type != func_b.return_type:
            changes["return_type"] = {
                "from": func_a.return_type,
                "to": func_b.return_type,
            }

        # Function type
        if func_a.function_type != func_b.function_type:
            changes["function_type"] = {
                "from": func_a.function_type,
                "to": func_b.function_type,
            }

        # Definition
        if func_a.function_definition != func_b.function_definition:
            changes["definition"] = {
                "from": func_a.function_definition,
                "to": func_b.function_definition,
            }

        # Argument types
        if func_a.argument_types != func_b.argument_types:
            changes["argument_types"] = {
                "from": func_a.argument_types,
                "to": func_b.argument_types,
            }

        return changes if changes else None

    def _compare_sequences(self, schema_a: SchemaInfo, schema_b: SchemaInfo):
        """Compare sequences between schemas."""
        seqs_a = {s.name: s for s in schema_a.sequences}
        seqs_b = {s.name: s for s in schema_b.sequences}

        seq_names_a = set(seqs_a.keys())
        seq_names_b = set(seqs_b.keys())

        # Added sequences
        added = seq_names_b - seq_names_a
        for seq_name in added:
            self.result.sequences["added"].append(seqs_b[seq_name])

        # Removed sequences
        removed = seq_names_a - seq_names_b
        for seq_name in removed:
            self.result.sequences["removed"].append(seqs_a[seq_name])

        # Modified sequences
        common = seq_names_a & seq_names_b
        for seq_name in common:
            seq_changes = self._compare_sequence_details(
                seqs_a[seq_name], seqs_b[seq_name]
            )
            if seq_changes:
                self.result.sequences["modified"].append(
                    {"sequence": seqs_b[seq_name], "changes": seq_changes}
                )

    def _compare_sequence_details(
        self, seq_a: SequenceInfo, seq_b: SequenceInfo
    ) -> Optional[Dict[str, Any]]:
        """Compare detailed attributes of two sequences."""
        changes = {}

        # Data type
        if seq_a.data_type != seq_b.data_type:
            changes["data_type"] = {"from": seq_a.data_type, "to": seq_b.data_type}

        # Start value
        if seq_a.start_value != seq_b.start_value:
            changes["start_value"] = {
                "from": seq_a.start_value,
                "to": seq_b.start_value,
            }

        # Increment
        if seq_a.increment != seq_b.increment:
            changes["increment"] = {"from": seq_a.increment, "to": seq_b.increment}

        # Min value
        if seq_a.minimum_value != seq_b.minimum_value:
            changes["minimum_value"] = {
                "from": seq_a.minimum_value,
                "to": seq_b.minimum_value,
            }

        # Max value
        if seq_a.maximum_value != seq_b.maximum_value:
            changes["maximum_value"] = {
                "from": seq_a.maximum_value,
                "to": seq_b.maximum_value,
            }

        # Cycle flag
        if seq_a.cycle_option != seq_b.cycle_option:
            changes["cycle_option"] = {
                "from": seq_a.cycle_option,
                "to": seq_b.cycle_option,
            }

        return changes if changes else None
