import setuptools


if __name__ == "__main__":
    setuptools.setup(
        # Name of the project
        name='stempeg',

        # Version
        version='0.1.3',

        url='http://github.com/faroit/stempeg',

        download_url='http://github.com/faroit/stempeg',

        # Description
        description='Read and write stem multistream audio files',

        # Your contact information
        author='Fabian-Robert Stoeter',
        author_email='mail@faroit.com',

        # License
        license='MIT',

        # Packages in this project
        # find_packages() finds all these automatically for you
        packages=setuptools.find_packages(exclude=['tests']),

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

        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Telecommunications Industry',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Multimedia :: Sound/Audio :: Analysis',
            'Topic :: Multimedia :: Sound/Audio :: Sound Synthesis'
        ],
        zip_safe=True,

        entry_points={'console_scripts': [
            'stem2wav=stempeg:cli',
        ]}
    )
