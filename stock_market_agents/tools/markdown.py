"""Markdown utilities for generating formatted reports."""

from typing import Dict, List, Any
import pandas as pd

def create_header(text: str, level: int = 1) -> str:
    """Create a markdown header.
    
    Args:
        text: Header text
        level: Header level (1-6)
        
    Returns:
        Markdown formatted header
    """
    return f"{'#' * level} {text}"

def create_table(data: Dict[str, List[Any]]) -> str:
    """Create a markdown table from dictionary data.
    
    Args:
        data: Dictionary with column names as keys and column values as lists
        
    Returns:
        Markdown formatted table
    """
    if not data:
        return ""
    
    # Convert to DataFrame for easy formatting
    df = pd.DataFrame(data)
    
    # Create header
    header = f"| {' | '.join(df.columns)} |"
    separator = f"|{'|'.join(['---' for _ in df.columns])}|"
    
    # Create rows
    rows = []
    for _, row in df.iterrows():
        rows.append(f"| {' | '.join(str(val) for val in row)} |")
    
    return "\n".join([header, separator] + rows)

def create_chart(title: str, data: Dict[str, List[float]], chart_type: str = "line") -> str:
    """Create a markdown chart using mermaid.
    
    Args:
        title: Chart title
        data: Dictionary with series names as keys and values as lists
        chart_type: Type of chart (line, bar)
        
    Returns:
        Markdown formatted mermaid chart
    """
    chart = [
        "```mermaid",
        f"{chart_type}Chart",
        f"title {title}",
    ]
    
    # Add data series
    for series_name, values in data.items():
        chart.append(f"{series_name} {' '.join(str(val) for val in values)}")
    
    chart.append("```")
    return "\n".join(chart)

def format_currency(value: float, currency: str = "$") -> str:
    """Format a value as currency.
    
    Args:
        value: Numeric value
        currency: Currency symbol
        
    Returns:
        Formatted currency string
    """
    if value is None:
        return "N/A"
    return f"{currency}{value:,.2f}"

def format_percentage(value: float) -> str:
    """Format a value as percentage.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"
    return f"{value:.2f}%"
