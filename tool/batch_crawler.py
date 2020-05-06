import sys
import argparse
import sqlite3
import os
import threading
from searchcode.fetchfile import work as fetchall_work
from searchcode.cloneall import work as cloneall_work


class BatchCrawler:

    def __init__(self, input, output, thread, clone_all):
        self.db_conn = sqlite3.connect(input)
        self.db_cur = self.db_conn.cursor()
        self.root = output
        self.thread = int(thread)
        self.clone_all = clone_all
        self.worker = cloneall_work if clone_all else fetchall_work

    def __del__(self):
        self.db_cur.close()
        self.db_conn.close()

    def run(self):
        self.db_cur.execute('''
            SELECT function, visited FROM python_library
            ''')

        cases = []
        rows = self.db_cur.fetchall()
        for row in rows:
            function = row[0]
            visited = row[1]
            if visited:
                continue

            split_name = function.split(os.sep)
            base_url = f'https://searchcode.com/api/codesearch_I/?q={"+".join(split_name)}&src=2&lan=19'

            sample_root = os.path.join(self.root, function.replace('.', os.sep))
            os.makedirs(sample_root, exist_ok=True)

            worker_pool = [None for _ in range(self.thread)]
            for i in range(self.thread):
                worker_pool[i] = threading.Thread(target=self.worker,
                                                  args=(sample_root, base_url),
                                                  kwargs={
                                                      'start': i,
                                                      'offset': self.thread,
                                                      'per_page': 100,
                                                      'num_limit': 0,
                                                      'clone_all': self.clone_all
                                                  })
                worker_pool[i].start()

            for i in range(self.thread):
                worker_pool[i].join()

            print(f'Finish {sample_root}')

            self.db_conn.execute(
                '''
                INSERT or REPLACE INTO python_library
                (function, visited) VALUES (?, ?)
            ''', (function, 1))
            self.db_conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Path to the sqlite dump.')
    parser.add_argument('-o', '--output', help='Path to the sample folder.')
    parser.add_argument('-t', '--thread', help='Number of worker threads.')
    parser.add_argument('-c', '--clone_all', default='', help='Knob to clone a complete repo')

    args = parser.parse_args()
    if args.input is None or args.output is None or args.thread is None:
        print(parser.print_help())
        return

    crawler = BatchCrawler(args.input, args.output, args.thread, args.clone_all)
    crawler.run()


if __name__ == "__main__":
    main()
