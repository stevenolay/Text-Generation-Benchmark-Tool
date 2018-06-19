import tempfile
import contextlib
import shutil
import os


@contextlib.contextmanager
def TemporaryDirectory(*args, **kwargs):
    d = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        shutil.rmtree(d)


def file_len_open(f):
    fname = f.name
    return file_len(fname)


def file_len(fname):
    '''
        Calculates the line count for a given file line by line to prevent
         loading lines into memory all at once.
        SOURCE:
            https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python
    '''
    i = -1
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
        f.seek(0)
    return i + 1


def create_folder_if_not_exists(directory):
    '''
    Create the folder if it doesn't exist already.
    '''
    if not os.path.exists(directory):
        os.makedirs(directory)
