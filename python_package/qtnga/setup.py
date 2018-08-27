from setuptools import setup

about = {}
with open('./qtnga/__version__.py', 'r') as f:
    exec(f.read(), about)

with open('README.md', 'r') as f:
    readme = f.read()

tests_require = [
]

setup(
    name=about['__title__'],
    version=about['__version__'],
    packages=['qtnga'],
    url=about['__url__'],
    license=about['__license__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'PyQt5',
        'pynga>=2.1.4',
        'wrapt',
    ],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },
    python_requires='>=3.6',
)
