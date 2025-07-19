"""Table-based grouping utilities for report generation.

This module provides functionality to transform change-type-based diff results
into table-based grouped structures for improved report readability.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set

from ..core.analyzer import DiffResult


logger = logging.getLogger(__name__)


@dataclass
class TableGroupedChanges:
    """Table-grouped changes for improved report organization.
    
    This class represents all changes related to a single table,
    organized by change type for better readability.
    """
    table_name: str
    change_type: str  # "added", "removed", "modified"
    table_info: Optional[Any] = None
    changes: Dict[str, List[Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize changes dictionary with empty lists."""
        change_types = [
            "columns_added", "columns_removed", "columns_modified",
            "constraints_added", "constraints_removed", "constraints_modified", 
            "indexes_added", "indexes_removed", "indexes_modified",
            "triggers_added", "triggers_removed", "triggers_modified"
        ]
        for change_type in change_types:
            if change_type not in self.changes:
                self.changes[change_type] = []
    
    @property
    def has_changes(self) -> bool:
        """Check if this table has any changes."""
        if self.change_type in ["added", "removed"]:
            return True
        return any(self.changes.values())
    
    @property
    def total_changes(self) -> int:
        """Get total number of changes for this table."""
        if self.change_type in ["added", "removed"]:
            return 1
        return sum(len(changes) for changes in self.changes.values())


@dataclass  
class GroupedDiffResult:
    """Diff result organized by tables for improved reporting."""
    tables_by_change: Dict[str, List[TableGroupedChanges]] = field(default_factory=dict)
    original_result: Optional[DiffResult] = None
    
    def __post_init__(self):
        """Initialize change type categories."""
        for change_type in ["added", "removed", "modified"]:
            if change_type not in self.tables_by_change:
                self.tables_by_change[change_type] = []
    
    @property
    def all_tables(self) -> List[TableGroupedChanges]:
        """Get all tables with changes."""
        all_tables = []
        for tables in self.tables_by_change.values():
            all_tables.extend(tables)
        return all_tables
    
    @property
    def total_changed_tables(self) -> int:
        """Get total number of tables with changes."""
        return len(self.all_tables)
    
    @property
    def total_changes(self) -> int:
        """Get total number of all changes."""
        return sum(table.total_changes for table in self.all_tables)


def extract_table_name(obj: Any) -> str:
    """Extract table name from various object types.
    
    Args:
        obj: Object that may contain table name information
        
    Returns:
        Table name string
    """
    # Handle different object types that may contain table names
    if hasattr(obj, 'table_name'):
        return obj.table_name
    elif hasattr(obj, 'name') and hasattr(obj, 'table'):
        return obj.table  # For constraints, indexes that reference table
    elif isinstance(obj, dict):
        return obj.get('table_name', obj.get('table', str(obj)))
    elif hasattr(obj, '__dict__'):
        obj_dict = obj.__dict__
        return obj_dict.get('table_name', obj_dict.get('table', str(obj)))
    else:
        return str(obj)


def group_changes_by_table(diff_result: DiffResult) -> GroupedDiffResult:
    """Group diff result changes by table for improved reporting.
    
    This function transforms the traditional change-type-based organization
    into a table-based organization for better readability.
    
    Args:
        diff_result: Original diff result organized by change types
        
    Returns:
        GroupedDiffResult organized by tables
    """
    logger.debug("Starting table-based grouping of diff results")
    
    grouped_result = GroupedDiffResult(original_result=diff_result)
    table_changes_map: Dict[str, TableGroupedChanges] = {}
    
    # Process table-level changes first
    _process_table_level_changes(diff_result, grouped_result, table_changes_map)
    
    # Process column changes
    _process_column_changes(diff_result, table_changes_map)
    
    # Process constraint changes  
    _process_constraint_changes(diff_result, table_changes_map)
    
    # Process index changes
    _process_index_changes(diff_result, table_changes_map)
    
    # Process trigger changes
    _process_trigger_changes(diff_result, table_changes_map)
    
    # Add modified tables to grouped result
    modified_tables = [
        table for table in table_changes_map.values() 
        if table.change_type == "modified" and table.has_changes
    ]
    grouped_result.tables_by_change["modified"] = modified_tables
    
    logger.info(f"Grouped {len(grouped_result.all_tables)} tables with changes")
    return grouped_result


def _process_table_level_changes(
    diff_result: DiffResult,
    grouped_result: GroupedDiffResult, 
    table_changes_map: Dict[str, TableGroupedChanges]
) -> None:
    """Process table-level additions and removals."""
    
    # Handle added tables
    for table in diff_result.tables.get("added", []):
        table_name = extract_table_name(table)
        table_change = TableGroupedChanges(
            table_name=table_name,
            change_type="added",
            table_info=table
        )
        grouped_result.tables_by_change["added"].append(table_change)
        logger.debug(f"Processed table addition: {table_name}")
    
    # Handle removed tables
    for table in diff_result.tables.get("removed", []):
        table_name = extract_table_name(table)
        table_change = TableGroupedChanges(
            table_name=table_name,
            change_type="removed", 
            table_info=table
        )
        grouped_result.tables_by_change["removed"].append(table_change)
        logger.debug(f"Processed table removal: {table_name}")
    
    # Initialize entries for modified tables
    for table in diff_result.tables.get("modified", []):
        table_name = extract_table_name(table)
        if table_name not in table_changes_map:
            table_changes_map[table_name] = TableGroupedChanges(
                table_name=table_name,
                change_type="modified",
                table_info=table
            )


def _process_column_changes(
    diff_result: DiffResult,
    table_changes_map: Dict[str, TableGroupedChanges]
) -> None:
    """Process column-level changes and group by table."""
    
    # Get list of added and removed table names to skip their columns
    added_table_names = {extract_table_name(t) for t in diff_result.tables.get("added", [])}
    removed_table_names = {extract_table_name(t) for t in diff_result.tables.get("removed", [])}
    
    for change_type in ["added", "removed", "modified"]:
        for column in diff_result.columns.get(change_type, []):
            table_name = extract_table_name(column)
            
            # Skip columns from tables that were added/removed entirely
            if table_name in added_table_names or table_name in removed_table_names:
                logger.debug(f"Skipping column {change_type} for {table_name} (table-level change)")
                continue
            
            # Ensure table entry exists
            if table_name not in table_changes_map:
                table_changes_map[table_name] = TableGroupedChanges(
                    table_name=table_name,
                    change_type="modified"
                )
            
            # Add column change to appropriate list
            key = f"columns_{change_type}"
            table_changes_map[table_name].changes[key].append(column)
            logger.debug(f"Added column {change_type} for table {table_name}")


def _process_constraint_changes(
    diff_result: DiffResult,
    table_changes_map: Dict[str, TableGroupedChanges]
) -> None:
    """Process constraint-level changes and group by table."""
    
    # Get list of added and removed table names to skip their constraints
    added_table_names = {extract_table_name(t) for t in diff_result.tables.get("added", [])}
    removed_table_names = {extract_table_name(t) for t in diff_result.tables.get("removed", [])}
    
    for change_type in ["added", "removed", "modified"]:
        for constraint in diff_result.constraints.get(change_type, []):
            table_name = extract_table_name(constraint)
            
            # Skip constraints from tables that were added/removed entirely
            if table_name in added_table_names or table_name in removed_table_names:
                logger.debug(f"Skipping constraint {change_type} for {table_name} (table-level change)")
                continue
            
            # Ensure table entry exists
            if table_name not in table_changes_map:
                table_changes_map[table_name] = TableGroupedChanges(
                    table_name=table_name,
                    change_type="modified"
                )
            
            # Add constraint change to appropriate list
            key = f"constraints_{change_type}"
            table_changes_map[table_name].changes[key].append(constraint)
            logger.debug(f"Added constraint {change_type} for table {table_name}")


def _process_index_changes(
    diff_result: DiffResult,
    table_changes_map: Dict[str, TableGroupedChanges]
) -> None:
    """Process index-level changes and group by table."""
    
    # Get list of added and removed table names to skip their indexes
    added_table_names = {extract_table_name(t) for t in diff_result.tables.get("added", [])}
    removed_table_names = {extract_table_name(t) for t in diff_result.tables.get("removed", [])}
    
    for change_type in ["added", "removed", "modified"]:
        for index in diff_result.indexes.get(change_type, []):
            table_name = extract_table_name(index)
            
            # Skip indexes from tables that were added/removed entirely
            if table_name in added_table_names or table_name in removed_table_names:
                logger.debug(f"Skipping index {change_type} for {table_name} (table-level change)")
                continue
            
            # Ensure table entry exists
            if table_name not in table_changes_map:
                table_changes_map[table_name] = TableGroupedChanges(
                    table_name=table_name,
                    change_type="modified"
                )
            
            # Add index change to appropriate list
            key = f"indexes_{change_type}"
            table_changes_map[table_name].changes[key].append(index)
            logger.debug(f"Added index {change_type} for table {table_name}")


def _process_trigger_changes(
    diff_result: DiffResult,
    table_changes_map: Dict[str, TableGroupedChanges]
) -> None:
    """Process trigger-level changes and group by table."""
    
    for change_type in ["added", "removed", "modified"]:
        for trigger in diff_result.triggers.get(change_type, []):
            table_name = extract_table_name(trigger)
            
            # Ensure table entry exists
            if table_name not in table_changes_map:
                table_changes_map[table_name] = TableGroupedChanges(
                    table_name=table_name,
                    change_type="modified"
                )
            
            # Add trigger change to appropriate list
            key = f"triggers_{change_type}"
            table_changes_map[table_name].changes[key].append(trigger)
            logger.debug(f"Added trigger {change_type} for table {table_name}")


def get_table_summary(grouped_changes: TableGroupedChanges) -> Dict[str, Any]:
    """Get summary information for a table's changes.
    
    Args:
        grouped_changes: Table changes to summarize
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        "table_name": grouped_changes.table_name,
        "change_type": grouped_changes.change_type,
        "total_changes": grouped_changes.total_changes,
        "has_column_changes": any(
            grouped_changes.changes.get(key, []) 
            for key in ["columns_added", "columns_removed", "columns_modified"]
        ),
        "has_constraint_changes": any(
            grouped_changes.changes.get(key, [])
            for key in ["constraints_added", "constraints_removed", "constraints_modified"] 
        ),
        "has_index_changes": any(
            grouped_changes.changes.get(key, [])
            for key in ["indexes_added", "indexes_removed", "indexes_modified"]
        ),
        "has_trigger_changes": any(
            grouped_changes.changes.get(key, [])
            for key in ["triggers_added", "triggers_removed", "triggers_modified"]
        ),
    }
    
    # Add detailed counts
    for change_category in ["columns", "constraints", "indexes", "triggers"]:
        for change_type in ["added", "removed", "modified"]:
            key = f"{change_category}_{change_type}"
            summary[f"{key}_count"] = len(grouped_changes.changes.get(key, []))
    
    return summary