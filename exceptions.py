"""
Custom exceptions for the RDBMS.
"""


class RDBMSError(Exception):
    """Base exception for all RDBMS errors."""
    pass


class SQLSyntaxError(RDBMSError):
    """Raised when SQL syntax is invalid."""
    
    def __init__(self, message: str, line: int = None, column: int = None):
        self.line = line
        self.column = column
        if line is not None and column is not None:
            message = f"Syntax error at line {line}, column {column}: {message}"
        super().__init__(message)


class SemanticError(RDBMSError):
    """Raised when SQL is syntactically valid but semantically invalid."""
    pass


class TableNotFoundError(SemanticError):
    """Raised when referencing a non-existent table."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        super().__init__(f"Table '{table_name}' does not exist")


class TableExistsError(SemanticError):
    """Raised when creating a table that already exists."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        super().__init__(f"Table '{table_name}' already exists")


class ColumnNotFoundError(SemanticError):
    """Raised when referencing a non-existent column."""
    
    def __init__(self, column_name: str, table_name: str = None):
        self.column_name = column_name
        self.table_name = table_name
        if table_name:
            msg = f"Column '{column_name}' does not exist in table '{table_name}'"
        else:
            msg = f"Column '{column_name}' does not exist"
        super().__init__(msg)


class AmbiguousColumnError(SemanticError):
    """Raised when a column reference is ambiguous in a JOIN."""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
        super().__init__(f"Ambiguous column reference: '{column_name}'")


class ConstraintError(RDBMSError):
    """Base class for constraint violations."""
    pass


class PrimaryKeyViolation(ConstraintError):
    """Raised when a PRIMARY KEY constraint is violated."""
    
    def __init__(self, column_name: str, value):
        self.column_name = column_name
        self.value = value
        super().__init__(f"PRIMARY KEY violation: duplicate value '{value}' for column '{column_name}'")


class UniqueViolation(ConstraintError):
    """Raised when a UNIQUE constraint is violated."""
    
    def __init__(self, column_name: str, value):
        self.column_name = column_name
        self.value = value
        super().__init__(f"UNIQUE constraint violation: duplicate value '{value}' for column '{column_name}'")


class NotNullViolation(ConstraintError):
    """Raised when a NOT NULL constraint is violated."""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
        super().__init__(f"NOT NULL constraint violation: column '{column_name}' cannot be NULL")


class DataTypeError(RDBMSError):
    """Raised when there's a data type mismatch."""
    
    def __init__(self, expected_type: str, actual_value, column_name: str = None):
        self.expected_type = expected_type
        self.actual_value = actual_value
        self.column_name = column_name
        if column_name:
            msg = f"Type error for column '{column_name}': expected {expected_type}, got {type(actual_value).__name__}"
        else:
            msg = f"Type error: expected {expected_type}, got {type(actual_value).__name__}"
        super().__init__(msg)
