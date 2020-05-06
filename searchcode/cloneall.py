import os
import tempfile
from pathlib import Path
import shutil

from .searchcodeapicaller import SearchcodeApiCaller


def work(outputdir,
         base_url,
         *,
         start=0,
         offset=1,
         per_page=20,
         num_limit=0,
         **kwargs):
    """
    Call searchcode api starting from page={start} and with {offset} pages.
    Stop when result is empty.
    Only doenload files from github.
    Try to download files from branches specified in BRANCH list in order.

    Downloaded files will be named as {username}_{reponame}_{path_to_file}_{filename}.py
    Files with the same name will be wiped out.
    Files will be placed in outputdir/reponame/

    Arguments:
        outputdir:
            A directory to put all the output file
        base_url:
            Searchcode api url.

    Keyword Arguments:
        start:
            Starting page. Start from 0.
        offset:
            Offset pages. p=start, p=start + offset ...
        per_page:
            Number of repository per page (per request).
        num_limit:
            Numer of repository to download accross all threads. Set 0 for no limit.
        clone_all:
            File extension to clone.
    """
    caller = SearchcodeApiCaller()
    page = start - offset

    while True:
        page += offset

        # return when reach download limit
        if num_limit > 0 and page * per_page > num_limit:
            return

        url = f'{base_url}&per_page={per_page}&p={page}'
        res = caller.call(url)

        if res is None or res['results'] is None or not res['results']:
            return

        # max number
        result_repos = res['results']
        if num_limit > 0:
            result_repos = result_repos[:max(
                min(len(res), num_limit - page * per_page), 0)]

        for result in result_repos:
            ## form url to get target file.
            # parse username
            username = result['repo'].find('github.com/')
            username = result['repo'][username + 11:]
            username = username[:username.find('/')]

            # create a temp directory and clone the whole repo
            tempdir = tempfile.TemporaryDirectory()
            my_cwd = os.getcwd()
            os.chdir(tempdir.name)
            os.system(f'git clone --depth 1 {result["repo"]}')
            os.chdir(my_cwd)

            # create output folder
            os.mkdir(os.path.join(outputdir, result['name']))

            # Form generator and copy all files with given extension to outputdir
            ext = f'*.{kwargs["clone_all"]}'
            temprepo = os.path.join(tempdir.name, result['name'])
            fg = Path(temprepo).rglob(ext)
            for srcfn in fg:
                # form output filename
                rel_loc = os.path.relpath(srcfn, temprepo)
                ofn = os.path.join(
                    outputdir, result['name'],
                    f'{username}_{result["name"]}_{os.path.dirname(rel_loc).replace(os.path.sep, "_")}_{os.path.basename(rel_loc).replace(os.path.sep, "_")}'
                )
                try:
                    shutil.copyfile(srcfn, ofn)
                except Exception as e:
                    print(e)

            # cleanup
            tempdir.cleanup()
