import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    # skip comments
    requirements = list(filter(lambda x: x and not x.startswith("#"), requirements))

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='pywiki',
    version='0.2.0',
    install_requires=requirements,
    packages=find_packages(),
    scripts=["wiki"],
    include_package_data=True,
    license='MIT License',
    description='A command line mediawiki client.',
    long_description=README,
    author='Pawel Suwala',
    author_email='pawel.suwala@gmail.com',
    classifiers=['Development Status :: 0.2 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 'License :: GPL License',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Internet :: WWW/HTTP',
                 ],
)
