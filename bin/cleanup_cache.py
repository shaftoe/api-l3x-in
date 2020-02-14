from os import (walk, remove)
from sys import argv
import cli_helper


def cleanup_cache_files(root_path: str) -> None:
    import shutil

    for dirpath, _, filenames in walk(root_path):

        for filename in filenames:
            if filename.endswith(".pyc"):
                pyc_file = "{}/{}".format(dirpath, filename)
                cli_helper.log.info("Removing file %s" % pyc_file)
                remove(pyc_file)

        if any(map(lambda x: dirpath.endswith(x), ["__pycache__", ".egg-info"])):

            cli_helper.log.info("Removing folder %s" % dirpath)
            shutil.rmtree(dirpath, ignore_errors=True)


if __name__ == "__main__":
    if len(argv) < 2:
        print("Usage: python %s <folder> [<folder> ...]" % argv[0])

    else:
        for folder in argv[1:]:
            cleanup_cache_files(folder)
