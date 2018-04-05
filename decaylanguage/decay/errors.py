from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



class LineFailure(RuntimeError):
    def __init__(self, line, message, *args,**kwargs):
        super(LineFailure, self).__init__("{0}: {1}".format(line, message), *args, **kwargs)
