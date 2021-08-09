
from setuptools import setup, find_packages

setup(
      name='autotrader',
      version='0.0.13',
      author='Kieran Mackle',
      author_email='kemackle98@gmail.com',
      packages=find_packages(),
      url='https://kieran-mackle.github.io/AutoTrader/',
      project_urls={'Bug Tracker': 'https://github.com/kieran-mackle/AutoTrader/issues',
      }
      license='GPLv3',
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
