import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='autotrader',
    version='0.2.6',
    author='Kieran Mackle',
    author_email='kemackle98@gmail.com',
    description="A Python-based platform for developing, optimising and deploying automated trading systems.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://kieran-mackle.github.io/AutoTrader/',
    project_urls={
        "Bug Tracker": "https://github.com/kieran-mackle/AutoTrader/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.6",
    install_requires = [
        "pandas",
        "pyfiglet",
        "PyYAML",
        "bokeh >= 2.3.1",
        ],
    setup_requires=[
            'setuptools_git',
            'setuptools_scm',
        ],
    package_data={'': ['*.js']},
    include_package_data=True,
)
