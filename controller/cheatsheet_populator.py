import queue
import argparse
import threading
import os
import sys
import time
import json
import yaml
import requests
import cleancode.sanitizer


class TaskProducer(threading.Thread):

    def __init__(self, task_queue, data_warehouse):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.data_warehouse = data_warehouse

    def run(self):
        for root, dirs, files in os.walk(self.data_warehouse):
            for file in files:
                if not file.endswith('.py'):
                    continue
                path = os.path.join(root, file)
                doc = cleancode.sanitizer.clean_snippet(path)
                self.task_queue.put(doc)


class TaskConsumer(threading.Thread):

    def __init__(self, task_queue, node):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.node = node

        # TODO: Factor out these 3 parameters and put them in the config.
        self.max_backoff = 10
        self.wait_period = 10
        self.checkpoint = 1000

    def run(self):
        backoff = 0
        task_num = 0

        while True:
            try:
                task = self.task_queue.get(timeout=self.wait_period)

                try:
                    url = f'http://{self.node}:9200/cheatsheet/python'
                    result = requests.post(url, json=task)
                except Exception as e:
                    print(e, file=sys.stderr)
                    continue

                task_num += 1
                if task_num % self.checkpoint == 0:
                    print(f'Insert {task_num} documents into {self.node}')

            except Exception as e:
                print(
                    f'No pending task, try to wait for {self.wait_period} seconds...'
                )
                backoff += 1
                if backoff == self.max_backoff:
                    print(f'No pending task after {backoff} tries, so quit...')
                    break

        print(f'Insert {task_num} documents into {self.node}')


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

    task_queue = queue.Queue()
    workers = []

    # Create the task producer that generate code snippet documents.
    producer = TaskProducer(task_queue, config['data_warehouse'])
    producer.start()
    workers.append(producer)

    # Create the task consumers that insert documents into the ElasticSearch cluster.
    for node in config['cheatsheet_cluster']:
        consumer = TaskConsumer(task_queue, node)
        consumer.start()
        workers.append(consumer)

    start_time = time.time()

    for worker in workers:
        worker.join()

    elapsed_time = time.time() - start_time
    wall_clock = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
    print(f'Data ingestion elapsed time: {wall_clock}')


if __name__ == "__main__":
    main()
