import os
import json
from .storage.pager import Pager
from .sql.parser import Parser
from .query.executor import Executor


class Database:
    def __init__(self, filepath):
        self.pager = Pager(filepath)
        self.schema = {}  # 테이블 메타데이터
        self.indexes = {}
        self._load_metadata()

    def _load_metadata(self):
        page0 = self.pager.read_page(0)
        metadata_str = page0.decode("utf-8").strip("\x00")
        if metadata_str:
            data = json.loads(metadata_str)
            self.schema = data.get("schema", {})
            self.indexes = data.get("indexes", {})
        else:
            self._save_metadata()

    def _save_metadata(self):
        data = {"schema": self.schema, "indexes": self.indexes}
        metadata_str = json.dumps(data)
        padded = metadata_str.encode("utf-8").ljust(Pager.PAGE_SIZE, b"\x00")
        self.pager.write_page(0, padded)

    def execute(self, sql):
        parser = Parser(sql)
        ast = parser.parse()
        executor = Executor(self)
        return executor.execute(ast)

    def stats(self):
        print(f"Tables: {len(self.schema)}")
        records = sum(self.schema[t].get("record_count", 0) for t in self.schema)
        print(f"Records: {records}")
        print(f"Indexes: {sum(len(idx) for idx in self.indexes.values())}")
        print(f"Pages: {self.pager.num_pages}")

    def close(self):
        self._save_metadata()
        self.pager.close()
