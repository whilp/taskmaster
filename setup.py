from setuptools import setup

options = dict(
    name="taskmaster",
    version = "0.1",
    description="run tasks in parallel",
    author="Will Maier",
    author_email="willmaier@ml1.net",
    py_modules=["taskmaster"],
    test_suite="tests",
    use_2to3=True,
    keywords="parallel ssh distributed management",
    url="http://packages.python.org/taskmaster",
    entry_points={
        "console_scripts":
            ["tm = taskmaster:entry"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Natural Language :: English",
        "Programming Language :: Python",
        "#Programming Language :: Python :: 3",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Software Distribution",
        "Topic :: Utilities",
    ],
)

setup(**options)
