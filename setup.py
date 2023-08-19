from setuptools import setup

setup(
    name='sat_logic',
    url='https://github.com/ilijavorontsov/sat_logic',
    author='Ilija Vorontsov',
    author_email='ilija@vorontsov.cloud',
    packages=['sat_logic'],
    version='0.1',
    license='MIT',
    description='Logic objects, cadical SAT solvers and more.',
    long_description=open('README.md').read(),
    package_data={'sat_logic': ['bin/ccadical.so']},
)
