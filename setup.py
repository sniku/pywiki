import os
from setuptools import setup, find_packages

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    # skip comments
    requirements = list(filter(lambda x: x and not x.startswith("#"), requirements))

# allow setup.py to be run from any path

setup(
    name='pywiki',
    version='0.2.1',
    install_requires=requirements,
    packages=find_packages(),
    scripts=["wiki"],
    include_package_data=True,
    license='MIT License',
    description='A command line mediawiki client.',
    long_description=README,
    url="https://github.com/sniku/pywiki",
    author='Pawel Suwala',
    author_email='pawel.suwala@gmail.com',
    classifiers=['Environment :: Console',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Internet :: WWW/HTTP',
                 ],
)
