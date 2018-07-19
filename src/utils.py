import tempfile
import contextlib
import shutil
import os
import sys


@contextlib.contextmanager
def TemporaryDirectory(*args, **kwargs):
    d = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        shutil.rmtree(d)


def fileLenOpen(f):
    fname = f.name
    return fileLen(fname)


def fileLen(fname):
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


def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def createFolderIfNotExists(directory):
    '''
    Create the folder if it doesn't exist already.
    '''
    if not os.path.exists(directory):
        os.makedirs(directory)


def fileExists(directory):
    return os.path.exists(directory)


def listFilesInDir(dir):
    r = []
    subdirs = [x[0] for x in os.walk(dir)]
    for subdir in subdirs:
        files = os.walk(subdir).next()[2]
        if (len(files) > 0):
            for file in files:
                r.append(subdir + "/" + file)
    return r
