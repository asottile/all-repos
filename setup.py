from setuptools import find_packages
from setuptools import setup

setup(
    name='all_repos',
    description='Clone all your repositories and apply sweeping changes.',
    url='https://github.com/asottile/all-repos',
    version='1.9.0',
    author='Anthony Sottile',
    author_email='asottile@umich.edu',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=['identify'],
    packages=find_packages(exclude=('tests*', 'testing*')),
    entry_points={
        'console_scripts': [
            'all-repos-clone=all_repos.clone:main',
            'all-repos-complete=all_repos.complete:main',
            'all-repos-find-files=all_repos.find_files:main',
            'all-repos-grep=all_repos.grep:main',
            'all-repos-list-repos=all_repos.list_repos:main',
            'all-repos-manual=all_repos.manual:main',
            'all-repos-sed=all_repos.sed:main',
        ],
    },
)
