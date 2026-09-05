import re
from dataclasses import dataclass
from typing import List, Any

# --- AST Definitions ---
@dataclass
class CreateTable:
    table: str
    columns: list

@dataclass
class Insert:
    table: str
    values: list

@dataclass
class Select:
    columns: list
    table: str
    where: dict = None
    order_by: dict = None
    limit: int = None

@dataclass
class CreateIndex:
    index_name: str
    table: str
    column: str
    
class Parser:
    def __init__(self, sql):
        self.sql = sql
        # 정규식
        pattern = r'\s*(?:(--.*)|([\'"].*?[\'"])|(>=|<=|!=|=|<|>|\*|,|\(|\)|;)|([a-zA-Z_][a-zA-Z0-9_]*)|(\d+))\s*'
        self.tokens = [t for match in re.findall(pattern, sql) for t in match if t]
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        token = self.peek()
        self.pos += 1
        return token

    def parse(self):
        token = self.consume().upper()
        if token == "CREATE":
            token2 = self.consume().upper()
            if token2 == "TABLE": return self.parse_create_table()
            elif token2 == "INDEX": return self.parse_create_index()
        elif token == "INSERT": return self.parse_insert()
        elif token == "SELECT": return self.parse_select()
        raise ValueError(f"Syntax error near '{token}'")

    def parse_create_table(self):
        table = self.consume()
        self.consume()
        columns = []
        while self.peek() != ")":
            col_name = self.consume()
            col_type = self.consume().upper()
            columns.append({"name": col_name, "type": col_type})
            if self.peek() == ",": self.consume()
        self.consume()
        return CreateTable(table, columns)

    def parse_insert(self):
        self.consume()
        table = self.consume()
        self.consume()
        self.consume()
        values = []
        while self.peek() != ")":
            val = self.consume()
            if val.startswith("'") or val.startswith('"'): val = val[1:-1]
            elif val.isdigit(): val = int(val)
            values.append(val)
            if self.peek() == ",": self.consume()
        self.consume()
        return Insert(table, values)

    def parse_select(self):
        columns = []
        while self.peek().upper() != "FROM":
            col = self.consume()
            if col != ",": columns.append(col)
        self.consume()
        table = self.consume()
        
        where = None
        if self.peek() and self.peek().upper() == "WHERE":
            self.consume()
            col = self.consume()
            op = self.consume()
            val = self.consume()
            if str(val).isdigit(): val = int(val)
            where = {"column": col, "op": op, "value": val}
            
        return Select(columns, table, where)
        
    def parse_create_index(self):
        idx_name = self.consume()
        self.consume() # ON
        table = self.consume()
        self.consume() # (
        col = self.consume()
        self.consume() # )
        return CreateIndex(idx_name, table, col)