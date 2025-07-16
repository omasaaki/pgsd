"""Template management for report generation.

This module provides template management functionality for generating
reports in various formats. It includes built-in templates and support
for custom template loading.

Classes:
    TemplateManager: Manages report templates
    BuiltinTemplates: Built-in template definitions
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any
import textwrap

from .base import ReportFormat
from ..exceptions.processing import ProcessingError


logger = logging.getLogger(__name__)


class BuiltinTemplates:
    """Built-in template definitions for different report formats."""

    # HTML template with embedded CSS
    HTML_TEMPLATE = textwrap.dedent(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PostgreSQL Schema Diff Report</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 30px;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
                margin-bottom: 15px;
            }
            .metadata {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 25px;
            }
            .summary {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            .summary-card {
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .summary-card h3 {
                margin: 0 0 10px 0;
                color: #2c3e50;
                font-size: 0.9em;
                text-transform: uppercase;
            }
            .summary-card .count {
                font-size: 2em;
                font-weight: bold;
                color: #3498db;
            }
            .change-list {
                margin-bottom: 25px;
            }
            .change-item {
                padding: 8px 12px;
                margin: 5px 0;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }
            .added {
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                color: #155724;
            }
            .removed {
                background-color: #f8d7da;
                border-left: 4px solid #dc3545;
                color: #721c24;
            }
            .modified {
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                color: #856404;
            }
            .details {
                margin-left: 20px;
                font-size: 0.85em;
                color: #666;
            }
            .no-changes {
                text-align: center;
                color: #6c757d;
                font-style: italic;
                padding: 20px;
            }
            .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #6c757d;
                font-size: 0.9em;
            }
            .table-group {
                margin-bottom: 30px;
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
            }
            .table-header {
                background: #f8f9fa;
                padding: 15px 20px;
                border-bottom: 1px solid #ddd;
                cursor: pointer;
                position: relative;
            }
            .table-header:hover {
                background: #e9ecef;
            }
            .table-header h3 {
                margin: 0;
                color: #2c3e50;
                display: inline-block;
            }
            .table-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
                margin-left: 10px;
            }
            .table-badge.added {
                background: #d4edda;
                color: #155724;
            }
            .table-badge.removed {
                background: #f8d7da;
                color: #721c24;
            }
            .table-badge.modified {
                background: #fff3cd;
                color: #856404;
            }
            .table-content {
                padding: 20px;
                display: none;
            }
            .table-content.expanded {
                display: block;
            }
            .change-section {
                margin-bottom: 20px;
            }
            .change-section h4 {
                margin: 0 0 10px 0;
                color: #495057;
                font-size: 1em;
            }
            .change-detail {
                padding: 5px 10px;
                margin: 3px 0;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.85em;
                background: #f8f9fa;
                border-left: 3px solid #dee2e6;
            }
            .toggle-icon {
                float: right;
                transition: transform 0.2s;
            }
            .toggle-icon.expanded {
                transform: rotate(180deg);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PostgreSQL Schema Diff Report</h1>

            <div class="metadata">
                <strong>Generated:</strong> {{ metadata.generated_at }}<br>
                <strong>Source:</strong> 
                    {{ metadata.source_database }}.{{ metadata.source_schema }}<br>
                <strong>Target:</strong> 
                    {{ metadata.target_database }}.{{ metadata.target_schema }}<br>
                <strong>Analysis Time:</strong> 
                    {{ "%.3f"|format(metadata.analysis_time_seconds) }} seconds
            </div>

            <div class="summary">
                <div class="summary-card">
                    <h3>Total Changes</h3>
                    <div class="count">{{ summary.total_changes }}</div>
                </div>
                <div class="summary-card">
                    <h3>Tables</h3>
                    <div class="count">{{ summary.tables_added + summary.tables_removed + summary.tables_modified }}</div>
                </div>
                <div class="summary-card">
                    <h3>Columns</h3>
                    <div class="count">{{ summary.columns_added + summary.columns_removed + summary.columns_modified }}</div>
                </div>
                <div class="summary-card">
                    <h3>Constraints</h3>
                    <div class="count">{{ summary.constraints_added + summary.constraints_removed + summary.constraints_modified }}</div>
                </div>
            </div>

            {% if summary.total_changes > 0 %}
                {% if use_table_grouping %}
                    <h2>Schema Changes by Table</h2>
                    {% for change_type in ['added', 'removed', 'modified'] %}
                        {% set tables = grouped_result.tables_by_change[change_type] %}
                        {% if tables %}
                            <h3>Tables {{ change_type.title() }} ({{ tables|length }})</h3>
                            {% for table in tables %}
                                <div class="table-group">
                                    <div class="table-header" onclick="toggleTable('{{ table.table_name }}_{{ change_type }}')">
                                        <h3>{{ table.table_name }}</h3>
                                        <span class="table-badge {{ change_type }}">{{ change_type.upper() }}</span>
                                        {% if config.show_change_counts and table.change_type == 'modified' %}
                                            <span class="table-badge modified">{{ table.total_changes }} changes</span>
                                        {% endif %}
                                        <span class="toggle-icon" id="icon_{{ table.table_name }}_{{ change_type }}">▼</span>
                                    </div>
                                    <div class="table-content" id="content_{{ table.table_name }}_{{ change_type }}">
                                        {% if table.change_type == 'modified' %}
                                            {% for section, items in table.changes.items() %}
                                                {% if items %}
                                                    <div class="change-section">
                                                        <h4>{{ section.replace('_', ' ').title() }} ({{ items|length }})</h4>
                                                        {% for item in items %}
                                                            <div class="change-detail">{{ item }}</div>
                                                        {% endfor %}
                                                    </div>
                                                {% endif %}
                                            {% endfor %}
                                        {% else %}
                                            <div class="change-section">
                                                <h4>Table {{ change_type.title() }}</h4>
                                                <div class="change-detail">
                                                    Table "{{ table.table_name }}" was {{ change_type }}
                                                    {% if table.table_info and table.table_info.columns %}
                                                        ({{ table.table_info.columns|length }} columns)
                                                    {% endif %}
                                                </div>
                                            </div>
                                        {% endif %}
                                    </div>
                                </div>
                            {% endfor %}
                        {% endif %}
                    {% endfor %}
                    
                    {% if config.show_legacy_format %}
                        <h2>Traditional View</h2>
                        {{ content }}
                    {% endif %}
                {% else %}
                    {{ content }}
                {% endif %}
            {% else %}
                <div class="no-changes">
                    <h2>No Changes Detected</h2>
                    <p>The schemas are identical.</p>
                </div>
            {% endif %}

            <div class="footer">
                Generated by PGSD v{{ metadata.generator_version }} at {{ metadata.generated_at }}
            </div>
        </div>
        
        <script>
            function toggleTable(tableId) {
                const content = document.getElementById('content_' + tableId);
                const icon = document.getElementById('icon_' + tableId);
                
                if (content.classList.contains('expanded')) {
                    content.classList.remove('expanded');
                    icon.classList.remove('expanded');
                    icon.textContent = '▼';
                } else {
                    content.classList.add('expanded');
                    icon.classList.add('expanded');
                    icon.textContent = '▲';
                }
            }
            
            // Auto-expand if only a few tables or if config says so
            document.addEventListener('DOMContentLoaded', function() {
                const tableGroups = document.querySelectorAll('.table-group');
                if (tableGroups.length <= 3 || {{ config.collapse_sections|lower }} === false) {
                    tableGroups.forEach(function(group) {
                        const header = group.querySelector('.table-header');
                        if (header && header.onclick) {
                            const tableId = header.onclick.toString().match(/'([^']+)'/)[1];
                            toggleTable(tableId);
                        }
                    });
                }
            });
        </script>
    </body>
    </html>
    """
    ).strip()

    # Markdown template
    MARKDOWN_TEMPLATE = textwrap.dedent(
        """
    # PostgreSQL Schema Diff Report

    ## Metadata

    - **Generated:** {{ metadata.generated_at }}
    - **Source:** {{ metadata.source_database }}.{{ metadata.source_schema }}
    - **Target:** {{ metadata.target_database }}.{{ metadata.target_schema }}
    - **Analysis Time:** {{ "%.3f"|format(metadata.analysis_time_seconds) }} seconds

    ## Summary

    | Category | Added | Removed | Modified | Total |
    |----------|--------|---------|----------|-------|
    | Tables | {{ summary.tables_added }} | {{ summary.tables_removed }} | {{ summary.tables_modified }} | {{ summary.tables_added + summary.tables_removed + summary.tables_modified }} |
    | Columns | {{ summary.columns_added }} | {{ summary.columns_removed }} | {{ summary.columns_modified }} | {{ summary.columns_added + summary.columns_removed + summary.columns_modified }} |
    | Constraints | {{ summary.constraints_added }} | {{ summary.constraints_removed }} | {{ summary.constraints_modified }} | {{ summary.constraints_added + summary.constraints_removed + summary.constraints_modified }} |
    | Indexes | {{ summary.indexes_added }} | {{ summary.indexes_removed }} | {{ summary.indexes_modified }} | {{ summary.indexes_added + summary.indexes_removed + summary.indexes_modified }} |
    | **Total Changes** | | | | **{{ summary.total_changes }}** |

    {% if summary.total_changes > 0 %}
        {% if use_table_grouping %}
    ## Schema Changes by Table
            {% for change_type in ['added', 'removed', 'modified'] %}
                {% set tables = grouped_result.tables_by_change[change_type] %}
                {% if tables %}

    ### Tables {{ change_type.title() }} ({{ tables|length }})
                    {% for table in tables %}

    #### {{ table.table_name }} `{{ change_type.upper() }}`
                        {% if config.show_change_counts and table.change_type == 'modified' %}
    > **{{ table.total_changes }}** changes detected
                        {% endif %}
                        {% if table.change_type == 'modified' %}
                            {% for section, items in table.changes.items() %}
                                {% if items %}

    **{{ section.replace('_', ' ').title() }}** ({{ items|length }}):
                                    {% for item in items %}
    - `{{ item }}`
                                    {% endfor %}
                                {% endif %}
                            {% endfor %}
                        {% else %}

    - Table "{{ table.table_name }}" was **{{ change_type }}**
                            {% if table.table_info and table.table_info.columns %}
      ({{ table.table_info.columns|length }} columns)
                            {% endif %}
                        {% endif %}
                    {% endfor %}
                {% endif %}
            {% endfor %}
            
            {% if config.show_legacy_format %}

    ## Traditional View
    {{ content }}
            {% endif %}
        {% else %}
    {{ content }}
        {% endif %}
    {% else %}
    ## No Changes Detected

    The schemas are identical.
    {% endif %}

    ---
    *Generated by PGSD v{{ metadata.generator_version }}*
    """
    ).strip()

    # JSON template structure
    JSON_TEMPLATE = {
        "report_metadata": {
            "generated_at": "{{ metadata.generated_at }}",
            "source_database": "{{ metadata.source_database }}",
            "target_database": "{{ metadata.target_database }}",
            "source_schema": "{{ metadata.source_schema }}",
            "target_schema": "{{ metadata.target_schema }}",
            "analysis_time_seconds": "{{ metadata.analysis_time_seconds }}",
            "generator_version": "{{ metadata.generator_version }}",
            "total_changes": "{{ summary.total_changes }}",
        },
        "summary": "{{ summary }}",
        "changes": "{{ changes }}",
    }

    # XML template
    XML_TEMPLATE = textwrap.dedent(
        """
    <?xml version="1.0" encoding="UTF-8"?>
    <schema_diff_report>
        <metadata>
            <generated_at>{{ metadata.generated_at }}</generated_at>
            <source_database>{{ metadata.source_database }}</source_database>
            <target_database>{{ metadata.target_database }}</target_database>
            <source_schema>{{ metadata.source_schema }}</source_schema>
            <target_schema>{{ metadata.target_schema }}</target_schema>
            <analysis_time_seconds>{{ metadata.analysis_time_seconds }}</analysis_time_seconds>
            <generator_version>{{ metadata.generator_version }}</generator_version>
        </metadata>

        <summary total_changes="{{ summary.total_changes }}">
            <tables added="{{ summary.tables_added }}" 
                    removed="{{ summary.tables_removed }}" 
                    modified="{{ summary.tables_modified }}" />
            <columns added="{{ summary.columns_added }}" 
                     removed="{{ summary.columns_removed }}" 
                     modified="{{ summary.columns_modified }}" />
            <constraints added="{{ summary.constraints_added }}" 
                         removed="{{ summary.constraints_removed }}" 
                         modified="{{ summary.constraints_modified }}" />
            <indexes added="{{ summary.indexes_added }}" 
                     removed="{{ summary.indexes_removed }}" 
                     modified="{{ summary.indexes_modified }}" />
        </summary>

        <changes>
            {{ content }}
        </changes>
    </schema_diff_report>
    """
    ).strip()


class TemplateManager:
    """Manages report templates for different formats.

    This class provides functionality to load, cache, and render templates
    for various report formats. It supports both built-in templates and
    custom templates loaded from files.

    Attributes:
        _template_cache: Cache of loaded templates
        _custom_template_paths: Paths to custom template directories
    """

    def __init__(self):
        """Initialize the template manager."""
        self._template_cache: Dict[ReportFormat, str] = {}
        self._custom_template_paths: list[Path] = []
        self.logger = logging.getLogger(__name__)

    def add_template_path(self, path: Path) -> None:
        """Add a custom template directory path.

        Args:
            path: Path to template directory

        Raises:
            ProcessingError: If path is not a directory
        """
        if not isinstance(path, Path):
            path = Path(path)

        if not path.exists():
            raise ProcessingError(f"Template path does not exist: {path}")

        if not path.is_dir():
            raise ProcessingError(f"Template path is not a directory: {path}")

        self._custom_template_paths.append(path)
        self.logger.debug(f"Added template path: {path}")

    def get_builtin_template(self, format_type: ReportFormat) -> str:
        """Get built-in template for the specified format.

        Args:
            format_type: Report format

        Returns:
            Template content as string

        Raises:
            ProcessingError: If format is not supported
        """
        templates = {
            ReportFormat.HTML: BuiltinTemplates.HTML_TEMPLATE,
            ReportFormat.MARKDOWN: BuiltinTemplates.MARKDOWN_TEMPLATE,
            ReportFormat.XML: BuiltinTemplates.XML_TEMPLATE,
        }

        if format_type not in templates:
            raise ProcessingError(
                f"No built-in template for format: {format_type.value}"
            )

        return templates[format_type]

    def load_custom_template(self, format_type: ReportFormat) -> Optional[str]:
        """Load custom template for the specified format.

        Args:
            format_type: Report format

        Returns:
            Template content if found, None otherwise
        """
        template_filename = f"template{format_type.file_extension}"

        for template_path in self._custom_template_paths:
            template_file = template_path / template_filename

            if template_file.exists():
                try:
                    with open(template_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        self.logger.debug(f"Loaded custom template: {template_file}")
                        return content
                except Exception as e:
                    self.logger.warning(
                        f"Failed to load custom template {template_file}: {e}"
                    )

        return None

    def get_template(self, format_type: ReportFormat, use_cache: bool = True) -> str:
        """Get template for the specified format.

        This method first tries to load a custom template, then falls back
        to the built-in template if no custom template is found.

        Args:
            format_type: Report format
            use_cache: Whether to use cached templates

        Returns:
            Template content as string

        Raises:
            ProcessingError: If no template is available
        """
        # Check cache first
        if use_cache and format_type in self._template_cache:
            return self._template_cache[format_type]

        # Try custom template first
        template_content = self.load_custom_template(format_type)

        # Fall back to built-in template
        if template_content is None:
            template_content = self.get_builtin_template(format_type)

        # Cache the result
        if use_cache:
            self._template_cache[format_type] = template_content

        return template_content

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._template_cache.clear()
        self.logger.debug("Template cache cleared")

    def preload_templates(self) -> None:
        """Preload all available templates into cache."""
        for format_type in ReportFormat:
            try:
                self.get_template(format_type, use_cache=True)
                self.logger.debug(f"Preloaded template for {format_type.value}")
            except Exception as e:
                self.logger.warning(
                    f"Failed to preload template for {format_type.value}: {e}"
                )

    def get_template_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available templates.

        Returns:
            Dictionary with template information
        """
        info = {}

        for format_type in ReportFormat:
            format_info = {
                "format": format_type.value,
                "has_builtin": True,  # We have built-in templates for most formats
                "has_custom": self.load_custom_template(format_type) is not None,
                "cached": format_type in self._template_cache,
                "file_extension": format_type.file_extension,
            }

            # Check if built-in template actually exists
            try:
                self.get_builtin_template(format_type)
            except ProcessingError:
                format_info["has_builtin"] = False

            info[format_type.value] = format_info

        return info

    def __repr__(self) -> str:
        """String representation of the template manager."""
        cached_formats = [f.value for f in self._template_cache.keys()]
        return f"TemplateManager(cached={cached_formats}, paths={len(self._custom_template_paths)})"


# Global template manager instance
_global_template_manager: Optional[TemplateManager] = None


def get_global_template_manager() -> TemplateManager:
    """Get the global template manager instance.

    Returns:
        Global TemplateManager instance
    """
    global _global_template_manager

    if _global_template_manager is None:
        _global_template_manager = TemplateManager()
        logger.debug("Created global template manager instance")

    return _global_template_manager


def get_template(format_type: ReportFormat) -> str:
    """Get template using the global template manager.

    Args:
        format_type: Report format

    Returns:
        Template content as string
    """
    manager = get_global_template_manager()
    return manager.get_template(format_type)

