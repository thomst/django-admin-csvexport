#!/usr/bin/env python

import os
from pathlib import Path
from setuptools import setup
from setuptools import find_packages


def get_version():
    """Get the local package version."""
    namespace = {}
    path = Path("csvexport", "__version__.py")
    exec(path.read_text(), namespace)
    return namespace["__version__"]


def read(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding="utf-8") as file:
        return file.read()


version = get_version()
if 'dev' in version:
    dev_status = 'Development Status :: 3 - Alpha'
elif 'beta' in version:
    dev_status = 'Development Status :: 4 - Beta'
else:
    dev_status = 'Development Status :: 5 - Production/Stable'


setup(
    name="django-admin-csvexport",
    version=version,
    description="Django-admin-action to export items as csv-formatted data.",
    long_description=read("README.rst"),
    author="Thomas Leichtfuß",
    author_email="thomas.leichtfuss@posteo.de",
    url="https://github.com/thomst/django-admin-csvexport",
    license="BSD-2-Clause",
    platforms=["OS Independent"],
    packages=find_packages(include=['csvexport', 'csvexport.*']),
    package_data={'csvexport': ['static/**', 'templates/**'],},
    include_package_data=False,
    install_requires=[
        "Django>=2.2",
        "django-modeltree>=0.3",
    ],
    classifiers=[
        dev_status,
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6.0",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    zip_safe=True,
)
