class BTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.child_pages = []


class BTreeIndex:
    def __init__(self, db, table, column):
        self.db = db
        self.table = table
        self.column = column
        self.root = BTreeNode(leaf=True)

    def insert(self, key, record_pointer):
        pass

    def search(self, key):
        pass
