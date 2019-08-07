#!/usr/bin/env python3

from setuptools import setup

setup(
	  name='bioexcel-cli',
      version='1.0.0',
      description='Bioexcel portal command line tool',
      url='https://github.com/EMBL-EBI-TSI/bioexcel-cli/',
      author='Felix Xavier Amaladoss',
      author_email='famaladoss@ebi.ac.uk',
      license='Apache License 2.0',
	  install_requires=[
		'wheel','PyJWT'
      ],
	  entry_points={
          'console_scripts': ["bioexcel-cli=bioexcel:run"]
      },
      packages=['.'],
	  python_requires='>=3.6',
      zip_safe=False
	  )
