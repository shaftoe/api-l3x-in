from os import (walk, remove)
from shutil import rmtree
from sys import argv

import cli_helper


def cleanup_cache_files(root_path: str) -> None:

    for dirpath, _, filenames in walk(root_path):

        for filename in filenames:
            if filename.endswith(".pyc") or filename.endswith(".bak"):
                cache_file = "%s/%s" % (dirpath, filename)
                cli_helper.log.info("Removing file   %s", cache_file)
                remove(cache_file)

        if any(map(dirpath.endswith, ["__pycache__", ".egg-info"])):

            cli_helper.log.info("Removing folder %s", dirpath)
            rmtree(dirpath, ignore_errors=True)


if __name__ == "__main__":
    if len(argv) < 2:
        print("Usage: python %s <folder> [<folder> ...]" % argv[0])

    else:
        for folder in argv[1:]:
            cleanup_cache_files(folder)
