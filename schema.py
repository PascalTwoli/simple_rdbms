"""
Schema definitions for tables and columns.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

from datatypes import DataType
from exceptions import TableNotFoundError, TableExistsError, ColumnNotFoundError


@dataclass
class Column:
    """Definition of a table column."""
    name: str
    data_type: DataType
    primary_key: bool = False
    unique: bool = False
    not_null: bool = False
    
    def __post_init__(self):
        # Primary keys are implicitly unique and not null
        if self.primary_key:
            self.unique = True
            self.not_null = True
    
    def __str__(self) -> str:
        parts = [self.name, str(self.data_type)]
        if self.primary_key:
            parts.append('PRIMARY KEY')
        elif self.unique:
            parts.append('UNIQUE')
        if self.not_null and not self.primary_key:
            parts.append('NOT NULL')
        return ' '.join(parts)


@dataclass
class TableSchema:
    """Schema definition for a table."""
    name: str
    columns: List[Column] = field(default_factory=list)
    
    def __post_init__(self):
        self._column_map: Dict[str, Column] = {}
        self._primary_key: Optional[Column] = None
        self._unique_columns: Set[str] = set()
        
        for col in self.columns:
            self._column_map[col.name.lower()] = col
            if col.primary_key:
                if self._primary_key is not None:
                    raise ValueError(f"Table {self.name} has multiple primary keys")
                self._primary_key = col
            if col.unique:
                self._unique_columns.add(col.name.lower())
    
    def get_column(self, name: str) -> Column:
        """Get a column by name."""
        lower_name = name.lower()
        if lower_name not in self._column_map:
            raise ColumnNotFoundError(name, self.name)
        return self._column_map[lower_name]
    
    def has_column(self, name: str) -> bool:
        """Check if a column exists."""
        return name.lower() in self._column_map
    
    @property
    def primary_key(self) -> Optional[Column]:
        """Get the primary key column, if any."""
        return self._primary_key
    
    @property
    def unique_columns(self) -> Set[str]:
        """Get the set of unique column names."""
        return self._unique_columns
    
    @property
    def column_names(self) -> List[str]:
        """Get list of column names in order."""
        return [col.name for col in self.columns]
    
    def __str__(self) -> str:
        cols_str = ',\n  '.join(str(col) for col in self.columns)
        return f"CREATE TABLE {self.name} (\n  {cols_str}\n);"


class Catalog:
    """
    Database catalog - stores all table schemas.
    Acts as the central registry for database metadata.
    """
    
    def __init__(self):
        self._tables: Dict[str, TableSchema] = {}
    
    def create_table(self, schema: TableSchema) -> None:
        """Register a new table schema."""
        lower_name = schema.name.lower()
        if lower_name in self._tables:
            raise TableExistsError(schema.name)
        self._tables[lower_name] = schema
    
    def drop_table(self, name: str) -> None:
        """Remove a table schema."""
        lower_name = name.lower()
        if lower_name not in self._tables:
            raise TableNotFoundError(name)
        del self._tables[lower_name]
    
    def get_table(self, name: str) -> TableSchema:
        """Get a table schema by name."""
        lower_name = name.lower()
        if lower_name not in self._tables:
            raise TableNotFoundError(name)
        return self._tables[lower_name]
    
    def has_table(self, name: str) -> bool:
        """Check if a table exists."""
        return name.lower() in self._tables
    
    def list_tables(self) -> List[str]:
        """Get a list of all table names."""
        return [schema.name for schema in self._tables.values()]
    
    def clear(self) -> None:
        """Remove all tables from the catalog."""
        self._tables.clear()
