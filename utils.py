#
# Copyright (c) 2010 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of TKLBAM (TurnKey Linux BAckup and Migration).
#
# TKLBAM is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of
# the License, or (at your option) any later version.
#
import os
from os.path import *

import shutil
import stat

def remove_any(path):
    """Remove a path whether it is a file or a directory.
       Return: True if removed, False if nothing to remove"""

    if not lexists(path):
        return False

    if not islink(path) and isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

    return True

class AttrDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError("no such attribute '%s'" % name)

    def __setattr__(self, name, val):
        self[name] = val

def is_writeable(fpath):
    try:
        file(fpath, "w+")
        return True
    except IOError:
        return False

# workaround for shutil.move across-filesystem bugs
def move(src, dst):
    st = os.lstat(src)

    is_symlink = stat.S_ISLNK(st.st_mode)

    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(os.path.abspath(src)))

    if is_symlink:
        linkto = os.readlink(src)
        os.symlink(linkto, dst)
        os.unlink(src)
    else: 
        shutil.move(src, dst) 
        os.lchown(dst, st.st_uid, st.st_gid)
