import sys
import time

from functools import wraps

from flask import g, current_app

class _CacheRequestInfo():
    """Cache request debug information"""


    def __init__(self, method, args, kwargs, result,
                 start_time, end_time, context):
        self.method = method
        self.args = args
        self.kwargs = kwargs
        self.result = result
        self.start_time = start_time
        self.end_time = end_time
        self.context = context

    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def hit(self):
        return bool(self.result)

    @property
    def parameters(self):
        parts = []
        args_repr = ', '.join(["'{}'".format(arg) for arg in self.args])
        if args_repr:
            parts.append(args_repr)
        kwargs_repr = ', '.join(["{}='{}'".format(name, value)
                                 for name, value in self.kwargs.iteritems()])
        if kwargs_repr:
            parts.append(kwargs_repr)
        return ', '.join(parts)

    def __repr__(self):
        return ('<cache request method="%s" parameters="%s"'
                ' result="%s" duration=%.03f>') % (self.method, self.parameters,
                                                   self.result, self.duration)


def _record_requests(app):
    """Check if cache request recording is enabled"""
    rq = app.config.get('CACHE_RECORD_REQUESTS')
    if rq is not None:
        return rq
    return app.debug


def _calling_context(app_path):
    """Return calling context"""
    frm = sys._getframe(1)
    while frm.f_back is not None:
        name = frm.f_globals.get('__name__')
        if name and (name == app_path or name.startswith(app_path + '.')):
            funcname = frm.f_code.co_name
            return '%s:%s (%s)' % (frm.f_code.co_filename,
                                   frm.f_lineno,
                                   funcname)
        frm = frm.f_back
    return '<unknown>'


def get_debug_requests():
    """In debug mode Flask-Cache will log all the cache requests sent to the
    server. This information is available until the end of request. If you don't
    want to enable the DEBUG mode you can also enable the query recording by
    setting the CACHE_RECORD_REQUESTS config variable to `True`."""
    if hasattr(g, '_cache_debug_requests'):
        return g._cache_debug_requests
    else:
        return []

def log_debug_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        app = args[0].app or current_app

        if not _record_requests(app):
            return func(*args, **kwargs)

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        context = _calling_context(app.import_name)

        if not hasattr(g, '_cache_debug_requests'):
            g._cache_debug_requests = []

        g._cache_debug_requests.append(
            _CacheRequestInfo(func.__name__, args, kwargs, result,
                              start_time, end_time, context))

        return result
    return wrapper
