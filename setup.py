from __future__ import print_function
import os
import platform
import stat
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.command.install import install
from setuptools.command.sdist import sdist

with open(os.path.join(os.path.split(__file__)[0], 'LemonGraph', 'version.py')) as vf:
    exec(vf.read(), locals())

def fetch_external():
    try:
        return fetch_external.once
    except AttributeError:
        pass
    subprocess.check_call('make --no-print-directory deps'.split())
    setattr(fetch_external, 'once', None)

def Wrap(cls):
    class Wrapper(cls):
        def run(self):
            fetch_external()
            return cls.run(self)
    return Wrapper

def wrap(**classes):
    for label, cls in classes.items():
        classes[label] = Wrap(cls)
    return classes
#    return dict((cls.__module__.split('.')[-1], Wrap(cls)) for cls in classes)

with open('requirements.txt') as rh:
    reqs = [line.strip() for line in rh]
cffi, = [r for r in reqs if r.startswith('cffi')]

if platform.python_implementation() == 'CPython':
    reqs.append('ujson')

if __name__ == "__main__":
    setup(
        name='LemonGraph',
        maintainer='National Security Agency',
        maintainer_email='/dev/null',
        url='https://github.com/NationalSecurityAgency/lemongraph',
        version=VERSION,
        description='LemonGraph Database',
        packages=['LemonGraph', 'LemonGraph.server'],
        package_data={'LemonGraph': ['data/*']},
        install_requires=reqs,
        setup_requires=cffi,
        cffi_modules=['LemonGraph/cffi_stubs.py:ffi'],
        cmdclass=wrap(build_ext=build_ext, install=install, sdist=sdist))
