"""
Storage engine for tables and rows.
"""

from typing import Any, Dict, List, Iterator, Optional, Set, Tuple
from dataclasses import dataclass, field

from schema import TableSchema, Column
from datatypes import DataType, validate_and_coerce
from index import IndexManager
from exceptions import (
    PrimaryKeyViolation,
    UniqueViolation,
    NotNullViolation,
    ColumnNotFoundError,
)


@dataclass
class Row:
    """
    Represents a single row in a table.
    """
    row_id: int
    data: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, column_name: str, default: Any = None) -> Any:
        """Get a column value."""
        return self.data.get(column_name.lower(), default)
    
    def set(self, column_name: str, value: Any) -> None:
        """Set a column value."""
        self.data[column_name.lower()] = value
    
    def __getitem__(self, column_name: str) -> Any:
        return self.data[column_name.lower()]
    
    def __setitem__(self, column_name: str, value: Any) -> None:
        self.data[column_name.lower()] = value
    
    def __contains__(self, column_name: str) -> bool:
        return column_name.lower() in self.data
    
    def copy(self) -> 'Row':
        """Create a copy of this row."""
        return Row(row_id=self.row_id, data=dict(self.data))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary."""
        return dict(self.data)


class Table:
    """
    In-memory table storage.
    """
    
    def __init__(self, schema: TableSchema):
        self.schema = schema
        self._rows: Dict[int, Row] = {}  # row_id -> Row
        self._next_row_id = 1
        self._index_manager = IndexManager()
        
        # Create index on primary key
        if schema.primary_key:
            self._index_manager.create_index(schema.primary_key.name)
        
        # Create indexes on unique columns
        for col in schema.columns:
            if col.unique and not col.primary_key:
                self._index_manager.create_index(col.name)
        
        # Track unique values for constraint checking
        self._unique_values: Dict[str, Set[Any]] = {
            col.name.lower(): set() for col in schema.columns if col.unique
        }
    
    def insert(self, values: Dict[str, Any]) -> Row:
        """
        Insert a new row into the table.
        
        Args:
            values: Dictionary mapping column names to values
            
        Returns:
            The newly created Row
            
        Raises:
            ConstraintError: If any constraint is violated
        """
        # Normalize column names
        normalized = {k.lower(): v for k, v in values.items()}
        
        # Validate and coerce all values
        row_data = {}
        for col in self.schema.columns:
            col_name = col.name.lower()
            value = normalized.get(col_name)
            
            # Check NOT NULL constraint
            if value is None and col.not_null:
                raise NotNullViolation(col.name)
            
            # Validate and coerce type
            if value is not None:
                value = validate_and_coerce(value, col.data_type, col.name)
            
            # Check UNIQUE/PRIMARY KEY constraint
            if col.unique and value is not None:
                if value in self._unique_values[col_name]:
                    if col.primary_key:
                        raise PrimaryKeyViolation(col.name, value)
                    else:
                        raise UniqueViolation(col.name, value)
            
            row_data[col_name] = value
        
        # All constraints passed, create the row
        row_id = self._next_row_id
        self._next_row_id += 1
        
        row = Row(row_id=row_id, data=row_data)
        self._rows[row_id] = row
        
        # Update unique value sets
        for col in self.schema.columns:
            if col.unique:
                col_name = col.name.lower()
                value = row_data.get(col_name)
                if value is not None:
                    self._unique_values[col_name].add(value)
        
        # Update indexes
        for col_name, value in row_data.items():
            if value is not None:
                self._index_manager.insert(col_name, value, row_id)
        
        return row
    
    def update(self, row_id: int, values: Dict[str, Any]) -> Optional[Row]:
        """
        Update an existing row.
        
        Args:
            row_id: The ID of the row to update
            values: Dictionary of columns to update
            
        Returns:
            The updated Row, or None if row not found
        """
        if row_id not in self._rows:
            return None
        
        row = self._rows[row_id]
        normalized = {k.lower(): v for k, v in values.items()}
        
        # Validate updates
        for col_name, new_value in normalized.items():
            col = self.schema.get_column(col_name)
            old_value = row.data.get(col_name)
            
            # Check NOT NULL
            if new_value is None and col.not_null:
                raise NotNullViolation(col.name)
            
            # Validate and coerce type
            if new_value is not None:
                new_value = validate_and_coerce(new_value, col.data_type, col.name)
                normalized[col_name] = new_value
            
            # Check UNIQUE constraint
            if col.unique and new_value is not None and new_value != old_value:
                if new_value in self._unique_values[col_name]:
                    if col.primary_key:
                        raise PrimaryKeyViolation(col.name, new_value)
                    else:
                        raise UniqueViolation(col.name, new_value)
        
        # Apply updates
        for col_name, new_value in normalized.items():
            col = self.schema.get_column(col_name)
            old_value = row.data.get(col_name)
            
            # Update unique value tracking
            if col.unique:
                if old_value is not None:
                    self._unique_values[col_name].discard(old_value)
                if new_value is not None:
                    self._unique_values[col_name].add(new_value)
            
            # Update indexes
            if old_value is not None:
                self._index_manager.delete(col_name, old_value, row_id)
            if new_value is not None:
                self._index_manager.insert(col_name, new_value, row_id)
            
            row.data[col_name] = new_value
        
        return row
    
    def delete(self, row_id: int) -> Optional[Row]:
        """
        Delete a row from the table.
        
        Args:
            row_id: The ID of the row to delete
            
        Returns:
            The deleted Row, or None if row not found
        """
        if row_id not in self._rows:
            return None
        
        row = self._rows.pop(row_id)
        
        # Update unique value tracking
        for col in self.schema.columns:
            if col.unique:
                col_name = col.name.lower()
                value = row.data.get(col_name)
                if value is not None:
                    self._unique_values[col_name].discard(value)
        
        # Update indexes
        for col_name, value in row.data.items():
            if value is not None:
                self._index_manager.delete(col_name, value, row_id)
        
        return row
    
    def get(self, row_id: int) -> Optional[Row]:
        """Get a row by its ID."""
        return self._rows.get(row_id)
    
    def find_by_index(self, column_name: str, value: Any) -> List[Row]:
        """
        Find rows using an index.
        
        Args:
            column_name: The indexed column name
            value: The value to search for
            
        Returns:
            List of matching rows
        """
        row_ids = self._index_manager.search(column_name, value)
        if row_ids is None:
            # No index, fall back to scan
            return [row for row in self._rows.values() 
                    if row.data.get(column_name.lower()) == value]
        return [self._rows[rid] for rid in row_ids if rid in self._rows]
    
    def scan(self) -> Iterator[Row]:
        """Iterate over all rows in the table."""
        return iter(self._rows.values())
    
    def count(self) -> int:
        """Get the number of rows in the table."""
        return len(self._rows)
    
    @property
    def index_manager(self) -> IndexManager:
        """Get the index manager for this table."""
        return self._index_manager
    
    def clear(self) -> None:
        """Remove all rows from the table."""
        self._rows.clear()
        self._next_row_id = 1
        for col_name in self._unique_values:
            self._unique_values[col_name].clear()
        self._index_manager.clear()
        
        # Recreate indexes
        if self.schema.primary_key:
            self._index_manager.create_index(self.schema.primary_key.name)
        for col in self.schema.columns:
            if col.unique and not col.primary_key:
                self._index_manager.create_index(col.name)


class Database:
    """
    The main database class that manages tables.
    """
    
    def __init__(self):
        from schema import Catalog
        self.catalog = Catalog()
        self._tables: Dict[str, Table] = {}
    
    def create_table(self, schema: TableSchema) -> Table:
        """Create a new table."""
        self.catalog.create_table(schema)
        table = Table(schema)
        self._tables[schema.name.lower()] = table
        return table
    
    def drop_table(self, name: str) -> None:
        """Drop a table."""
        self.catalog.drop_table(name)
        del self._tables[name.lower()]
    
    def get_table(self, name: str) -> Table:
        """Get a table by name."""
        self.catalog.get_table(name)  # Check existence
        return self._tables[name.lower()]
    
    def has_table(self, name: str) -> bool:
        """Check if a table exists."""
        return self.catalog.has_table(name)
    
    def list_tables(self) -> List[str]:
        """List all table names."""
        return self.catalog.list_tables()
    
    def get_schema(self, name: str) -> TableSchema:
        """Get the schema for a table."""
        return self.catalog.get_table(name)
    
    def clear(self) -> None:
        """Remove all tables from the database."""
        self.catalog.clear()
        self._tables.clear()
