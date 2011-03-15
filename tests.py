import unittest

import taskmaster

from taskmaster import groups

class BaseTest(unittest.TestCase):
    pass

class TestGroups(BaseTest):
    
    def test_basic(self):
        stream = iter("""
            [login]
            login01
            login02
            login03""".split())
        result = groups(stream)

        self.assertEqual(result["login"], 
            set(["login01", "login02", "login03"]))

    def test_default(self):
        stream = iter("""
            [login]
            login01
            login02
            login03""".split())
        result = groups(stream, default="all")

        self.assertEqual(result["all"], 
            set(["login01", "login02", "login03"]))

    def test_exclude(self):
        stream = iter("""
            [login]
            login01
            login02
            login03
            -login02""".split())
        result = groups(stream)

        self.assertEqual(result["login"], set(["login01", "login03"]))

    def test_include_groups(self):
        stream = iter("""
            [a]
            foo
            bar

            [b]
            +a
            """.split())
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
            +b
            -a
            """.split())
        result = groups(stream)

        self.assertEqual(result["c"], set(["baz"]))

    def test_multiple_runs(self):
        stream = iter("""
            [a]
            foo
            bar""".split())
        result = groups(stream)

        stream = iter("""
            [b]
            spam
            +a""".split())
        result = groups(stream, data=result)

        self.assertEqual(result["b"], set(["foo", "bar", "spam"]))

    def test_runtime_groups(self):
        stream = iter("""[a] baz""".split())
        data = groups(stream)
        stream = iter("""foo bar +a""".split())
        result = groups(stream, default="all", data=data)

        self.assertEquals(result["all"], set(['baz', 'foo', 'bar']))

    def test_undefined_group(self):
        stream = iter("""baz +a""".split())
        result = groups(stream, default="all")

        self.assertEquals(result["all"], set(["baz"]))
