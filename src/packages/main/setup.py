from setuptools import setup

setup(
    name='lektor-main',
    packages=['lektor_main'],
    entry_points={
        'lektor.plugins': [
            'main = lektor_main:MainPlugin',
        ]
    },
    author='relikd',
    version='0.1',
    description='Main code for this repository',
    license='MIT',
    python_requires='>=3.6',
    keywords=['lektor', 'plugin'],
    classifiers=[
        'Environment :: Plugins',
        'Framework :: Lektor',
    ],
)
