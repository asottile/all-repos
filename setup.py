from setuptools import find_packages
from setuptools import setup

setup(
    name='all_repos',
    description='Clone all your repositories and apply sweeping changes.',
    url='https://github.com/asottile/all-repos',
    version='0.1.0',
    author='Anthony Sottile',
    author_email='asottile@umich.edu',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=['requests'],
    packages=find_packages(exclude=('tests*',)),
    entry_points={'console_scripts': ['all-repos-clone=all_repos.clone:main']},
)
