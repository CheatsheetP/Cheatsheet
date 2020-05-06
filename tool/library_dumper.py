import os
import importlib
import inspect
import sqlite3
import argparse
import ast
import sys
from stdlib_list import stdlib_list


class LibraryDumpaer():

    def __init__(self, output):
        self.db_conn = sqlite3.connect(output)
        try:
            self.db_conn.execute('''
                CREATE TABLE python_library (
                function TEXT PRIMARY KEY NOT NULL,
                visited INTEGER NOT NULL)''')
        except Exception as e:
            pass

    def __del__(self):
        self.db_conn.close()

    def parse_ast(self, filename):
        with open(filename, 'rt') as file:
            return ast.parse(file.read(), filename=filename)

    def parse_ast_node(self, body, prefix, collect):
        for node in body:
            if isinstance(node, ast.FunctionDef):
                func = node.name
                sig = '.'.join([prefix, func]).replace('.', os.sep)
                collect.append(sig)
            elif isinstance(node, ast.ClassDef):
                extend_prefix = '.'.join([prefix, node.name])
                self.parse_ast_node(node.body, extend_prefix, collect)

    def run(self):
        libs = stdlib_list("3.7")
        for lib in libs:
            try:
                module = importlib.import_module(lib)
                src = inspect.getsourcefile(module)
                tree = self.parse_ast(src)

                collect = []
                self.parse_ast_node(tree.body, lib, collect)

                for sig in collect:
                    self.db_conn.execute(
                        '''
                        INSERT or REPLACE INTO python_library
                        (function, visited) VALUES (?, ?)
                    ''', (sig, 0))
                    self.db_conn.commit()
            except Exception as e:
                print(e, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='Path to the sqlite dump.')

    args = parser.parse_args()
    if args.output is None:
        print(parser.print_help())
        return

    dumper = LibraryDumpaer(args.output)
    dumper.run()


if __name__ == '__main__':
    main()
