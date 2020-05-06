import argparse
import os
import threading

from .searchcodeapicaller import SearchcodeApiCaller
from .fetchfile import work as fetchfilework
from .cloneall import work as cloneallwork


def main(myarg):
    # form query url for searchcode api
    # src: 2 = from github
    # lan: 19 = python
    base_url = f'https://searchcode.com/api/codesearch_I/?q={"+".join(myarg.Q)}&src=2&lan=19'

    if myarg.num == -1:
        # just print number of results
        # call api
        res = SearchcodeApiCaller().call(base_url)
        print(f'Number of results: {res["total"]}')
        exit(0)

    # create output dir if not exist
    os.makedirs(myarg.output, exist_ok=True)

    # check worker
    worker = fetchfilework
    if myarg.clone_all != '':
        worker = cloneallwork

    # create workers pool and start working
    worker_pool = [None for _ in range(myarg.thread)]
    for i in range(myarg.thread):
        worker_pool[i] = threading.Thread(target=worker,
                                          args=(myarg.output, base_url),
                                          kwargs={
                                              'start': i,
                                              'offset': myarg.thread,
                                              'per_page': myarg.per_query,
                                              'num_limit': myarg.num,
                                              'clone_all': myarg.clone_all
                                          })
        worker_pool[i].start()

    # join all and exit
    for i in range(myarg.thread):
        worker_pool[i].join()


if __name__ == '__main__':
    # parse arg
    parser = argparse.ArgumentParser(
        description='Clone git repos with keywords')
    parser.add_argument(
        '-n',
        '--num',
        type=int,
        default=-1,
        help=
        'Number of repo to download, pass 0 for all. Only print out number of repo by default.'
    )
    parser.add_argument(
        '-t',
        '--thread',
        type=int,
        default=1,
        help=
        'Number of threads. It make sense since most workload should be on disk writing.'
    )
    parser.add_argument('-p',
                        '--per_query',
                        type=int,
                        default=20,
                        help='Max number of result per query.')
    parser.add_argument(
        '-c',
        '--clone_all',
        default='',
        help=
        'Clone the whole repository and parse all files with given extension.')
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default=os.getcwd(),
        help=
        "A director to store all downloaded files. The directory will be created if it doesn't exist"
    )
    parser.add_argument(
        'Q',
        type=str,
        nargs='+',
        help="Keywords to query. Don't need to type 'Q', just type keywords.")
    arg = parser.parse_args()

    main(arg)
