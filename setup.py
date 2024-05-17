from setuptools import setup, find_packages

setup(
    name='scanner',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'scanner=scanner.cli:main',
        ],
    },
    install_requires=[
        'clang',
    ],
    setup_requires=[
        'black',
    ],
)
