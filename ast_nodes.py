"""
Abstract Syntax Tree node definitions for SQL statements.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple
from enum import Enum, auto


class JoinType(Enum):
    """Types of JOIN operations."""
    INNER = auto()
    LEFT = auto()
    RIGHT = auto()
    CROSS = auto()


class OrderDirection(Enum):
    """Ordering direction for ORDER BY."""
    ASC = auto()
    DESC = auto()


class BinaryOp(Enum):
    """Binary operators for expressions."""
    EQ = '='
    NE = '<>'
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    AND = 'AND'
    OR = 'OR'
    LIKE = 'LIKE'


class UnaryOp(Enum):
    """Unary operators for expressions."""
    NOT = 'NOT'
    IS_NULL = 'IS NULL'
    IS_NOT_NULL = 'IS NOT NULL'


# ============================================================================
# Expression Nodes
# ============================================================================

@dataclass
class Expression:
    """Base class for all expressions."""
    pass


@dataclass
class Literal(Expression):
    """A literal value (number, string, boolean, null)."""
    value: Any
    
    def __repr__(self):
        if isinstance(self.value, str):
            return f"'{self.value}'"
        return str(self.value)


@dataclass
class ColumnRef(Expression):
    """A reference to a column, optionally with table qualifier."""
    column: str
    table: Optional[str] = None
    
    def __repr__(self):
        if self.table:
            return f"{self.table}.{self.column}"
        return self.column
    
    @property
    def qualified_name(self) -> str:
        if self.table:
            return f"{self.table}.{self.column}"
        return self.column


@dataclass
class BinaryExpr(Expression):
    """Binary expression (left op right)."""
    left: Expression
    op: BinaryOp
    right: Expression
    
    def __repr__(self):
        return f"({self.left} {self.op.value} {self.right})"


@dataclass
class UnaryExpr(Expression):
    """Unary expression (op operand)."""
    op: UnaryOp
    operand: Expression
    
    def __repr__(self):
        return f"({self.op.value} {self.operand})"


@dataclass
class StarExpr(Expression):
    """Represents SELECT * or table.*"""
    table: Optional[str] = None
    
    def __repr__(self):
        if self.table:
            return f"{self.table}.*"
        return "*"


@dataclass
class FunctionCall(Expression):
    """A function call expression (for future extension)."""
    name: str
    args: List[Expression] = field(default_factory=list)
    
    def __repr__(self):
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"{self.name}({args_str})"


# ============================================================================
# Column Definition (for CREATE TABLE)
# ============================================================================

@dataclass
class ColumnDef:
    """Column definition in CREATE TABLE."""
    name: str
    data_type: str
    primary_key: bool = False
    unique: bool = False
    not_null: bool = False
    
    def __repr__(self):
        parts = [self.name, self.data_type]
        if self.primary_key:
            parts.append('PRIMARY KEY')
        if self.unique and not self.primary_key:
            parts.append('UNIQUE')
        if self.not_null and not self.primary_key:
            parts.append('NOT NULL')
        return ' '.join(parts)


# ============================================================================
# Table References (for FROM clause)
# ============================================================================

@dataclass
class TableRef:
    """A reference to a table, optionally with alias."""
    name: str
    alias: Optional[str] = None
    
    @property
    def effective_name(self) -> str:
        return self.alias or self.name
    
    def __repr__(self):
        if self.alias:
            return f"{self.name} AS {self.alias}"
        return self.name


@dataclass
class JoinClause:
    """A JOIN clause."""
    join_type: JoinType
    table: TableRef
    condition: Optional[Expression] = None
    
    def __repr__(self):
        result = f"{self.join_type.name} JOIN {self.table}"
        if self.condition:
            result += f" ON {self.condition}"
        return result


@dataclass
class FromClause:
    """Complete FROM clause with base table and optional joins."""
    table: TableRef
    joins: List[JoinClause] = field(default_factory=list)
    
    def __repr__(self):
        result = str(self.table)
        for join in self.joins:
            result += f" {join}"
        return result


# ============================================================================
# Order By
# ============================================================================

@dataclass
class OrderByItem:
    """An item in ORDER BY clause."""
    column: ColumnRef
    direction: OrderDirection = OrderDirection.ASC
    
    def __repr__(self):
        return f"{self.column} {self.direction.name}"


# ============================================================================
# Statement Nodes
# ============================================================================

@dataclass
class Statement:
    """Base class for all SQL statements."""
    pass


@dataclass
class CreateTableStmt(Statement):
    """CREATE TABLE statement."""
    table_name: str
    columns: List[ColumnDef]
    if_not_exists: bool = False
    
    def __repr__(self):
        cols = ', '.join(str(col) for col in self.columns)
        exists = "IF NOT EXISTS " if self.if_not_exists else ""
        return f"CREATE TABLE {exists}{self.table_name} ({cols})"


@dataclass
class DropTableStmt(Statement):
    """DROP TABLE statement."""
    table_name: str
    if_exists: bool = False
    
    def __repr__(self):
        exists = "IF EXISTS " if self.if_exists else ""
        return f"DROP TABLE {exists}{self.table_name}"


@dataclass
class InsertStmt(Statement):
    """INSERT INTO statement."""
    table_name: str
    columns: Optional[List[str]]  # None means all columns in order
    values: List[List[Expression]]  # Multiple rows can be inserted
    
    def __repr__(self):
        cols = f"({', '.join(self.columns)})" if self.columns else ""
        vals = ', '.join(
            '(' + ', '.join(str(v) for v in row) + ')'
            for row in self.values
        )
        return f"INSERT INTO {self.table_name} {cols} VALUES {vals}"


@dataclass
class SelectStmt(Statement):
    """SELECT statement."""
    columns: List[Expression]  # Can include StarExpr
    from_clause: Optional[FromClause] = None
    where: Optional[Expression] = None
    order_by: List[OrderByItem] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def __repr__(self):
        cols = ', '.join(str(col) for col in self.columns)
        result = f"SELECT {cols}"
        if self.from_clause:
            result += f" FROM {self.from_clause}"
        if self.where:
            result += f" WHERE {self.where}"
        if self.order_by:
            orders = ', '.join(str(o) for o in self.order_by)
            result += f" ORDER BY {orders}"
        if self.limit is not None:
            result += f" LIMIT {self.limit}"
        if self.offset is not None:
            result += f" OFFSET {self.offset}"
        return result


@dataclass
class UpdateStmt(Statement):
    """UPDATE statement."""
    table_name: str
    assignments: List[Tuple[str, Expression]]  # (column_name, value)
    where: Optional[Expression] = None
    
    def __repr__(self):
        sets = ', '.join(f"{col} = {val}" for col, val in self.assignments)
        result = f"UPDATE {self.table_name} SET {sets}"
        if self.where:
            result += f" WHERE {self.where}"
        return result


@dataclass
class DeleteStmt(Statement):
    """DELETE FROM statement."""
    table_name: str
    where: Optional[Expression] = None
    
    def __repr__(self):
        result = f"DELETE FROM {self.table_name}"
        if self.where:
            result += f" WHERE {self.where}"
        return result
