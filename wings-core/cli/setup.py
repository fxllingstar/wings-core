from setuptools import setup

setup(
    name='wings-core',
    version='0.1.1',
    py_modules=['wings_core'], # This looks for wings_core.py
    install_requires=[
        'requests',
        'flask',
    ],
    entry_points={
        'console_scripts': [
            'wings-core=wings_core:main', # This creates the wings-core command
        ],
    },
)