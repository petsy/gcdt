import io
import os
from zipfile import ZipFile
import tarfile
import sys
import threading


def files_to_bundle(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            full_path = os.path.join(root, f)
            archive_name = full_path[len(path) + len(os.sep):]
            #print "full_path, archive_name" + full_path, archive_name
            yield full_path, archive_name

def make_tar_file(path, outputpath):
    # make sure we add a unique identifiere when we are running within jenkins
    file_suffix = os.getenv('BUILD_TAG', '')
    destfile = '%s/tenkai-bundle%s.tar.gz' % (outputpath, file_suffix)
    with tarfile.open(destfile, "w:gz") as tar:
        for full_path, archive_name in files_to_bundle(path=path):
            tar.add(full_path, recursive=False, arcname=archive_name)
    return destfile



class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far,
                                             self._size, percentage))
            sys.stdout.flush()
