#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='grm',
    version='0.1.0',
    description='Git Release Manager - A CLI tool for managing Git releases',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='GRM Development Team',
    author_email='grm@example.com',
    url='https://github.com/example/grm',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'click>=8.0.0',
        'GitPython>=3.1.0',
        'colorama>=0.4.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-mock>=3.0.0',
            'pytest-cov>=2.0.0',
            'black>=21.0.0',
            'flake8>=3.8.0',
            'mypy>=0.800',
        ],
    },
    entry_points={
        'console_scripts': [
            'grm=grm.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Version Control :: Git',
    ],
    keywords='git release management versioning changelog',
)