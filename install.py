import sys
import os
import requests


def main():
    samples = os.listdir(sys.argv[1])
    index = 0

    for sample in samples:
        if not sample.endswith(".json"):
            continue

        sample_path = os.path.join(sys.argv[1], sample)
        if not os.path.isfile(sample_path):
            continue

        url = f"""http://localhost:9200/cheatsheet/python/{index}"""

        payload = None
        with open(sample_path, "r") as hdle:
            payload = hdle.read()

        result = requests.post(url, data=payload)
        print(f"""Install {sample_path} ...""")
        index += 1


if __name__ == "__main__":
    main()
