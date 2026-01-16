"""
SQL Parser - converts tokens into an Abstract Syntax Tree.
"""

from typing import List, Optional, Tuple, Any

from lexer import Lexer, Token, TokenType
from ast_nodes import (
    Statement, Expression, Literal, ColumnRef, BinaryExpr, UnaryExpr, StarExpr,
    ColumnDef, TableRef, JoinClause, FromClause, OrderByItem,
    CreateTableStmt, DropTableStmt, InsertStmt, SelectStmt, UpdateStmt, DeleteStmt,
    JoinType, OrderDirection, BinaryOp, UnaryOp,
)
from exceptions import SQLSyntaxError


class Parser:
    """
    Recursive descent parser for SQL.
    """
    
    def __init__(self, text: str):
        self.lexer = Lexer(text)
        self.tokens = self.lexer.tokenize()
        self.pos = 0
    
    @property
    def current(self) -> Token:
        """Get the current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 1) -> Token:
        """Peek at a token ahead."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """Advance to the next token and return current."""
        token = self.current
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current.type in types
    
    def expect(self, token_type: TokenType, message: str = None) -> Token:
        """Expect a specific token type, raise error if not matched."""
        if self.current.type != token_type:
            msg = message or f"Expected {token_type.name}, got {self.current.type.name}"
            raise SQLSyntaxError(msg, self.current.line, self.current.column)
        return self.advance()
    
    def consume_if(self, token_type: TokenType) -> bool:
        """Consume token if it matches, return True if consumed."""
        if self.current.type == token_type:
            self.advance()
            return True
        return False
    
    def parse(self) -> Statement:
        """Parse a single SQL statement."""
        stmt = self.parse_statement()
        
        # Optional semicolon
        self.consume_if(TokenType.SEMICOLON)
        
        return stmt
    
    def parse_statement(self) -> Statement:
        """Parse a statement based on current token."""
        if self.match(TokenType.SELECT):
            return self.parse_select()
        elif self.match(TokenType.INSERT):
            return self.parse_insert()
        elif self.match(TokenType.UPDATE):
            return self.parse_update()
        elif self.match(TokenType.DELETE):
            return self.parse_delete()
        elif self.match(TokenType.CREATE):
            return self.parse_create()
        elif self.match(TokenType.DROP):
            return self.parse_drop()
        else:
            raise SQLSyntaxError(
                f"Unexpected token: {self.current.type.name}",
                self.current.line, self.current.column
            )
    
    # ========================================================================
    # CREATE TABLE
    # ========================================================================
    
    def parse_create(self) -> CreateTableStmt:
        """Parse CREATE TABLE statement."""
        self.expect(TokenType.CREATE)
        self.expect(TokenType.TABLE)
        
        # IF NOT EXISTS
        if_not_exists = False
        if self.match(TokenType.IF):
            self.advance()
            self.expect(TokenType.NOT)
            self.expect(TokenType.EXISTS)
            if_not_exists = True
        
        # Table name
        table_name = self.expect(TokenType.IDENTIFIER).value
        
        # Column definitions
        self.expect(TokenType.LPAREN)
        columns = [self.parse_column_def()]
        
        while self.match(TokenType.COMMA):
            self.advance()
            columns.append(self.parse_column_def())
        
        self.expect(TokenType.RPAREN)
        
        return CreateTableStmt(
            table_name=table_name,
            columns=columns,
            if_not_exists=if_not_exists
        )
    
    def parse_column_def(self) -> ColumnDef:
        """Parse a column definition."""
        name = self.expect(TokenType.IDENTIFIER).value
        
        # Data type
        type_token = self.current
        if type_token.type not in (
            TokenType.INTEGER, TokenType.INT, TokenType.TEXT, TokenType.VARCHAR,
            TokenType.REAL, TokenType.FLOAT, TokenType.BOOLEAN, TokenType.BOOL
        ):
            raise SQLSyntaxError(
                f"Expected data type, got {type_token.type.name}",
                type_token.line, type_token.column
            )
        data_type = self.advance().value.upper()
        
        # Column constraints
        primary_key = False
        unique = False
        not_null = False
        
        while True:
            if self.match(TokenType.PRIMARY):
                self.advance()
                self.expect(TokenType.KEY)
                primary_key = True
            elif self.match(TokenType.UNIQUE):
                self.advance()
                unique = True
            elif self.match(TokenType.NOT):
                self.advance()
                self.expect(TokenType.NULL)
                not_null = True
            else:
                break
        
        return ColumnDef(
            name=name,
            data_type=data_type,
            primary_key=primary_key,
            unique=unique,
            not_null=not_null
        )
    
    # ========================================================================
    # DROP TABLE
    # ========================================================================
    
    def parse_drop(self) -> DropTableStmt:
        """Parse DROP TABLE statement."""
        self.expect(TokenType.DROP)
        self.expect(TokenType.TABLE)
        
        # IF EXISTS
        if_exists = False
        if self.match(TokenType.IF):
            self.advance()
            self.expect(TokenType.EXISTS)
            if_exists = True
        
        table_name = self.expect(TokenType.IDENTIFIER).value
        
        return DropTableStmt(table_name=table_name, if_exists=if_exists)
    
    # ========================================================================
    # INSERT
    # ========================================================================
    
    def parse_insert(self) -> InsertStmt:
        """Parse INSERT INTO statement."""
        self.expect(TokenType.INSERT)
        self.expect(TokenType.INTO)
        
        table_name = self.expect(TokenType.IDENTIFIER).value
        
        # Optional column list
        columns = None
        if self.match(TokenType.LPAREN):
            self.advance()
            columns = [self.expect(TokenType.IDENTIFIER).value]
            while self.match(TokenType.COMMA):
                self.advance()
                columns.append(self.expect(TokenType.IDENTIFIER).value)
            self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.VALUES)
        
        # Value lists
        values = [self.parse_value_list()]
        while self.match(TokenType.COMMA):
            self.advance()
            values.append(self.parse_value_list())
        
        return InsertStmt(table_name=table_name, columns=columns, values=values)
    
    def parse_value_list(self) -> List[Expression]:
        """Parse a parenthesized list of values."""
        self.expect(TokenType.LPAREN)
        values = [self.parse_expression()]
        while self.match(TokenType.COMMA):
            self.advance()
            values.append(self.parse_expression())
        self.expect(TokenType.RPAREN)
        return values
    
    # ========================================================================
    # SELECT
    # ========================================================================
    
    def parse_select(self) -> SelectStmt:
        """Parse SELECT statement."""
        self.expect(TokenType.SELECT)
        
        # Column list
        columns = [self.parse_select_column()]
        while self.match(TokenType.COMMA):
            self.advance()
            columns.append(self.parse_select_column())
        
        # FROM clause
        from_clause = None
        if self.match(TokenType.FROM):
            from_clause = self.parse_from_clause()
        
        # WHERE clause
        where = None
        if self.match(TokenType.WHERE):
            self.advance()
            where = self.parse_expression()
        
        # ORDER BY clause
        order_by = []
        if self.match(TokenType.ORDER):
            self.advance()
            self.expect(TokenType.BY)
            order_by = [self.parse_order_by_item()]
            while self.match(TokenType.COMMA):
                self.advance()
                order_by.append(self.parse_order_by_item())
        
        # LIMIT clause
        limit = None
        if self.match(TokenType.LIMIT):
            self.advance()
            limit = int(self.expect(TokenType.NUMBER).value)
        
        # OFFSET clause
        offset = None
        if self.match(TokenType.OFFSET):
            self.advance()
            offset = int(self.expect(TokenType.NUMBER).value)
        
        return SelectStmt(
            columns=columns,
            from_clause=from_clause,
            where=where,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
    
    def parse_select_column(self) -> Expression:
        """Parse a column in SELECT list (can be *, table.*, or expression)."""
        if self.match(TokenType.STAR):
            self.advance()
            return StarExpr()
        
        # Could be table.* or table.column or just column
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value
            if self.match(TokenType.DOT):
                self.advance()
                if self.match(TokenType.STAR):
                    self.advance()
                    return StarExpr(table=name)
                else:
                    col_name = self.expect(TokenType.IDENTIFIER).value
                    return ColumnRef(column=col_name, table=name)
            return ColumnRef(column=name)
        
        return self.parse_expression()
    
    def parse_from_clause(self) -> FromClause:
        """Parse FROM clause with optional JOINs."""
        self.expect(TokenType.FROM)
        
        # Base table
        table = self.parse_table_ref()
        
        # JOINs
        joins = []
        while self.match(TokenType.JOIN, TokenType.INNER, TokenType.LEFT, 
                         TokenType.RIGHT, TokenType.CROSS):
            joins.append(self.parse_join())
        
        return FromClause(table=table, joins=joins)
    
    def parse_table_ref(self) -> TableRef:
        """Parse a table reference with optional alias."""
        name = self.expect(TokenType.IDENTIFIER).value
        
        alias = None
        if self.match(TokenType.AS):
            self.advance()
            alias = self.expect(TokenType.IDENTIFIER).value
        elif self.match(TokenType.IDENTIFIER):
            # Alias without AS
            alias = self.advance().value
        
        return TableRef(name=name, alias=alias)
    
    def parse_join(self) -> JoinClause:
        """Parse a JOIN clause."""
        # Determine join type
        join_type = JoinType.INNER
        
        if self.match(TokenType.LEFT):
            self.advance()
            join_type = JoinType.LEFT
        elif self.match(TokenType.RIGHT):
            self.advance()
            join_type = JoinType.RIGHT
        elif self.match(TokenType.CROSS):
            self.advance()
            join_type = JoinType.CROSS
        elif self.match(TokenType.INNER):
            self.advance()
        
        self.expect(TokenType.JOIN)
        
        table = self.parse_table_ref()
        
        # ON clause (not required for CROSS JOIN)
        condition = None
        if self.match(TokenType.ON):
            self.advance()
            condition = self.parse_expression()
        
        return JoinClause(join_type=join_type, table=table, condition=condition)
    
    def parse_order_by_item(self) -> OrderByItem:
        """Parse an ORDER BY item."""
        column = self.parse_column_ref()
        
        direction = OrderDirection.ASC
        if self.match(TokenType.ASC):
            self.advance()
        elif self.match(TokenType.DESC):
            self.advance()
            direction = OrderDirection.DESC
        
        return OrderByItem(column=column, direction=direction)
    
    def parse_column_ref(self) -> ColumnRef:
        """Parse a column reference."""
        name = self.expect(TokenType.IDENTIFIER).value
        
        if self.match(TokenType.DOT):
            self.advance()
            col_name = self.expect(TokenType.IDENTIFIER).value
            return ColumnRef(column=col_name, table=name)
        
        return ColumnRef(column=name)
    
    # ========================================================================
    # UPDATE
    # ========================================================================
    
    def parse_update(self) -> UpdateStmt:
        """Parse UPDATE statement."""
        self.expect(TokenType.UPDATE)
        
        table_name = self.expect(TokenType.IDENTIFIER).value
        
        self.expect(TokenType.SET)
        
        # Assignments
        assignments = [self.parse_assignment()]
        while self.match(TokenType.COMMA):
            self.advance()
            assignments.append(self.parse_assignment())
        
        # WHERE clause
        where = None
        if self.match(TokenType.WHERE):
            self.advance()
            where = self.parse_expression()
        
        return UpdateStmt(
            table_name=table_name,
            assignments=assignments,
            where=where
        )
    
    def parse_assignment(self) -> Tuple[str, Expression]:
        """Parse a column = value assignment."""
        column = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.EQ)
        value = self.parse_expression()
        return (column, value)
    
    # ========================================================================
    # DELETE
    # ========================================================================
    
    def parse_delete(self) -> DeleteStmt:
        """Parse DELETE FROM statement."""
        self.expect(TokenType.DELETE)
        self.expect(TokenType.FROM)
        
        table_name = self.expect(TokenType.IDENTIFIER).value
        
        # WHERE clause
        where = None
        if self.match(TokenType.WHERE):
            self.advance()
            where = self.parse_expression()
        
        return DeleteStmt(table_name=table_name, where=where)
    
    # ========================================================================
    # Expressions
    # ========================================================================
    
    def parse_expression(self) -> Expression:
        """Parse an expression (entry point)."""
        return self.parse_or_expr()
    
    def parse_or_expr(self) -> Expression:
        """Parse OR expression."""
        left = self.parse_and_expr()
        
        while self.match(TokenType.OR):
            self.advance()
            right = self.parse_and_expr()
            left = BinaryExpr(left=left, op=BinaryOp.OR, right=right)
        
        return left
    
    def parse_and_expr(self) -> Expression:
        """Parse AND expression."""
        left = self.parse_not_expr()
        
        while self.match(TokenType.AND):
            self.advance()
            right = self.parse_not_expr()
            left = BinaryExpr(left=left, op=BinaryOp.AND, right=right)
        
        return left
    
    def parse_not_expr(self) -> Expression:
        """Parse NOT expression."""
        if self.match(TokenType.NOT):
            self.advance()
            operand = self.parse_not_expr()
            return UnaryExpr(op=UnaryOp.NOT, operand=operand)
        
        return self.parse_comparison()
    
    def parse_comparison(self) -> Expression:
        """Parse comparison expression."""
        left = self.parse_primary()
        
        # IS NULL / IS NOT NULL
        if self.match(TokenType.IS):
            self.advance()
            if self.match(TokenType.NOT):
                self.advance()
                self.expect(TokenType.NULL)
                return UnaryExpr(op=UnaryOp.IS_NOT_NULL, operand=left)
            else:
                self.expect(TokenType.NULL)
                return UnaryExpr(op=UnaryOp.IS_NULL, operand=left)
        
        # Comparison operators
        op_map = {
            TokenType.EQ: BinaryOp.EQ,
            TokenType.NE: BinaryOp.NE,
            TokenType.LT: BinaryOp.LT,
            TokenType.LE: BinaryOp.LE,
            TokenType.GT: BinaryOp.GT,
            TokenType.GE: BinaryOp.GE,
            TokenType.LIKE: BinaryOp.LIKE,
        }
        
        if self.current.type in op_map:
            op = op_map[self.advance().type]
            right = self.parse_primary()
            return BinaryExpr(left=left, op=op, right=right)
        
        return left
    
    def parse_primary(self) -> Expression:
        """Parse a primary expression (literal, column ref, or parenthesized)."""
        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        # NULL literal
        if self.match(TokenType.NULL):
            self.advance()
            return Literal(value=None)
        
        # Boolean literals
        if self.match(TokenType.TRUE):
            self.advance()
            return Literal(value=True)
        if self.match(TokenType.FALSE):
            self.advance()
            return Literal(value=False)
        
        # Number literal
        if self.match(TokenType.NUMBER):
            return Literal(value=self.advance().value)
        
        # String literal
        if self.match(TokenType.STRING):
            return Literal(value=self.advance().value)
        
        # Column reference (possibly qualified)
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value
            if self.match(TokenType.DOT):
                self.advance()
                col_name = self.expect(TokenType.IDENTIFIER).value
                return ColumnRef(column=col_name, table=name)
            return ColumnRef(column=name)
        
        raise SQLSyntaxError(
            f"Unexpected token: {self.current.type.name}",
            self.current.line, self.current.column
        )


def parse(sql: str) -> Statement:
    """Convenience function to parse a SQL statement."""
    parser = Parser(sql)
    return parser.parse()
