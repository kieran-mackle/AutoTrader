
from setuptools import setup, find_packages

setup(
      name='autotrader',
      version='0.0.12',
      author='Kieran Mackle',
      author_email='kemackle98@gmail.com',
      packages=find_packages(),
      url='https://pypi.org/project/autotrader/',
      license='LICENSE',
      description='A Python-based platform for developing, optimising and deploying automated trading systems.',
      long_description=open('README.md').read(),
      install_requires=[
          "pandas",
          "yfinance",
          "pyfiglet",
          "PyYAML",
          "v20",
          "bokeh",
          "plotly"
          ],
      )