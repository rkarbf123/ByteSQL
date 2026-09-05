import sys
import traceback
from py_db.database import Database


def print_help():
    print("Meta commands:")
    print("  .help    Show this message")
    print("  .tables  List all tables")
    print("  .schema  Show table schema")
    print("  .stats   Show database statistics")
    print("  .exit    Exit the REPL")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <database.db>")
        sys.exit(1)

    db_path = sys.argv[1]
    db = Database(db_path)
    print(f"py_db v1.0 - Connected to {db_path}")

    while True:
        try:
            query = input("py_db> ").strip()
            if not query:
                continue

            if query.startswith("."):
                cmd = query.split()
                if cmd[0] == ".exit":
                    db.close()
                    break
                elif cmd[0] == ".help":
                    print_help()
                elif cmd[0] == ".tables":
                    print("Tables:", ", ".join(db.schema.keys()) or "None")
                elif cmd[0] == ".stats":
                    db.stats()
                else:
                    print(f"Unknown meta command: {cmd[0]}")
                continue

            # SQL 멀티라인
            while not query.endswith(";"):
                line = input("      > ").strip()
                query += " " + line

            result = db.execute(query)
            if result:
                for row in result:
                    print(row)

        except EOFError:
            db.close()
            break
        except Exception as e:
            print(f"Error: {e}")
            # traceback.print_exc() # 디버깅


if __name__ == "__main__":
    main()
