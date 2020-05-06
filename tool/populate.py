import sys
import os
import json
import argparse
import requests


def populate(ip, root):
    samples = os.listdir(root)
    index = 0

    for sample in samples:
        if not sample.endswith(".py"):
            continue

        sample_path = os.path.join(root, sample)
        if not os.path.isfile(sample_path):
            continue

        code = None
        try:
            with open(sample_path, "r") as hdle:
                code = hdle.read()
        except:
            continue

        payload = {
            'language': 'python',
            'code': json.dumps(code),
        }

        url = f"""http://{ip}:9200/cheatsheet/python/{index}"""

        result = requests.post(url, json=payload)
        print(result.text)
        print(f"""Install {sample_path} ...""")
        index += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help="ElasticSearch data node.")
    parser.add_argument("-s", "--sample", help="Path to the sampe folder.")

    args = parser.parse_args()
    if args.ip is None or args.sample is None:
        print(parser.print_help())
        return

    populate(args.ip, args.sample)


if __name__ == "__main__":
    main()
