# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 - 2022 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

import cProfile
import io
import pstats
import time
from functools import wraps

def _profile(func):
    """Decorate function for profiling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative' #SortKey.CUMULATIVE  # 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return wrapper

def _timeit(func):
    """Measure time of the function
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        time_model = time.time()
        f = func(*args, **kwargs)
        time_described = time.time()
        time_diff = time_described - time_model
        print(F"[TIME] Function {func.__name__} needed: {time_diff}")
        return f
    return wrap