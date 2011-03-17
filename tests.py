import unittest

import taskmaster

from taskmaster import StringSets

class BaseTest(unittest.TestCase):
    pass

class TestStringSets(BaseTest):
    
    def test_basic(self):
        stream = iter("""
            [login]
            login01
            login02
            login03""".splitlines())
        result = StringSets().parse(stream)

        self.assertEqual(result["login"], 
            set(["login01", "login02", "login03"]))

    def test_comments(self):
        stream = iter("""
            [a]
            b
            # c!!!
            d""".splitlines())
        result = StringSets().parse(stream)

        self.assertEqual(result["a"], set(["b", "d"]))

    def test_default(self):
        stream = iter("""
            [login]
            login01
            login02
            login03""".splitlines())
        result = StringSets(default="all").parse(stream)

        self.assertEqual(result["all"], 
            set(["login01", "login02", "login03"]))

    def test_exclude(self):
        stream = iter("""
            [login]
            login01
            login02
            login03
            -login02""".splitlines())
        result = StringSets().parse(stream)

        self.assertEqual(result["login"], set(["login01", "login03"]))

    def test_include_setstream(self):
        stream = iter("""
            [a]
            foo
            bar

            [b]
            |a
            """.splitlines())
        result = StringSets().parse(stream)

        self.assertEqual(result["b"], set(["foo", "bar"]))

    def test_exclude_setstream(self):
        stream = iter("""
            [a]
            foo
            bar

            [b]
            foo
            bar
            baz

            [c]
            |b
            -a
            """.splitlines())
        result = StringSets(stream).parse(stream)

        self.assertEqual(result["c"], set(["baz"]))

    def test_multiple_runs(self):
        sets = StringSets()
        stream = iter("""
            [a]
            foo
            bar""".splitlines())
        sets.parse(stream)

        stream = iter("""
            [b]
            spam
            |a""".splitlines())
        result = sets.parse(stream)

        self.assertEqual(result["b"], set(["foo", "bar", "spam"]))

    def test_runtime_setstream(self):
        sets = StringSets(default="all")
        stream = iter("""[a] baz""".split())
        sets.parse(stream)
        stream = iter("""foo bar |a""".split())
        result = sets.parse(stream)

        self.assertEquals(result["all"], set(['baz', 'foo', 'bar']))

    def test_undefined_setstream(self):
        stream = iter("""baz |a""".split())
        result = StringSets(default="all").parse(stream)

        self.assertEquals(result["all"], set(["baz"]))

    def test_empty_intersection_setstream(self):
        stream = iter("""baz &a""".split())
        result = StringSets(default="all").parse(stream)

        self.assertEquals(result["all"], set())

    def test_intersection_setstream(self):
        stream = iter("""[a] foo bar [b] foo baz [c] |a &b""".split())
        result = StringSets(default="all").parse(stream)

        self.assertEquals(result["c"], set(["foo"]))

    def test_difference_setstream(self):
        stream = iter("""[a] foo bar [b] foo baz [c] |a ^b""".split())
        result = StringSets(default="all").parse(stream)
        
        self.assertEquals(result["c"], set(["baz", "bar"]))

    def test_alternate_setstream_syntax(self):
        stream = iter("""[a] foo bar [b] foo baz [c] +a *b""".split())
        result = StringSets(default="all").parse(stream)

        print result

        self.assertEquals(result["c"], set(["foo"]))

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

    def test_getvalue_missing(self):
        result = StringSets.getvalue(object(), "foo", "1")

        self.assertEqual(result, 1)
