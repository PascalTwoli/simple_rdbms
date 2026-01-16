#!/usr/bin/env python3
"""
Simple RDBMS - Interactive SQL REPL

A lightweight relational database management system with SQL interface.
"""

import sys
import os
import readline  # For command history and line editing

from parser import parse
from executor import Executor, QueryResult
from storage import Database
from exceptions import RDBMSError


class TablePrinter:
    """Pretty-prints query results as tables."""
    
    @staticmethod
    def print_result(result: QueryResult) -> None:
        """Print a query result."""
        if result.message and not result.rows:
            print(result.message)
            return
        
        if not result.columns:
            if result.message:
                print(result.message)
            return
        
        # Calculate column widths
        widths = {}
        for col in result.columns:
            # Get display name (without table prefix for cleaner output)
            display = col.split('.')[-1] if '.' in col else col
            widths[col] = len(display)
        
        for row in result.rows:
            for col in result.columns:
                value = row.get(col, '')
                value_str = TablePrinter._format_value(value)
                widths[col] = max(widths[col], len(value_str))
        
        # Print header
        header_parts = []
        for col in result.columns:
            display = col.split('.')[-1] if '.' in col else col
            header_parts.append(display.ljust(widths[col]))
        
        header = ' | '.join(header_parts)
        separator = '-+-'.join('-' * widths[col] for col in result.columns)
        
        print(header)
        print(separator)
        
        # Print rows
        for row in result.rows:
            parts = []
            for col in result.columns:
                value = row.get(col, '')
                value_str = TablePrinter._format_value(value)
                parts.append(value_str.ljust(widths[col]))
            print(' | '.join(parts))
        
        # Print row count
        count = len(result.rows)
        print(f"\n({count} row{'s' if count != 1 else ''})")
    
    @staticmethod
    def _format_value(value) -> str:
        """Format a value for display."""
        if value is None:
            return 'NULL'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.6g}"
        return str(value)


class REPL:
    """Interactive Read-Eval-Print Loop for the RDBMS."""
    
    PROMPT = 'sql> '
    CONTINUATION_PROMPT = '  -> '
    
    def __init__(self):
        self.db = Database()
        self.executor = Executor(self.db)
        self.running = True
        
        # Set up readline history
        self.history_file = os.path.expanduser('~/.rdbms_history')
        try:
            readline.read_history_file(self.history_file)
        except FileNotFoundError:
            pass
        readline.set_history_length(1000)
    
    def run(self):
        """Run the REPL."""
        self.print_welcome()
        
        while self.running:
            try:
                stmt = self.read_statement()
                if stmt is None:
                    continue
                
                # Check for meta-commands
                if stmt.strip().startswith('.'):
                    self.handle_meta_command(stmt.strip())
                else:
                    self.execute(stmt)
                    
            except KeyboardInterrupt:
                print("\n(Use .quit to exit)")
                continue
            except EOFError:
                print()
                self.running = False
        
        self.save_history()
        print("Goodbye!")
    
    def print_welcome(self):
        """Print welcome message."""
        print("╔════════════════════════════════════════════════════════════╗")
        print("║            Simple RDBMS - SQL Database Engine              ║")
        print("╠════════════════════════════════════════════════════════════╣")
        print("║  Type SQL statements ending with ; or use meta-commands:   ║")
        print("║    .tables    - List all tables                            ║")
        print("║    .schema    - Show table schema                          ║")
        print("║    .indexes   - Show indexes                               ║")
        print("║    .help      - Show help                                  ║")
        print("║    .quit      - Exit                                       ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print()
    
    def read_statement(self) -> str:
        """Read a complete SQL statement (may span multiple lines)."""
        lines = []
        prompt = self.PROMPT
        
        while True:
            try:
                line = input(prompt)
            except EOFError:
                if lines:
                    raise
                return None
            
            lines.append(line)
            full = '\n'.join(lines)
            
            # Check if statement is complete
            stripped = full.strip()
            if not stripped:
                return None
            
            # Meta-commands are single-line
            if stripped.startswith('.'):
                return stripped
            
            # SQL statements end with semicolon
            if stripped.endswith(';'):
                return full
            
            prompt = self.CONTINUATION_PROMPT
    
    def execute(self, sql: str):
        """Execute a SQL statement."""
        try:
            stmt = parse(sql)
            result = self.executor.execute(stmt)
            TablePrinter.print_result(result)
        except RDBMSError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Internal error: {e}")
            if os.environ.get('DEBUG'):
                import traceback
                traceback.print_exc()
    
    def handle_meta_command(self, cmd: str):
        """Handle a meta-command."""
        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]
        
        if command in ('.quit', '.exit', '.q'):
            self.running = False
        
        elif command == '.tables':
            self.show_tables()
        
        elif command == '.schema':
            if args:
                self.show_schema(args[0])
            else:
                self.show_all_schemas()
        
        elif command == '.indexes':
            if args:
                self.show_indexes(args[0])
            else:
                self.show_all_indexes()
        
        elif command == '.help':
            self.show_help()
        
        elif command == '.clear':
            self.db.clear()
            print("Database cleared.")
        
        else:
            print(f"Unknown command: {command}")
            print("Type .help for available commands.")
    
    def show_tables(self):
        """Show all tables."""
        tables = self.db.list_tables()
        if not tables:
            print("No tables.")
            return
        
        print("Tables:")
        for table in tables:
            schema = self.db.get_schema(table)
            row_count = self.db.get_table(table).count()
            print(f"  {table} ({len(schema.columns)} columns, {row_count} rows)")
    
    def show_schema(self, table_name: str):
        """Show schema for a specific table."""
        try:
            schema = self.db.get_schema(table_name)
            print(f"\nTable: {schema.name}")
            print("-" * 60)
            print(f"{'Column':<20} {'Type':<12} {'Constraints':<20}")
            print("-" * 60)
            for col in schema.columns:
                constraints = []
                if col.primary_key:
                    constraints.append('PRIMARY KEY')
                elif col.unique:
                    constraints.append('UNIQUE')
                if col.not_null and not col.primary_key:
                    constraints.append('NOT NULL')
                print(f"{col.name:<20} {col.data_type.name:<12} {' '.join(constraints):<20}")
            print()
        except RDBMSError as e:
            print(f"Error: {e}")
    
    def show_all_schemas(self):
        """Show schemas for all tables."""
        tables = self.db.list_tables()
        if not tables:
            print("No tables.")
            return
        for table in tables:
            self.show_schema(table)
    
    def show_indexes(self, table_name: str):
        """Show indexes for a specific table."""
        try:
            table = self.db.get_table(table_name)
            indexes = table.index_manager.list_indexes()
            if not indexes:
                print(f"No indexes on table '{table_name}'.")
                return
            
            print(f"\nIndexes on {table_name}:")
            for col in indexes:
                index = table.index_manager.get_index(col)
                print(f"  {col}: B-tree ({len(index)} entries)")
            print()
        except RDBMSError as e:
            print(f"Error: {e}")
    
    def show_all_indexes(self):
        """Show indexes for all tables."""
        tables = self.db.list_tables()
        if not tables:
            print("No tables.")
            return
        for table in tables:
            self.show_indexes(table)
    
    def show_help(self):
        """Show help information."""
        print("""
Available meta-commands:
  .tables              List all tables
  .schema [table]      Show table schema (all tables if no name given)
  .indexes [table]     Show indexes (all tables if no name given)
  .clear               Clear the database
  .help                Show this help
  .quit / .exit        Exit the REPL

Supported SQL:
  CREATE TABLE name (col1 TYPE [constraints], ...)
  DROP TABLE [IF EXISTS] name
  INSERT INTO name [(columns)] VALUES (values), ...
  SELECT columns FROM table [JOIN ...] [WHERE ...] [ORDER BY ...]
  UPDATE name SET col=val, ... [WHERE ...]
  DELETE FROM name [WHERE ...]

Data types:
  INTEGER, INT         64-bit signed integer
  TEXT, VARCHAR        Variable-length string
  REAL, FLOAT          Floating-point number
  BOOLEAN, BOOL        Boolean (true/false)

Constraints:
  PRIMARY KEY          Unique, non-null identifier
  UNIQUE               Must be unique (allows NULL)
  NOT NULL             Cannot be NULL

Join types:
  INNER JOIN           Only matching rows
  LEFT JOIN            All left rows + matching right
  RIGHT JOIN           All right rows + matching left
  CROSS JOIN           Cartesian product

Examples:
  CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
  INSERT INTO users (id, name) VALUES (1, 'Alice'), (2, 'Bob');
  SELECT * FROM users WHERE id > 1;
  SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id;
""")
    
    def save_history(self):
        """Save command history."""
        try:
            readline.write_history_file(self.history_file)
        except Exception:
            pass


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Execute SQL from command line or file
        if sys.argv[1] == '-c':
            # Execute single command
            if len(sys.argv) < 3:
                print("Usage: python main.py -c 'SQL STATEMENT'", file=sys.stderr)
                sys.exit(1)
            
            db = Database()
            executor = Executor(db)
            sql = sys.argv[2]
            
            try:
                stmt = parse(sql)
                result = executor.execute(stmt)
                TablePrinter.print_result(result)
            except RDBMSError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        
        elif sys.argv[1] == '-f':
            # Execute from file
            if len(sys.argv) < 3:
                print("Usage: python main.py -f script.sql", file=sys.stderr)
                sys.exit(1)
            
            db = Database()
            executor = Executor(db)
            
            try:
                with open(sys.argv[2], 'r') as f:
                    content = f.read()
                
                # Split by semicolons and execute each statement
                statements = [s.strip() for s in content.split(';') if s.strip()]
                for sql in statements:
                    try:
                        stmt = parse(sql + ';')
                        result = executor.execute(stmt)
                        if result.rows:
                            TablePrinter.print_result(result)
                        elif result.message:
                            print(result.message)
                    except RDBMSError as e:
                        print(f"Error: {e}", file=sys.stderr)
                        
            except FileNotFoundError:
                print(f"File not found: {sys.argv[2]}", file=sys.stderr)
                sys.exit(1)
        
        elif sys.argv[1] in ('-h', '--help'):
            print("""
Simple RDBMS - A lightweight SQL database engine

Usage:
  python main.py              Start interactive REPL
  python main.py -c 'SQL'     Execute single SQL statement
  python main.py -f file.sql  Execute SQL from file
  python main.py -h           Show this help
""")
        else:
            print(f"Unknown option: {sys.argv[1]}", file=sys.stderr)
            print("Use -h for help", file=sys.stderr)
            sys.exit(1)
    else:
        # Start interactive REPL
        repl = REPL()
        repl.run()


if __name__ == '__main__':
    main()
