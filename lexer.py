"""
SQL Lexer/Tokenizer.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Iterator
import re


class TokenType(Enum):
    """Types of tokens in SQL."""
    # Keywords
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()
    CREATE = auto()
    DROP = auto()
    TABLE = auto()
    IF = auto()
    EXISTS = auto()
    NOT = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    JOIN = auto()
    INNER = auto()
    LEFT = auto()
    RIGHT = auto()
    CROSS = auto()
    ON = auto()
    AS = auto()
    ORDER = auto()
    BY = auto()
    ASC = auto()
    DESC = auto()
    LIMIT = auto()
    OFFSET = auto()
    PRIMARY = auto()
    KEY = auto()
    UNIQUE = auto()
    IS = auto()
    LIKE = auto()
    TRUE = auto()
    FALSE = auto()
    
    # Data types
    INTEGER = auto()
    INT = auto()
    TEXT = auto()
    VARCHAR = auto()
    REAL = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    BOOL = auto()
    
    # Literals
    NUMBER = auto()
    STRING = auto()
    
    # Identifiers
    IDENTIFIER = auto()
    
    # Operators
    EQ = auto()        # =
    NE = auto()        # <> or !=
    LT = auto()        # <
    LE = auto()        # <=
    GT = auto()        # >
    GE = auto()        # >=
    STAR = auto()      # *
    PLUS = auto()      # +
    MINUS = auto()     # -
    SLASH = auto()     # /
    DOT = auto()       # .
    
    # Punctuation
    LPAREN = auto()    # (
    RPAREN = auto()    # )
    COMMA = auto()     # ,
    SEMICOLON = auto() # ;
    
    # Special
    EOF = auto()
    NEWLINE = auto()


# Keyword map
KEYWORDS = {
    'SELECT': TokenType.SELECT,
    'FROM': TokenType.FROM,
    'WHERE': TokenType.WHERE,
    'INSERT': TokenType.INSERT,
    'INTO': TokenType.INTO,
    'VALUES': TokenType.VALUES,
    'UPDATE': TokenType.UPDATE,
    'SET': TokenType.SET,
    'DELETE': TokenType.DELETE,
    'CREATE': TokenType.CREATE,
    'DROP': TokenType.DROP,
    'TABLE': TokenType.TABLE,
    'IF': TokenType.IF,
    'EXISTS': TokenType.EXISTS,
    'NOT': TokenType.NOT,
    'NULL': TokenType.NULL,
    'AND': TokenType.AND,
    'OR': TokenType.OR,
    'JOIN': TokenType.JOIN,
    'INNER': TokenType.INNER,
    'LEFT': TokenType.LEFT,
    'RIGHT': TokenType.RIGHT,
    'CROSS': TokenType.CROSS,
    'ON': TokenType.ON,
    'AS': TokenType.AS,
    'ORDER': TokenType.ORDER,
    'BY': TokenType.BY,
    'ASC': TokenType.ASC,
    'DESC': TokenType.DESC,
    'LIMIT': TokenType.LIMIT,
    'OFFSET': TokenType.OFFSET,
    'PRIMARY': TokenType.PRIMARY,
    'KEY': TokenType.KEY,
    'UNIQUE': TokenType.UNIQUE,
    'IS': TokenType.IS,
    'LIKE': TokenType.LIKE,
    'TRUE': TokenType.TRUE,
    'FALSE': TokenType.FALSE,
    'INTEGER': TokenType.INTEGER,
    'INT': TokenType.INT,
    'TEXT': TokenType.TEXT,
    'VARCHAR': TokenType.VARCHAR,
    'REAL': TokenType.REAL,
    'FLOAT': TokenType.FLOAT,
    'BOOLEAN': TokenType.BOOLEAN,
    'BOOL': TokenType.BOOL,
}


@dataclass
class Token:
    """Represents a lexical token."""
    type: TokenType
    value: any
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class Lexer:
    """
    SQL Lexer - converts input text into a stream of tokens.
    """
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self._tokens: Optional[List[Token]] = None
    
    @property
    def current_char(self) -> Optional[str]:
        """Get the current character, or None if at end."""
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]
    
    def peek(self, offset: int = 1) -> Optional[str]:
        """Peek at a character ahead without advancing."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]
    
    def advance(self) -> Optional[str]:
        """Advance to the next character and return current."""
        char = self.current_char
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1
        return char
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char and self.current_char.isspace():
            self.advance()
    
    def skip_comment(self) -> bool:
        """Skip SQL comments. Returns True if a comment was skipped."""
        # Single line comment: -- ...
        if self.current_char == '-' and self.peek() == '-':
            while self.current_char and self.current_char != '\n':
                self.advance()
            return True
        
        # Multi-line comment: /* ... */
        if self.current_char == '/' and self.peek() == '*':
            self.advance()  # skip /
            self.advance()  # skip *
            while self.current_char:
                if self.current_char == '*' and self.peek() == '/':
                    self.advance()  # skip *
                    self.advance()  # skip /
                    return True
                self.advance()
            return True
        
        return False
    
    def read_number(self) -> Token:
        """Read a numeric literal."""
        start_line = self.line
        start_col = self.column
        
        result = ''
        is_float = False
        
        # Handle negative sign
        if self.current_char == '-':
            result += self.advance()
        
        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if is_float:
                    break  # Second dot, stop here
                is_float = True
            result += self.advance()
        
        value = float(result) if is_float else int(result)
        return Token(TokenType.NUMBER, value, start_line, start_col)
    
    def read_string(self) -> Token:
        """Read a string literal."""
        start_line = self.line
        start_col = self.column
        
        quote = self.advance()  # Skip opening quote
        result = ''
        
        while self.current_char:
            if self.current_char == quote:
                if self.peek() == quote:
                    # Escaped quote
                    result += self.advance()
                    self.advance()
                else:
                    # End of string
                    self.advance()
                    break
            elif self.current_char == '\\':
                # Handle escape sequences
                self.advance()
                if self.current_char == 'n':
                    result += '\n'
                elif self.current_char == 't':
                    result += '\t'
                elif self.current_char == '\\':
                    result += '\\'
                elif self.current_char == quote:
                    result += quote
                else:
                    result += self.current_char
                self.advance()
            else:
                result += self.advance()
        
        return Token(TokenType.STRING, result, start_line, start_col)
    
    def read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start_line = self.line
        start_col = self.column
        
        result = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.advance()
        
        # Check if it's a keyword
        upper = result.upper()
        if upper in KEYWORDS:
            return Token(KEYWORDS[upper], result, start_line, start_col)
        
        return Token(TokenType.IDENTIFIER, result, start_line, start_col)
    
    def next_token(self) -> Token:
        """Get the next token from the input."""
        while True:
            self.skip_whitespace()
            
            if self.skip_comment():
                continue
            
            break
        
        if self.current_char is None:
            return Token(TokenType.EOF, None, self.line, self.column)
        
        start_line = self.line
        start_col = self.column
        char = self.current_char
        
        # Numbers
        if char.isdigit() or (char == '-' and self.peek() and self.peek().isdigit()):
            return self.read_number()
        
        # Strings
        if char in ('"', "'"):
            return self.read_string()
        
        # Identifiers and keywords
        if char.isalpha() or char == '_':
            return self.read_identifier()
        
        # Two-character operators
        two_char = char + (self.peek() or '')
        if two_char == '<>':
            self.advance()
            self.advance()
            return Token(TokenType.NE, '<>', start_line, start_col)
        if two_char == '!=':
            self.advance()
            self.advance()
            return Token(TokenType.NE, '!=', start_line, start_col)
        if two_char == '<=':
            self.advance()
            self.advance()
            return Token(TokenType.LE, '<=', start_line, start_col)
        if two_char == '>=':
            self.advance()
            self.advance()
            return Token(TokenType.GE, '>=', start_line, start_col)
        
        # Single-character operators and punctuation
        single_char_tokens = {
            '=': TokenType.EQ,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '*': TokenType.STAR,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '/': TokenType.SLASH,
            '.': TokenType.DOT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            ',': TokenType.COMMA,
            ';': TokenType.SEMICOLON,
        }
        
        if char in single_char_tokens:
            self.advance()
            return Token(single_char_tokens[char], char, start_line, start_col)
        
        # Unknown character
        from exceptions import SQLSyntaxError
        self.advance()
        raise SQLSyntaxError(f"Unexpected character: {char!r}", start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire input and return list of tokens."""
        if self._tokens is not None:
            return self._tokens
        
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        
        self._tokens = tokens
        return tokens
    
    def __iter__(self) -> Iterator[Token]:
        """Iterate over tokens."""
        for token in self.tokenize():
            yield token
