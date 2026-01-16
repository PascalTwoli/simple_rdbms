"""
Data type definitions for the RDBMS.
"""

from enum import Enum, auto
from typing import Any, Optional

from exceptions import DataTypeError


class DataType(Enum):
    """Supported data types in the RDBMS."""
    INTEGER = auto()
    TEXT = auto()
    REAL = auto()
    BOOLEAN = auto()
    
    @classmethod
    def from_string(cls, type_str: str) -> 'DataType':
        """Parse a data type from a string."""
        type_map = {
            'INTEGER': cls.INTEGER,
            'INT': cls.INTEGER,
            'TEXT': cls.TEXT,
            'VARCHAR': cls.TEXT,
            'STRING': cls.TEXT,
            'REAL': cls.REAL,
            'FLOAT': cls.REAL,
            'DOUBLE': cls.REAL,
            'BOOLEAN': cls.BOOLEAN,
            'BOOL': cls.BOOLEAN,
        }
        upper = type_str.upper()
        if upper in type_map:
            return type_map[upper]
        raise ValueError(f"Unknown data type: {type_str}")
    
    def __str__(self) -> str:
        return self.name


def validate_and_coerce(value: Any, data_type: DataType, column_name: str = None) -> Any:
    """
    Validate and coerce a value to the specified data type.
    
    Args:
        value: The value to validate/coerce
        data_type: The target data type
        column_name: Optional column name for error messages
        
    Returns:
        The coerced value
        
    Raises:
        DataTypeError: If the value cannot be coerced to the target type
    """
    if value is None:
        return None
    
    try:
        if data_type == DataType.INTEGER:
            if isinstance(value, bool):
                raise DataTypeError('INTEGER', value, column_name)
            if isinstance(value, int):
                return value
            if isinstance(value, float) and value.is_integer():
                return int(value)
            if isinstance(value, str):
                return int(value)
            raise DataTypeError('INTEGER', value, column_name)
        
        elif data_type == DataType.TEXT:
            if isinstance(value, str):
                return value
            return str(value)
        
        elif data_type == DataType.REAL:
            if isinstance(value, bool):
                raise DataTypeError('REAL', value, column_name)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                return float(value)
            raise DataTypeError('REAL', value, column_name)
        
        elif data_type == DataType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, int):
                return bool(value)
            if isinstance(value, str):
                lower = value.lower()
                if lower in ('true', '1', 'yes', 'on'):
                    return True
                if lower in ('false', '0', 'no', 'off'):
                    return False
            raise DataTypeError('BOOLEAN', value, column_name)
        
    except (ValueError, TypeError):
        raise DataTypeError(data_type.name, value, column_name)
    
    raise DataTypeError(data_type.name, value, column_name)


def compare_values(left: Any, right: Any) -> int:
    """
    Compare two values for ordering.
    
    Returns:
        -1 if left < right
         0 if left == right
         1 if left > right
    """
    # Handle NULL values - NULL is considered less than any value
    if left is None and right is None:
        return 0
    if left is None:
        return -1
    if right is None:
        return 1
    
    # Standard comparison
    if left < right:
        return -1
    elif left > right:
        return 1
    else:
        return 0
