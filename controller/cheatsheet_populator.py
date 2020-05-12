import argparse
import os
import sys
import time
import json
import multiprocessing
import yaml
import requests


def producer(task_queue, data_warehouse, max_task_num):
    task_num = 0
    total_size = 0

    for root, dirs, files in os.walk(data_warehouse):
        for file in files:
            if not file.endswith('.py'):
                continue

            task_num += 1
            if task_num == max_task_num:
                return

            path = os.path.join(root, file)

            code = None
            try:
                with open(path, 'r') as hdle:
                    code = hdle.read()
            except:
                continue

            total_size += os.path.getsize(path)

            payload = {
                'language': 'python',
                'code': json.dumps(code),
            }

            task_queue.put(payload)

    print(f'Produce {task_num} tasks with {total_size} bytes.')


def consumer(task_queue, node):

    # TODO: Factor out these 3 parameters and put them in the config.
    max_backoff = 10
    wait_period = 10
    checkpoint = 1000

    backoff = 0
    task_num = 0

    while True:
        try:
            task = task_queue.get(timeout=wait_period)

            try:
                url = f'http://{node}:9200/cheatsheet/python'
                result = requests.post(url, json=task)
            except Exception as e:
                print(e, file=sys.stderr)
                continue

            task_num += 1
            if task_num % checkpoint == 0:
                print(f'Insert {task_num} documents into {node}')

        except Exception as e:
            print(f'No pending task, try to wait for {wait_period} seconds...')
            backoff += 1
            if backoff == max_backoff:
                print(f'No pending task after {backoff} tries, so quit...')
                break

    print(f'Insert {task_num} documents into {node}')


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

    task_scheduler = config['task_scheduler']
    post_worker = config['post_worker']

    # Create the producer that generate code snippet documents.
    prod = multiprocessing.Process(target=producer,
                                   args=(task_queue,
                                         task_scheduler['data_warehouse'],
                                         task_scheduler['max_task_num']))
    prod.start()
    workers.append(prod)

    # Create the consumers that insert documents into the ElasticSearch cluster.
    for node in post_worker['cheatsheet_cluster']:
        cons = multiprocessing.Process(target=consumer, args=(task_queue, node))
        cons.start()
        workers.append(cons)

    start_time = time.time()

    for worker in workers:
        worker.join()

    elapsed_time = time.time() - start_time
    wall_clock = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
    print(f'Data ingestion elapsed time: {wall_clock}')


if __name__ == "__main__":
    main()
