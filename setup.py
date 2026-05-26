import setuptools

setuptools.setup(
    name = 'terminalCanvas',
    version = '0.1.0',
    description = 'A module for creating a canvas and displaying text-based graphics in the terminal',
    author = 'RandomMaerks',
    author_email = 'rmforbusiness@gmail.com',
    url = 'https://github.com/RandomMaerks/terminalCanvas',
    license = 'GPLv3',
    license_files = ['LICENSE',],
    packages = setuptools.find_packages(),
    python_requires = '>=3.10',
    install_requires = ['pillow', 'numpy',],
    classifiers = [
        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Multimedia :: Graphics',
    ]
)