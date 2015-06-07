from setuptools import setup, find_packages

install_requires = [
    "requests",
    "ws4py",
]

tests_require = [
    "nose >= 1.0",
    "coverage",
]

setup(
    name = "plugdj",
    version = "0.2",

    install_requires = install_requires,
    tests_require = tests_require,

    packages = find_packages(),
    test_suite = "nose.collector"
)
