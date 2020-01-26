# coding: utf-8
# compat: py3
from __future__ import absolute_import

import pytest
import re

import escalate


class Collector:
    """ Class to collect escalations.
    """
    def __init__(self):
        self.collection = []

    def escalate(self, ex, fn, args, kwargs):
        """ Use this as escalation mechanism. """
        self.collection.append((ex, fn, args, kwargs))


def a0_plus_ba(a, b):
    # add a[0] and b["a"], thus potentially raising IndexError on a[0],
    # KeyError on b["a"] (and a lot more!)
    return a[0] + b["a"]


def test_all_good():
    """ Just testing the function itself, as a sanity check.
    """
    a = [1]
    b = {"a": 2}
    result = a0_plus_ba(a, b)
    assert result == 3


def test_no_escalation():
    """ See that the decorator doesn't do any damage when everything goes well.
    """
    coll = Collector()
    a = [1]
    b = {"a": 2}
    result = escalate.escalate([KeyError], mechanism=coll.escalate)(a0_plus_ba)(a, b)
    assert result == 3
    assert len(coll.collection) == 0


def test_escalation():
    """ Test if escalate() correctly escalates a KeyError with no string matches.
    """
    coll = Collector()
    a = [1]
    b = {"b": 2}  # "b" instead of "a" will raise KeyError
    with pytest.raises(escalate.Escalate):
        result = escalate.escalate([KeyError], mechanism=coll.escalate)(a0_plus_ba)(a, b)
    assert len(coll.collection) == 1
    err = coll.collection[0]
    assert isinstance(err[0], KeyError)
    assert err[1] == "a0_plus_ba"
    assert err[2] == (a, b)
    assert err[3] == {}


def test_escalation_with_match():
    """ Test if escalate() correctly escalates a KeyError with matching repr() match.
    """
    coll = Collector()
    a = [1]
    b = {"b": 2}  # "b" instead of "a" will raise KeyError
    with pytest.raises(escalate.Escalate):
        result = escalate.escalate([KeyError], repr_match=re.compile(".*KeyError.*").match, mechanism=coll.escalate)(a0_plus_ba)(a, b)
    assert len(coll.collection) == 1
    err = coll.collection[0]
    assert isinstance(err[0], KeyError)
    assert err[1] == "a0_plus_ba"
    assert err[2] == (a, b)
    assert err[3] == {}


def test_nonescalated_error():
    """ A non-escalated error should just be passed on. We escalate KeyErrors, but
        the test will raise an IndexError, which we should see in the test.
    """
    coll = Collector()
    a = []  # empty list will raise IndexError
    b = {"a": 2}
    with pytest.raises(IndexError):
        result = escalate.escalate([KeyError], mechanism=coll.escalate)(a0_plus_ba)(a, b)
    assert len(coll.collection) == 0


def test_nonescalated_error_mismatch():
    """ Test if escalate() correctly passes a KeyError with a non-matching str() match.
    """
    coll = Collector()
    a = [1]
    b = {"b": 2}  # "b" instead of "a" will raise KeyError
    with pytest.raises(KeyError):
        result = escalate.escalate([KeyError], str_match=re.compile(".*IndexError.*").match, mechanism=coll.escalate)(a0_plus_ba)(a, b)
    assert len(coll.collection) == 0


def test_ignore_escalated_errors():
    """ See if the @ignore_escalated_errors decorator correctly disposes of escalated
        exceptions.
    """
    coll = Collector()
    a = [1]
    b = {"b": 2}  # "b" instead of "a" will raise KeyError
    result = escalate.ignore_escalated_errors(escalate.escalate([KeyError], mechanism=coll.escalate)(a0_plus_ba))(a, b)
    assert len(coll.collection) == 1
    assert result is None


def test_ignore_escalated_errors_without_errors():
    """ Make sure the @ignore_escalated_errors decorator doesn't corrupt correct
        function calls.
    """
    coll = Collector()
    a = [1]
    b = {"a": 2}
    result = escalate.ignore_escalated_errors(escalate.escalate([KeyError], mechanism=coll.escalate)(a0_plus_ba))(a, b)
    assert result == 3
    assert len(coll.collection) == 0
