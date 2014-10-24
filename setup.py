#!/usr/bin/env python

import io
from setuptools import setup
from setuptools.command.test import test
import virtTrinity


class SelfTest(test):
    def run(self):
        print 'Testing'

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


long_description = read('README.md')


setup(
    name='virt-trinity',
    version=virtTrinity.__version__,
    url='http://github.com/Hao-Liu/virt-trinity/',
    license='GNU General Public License v2',
    author='Hao Liu',
    author_email='hliu@redhat.com',
    description='A fuzz test run random libvirt commands',
    long_description=long_description,
    platforms='any',

    scripts=['scripts/virt-trinity'],

    packages=['virtTrinity'],

    cmdclass={
        'test': SelfTest,
    },
)
