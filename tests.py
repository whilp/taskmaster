import unittest

import taskmaster

from taskmaster import groups, targetrange

class BaseTest(unittest.TestCase):
    pass

class TestGroups(BaseTest):
    
    def test_basic(self):
        stream = iter("""
            [login]
            login01
            login02
            login03""".splitlines())
        result = groups(stream)

        self.assertEqual(result["login"], 
            set(["login01", "login02", "login03"]))

    def test_comments(self):
        stream = iter("""
            [a]
            b
            # c!!!
            d""".splitlines())
        result = groups(stream)

        self.assertEqual(result["a"], set(["b", "d"]))

    def test_default(self):
        stream = iter("""
            [login]
            login01
            login02
            login03""".splitlines())
        result = groups(stream, default="all")

        self.assertEqual(result["all"], 
            set(["login01", "login02", "login03"]))

    def test_exclude(self):
        stream = iter("""
            [login]
            login01
            login02
            login03
            -login02""".splitlines())
        result = groups(stream)

        self.assertEqual(result["login"], set(["login01", "login03"]))

    def test_include_groups(self):
        stream = iter("""
            [a]
            foo
            bar

            [b]
            |a
            """.splitlines())
        result = groups(stream)

        self.assertEqual(result["b"], set(["foo", "bar"]))

    def test_exclude_groups(self):
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
        result = groups(stream)

        self.assertEqual(result["c"], set(["baz"]))

    def test_multiple_runs(self):
        stream = iter("""
            [a]
            foo
            bar""".splitlines())
        result = groups(stream)

        stream = iter("""
            [b]
            spam
            |a""".splitlines())
        result = groups(stream, data=result)

        self.assertEqual(result["b"], set(["foo", "bar", "spam"]))

    def test_runtime_groups(self):
        stream = iter("""[a] baz""".split())
        data = groups(stream)
        stream = iter("""foo bar |a""".split())
        result = groups(stream, default="all", data=data)

        self.assertEquals(result["all"], set(['baz', 'foo', 'bar']))

    def test_undefined_group(self):
        stream = iter("""baz |a""".split())
        result = groups(stream, default="all")

        self.assertEquals(result["all"], set(["baz"]))

    def test_empty_intersection_group(self):
        stream = iter("""baz &a""".split())
        result = groups(stream, default="all")

        self.assertEquals(result["all"], set())

    def test_intersection_group(self):
        stream = iter("""[a] foo bar [b] foo baz [c] |a &b""".split())
        result = groups(stream, default="all")

        self.assertEquals(result["c"], set(["foo"]))

    def test_targetrange_notarange(self):
        result = targetrange("login01")

        self.assertEqual(result, ["login01"])
    
    def test_targetrange_quoted(self):
        result = targetrange('"login01"')

        self.assertEqual(result, ["login01"])

    def test_targetrange_range(self):
        result = targetrange("login[01:04]")

        self.assertEqual(result,
            ["login01", "login02", "login03", "login04"])

    def test_targetrange_badrange(self):
        result = targetrange("login01-")

        self.assertEqual(result, ["login01-"])

    def test_targetrange_uneven_widths(self):
        result = targetrange("login[:04]")

        self.assertEqual(result,
            ["login01", "login02", "login03", "login04"])
