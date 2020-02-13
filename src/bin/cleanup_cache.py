from os import walk
from sys import argv
import cli_helper


def cleanup_cache_files(root_path: str) -> None:
    import shutil

    for dirpath, _, _ in walk(root_path):

        if any(map(lambda x: dirpath.endswith(x), ["__pycache__", ".egg-info"])):

            cli_helper.log.info("Removing folder {}".format(dirpath))
            shutil.rmtree(dirpath, ignore_errors=True)


if __name__ == "__main__":
    for folder in argv[1:]:
        cleanup_cache_files(folder)
    else:
        print("Usage: python %s <folder> [<folder> ...]" % argv[0])
