import unittest

import taskmaster

from taskmaster import StringSets

class BaseTest(unittest.TestCase):
    pass

class TestStringSets(BaseTest):

    def test_init(self):
        sets = StringSets()

        self.assertEqual(sets.sets, None)

    def test_expand(self):
        sets = StringSets()

        result = {}
        sets.expand("name", "foo", result)

        self.assertEqual(result, {"name": set(["foo"])})

    def test_expand_operator(self):
        sets = StringSets()

        result = {}
        sets.expand("name", "*foo", result)

        self.assertEqual(result, {})

    def test_range_invalid(self):
        result = StringSets.range("login01")

        self.assertEqual(result, ["login01"])
    
    def test_range_quoted(self):
        result = StringSets.range('"login01"')

        self.assertEqual(result, ["login01"])

    def test_range_range(self):
        result = StringSets.range("login[01:04]")

        self.assertEqual(result,
            ["login01", "login02", "login03", "login04"])

    def test_range_badrange(self):
        result = StringSets.range("login01-")

        self.assertEqual(result, ["login01-"])

    def test_range_uneven_widths(self):
        result = StringSets.range("login[:04]")

        self.assertEqual(result,
            ["login01", "login02", "login03", "login04"])

    def test_range_noninclusive(self):
        result = StringSets.range("foo[:04]", inclusive=False)

        self.assertEqual(result, ["foo01", "foo02", "foo03"])

    def test_getvalue(self):
        class Spec(object): pass
        spec = Spec()
        spec.attr = 1
        result = StringSets.getvalue(spec, "attr", 0)

        self.assertEqual(result, 1)

    def test_getvalue_missing(self):
        result = StringSets.getvalue(object(), "foo", "1")

        self.assertEqual(result, 1)
