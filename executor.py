"""
Query Executor - executes parsed SQL statements.
"""

from typing import Any, Dict, List, Optional, Tuple, Iterator
from dataclasses import dataclass

from ast_nodes import (
    Statement, Expression, Literal, ColumnRef, BinaryExpr, UnaryExpr, StarExpr,
    ColumnDef, TableRef, JoinClause, FromClause, OrderByItem,
    CreateTableStmt, DropTableStmt, InsertStmt, SelectStmt, UpdateStmt, DeleteStmt,
    JoinType, OrderDirection, BinaryOp, UnaryOp,
)
from schema import TableSchema, Column, Catalog
from datatypes import DataType, compare_values
from storage import Database, Table, Row
from exceptions import (
    RDBMSError, SemanticError, ColumnNotFoundError, AmbiguousColumnError,
    TableNotFoundError,
)
import re


@dataclass
class QueryResult:
    """Result of executing a query."""
    columns: List[str]
    rows: List[Dict[str, Any]]
    affected_rows: int = 0
    message: str = ""
    
    def __bool__(self):
        return True
    
    def __len__(self):
        return len(self.rows)


class ExecutionContext:
    """Context for query execution, tracking table aliases and columns."""
    
    def __init__(self, db: Database):
        self.db = db
        self.table_aliases: Dict[str, str] = {}  # alias -> table_name
        self.tables: Dict[str, Table] = {}  # alias/name -> Table
    
    def add_table(self, table_ref: TableRef) -> Table:
        """Add a table to the context."""
        table = self.db.get_table(table_ref.name)
        effective_name = table_ref.effective_name.lower()
        self.tables[effective_name] = table
        if table_ref.alias:
            self.table_aliases[table_ref.alias.lower()] = table_ref.name.lower()
        return table
    
    def get_table(self, name: str) -> Table:
        """Get a table by name or alias."""
        lower = name.lower()
        if lower in self.tables:
            return self.tables[lower]
        raise TableNotFoundError(name)
    
    def resolve_column(self, col_ref: ColumnRef, row_data: Dict[str, Any]) -> Any:
        """
        Resolve a column reference to its value.
        Row data should be prefixed with table names/aliases.
        """
        col_name = col_ref.column.lower()
        
        if col_ref.table:
            # Qualified reference
            key = f"{col_ref.table.lower()}.{col_name}"
            if key in row_data:
                return row_data[key]
            raise ColumnNotFoundError(col_ref.column, col_ref.table)
        
        # Unqualified - search all tables
        matches = []
        for prefix in self.tables.keys():
            key = f"{prefix}.{col_name}"
            if key in row_data:
                matches.append(key)
        
        if len(matches) == 0:
            raise ColumnNotFoundError(col_ref.column)
        if len(matches) > 1:
            raise AmbiguousColumnError(col_ref.column)
        
        return row_data[matches[0]]


class Executor:
    """
    Executes SQL statements against a database.
    """
    
    def __init__(self, db: Database = None):
        self.db = db or Database()
    
    def execute(self, stmt: Statement) -> QueryResult:
        """Execute a SQL statement and return the result."""
        if isinstance(stmt, CreateTableStmt):
            return self.execute_create_table(stmt)
        elif isinstance(stmt, DropTableStmt):
            return self.execute_drop_table(stmt)
        elif isinstance(stmt, InsertStmt):
            return self.execute_insert(stmt)
        elif isinstance(stmt, SelectStmt):
            return self.execute_select(stmt)
        elif isinstance(stmt, UpdateStmt):
            return self.execute_update(stmt)
        elif isinstance(stmt, DeleteStmt):
            return self.execute_delete(stmt)
        else:
            raise RDBMSError(f"Unknown statement type: {type(stmt).__name__}")
    
    # ========================================================================
    # CREATE TABLE
    # ========================================================================
    
    def execute_create_table(self, stmt: CreateTableStmt) -> QueryResult:
        """Execute CREATE TABLE statement."""
        # Check if table exists
        if stmt.if_not_exists and self.db.has_table(stmt.table_name):
            return QueryResult(
                columns=[], rows=[], affected_rows=0,
                message=f"Table '{stmt.table_name}' already exists"
            )
        
        # Convert column definitions
        columns = []
        for col_def in stmt.columns:
            data_type = DataType.from_string(col_def.data_type)
            columns.append(Column(
                name=col_def.name,
                data_type=data_type,
                primary_key=col_def.primary_key,
                unique=col_def.unique,
                not_null=col_def.not_null
            ))
        
        schema = TableSchema(name=stmt.table_name, columns=columns)
        self.db.create_table(schema)
        
        return QueryResult(
            columns=[], rows=[], affected_rows=0,
            message=f"Table '{stmt.table_name}' created"
        )
    
    # ========================================================================
    # DROP TABLE
    # ========================================================================
    
    def execute_drop_table(self, stmt: DropTableStmt) -> QueryResult:
        """Execute DROP TABLE statement."""
        if stmt.if_exists and not self.db.has_table(stmt.table_name):
            return QueryResult(
                columns=[], rows=[], affected_rows=0,
                message=f"Table '{stmt.table_name}' does not exist"
            )
        
        self.db.drop_table(stmt.table_name)
        
        return QueryResult(
            columns=[], rows=[], affected_rows=0,
            message=f"Table '{stmt.table_name}' dropped"
        )
    
    # ========================================================================
    # INSERT
    # ========================================================================
    
    def execute_insert(self, stmt: InsertStmt) -> QueryResult:
        """Execute INSERT statement."""
        table = self.db.get_table(stmt.table_name)
        schema = table.schema
        
        inserted_count = 0
        for value_list in stmt.values:
            # Determine columns
            if stmt.columns:
                columns = stmt.columns
            else:
                columns = schema.column_names
            
            if len(value_list) != len(columns):
                raise SemanticError(
                    f"Column count ({len(columns)}) doesn't match value count ({len(value_list)})"
                )
            
            # Evaluate values
            row_data = {}
            for col_name, expr in zip(columns, value_list):
                value = self.evaluate_expr(expr, {})
                row_data[col_name] = value
            
            table.insert(row_data)
            inserted_count += 1
        
        return QueryResult(
            columns=[], rows=[], affected_rows=inserted_count,
            message=f"Inserted {inserted_count} row(s)"
        )
    
    # ========================================================================
    # SELECT
    # ========================================================================
    
    def execute_select(self, stmt: SelectStmt) -> QueryResult:
        """Execute SELECT statement."""
        ctx = ExecutionContext(self.db)
        
        # Handle simple SELECT without FROM
        if stmt.from_clause is None:
            # SELECT expression (e.g., SELECT 1+1)
            row = {}
            columns = []
            for i, expr in enumerate(stmt.columns):
                value = self.evaluate_expr(expr, row)
                col_name = str(expr)
                columns.append(col_name)
                row[col_name] = value
            return QueryResult(columns=columns, rows=[row])
        
        # Add base table
        base_table = ctx.add_table(stmt.from_clause.table)
        
        # Get all rows from base table
        rows = self._table_to_rows(base_table, stmt.from_clause.table.effective_name)
        
        # Process JOINs
        for join in stmt.from_clause.joins:
            join_table = ctx.add_table(join.table)
            rows = self._execute_join(rows, join_table, join, ctx)
        
        # Apply WHERE clause
        if stmt.where:
            rows = [r for r in rows if self._evaluate_where(stmt.where, r, ctx)]
        
        # Apply ORDER BY
        if stmt.order_by:
            rows = self._apply_order_by(rows, stmt.order_by, ctx)
        
        # Apply OFFSET
        if stmt.offset:
            rows = rows[stmt.offset:]
        
        # Apply LIMIT
        if stmt.limit is not None:
            rows = rows[:stmt.limit]
        
        # Project columns
        result_columns, result_rows = self._project_columns(
            stmt.columns, rows, ctx
        )
        
        return QueryResult(columns=result_columns, rows=result_rows)
    
    def _table_to_rows(self, table: Table, prefix: str) -> List[Dict[str, Any]]:
        """Convert table rows to prefixed dictionaries."""
        result = []
        prefix = prefix.lower()
        for row in table.scan():
            prefixed = {f"{prefix}.{k}": v for k, v in row.data.items()}
            prefixed['_row_ids'] = {prefix: row.row_id}
            result.append(prefixed)
        return result
    
    def _execute_join(self, left_rows: List[Dict[str, Any]], 
                      right_table: Table, join: JoinClause,
                      ctx: ExecutionContext) -> List[Dict[str, Any]]:
        """Execute a JOIN operation."""
        right_prefix = join.table.effective_name.lower()
        right_rows = self._table_to_rows(right_table, right_prefix)
        
        result = []
        
        if join.join_type == JoinType.CROSS:
            # Cross join - cartesian product
            for left in left_rows:
                for right in right_rows:
                    result.append(self._merge_rows(left, right))
            return result
        
        # For LEFT/INNER joins, track which left rows matched
        for left in left_rows:
            matched = False
            for right in right_rows:
                merged = self._merge_rows(left, right)
                if join.condition is None or self._evaluate_where(join.condition, merged, ctx):
                    result.append(merged)
                    matched = True
            
            # LEFT JOIN: include unmatched left rows with NULL right side
            if not matched and join.join_type == JoinType.LEFT:
                null_right = {f"{right_prefix}.{col.name.lower()}": None 
                             for col in right_table.schema.columns}
                null_right['_row_ids'] = {}
                result.append(self._merge_rows(left, null_right))
        
        # RIGHT JOIN: include unmatched right rows with NULL left side
        if join.join_type == JoinType.RIGHT:
            # Get all left table prefixes
            left_prefixes = set()
            for key in left_rows[0].keys() if left_rows else []:
                if '.' in key and not key.startswith('_'):
                    left_prefixes.add(key.split('.')[0])
            
            for right in right_rows:
                matched = False
                for left in left_rows:
                    merged = self._merge_rows(left, right)
                    if join.condition is None or self._evaluate_where(join.condition, merged, ctx):
                        matched = True
                        break
                
                if not matched:
                    null_left = {}
                    for prefix in left_prefixes:
                        for key in left_rows[0].keys() if left_rows else []:
                            if key.startswith(f"{prefix}."):
                                null_left[key] = None
                    null_left['_row_ids'] = {}
                    result.append(self._merge_rows(null_left, right))
        
        return result
    
    def _merge_rows(self, left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two rows."""
        result = dict(left)
        for k, v in right.items():
            if k == '_row_ids':
                result['_row_ids'] = {**result.get('_row_ids', {}), **v}
            else:
                result[k] = v
        return result
    
    def _evaluate_where(self, expr: Expression, row: Dict[str, Any],
                        ctx: ExecutionContext) -> bool:
        """Evaluate a WHERE expression."""
        result = self.evaluate_expr(expr, row, ctx)
        if result is None:
            return False
        return bool(result)
    
    def _apply_order_by(self, rows: List[Dict[str, Any]], 
                        order_by: List[OrderByItem],
                        ctx: ExecutionContext) -> List[Dict[str, Any]]:
        """Apply ORDER BY to rows."""
        def sort_key(row):
            key = []
            for item in order_by:
                value = ctx.resolve_column(item.column, row)
                # Handle NULL - put NULLs last for ASC, first for DESC
                if value is None:
                    if item.direction == OrderDirection.ASC:
                        key.append((1, None))
                    else:
                        key.append((0, None))
                else:
                    if item.direction == OrderDirection.ASC:
                        key.append((0, value))
                    else:
                        # Negate for DESC (works for numbers, need special handling for strings)
                        key.append((1, value))
            return key
        
        # Custom comparison for mixed types
        def compare_keys(a, b):
            for i in range(len(a)):
                a_null_order, a_val = a[i]
                b_null_order, b_val = b[i]
                
                if a_null_order != b_null_order:
                    return a_null_order - b_null_order
                
                if a_val is None and b_val is None:
                    continue
                
                direction = order_by[i].direction
                cmp = compare_values(a_val, b_val)
                if cmp != 0:
                    return cmp if direction == OrderDirection.ASC else -cmp
            return 0
        
        from functools import cmp_to_key
        return sorted(rows, key=cmp_to_key(lambda a, b: compare_keys(sort_key(a), sort_key(b))))
    
    def _project_columns(self, columns: List[Expression], 
                         rows: List[Dict[str, Any]],
                         ctx: ExecutionContext) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Project selected columns from rows."""
        result_columns = []
        
        # First, expand star expressions to get column list
        for expr in columns:
            if isinstance(expr, StarExpr):
                if expr.table:
                    # table.*
                    table = ctx.get_table(expr.table)
                    for col in table.schema.columns:
                        result_columns.append(f"{expr.table}.{col.name}")
                else:
                    # * - all columns from all tables
                    for table_name, table in ctx.tables.items():
                        for col in table.schema.columns:
                            result_columns.append(f"{table_name}.{col.name}")
            elif isinstance(expr, ColumnRef):
                result_columns.append(str(expr))
            else:
                result_columns.append(str(expr))
        
        # Project rows
        result_rows = []
        for row in rows:
            projected = {}
            for i, expr in enumerate(columns):
                if isinstance(expr, StarExpr):
                    if expr.table:
                        table = ctx.get_table(expr.table)
                        for col in table.schema.columns:
                            col_name = f"{expr.table}.{col.name}"
                            key = f"{expr.table.lower()}.{col.name.lower()}"
                            projected[col_name] = row.get(key)
                    else:
                        for table_name, table in ctx.tables.items():
                            for col in table.schema.columns:
                                col_name = f"{table_name}.{col.name}"
                                key = f"{table_name.lower()}.{col.name.lower()}"
                                projected[col_name] = row.get(key)
                else:
                    col_name = result_columns[i] if i < len(result_columns) else str(expr)
                    projected[col_name] = self.evaluate_expr(expr, row, ctx)
            result_rows.append(projected)
        
        return result_columns, result_rows
    
    # ========================================================================
    # UPDATE
    # ========================================================================
    
    def execute_update(self, stmt: UpdateStmt) -> QueryResult:
        """Execute UPDATE statement."""
        table = self.db.get_table(stmt.table_name)
        prefix = stmt.table_name.lower()
        
        ctx = ExecutionContext(self.db)
        ctx.tables[prefix] = table
        
        updated_count = 0
        for row in list(table.scan()):
            # Create prefixed row for WHERE evaluation
            prefixed = {f"{prefix}.{k}": v for k, v in row.data.items()}
            
            if stmt.where is None or self._evaluate_where(stmt.where, prefixed, ctx):
                # Evaluate new values
                updates = {}
                for col_name, expr in stmt.assignments:
                    updates[col_name] = self.evaluate_expr(expr, prefixed, ctx)
                
                table.update(row.row_id, updates)
                updated_count += 1
        
        return QueryResult(
            columns=[], rows=[], affected_rows=updated_count,
            message=f"Updated {updated_count} row(s)"
        )
    
    # ========================================================================
    # DELETE
    # ========================================================================
    
    def execute_delete(self, stmt: DeleteStmt) -> QueryResult:
        """Execute DELETE statement."""
        table = self.db.get_table(stmt.table_name)
        prefix = stmt.table_name.lower()
        
        ctx = ExecutionContext(self.db)
        ctx.tables[prefix] = table
        
        to_delete = []
        for row in table.scan():
            prefixed = {f"{prefix}.{k}": v for k, v in row.data.items()}
            
            if stmt.where is None or self._evaluate_where(stmt.where, prefixed, ctx):
                to_delete.append(row.row_id)
        
        for row_id in to_delete:
            table.delete(row_id)
        
        return QueryResult(
            columns=[], rows=[], affected_rows=len(to_delete),
            message=f"Deleted {len(to_delete)} row(s)"
        )
    
    # ========================================================================
    # Expression Evaluation
    # ========================================================================
    
    def evaluate_expr(self, expr: Expression, row: Dict[str, Any],
                      ctx: ExecutionContext = None) -> Any:
        """Evaluate an expression in the context of a row."""
        if isinstance(expr, Literal):
            return expr.value
        
        elif isinstance(expr, ColumnRef):
            if ctx:
                return ctx.resolve_column(expr, row)
            else:
                # Simple case - just look up in row
                key = expr.column.lower()
                if key in row:
                    return row[key]
                raise ColumnNotFoundError(expr.column)
        
        elif isinstance(expr, BinaryExpr):
            left = self.evaluate_expr(expr.left, row, ctx)
            right = self.evaluate_expr(expr.right, row, ctx)
            return self._apply_binary_op(expr.op, left, right)
        
        elif isinstance(expr, UnaryExpr):
            operand = self.evaluate_expr(expr.operand, row, ctx)
            return self._apply_unary_op(expr.op, operand)
        
        else:
            raise RDBMSError(f"Cannot evaluate expression: {type(expr).__name__}")
    
    def _apply_binary_op(self, op: BinaryOp, left: Any, right: Any) -> Any:
        """Apply a binary operator."""
        # Handle NULL propagation
        if op not in (BinaryOp.AND, BinaryOp.OR):
            if left is None or right is None:
                return None
        
        if op == BinaryOp.EQ:
            return left == right
        elif op == BinaryOp.NE:
            return left != right
        elif op == BinaryOp.LT:
            return left < right
        elif op == BinaryOp.LE:
            return left <= right
        elif op == BinaryOp.GT:
            return left > right
        elif op == BinaryOp.GE:
            return left >= right
        elif op == BinaryOp.AND:
            # Three-valued logic
            if left is False or right is False:
                return False
            if left is None or right is None:
                return None
            return left and right
        elif op == BinaryOp.OR:
            # Three-valued logic
            if left is True or right is True:
                return True
            if left is None or right is None:
                return None
            return left or right
        elif op == BinaryOp.LIKE:
            # Convert SQL LIKE pattern to regex
            pattern = right.replace('%', '.*').replace('_', '.')
            pattern = f'^{pattern}$'
            return bool(re.match(pattern, str(left), re.IGNORECASE))
        
        raise RDBMSError(f"Unknown binary operator: {op}")
    
    def _apply_unary_op(self, op: UnaryOp, operand: Any) -> Any:
        """Apply a unary operator."""
        if op == UnaryOp.NOT:
            if operand is None:
                return None
            return not operand
        elif op == UnaryOp.IS_NULL:
            return operand is None
        elif op == UnaryOp.IS_NOT_NULL:
            return operand is not None
        
        raise RDBMSError(f"Unknown unary operator: {op}")
