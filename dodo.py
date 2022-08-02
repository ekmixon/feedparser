# This file is part of feedparser.
# Copyright 2020-2021 Kurt McKee <contactme@kurtmckee.org>
# Released under the BSD 2-clause license.

# The tasks defined in this file automates the entire
# development-to-release process.

import os
import pathlib
import random
import subprocess
import webbrowser

import colorama
import docutils.core
import doit.action


# Initialize colorama so that tox can output ANSI escape codes.
colorama.init()

DOIT_CONFIG = {'default_tasks': ['build', 'test']}
PROJECT = 'feedparser'

root = pathlib.Path(__file__).parent


def task_build():
    """Build the documentation.

    The documentation will be converted to HTML files to help double-check
    syntax and formatting on PyPI and on GitHub. Note that the HTML files
    will not be included in the distribution files.
    """

    def build_single_files():
        docutils.core.publish_cmdline(writer_name='html', argv=['README.rst', 'README.html'])

    return {
        'actions': [
            build_single_files,
            'sphinx-build -b html docs/ fpdocs',
        ],
        'verbosity': 2,
        'file_dep': [root / 'README.rst'] + list((root / 'docs').rglob('*.rst')),
        'targets': [root / 'README.html'],
    }


def task_test():
    """Run the unit tests."""

    env = dict(os.environ.items())
    env['PY_COLORS'] = '1'

    return {
        'actions': [
            doit.action.CmdAction('tox', env=env),
        ],
        'verbosity': 2,
    }


def remove_dist_files():
    """Erase existing files in the ``dist`` directory."""

    for file in (root / 'dist/').glob('*'):
        file.unlink()


def task_test_release():
    """Upload to test.pypi.org."""

    env = dict(os.environ.items()) | {
        'NAME_SUFFIX': ''.join(
            chr(i) for i in random.sample(range(0x61, 0x61 + 26), 10)
        ),
        'VERSION_SUFFIX': str(random.choice(range(1, 1000))),
    }

    return {
        'actions': [
            remove_dist_files,
            'poetry version prerelease',
            'poetry build',
            'poetry publish --repository testpypi',
            (webbrowser.open, [f'https://test.pypi.org/project/{PROJECT}']),
        ],
        'verbosity': 2,
    }


def validate_in_git_master_branch():
    """Validate that the repository is in the git master branch."""

    branch = subprocess.check_output('git rev-parse --abbrev-ref HEAD', shell=True)
    return branch.decode('utf8', errors='ignore').strip() == 'master'


def task_release():
    """Upload to pypi.org.

    This step must *always* be taken while in the git master branch.
    This is an enforced requirement.
    """

    return {
        'actions': [
            validate_in_git_master_branch,
            remove_dist_files,
            'poetry build',
            'poetry publish',
            (webbrowser.open, [f'https://pypi.org/project/{PROJECT}']),
        ],
        'verbosity': 2,
    }
