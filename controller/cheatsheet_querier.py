import argparse
import os
import sys
import time
import json
import multiprocessing
import yaml
import requests
import ast
import importlib
import inspect
from stdlib_list import stdlib_list


class LibraryDumpaer():

    def __init__(self, queue):
        self.queue = queue

    def parse_ast(self, filename):
        with open(filename, 'rt') as file:
            return ast.parse(file.read(), filename=filename)

    def parse_ast_node(self, body, prefix):
        for node in body:
            if isinstance(node, ast.FunctionDef):
                func = node.name
                sig = '.'.join([prefix, func])
                self.queue.put(sig)
            elif isinstance(node, ast.ClassDef):
                extend_prefix = '.'.join([prefix, node.name])
                self.parse_ast_node(node.body, extend_prefix)

    def run(self):
        libs = stdlib_list("3.7")
        for lib in libs:
            try:
                module = importlib.import_module(lib)
                src = inspect.getsourcefile(module)
                tree = self.parse_ast(src)
                self.parse_ast_node(tree.body, lib)
            except Exception as e:
                print(e, file=sys.stderr)


def producer(task_queue):
    dumper = LibraryDumpaer(task_queue)
    dumper.run()


def consumer(task_queue, node, method):

    # TODO: Factor out these 3 parameters and put them in the config.
    max_backoff = 5
    wait_period = 1
    checkpoint = 1000

    backoff = 0
    task_num = 0

    query_time = 0
    hit_count = 0

    while True:
        try:
            keyword = task_queue.get(timeout=wait_period)

            if method == 'fuzzy':
                '''
                For fuzzy mode, we split the signature into path tokens
                and merge them with suffix order.

                For example:
                    Consider the signature a.b.c,
                    we will generate a.b.c and b.c.

                '''
                tokens = keyword.split('.')
                count = len(tokens)
                multiple_keywords = []

                for i in range(count - 1):
                    buf = []
                    for j in range(i, count):
                        buf.append(tokens[j])
                    keyword ='.'.join(buf)

                    multiple_keywords.append(keyword)

                keyword = ' '.join(multiple_keywords)

            query = {
                "query": {
                    "match": {
                        "code": keyword
                    }
                },
                "size": 0,
                "track_total_hits": True
            }

            try:
                url = f'http://{node}:9200/cheatsheet/_search'
                result = requests.post(url, json=query)

                data = result.json()
                query_time += data['took']
                hit_count += data['hits']['total']['value']
            except Exception as e:
                print(e, file=sys.stderr)
                continue

            task_num += 1
            if task_num % checkpoint == 0:
                print(f'Query {task_num} api signatures from {node}')

        except Exception as e:
            print(f'No pending task, try to wait for {wait_period} seconds...')
            backoff += 1
            if backoff == max_backoff:
                print(f'No pending task after {backoff} tries, so quit...')
                break

    normalized = query_time / float(1000)

    print(f'Query {task_num} api signatures from {node}')
    print(f'Total query time: {normalized} seconds')
    print(f'Total hit count: {hit_count}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c',
                        '--config',
                        help='Path to the Cheatsheet populator config.')

    args = parser.parse_args()
    if args.config is None:
        print(parser.print_help())
        return

    config = None
    with open(args.config, 'r') as hdle:
        config = yaml.load(hdle, yaml.FullLoader)

    task_queue = multiprocessing.Queue()
    workers = []

    get_worker = config['get_worker']

    # Create the producer that generate Python api signatures.
    prod = multiprocessing.Process(target=producer, args=(task_queue,))
    prod.start()
    workers.append(prod)

    # Create the consumers that query the ElasticSearch cluster for the code
    # snippets which match the specified api signatures.
    for node in get_worker['cheatsheet_cluster']:
        cons = multiprocessing.Process(target=consumer,
                                       args=(task_queue, node,
                                             get_worker['search_method']))
        cons.start()
        workers.append(cons)

    start_time = time.time()

    for worker in workers:
        worker.join()

    elapsed_time = time.time() - start_time
    wall_clock = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
    print(f'Data query elapsed time: {wall_clock}')


if __name__ == "__main__":
    main()
