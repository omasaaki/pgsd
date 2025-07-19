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

    # HTML template with modern CSS Grid/Flexbox layout and advanced design
    HTML_TEMPLATE = textwrap.dedent(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PostgreSQL Schema Diff Report</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Color System - Modern & Accessible */
                --color-added: #10b981;
                --color-added-light: #d1fae5;
                --color-added-dark: #064e3b;
                --color-removed: #ef4444;
                --color-removed-light: #fee2e2;
                --color-removed-dark: #7f1d1d;
                --color-modified: #f59e0b;
                --color-modified-light: #fef3c7;
                --color-modified-dark: #78350f;
                --color-info: #3b82f6;
                --color-info-light: #dbeafe;
                --color-info-dark: #1e3a8a;
                --color-neutral: #6b7280;
                --color-neutral-light: #f9fafb;
                --color-neutral-dark: #1f2937;
                
                /* Typography System */
                --font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                --font-family-mono: 'Fira Code', 'Monaco', 'Consolas', monospace;
                
                /* Spacing System */
                --spacing-unit: 0.25rem;
                --spacing-xs: calc(var(--spacing-unit) * 2);
                --spacing-sm: calc(var(--spacing-unit) * 3);
                --spacing-md: calc(var(--spacing-unit) * 4);
                --spacing-lg: calc(var(--spacing-unit) * 6);
                --spacing-xl: calc(var(--spacing-unit) * 8);
                --spacing-2xl: calc(var(--spacing-unit) * 12);
                
                /* Shadow System */
                --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                
                /* Border Radius */
                --radius-sm: 0.25rem;
                --radius-md: 0.375rem;
                --radius-lg: 0.5rem;
                --radius-xl: 0.75rem;
                --radius-2xl: 1rem;
            }

            * {
                box-sizing: border-box;
            }

            body {
                font-family: var(--font-family-sans);
                margin: 0;
                padding: var(--spacing-lg);
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                color: var(--color-neutral-dark);
                line-height: 1.6;
                min-height: 100vh;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: var(--radius-2xl);
                box-shadow: var(--shadow-xl);
                overflow: hidden;
                min-height: calc(100vh - var(--spacing-xl));
                display: flex;
                flex-direction: column;
            }

            /* Header Section */
            .header {
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                color: white;
                padding: var(--spacing-2xl);
                position: relative;
                overflow: hidden;
            }

            .header::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
                opacity: 0.3;
            }

            .header-content {
                position: relative;
                z-index: 1;
            }

            .header h1 {
                margin: 0 0 var(--spacing-md) 0;
                font-size: 2.5rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                display: flex;
                align-items: center;
                gap: var(--spacing-md);
            }

            .header h1::before {
                content: '📊';
                font-size: 2rem;
            }

            .metadata {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: var(--spacing-lg);
                margin-top: var(--spacing-lg);
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: var(--radius-lg);
                padding: var(--spacing-lg);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            .metadata-item {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-xs);
            }

            .metadata-label {
                font-size: 0.875rem;
                opacity: 0.8;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .metadata-value {
                font-weight: 600;
                font-family: var(--font-family-mono);
                font-size: 0.875rem;
            }

            /* Main Content */
            .main-content {
                flex: 1;
                padding: var(--spacing-2xl);
            }

            /* Dashboard Cards */
            .dashboard {
                margin-bottom: var(--spacing-2xl);
            }

            .summary-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: var(--spacing-lg);
                margin-bottom: var(--spacing-xl);
            }

            .card {
                background: white;
                border-radius: var(--radius-xl);
                box-shadow: var(--shadow-md);
                padding: var(--spacing-lg);
                transition: all 0.2s ease;
                border: 1px solid rgba(0, 0, 0, 0.05);
                position: relative;
                overflow: hidden;
            }

            .card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: var(--gradient, linear-gradient(135deg, var(--color-info) 0%, var(--color-info) 100%));
            }

            .card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }

            .card.added { --gradient: linear-gradient(135deg, var(--color-added) 0%, #22c55e 100%); }
            .card.removed { --gradient: linear-gradient(135deg, var(--color-removed) 0%, #f87171 100%); }
            .card.modified { --gradient: linear-gradient(135deg, var(--color-modified) 0%, #fbbf24 100%); }
            .card.info { --gradient: linear-gradient(135deg, var(--color-info) 0%, #60a5fa 100%); }

            .card-header {
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
                margin-bottom: var(--spacing-md);
            }

            .card-icon {
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 48px;
                height: 48px;
                border-radius: var(--radius-lg);
                background: var(--icon-bg, var(--color-info-light));
                color: var(--icon-color, var(--color-info-dark));
            }

            .card.added .card-icon { 
                background: var(--color-added-light); 
                color: var(--color-added-dark);
            }
            .card.removed .card-icon { 
                background: var(--color-removed-light); 
                color: var(--color-removed-dark);
            }
            .card.modified .card-icon { 
                background: var(--color-modified-light); 
                color: var(--color-modified-dark);
            }
            .card.info .card-icon { 
                background: var(--color-info-light); 
                color: var(--color-info-dark);
            }

            .card-title {
                margin: 0;
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--color-neutral);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .card-metric {
                font-size: 2.5rem;
                font-weight: 700;
                line-height: 1;
                color: var(--metric-color, var(--color-neutral-dark));
                margin-bottom: var(--spacing-xs);
            }

            .card.added .card-metric { color: var(--color-added); }
            .card.removed .card-metric { color: var(--color-removed); }
            .card.modified .card-metric { color: var(--color-modified); }
            .card.info .card-metric { color: var(--color-info); }

            .card-subtitle {
                font-size: 0.875rem;
                color: var(--color-neutral);
                margin: 0;
            }

            /* Search and Filter */
            .controls {
                display: flex;
                flex-wrap: wrap;
                gap: var(--spacing-md);
                margin-bottom: var(--spacing-xl);
                align-items: center;
            }

            .search-box {
                flex: 1;
                min-width: 300px;
                position: relative;
            }

            .search-input {
                width: 100%;
                padding: var(--spacing-sm) var(--spacing-md) var(--spacing-sm) 3rem;
                border: 1px solid #d1d5db;
                border-radius: var(--radius-lg);
                font-size: 0.875rem;
                background: white;
                transition: all 0.2s ease;
            }

            .search-input:focus {
                outline: none;
                border-color: var(--color-info);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }

            .search-icon {
                position: absolute;
                left: var(--spacing-md);
                top: 50%;
                transform: translateY(-50%);
                color: var(--color-neutral);
                font-size: 1.125rem;
            }

            .filter-buttons {
                display: flex;
                gap: var(--spacing-xs);
                flex-wrap: wrap;
            }

            .filter-btn {
                padding: var(--spacing-xs) var(--spacing-md);
                border: 1px solid #d1d5db;
                background: white;
                border-radius: var(--radius-md);
                font-size: 0.875rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: var(--spacing-xs);
            }

            .filter-btn:hover {
                background: var(--color-neutral-light);
                border-color: var(--color-neutral);
            }

            .filter-btn.active {
                background: var(--color-info);
                color: white;
                border-color: var(--color-info);
            }

            /* Change Sections */
            .change-sections {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-xl);
            }

            .section {
                background: white;
                border-radius: var(--radius-xl);
                box-shadow: var(--shadow-md);
                overflow: hidden;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }

            .section-header {
                padding: var(--spacing-lg) var(--spacing-xl);
                background: var(--section-bg, var(--color-neutral-light));
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .section-header:hover {
                background: var(--section-bg-hover, #f3f4f6);
            }

            .section-header.added { 
                --section-bg: var(--color-added-light);
                --section-bg-hover: #bbf7d0;
            }
            .section-header.removed { 
                --section-bg: var(--color-removed-light);
                --section-bg-hover: #fecaca;
            }
            .section-header.modified { 
                --section-bg: var(--color-modified-light);
                --section-bg-hover: #fed7aa;
            }

            .section-title {
                display: flex;
                align-items: center;
                gap: var(--spacing-md);
                margin: 0;
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--color-neutral-dark);
            }

            .section-count {
                background: rgba(0, 0, 0, 0.1);
                color: var(--color-neutral-dark);
                padding: var(--spacing-xs) var(--spacing-sm);
                border-radius: var(--radius-md);
                font-size: 0.875rem;
                font-weight: 600;
                margin-left: var(--spacing-sm);
            }

            .toggle-icon {
                font-size: 1.25rem;
                transition: transform 0.2s ease;
                color: var(--color-neutral);
            }

            .toggle-icon.expanded {
                transform: rotate(180deg);
            }

            .section-content {
                display: none;
                padding: var(--spacing-xl);
            }

            .section-content.expanded {
                display: block;
            }

            /* Table Items */
            .table-items {
                display: grid;
                gap: var(--spacing-md);
            }

            .table-item {
                background: var(--color-neutral-light);
                border-radius: var(--radius-lg);
                padding: var(--spacing-lg);
                border-left: 4px solid var(--item-color, var(--color-neutral));
                transition: all 0.2s ease;
            }

            .table-item:hover {
                background: white;
                box-shadow: var(--shadow-sm);
            }

            .table-item.added { --item-color: var(--color-added); }
            .table-item.removed { --item-color: var(--color-removed); }
            .table-item.modified { --item-color: var(--color-modified); }

            .table-item-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: var(--spacing-md);
            }

            .table-name {
                font-family: var(--font-family-mono);
                font-weight: 600;
                font-size: 1.125rem;
                color: var(--color-neutral-dark);
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
            }

            .table-name::before {
                content: '📊';
                font-size: 1rem;
            }

            .badge-group {
                display: flex;
                gap: var(--spacing-xs);
                flex-wrap: wrap;
            }

            .badge {
                display: inline-flex;
                align-items: center;
                gap: var(--spacing-xs);
                padding: var(--spacing-xs) var(--spacing-sm);
                border-radius: var(--radius-md);
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .badge.added {
                background: var(--color-added);
                color: white;
            }

            .badge.removed {
                background: var(--color-removed);
                color: white;
            }

            .badge.modified {
                background: var(--color-modified);
                color: white;
            }

            .badge.info {
                background: var(--color-info-light);
                color: var(--color-info-dark);
            }

            /* Diff Display */
            .diff-container {
                margin-top: var(--spacing-md);
                background: #1e293b;
                border-radius: var(--radius-lg);
                overflow: hidden;
                font-family: var(--font-family-mono);
            }

            .diff-header {
                background: #334155;
                padding: var(--spacing-sm) var(--spacing-md);
                color: white;
                font-size: 0.875rem;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
            }

            .diff-content {
                max-height: 300px;
                overflow-y: auto;
            }

            .diff-line {
                padding: var(--spacing-xs) var(--spacing-md);
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
                font-size: 0.875rem;
                line-height: 1.5;
            }

            .diff-line.added {
                background: rgba(16, 185, 129, 0.1);
                color: #10b981;
            }

            .diff-line.removed {
                background: rgba(239, 68, 68, 0.1);
                color: #ef4444;
            }

            .diff-marker {
                font-weight: 600;
                width: 1.5rem;
                text-align: center;
            }

            /* No Changes State */
            .no-changes {
                text-align: center;
                padding: var(--spacing-2xl);
                color: var(--color-neutral);
            }

            .no-changes-icon {
                font-size: 4rem;
                margin-bottom: var(--spacing-lg);
                opacity: 0.5;
            }

            .no-changes h2 {
                margin: 0 0 var(--spacing-md) 0;
                color: var(--color-neutral);
                font-weight: 600;
            }

            .no-changes p {
                margin: 0;
                font-size: 1.125rem;
            }

            /* Footer */
            .footer {
                background: var(--color-neutral-light);
                padding: var(--spacing-lg) var(--spacing-xl);
                text-align: center;
                color: var(--color-neutral);
                font-size: 0.875rem;
                border-top: 1px solid rgba(0, 0, 0, 0.1);
            }

            /* Responsive Design */
            @media (max-width: 768px) {
                body {
                    padding: var(--spacing-md);
                }

                .header {
                    padding: var(--spacing-lg);
                }

                .header h1 {
                    font-size: 2rem;
                }

                .main-content {
                    padding: var(--spacing-lg);
                }

                .summary-grid {
                    grid-template-columns: 1fr;
                }

                .metadata {
                    grid-template-columns: 1fr;
                }

                .controls {
                    flex-direction: column;
                    align-items: stretch;
                }

                .search-box {
                    min-width: auto;
                }

                .filter-buttons {
                    justify-content: center;
                }
            }

            /* Animation and Interactions */
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .card, .section, .table-item {
                animation: slideIn 0.3s ease forwards;
            }

            /* Print Styles */
            @media print {
                body {
                    background: white;
                    padding: 0;
                }

                .container {
                    box-shadow: none;
                    border-radius: 0;
                }

                .header {
                    background: #1e293b !important;
                    -webkit-print-color-adjust: exact;
                    color-adjust: exact;
                }

                .section-content {
                    display: block !important;
                }

                .card:hover,
                .table-item:hover {
                    transform: none;
                    box-shadow: var(--shadow-sm);
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header Section -->
            <div class="header">
                <div class="header-content">
                    <h1>PostgreSQL Schema Diff Report</h1>
                    
                    <div class="metadata">
                        <div class="metadata-item">
                            <div class="metadata-label">Generated</div>
                            <div class="metadata-value">{{ metadata.generated_at }}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Source Database</div>
                            <div class="metadata-value">{{ metadata.source_database }}.{{ metadata.source_schema }}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Target Database</div>
                            <div class="metadata-value">{{ metadata.target_database }}.{{ metadata.target_schema }}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Analysis Time</div>
                            <div class="metadata-value">{{ "%.3f"|format(metadata.analysis_time_seconds) }}s</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="main-content">
                <!-- Dashboard Summary -->
                <div class="dashboard">
                    <div class="summary-grid">
                        <div class="card info">
                            <div class="card-header">
                                <div class="card-icon">📊</div>
                                <div>
                                    <h3 class="card-title">Total Changes</h3>
                                </div>
                            </div>
                            <div class="card-metric">{{ summary.total_changes }}</div>
                            <p class="card-subtitle">Overall modifications detected</p>
                        </div>
                        
                        <div class="card added">
                            <div class="card-header">
                                <div class="card-icon">📝</div>
                                <div>
                                    <h3 class="card-title">Tables Added</h3>
                                </div>
                            </div>
                            <div class="card-metric">{{ summary.tables_added }}</div>
                            <p class="card-subtitle">New tables created</p>
                        </div>
                        
                        <div class="card removed">
                            <div class="card-header">
                                <div class="card-icon">🗑️</div>
                                <div>
                                    <h3 class="card-title">Tables Removed</h3>
                                </div>
                            </div>
                            <div class="card-metric">{{ summary.tables_removed }}</div>
                            <p class="card-subtitle">Tables deleted</p>
                        </div>
                        
                        <div class="card modified">
                            <div class="card-header">
                                <div class="card-icon">⚡</div>
                                <div>
                                    <h3 class="card-title">Tables Modified</h3>
                                </div>
                            </div>
                            <div class="card-metric">{{ summary.tables_modified }}</div>
                            <p class="card-subtitle">Tables with changes</p>
                        </div>
                        
                        <div class="card info">
                            <div class="card-header">
                                <div class="card-icon">📋</div>
                                <div>
                                    <h3 class="card-title">Column Changes</h3>
                                </div>
                            </div>
                            <div class="card-metric">{{ summary.columns_added + summary.columns_removed + summary.columns_modified }}</div>
                            <p class="card-subtitle">Total column modifications</p>
                        </div>
                        
                        <div class="card info">
                            <div class="card-header">
                                <div class="card-icon">🔗</div>
                                <div>
                                    <h3 class="card-title">Constraint Changes</h3>
                                </div>
                            </div>
                            <div class="card-metric">{{ summary.constraints_added + summary.constraints_removed + summary.constraints_modified }}</div>
                            <p class="card-subtitle">Constraint modifications</p>
                        </div>
                    </div>
                    
                    <!-- Search and Filter Controls -->
                    {% if summary.total_changes > 0 %}
                    <div class="controls">
                        <div class="search-box">
                            <div class="search-icon">🔍</div>
                            <input type="text" class="search-input" placeholder="Search tables, columns, or changes..." id="searchInput">
                        </div>
                        <div class="filter-buttons">
                            <button class="filter-btn active" data-filter="all">
                                <span>📊</span> All Changes
                            </button>
                            <button class="filter-btn" data-filter="added">
                                <span>➕</span> Added
                            </button>
                            <button class="filter-btn" data-filter="removed">
                                <span>➖</span> Removed
                            </button>
                            <button class="filter-btn" data-filter="modified">
                                <span>⚡</span> Modified
                            </button>
                        </div>
                    </div>
                    {% endif %}
                </div>

                <!-- Change Details -->
                {% if use_table_grouping %}
                    <div class="change-sections">
                        {% for change_type in ['added', 'removed', 'modified'] %}
                            {% set tables = grouped_result.tables_by_change[change_type] %}
                            {% if tables %}
                                <div class="section" data-change-type="{{ change_type }}">
                                    <div class="section-header {{ change_type }}" onclick="toggleSection('{{ change_type }}_section')">
                                        <div class="section-title">
                                            {% if change_type == 'added' %}
                                                <span>➕</span> Tables Added
                                            {% elif change_type == 'removed' %}
                                                <span>➖</span> Tables Removed
                                            {% else %}
                                                <span>⚡</span> Tables Modified
                                            {% endif %}
                                            <span class="section-count">{{ tables|length }}</span>
                                        </div>
                                        <div class="toggle-icon" id="icon_{{ change_type }}_section">▼</div>
                                    </div>
                                    <div class="section-content" id="content_{{ change_type }}_section">
                                        <div class="table-items">
                                            {% for table in tables %}
                                                <div class="table-item {{ change_type }}" data-table-name="{{ table.table_name }}">
                                                    <div class="table-item-header">
                                                        <div class="table-name">{{ table.table_name }}</div>
                                                        <div class="badge-group">
                                                            <span class="badge {{ change_type }}">{{ change_type.upper() }}</span>
                                                            {% if table.table_info and table.table_info.columns %}
                                                                <span class="badge info">📝 {{ table.table_info.columns|length }} columns</span>
                                                            {% endif %}
                                                            {% if config.show_change_counts and table.change_type == 'modified' %}
                                                                <span class="badge info">⚡ {{ table.total_changes }} changes</span>
                                                            {% endif %}
                                                        </div>
                                                    </div>
                                                    
                                                    {% if table.change_type == 'modified' %}
                                                        {% for section, items in table.changes.items() %}
                                                            {% if items %}
                                                                <div class="diff-container">
                                                                    <div class="diff-header">
                                                                        <span>🔧</span>
                                                                        {{ section.replace('_', ' ').title() }} ({{ items|length }} changes)
                                                                    </div>
                                                                    <div class="diff-content">
                                                                        {% for item in items %}
                                                                            <div class="diff-line">
                                                                                <span class="diff-marker">•</span>
                                                                                <code>{{ item }}</code>
                                                                            </div>
                                                                        {% endfor %}
                                                                    </div>
                                                                </div>
                                                            {% endif %}
                                                        {% endfor %}
                                                    {% else %}
                                                        <div class="diff-container">
                                                            <div class="diff-header">
                                                                <span>📊</span>
                                                                Table {{ change_type.title() }}
                                                            </div>
                                                            <div class="diff-content">
                                                                <div class="diff-line">
                                                                    <span class="diff-marker">•</span>
                                                                    <code>Table "{{ table.table_name }}" was {{ change_type }}</code>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    {% endif %}
                                                </div>
                                            {% endfor %}
                                        </div>
                                    </div>
                                </div>
                            {% endif %}
                        {% endfor %}
                    </div>
                {% endif %}
                {% else %}
                    <!-- Legacy format fallback -->
                    <div class="section">
                        <div class="section-header" onclick="toggleSection('legacy_section')">
                            <div class="section-title">
                                <span>📋</span> Schema Changes
                            </div>
                            <div class="toggle-icon" id="icon_legacy_section">▼</div>
                        </div>
                        <div class="section-content expanded" id="content_legacy_section">
                            {{ content }}
                        </div>
                    </div>
                {% else %}
                <div class="no-changes">
                    <div class="no-changes-icon">✅</div>
                    <h2>No Changes Detected</h2>
                    <p>The source and target schemas are identical.</p>
                </div>
            {% endif %}
            
            </div> <!-- End main-content -->

            <div class="footer">
                Generated by PGSD v{{ metadata.generator_version }} at {{ metadata.generated_at }}
            </div>
        </div>
        
        <!-- Enhanced JavaScript -->
        <script>
            // Toggle section visibility
            function toggleSection(sectionId) {
                const content = document.getElementById('content_' + sectionId);
                const icon = document.getElementById('icon_' + sectionId);
                
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
            
            // Search functionality
            function initializeSearch() {
                const searchInput = document.getElementById('searchInput');
                if (!searchInput) return;
                
                searchInput.addEventListener('input', function(e) {
                    const searchTerm = e.target.value.toLowerCase();
                    const tableItems = document.querySelectorAll('.table-item');
                    
                    tableItems.forEach(function(item) {
                        const tableName = item.dataset.tableName?.toLowerCase() || '';
                        const content = item.textContent.toLowerCase();
                        
                        if (tableName.includes(searchTerm) || content.includes(searchTerm)) {
                            item.style.display = '';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                    
                    // Update section visibility based on filtered results
                    updateSectionVisibility();
                });
            }
            
            // Filter functionality
            function initializeFilters() {
                const filterButtons = document.querySelectorAll('.filter-btn');
                
                filterButtons.forEach(function(button) {
                    button.addEventListener('click', function() {
                        // Update active state
                        filterButtons.forEach(btn => btn.classList.remove('active'));
                        this.classList.add('active');
                        
                        const filter = this.dataset.filter;
                        const sections = document.querySelectorAll('.section[data-change-type]');
                        
                        sections.forEach(function(section) {
                            const changeType = section.dataset.changeType;
                            
                            if (filter === 'all' || filter === changeType) {
                                section.style.display = '';
                            } else {
                                section.style.display = 'none';
                            }
                        });
                        
                        // Clear search when filtering
                        const searchInput = document.getElementById('searchInput');
                        if (searchInput) {
                            searchInput.value = '';
                            const tableItems = document.querySelectorAll('.table-item');
                            tableItems.forEach(item => item.style.display = '');
                        }
                    });
                });
            }
            
            // Update section visibility based on content
            function updateSectionVisibility() {
                const sections = document.querySelectorAll('.section[data-change-type]');
                
                sections.forEach(function(section) {
                    const visibleItems = section.querySelectorAll('.table-item:not([style*="display: none"])');
                    const sectionHeader = section.querySelector('.section-header');
                    
                    if (visibleItems.length === 0) {
                        section.style.display = 'none';
                    } else {
                        section.style.display = '';
                        
                        // Update count in section header
                        const countSpan = sectionHeader.querySelector('.section-count');
                        if (countSpan) {
                            countSpan.textContent = visibleItems.length;
                        }
                    }
                });
            }
            
            // Keyboard shortcuts
            function initializeKeyboardShortcuts() {
                document.addEventListener('keydown', function(e) {
                    // Ctrl/Cmd + F to focus search
                    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                        e.preventDefault();
                        const searchInput = document.getElementById('searchInput');
                        if (searchInput) {
                            searchInput.focus();
                        }
                    }
                    
                    // Escape to clear search
                    if (e.key === 'Escape') {
                        const searchInput = document.getElementById('searchInput');
                        if (searchInput && searchInput.value) {
                            searchInput.value = '';
                            searchInput.dispatchEvent(new Event('input'));
                        }
                    }
                });
            }
            
            // Auto-expand sections based on configuration
            function autoExpandSections() {
                const sections = document.querySelectorAll('.section');
                const shouldAutoExpand = sections.length <= 3 || {{ config.collapse_sections|default(true)|lower }} === false;
                
                if (shouldAutoExpand) {
                    sections.forEach(function(section) {
                        const header = section.querySelector('.section-header');
                        if (header && header.onclick) {
                            const sectionId = header.onclick.toString().match(/'([^']+)'/);
                            if (sectionId) {
                                toggleSection(sectionId[1]);
                            }
                        }
                    });
                }
            }
            
            // Smooth scrolling for anchor links
            function initializeSmoothScrolling() {
                document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                    anchor.addEventListener('click', function (e) {
                        e.preventDefault();
                        const target = document.querySelector(this.getAttribute('href'));
                        if (target) {
                            target.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                            });
                        }
                    });
                });
            }
            
            // Print optimization
            function initializePrintOptimization() {
                window.addEventListener('beforeprint', function() {
                    // Expand all sections for printing
                    const sections = document.querySelectorAll('.section-content');
                    sections.forEach(section => section.classList.add('expanded'));
                });
                
                window.addEventListener('afterprint', function() {
                    // Restore original state after printing
                    autoExpandSections();
                });
            }
            
            // Initialize all functionality when DOM is loaded
            document.addEventListener('DOMContentLoaded', function() {
                initializeSearch();
                initializeFilters();
                initializeKeyboardShortcuts();
                initializeSmoothScrolling();
                initializePrintOptimization();
                autoExpandSections();
                
                // Add loading animation removal
                setTimeout(function() {
                    document.body.classList.add('loaded');
                }, 100);
            });
            
            // Add some accessibility improvements
            document.addEventListener('DOMContentLoaded', function() {
                // Add ARIA labels to interactive elements
                const filterButtons = document.querySelectorAll('.filter-btn');
                filterButtons.forEach(button => {
                    button.setAttribute('role', 'button');
                    button.setAttribute('aria-pressed', button.classList.contains('active'));
                });
                
                // Add keyboard navigation for filter buttons
                filterButtons.forEach((button, index) => {
                    button.addEventListener('keydown', function(e) {
                        if (e.key === 'ArrowLeft' && index > 0) {
                            filterButtons[index - 1].focus();
                        } else if (e.key === 'ArrowRight' && index < filterButtons.length - 1) {
                            filterButtons[index + 1].focus();
                        }
                    });
                });
                
                // Add ARIA labels to section headers
                const sectionHeaders = document.querySelectorAll('.section-header');
                sectionHeaders.forEach(header => {
                    header.setAttribute('role', 'button');
                    header.setAttribute('aria-expanded', 'false');
                    header.setAttribute('tabindex', '0');
                    
                    // Allow keyboard activation
                    header.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            header.click();
                        }
                    });
                });
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

