from __future__ import print_function

import json
import os
import os.path
import re
import sys
import warnings

from collections import defaultdict
from distutils.command.build_scripts import build_scripts as BuildScripts
from distutils.command.sdist import sdist as SDist

try:
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py as BuildPy
    from setuptools.command.install_lib import install_lib as InstallLib
    from setuptools.command.install_scripts import install_scripts as InstallScripts
except ImportError:
    print("HSuite needs setuptools in order to build. Install it using your package manager (usually python-setuptools) or via pip (pip install setuptools).", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, os.path.abspath('lib'))
from hsuite.release import __version__, __author__


SYMLINK_CACHE = 'SYMLINK_CACHE.json'


def _find_symlinks(topdir, extension=''):
    """
    Find symlinks that should be maintained
    Maintained symlinks exist in the bin dir or are modules which have
    aliases.  Our heuristic is that they are a link in a certain path which
    point to a file in the same directory.
    .. warn::
        We want the symlinks in :file:`bin/` that link into :file:`lib/hsuite/*` (currently,
        :command:`hsuite`) to become
        real files on install.  Updates to the heuristic here *must not* add them to the symlink
        cache.
    """

    symlinks = defaultdict(list)
    for base_path, dirs, files in os.walk(topdir):
        for filename in files:
            filepath = os.path.join(base_path, filename)
            if os.path.islink(filepath) and filename.endswith(extension):
                target = os.readlink(filepath)
                if target.startswith('/'):
                    continue

                if os.path.dirname(target) == '':
                    link = filepath[len(topdir):]
                    if link.startswith('/'):
                        link = link[1:]
                    symlinks[os.path.basename(target)].append(link)
                else:
                    levels_deep = os.path.dirname(filepath).count('/')
                    target_depth = 0

                    for path_component in target.split('/'):
                        if path_component == '..':
                            target_depth += 1
                            if target_depth >= levels_deep:
                                break
                        else:
                            target_depth -= 1
                    else:
                        link = filepath[len(topdir):]
                        if link.startswith('/'):
                            link = link[1:]
                        symlinks[target].append(link)

    return symlinks


def _cache_symlinks(symlink_data):
    with open(SYMLINK_CACHE, 'w') as f:
        json.dump(symlink_data, f)


def _maintain_symlinks(symlink_type, base_path):
    """Switch a real file into a symlink."""

    try:
        with open(SYMLINK_CACHE, 'r') as f:
            symlink_data = json.load(f)
    except (IOError, OSError) as e:
        if e.errno == 2:
            library_symlinks = _find_symlinks('lib', '.py')
            symlink_data = {'script': _find_symlinks(
                'bin'), 'library': library_symlinks}
        else:
            raise

    symlinks = symlink_data[symlink_type]

    for source in symlinks:
        for dest in symlinks[source]:
            dest_path = os.path.join(base_path, dest)
            if not os.path.islink(dest_path):
                try:
                    os.unlink(dest_path)
                except OSError as e:
                    if e.errno == 2:
                        pass

                os.symlink(source, dest_path)


class BuildPyCommand(BuildPy):
    def run(self):
        BuildPy.run(self)
        _maintain_symlinks('library', self.build_lib)


class BuildScriptsCommand(BuildScripts):
    def run(self):
        BuildScripts.run(self)
        _maintain_symlinks('script', self.build_dir)


class InstallLibCommand(InstallLib):
    def run(self):
        InstallLib.run(self)
        _maintain_symlinks('library', self.install_dir)


class InstallScriptsCommand(InstallScripts):
    def run(self):
        InstallScripts.run(self)
        _maintain_symlinks('script', self.install_dir)


class SDistCommand(SDist):
    def run(self):
        library_symlinks = _find_symlinks('lib', '.py')
        symlinks = {'script': _find_symlinks(
            'bin'), 'library': library_symlinks}
        _cache_symlinks(symlinks)
        SDist.run(self)


def read_file(file_name):
    """Read file and return its contents."""

    with open(file_name, 'r') as f:
        return f.read()


def read_requirements(file_name):
    """Read requirements file as a list."""

    reqs = read_file(file_name).splitlines()
    if not reqs:
        raise RuntimeError(
            "Unable to read requirements from the %s file That indicates this copy of the source code is incomplete." % file_name)
    return reqs


def get_dynamic_setup_params():
    """Add dynamically calculated setup params to static ones."""

    return {
        'long_description': read_file('README.md'),
        'install_requires': read_requirements('requirements.txt'),
    }


static_setup_params = dict(
    cmdclass={
        'build_py': BuildPyCommand,
        'build_scripts': BuildScriptsCommand,
        'install_lib': InstallLibCommand,
        'install_scripts': InstallScriptsCommand,
        'sdist': SDistCommand,
    },
    name="hsuite",
    version=__version__,
    description="HSuite is a toolset for pentest",
    author=__author__,
    author_email="placidina@protonmail.com",
    project_urls={
        'Bug Tracker': "https://github.com/Placidina/hsuite/issues",
        'Source Code': "https://github.com/Placidina/hsuite",
    },
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    include_package_data=True,
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Programming Language:: Python:: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: System :: Installation/Setup",
        "Topic :: Utilities",
    ],
    scripts=[
        'bin/hsuite-s3dump',
    ],
    data_files=[],
    zip_safe=False
)


def main():
    """Invoke installation process using setuptools."""

    setup_params = dict(static_setup_params, **get_dynamic_setup_params())
    ignore_warning_regex = (
        r"Unknown distribution option: '(project_urls|python_requires)'"
    )
    warnings.filterwarnings(
        'ignore',
        message=ignore_warning_regex,
        category=UserWarning,
        module='distutils.dist',
    )
    setup(**setup_params)
    warnings.resetwarnings()


if __name__ == '__main__':
    main()
