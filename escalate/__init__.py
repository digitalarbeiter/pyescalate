# coding: utf-8
# compat: py3
from __future__ import absolute_import

""" Escalate errors via other means than crashing with an exception:

    import click
    import json

    from escalate import escalate, ignore_escalated_errors, print_warning

    @escalate([KeyError, ValueError], mechanism=print_warning)
    def do_some_work(a, b):
        return a[0] + b["a"]

    @click.command()
    @click.option("--a")
    @click.option("--b")
    @ignore_escalated_errors
    def cli(a, b):
        a = json.loads(a)
        b = json.loads(b)
        do_some_work(a, b)
"""

class Escalate(BaseException):
    """ This exception is raised instead of escalated exceptions, and ignored
        via the @ignore_escalated_errors decorator.

        String conversions provided in case someone chooses to not ignore the
        already escalated exception.
    """
    def __init__(self, root_cause):
        self.root_cause = root_cause

    def __str__(self):
        return str(self.root_cause)

    def __repr__(self):
        return repr(self.root_cause)


def escalate(exceptions, repr_match=None, str_match=None, mechanism=None):
    """ Intercept certain exceptions and escalate them.

        A match function is a function that is given a string and then decides is this
        matches the intended escalation path, returning something True-ish if this is
        the case. A convenient match function would be `re.compile(...).match`.

        A report function is a function that reports the exception, thus escalating
        it in some way. It could send an email or a text message to on-call personell.
        It gets called with four parameters:
         * the exception that caused it to be called
         * the name of the decorated function
         * the args and the kwargs of the function call

        @param exceptions (list of classes)
        @param repr_match (match function, default None) if given, must match repr(ex).
        @param str_match (match function, default None) if given, must match str(ex).
        @param mechanism (report function, default None) how to escalate the exception.
    """
    def _escalate_f(f):
        def _escalate(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as ex:
                if type(ex) in exceptions:
                    if (
                        not repr_match and not str_match
                    ) or (
                        repr_match and repr_match(repr(ex))
                    ) or (
                        str_match and str_match(str(ex))
                    ):
                        if mechanism:
                            mechanism(ex, f.__name__, args, kwargs)
                        raise Escalate(ex)
                raise
        return _escalate
    return _escalate_f


def ignore_escalated_errors(f):
    """ Decorator that silences any escalated error.
        Use this to decorate your main/cli function.
    """
    def _ignore_escalated_errors(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Escalate:
            return None
    return _ignore_escalated_errors


def print_warning(ex, fn, args, kwargs):
    """ Escalate mechanism: print a warning. Pass this as escalate(mechanism=...)
    """
    print("Warning: {}(args={}, kwargs={}) raised {}".format(fn, args, kwargs, ex))
