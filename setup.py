# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='stempeg',
    version='0.1.7',
    description='Read and write stem multistream audio files',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/faroit/stempeg',
    author='Fabian-Robert Stoeter',
    author_email='mail@faroit.com',
    classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Telecommunications Industry',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Topic :: Multimedia :: Sound/Audio :: Analysis',
            'Topic :: Multimedia :: Sound/Audio :: Sound Synthesis'
    ],
    zip_safe=True,
    keywords='stems audio reader',
    packages=find_packages(exclude=['tests']),
    # Dependencies, this installs the entire Python scientific
    # computations stack
    install_requires=[
        'numpy>=1.6',
        'soundfile>=0.9.0'
    ],
    extras_require={
        'tests': [
            'pytest',
        ],
    },
    entry_points={'console_scripts': [
        'stem2wav=stempeg:cli',
    ]},
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/faroit/stempeg/issues',
    },
    include_package_data=True
)
