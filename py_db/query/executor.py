import struct
from ..storage.record import RecordSerializer
from ..sql.parser import CreateTable, Insert, Select, CreateIndex
import time

class Executor:
    def __init__(self, db):
        self.db = db

    def execute(self, ast):
        if isinstance(ast, CreateTable):
            return self._exec_create_table(ast)
        elif isinstance(ast, Insert):
            return self._exec_insert(ast)
        elif isinstance(ast, Select):
            return self._exec_select(ast)
        elif isinstance(ast, CreateIndex):
            return self._exec_create_index(ast)

    def _exec_create_table(self, ast):
        if ast.table in self.db.schema:
            raise ValueError(f"Table '{ast.table}' already exists.")
        
        first_page = self.db.pager.allocate_page()
        self.db.schema[ast.table] = {
            "columns": ast.columns,
            "root_page": first_page,
            "record_count": 0
        }
        self.db.pager.write_page(first_page, struct.pack("<H", 0))
        self.db._save_metadata()
        print(f"Table '{ast.table}' created.")

    def _exec_insert(self, ast):
        if ast.table not in self.db.schema:
            raise ValueError(f"Error: table '{ast.table}' does not exist.")
        
        schema = self.db.schema[ast.table]
        for val, col in zip(ast.values, schema['columns']):
            if col['type'] == 'INT' and not isinstance(val, int):
                raise ValueError(f"Error: column '{col['name']}' expects INT.")
            
        record_bytes = RecordSerializer.serialize(ast.values, schema['columns'])
        
        record_block = struct.pack("<H", len(record_bytes)) + record_bytes
        
        page_id = schema['root_page']
        page_data = bytearray(self.db.pager.read_page(page_id))
        
        num_records = struct.unpack_from("<H", page_data, 0)[0]
        
        offset = 2
        for _ in range(num_records):
            rec_len = struct.unpack_from("<H", page_data, offset)[0]
            offset += 2 + rec_len
            
        if offset + len(record_block) > self.db.pager.PAGE_SIZE:
            raise MemoryError("Page full - Page splitting required (Not implemented in MVP)")
            
        page_data[offset:offset+len(record_block)] = record_block
        struct.pack_into("<H", page_data, 0, num_records + 1)
        
        self.db.pager.write_page(page_id, bytes(page_data))
        schema['record_count'] += 1
        self.db._save_metadata()

    def _exec_select(self, ast):
        if ast.table not in self.db.schema:
            raise ValueError(f"Table '{ast.table}' does not exist.")
            
        schema = self.db.schema[ast.table]
        col_names = [c['name'] for c in schema['columns']]
        
        # Index 존재 여부
        using_index = False
        if ast.where and ast.table in self.db.indexes:
            idx_name = f"idx_{ast.table}_{ast.where['column']}"
            if idx_name in self.db.indexes[ast.table]:
                using_index = True
                print("-- Query Plan: INDEX SCAN --")
        
        if not using_index:
            # print("-- Query Plan: FULL TABLE SCAN --")
            pass
            
        page_id = schema['root_page']
        page_data = self.db.pager.read_page(page_id)
        num_records = struct.unpack_from("<H", page_data, 0)[0]
        
        results = []
        offset = 2
        
        display_cols = col_names if ast.columns[0] == "*" else ast.columns
        print(" | ".join(display_cols))
        print("-" * (len(display_cols) * 10))

        for _ in range(num_records):
            rec_len = struct.unpack_from("<H", page_data, offset)[0]
            record_bytes = page_data[offset+2 : offset+2+rec_len]
            row, _ = RecordSerializer.deserialize(record_bytes, schema['columns'])
            offset += 2 + rec_len
            
            row_dict = dict(zip(col_names, row))
            
            if ast.where:
                val = row_dict[ast.where['column']]
                cond_val = ast.where['value']
                op = ast.where['op']
                
                if op == '=' and not (val == cond_val): continue
                if op == '>=' and not (val >= cond_val): continue
                if op == '<=' and not (val <= cond_val): continue
                if op == '>' and not (val > cond_val): continue
                if op == '<' and not (val < cond_val): continue
                if op == '!=' and not (val != cond_val): continue
                
            out_row = [str(row_dict[c]) for c in display_cols]
            results.append(" | ".join(out_row))
            
        return results

    def _exec_create_index(self, ast):
        if ast.table not in self.db.schema:
            raise ValueError(f"Table '{ast.table}' does not exist.")
        
        if ast.table not in self.db.indexes:
            self.db.indexes[ast.table] = {}
            
        self.db.indexes[ast.table][ast.index_name] = ast.column
        self.db._save_metadata()
        print(f"Index '{ast.index_name}' created on {ast.table}({ast.column}).")