import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="autotrader",
    version="0.6.3",
    author="Kieran Mackle",
    author_email="kemackle98@gmail.com",
    license="gpl-3.0",
    description="A Python-based platform for developing, optimising and deploying automated trading systems.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://kieran-mackle.github.io/AutoTrader/",
    project_urls={
        "Bug Tracker": "https://github.com/kieran-mackle/AutoTrader/issues",
        "Source Code": "https://github.com/kieran-mackle/AutoTrader",
        "Documentation": "https://py-autotrader.readthedocs.io/en/latest/",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    keywords=["algotrading", "finance"],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.7",
    install_requires = [
        "numpy >= 1.20.3",
        "pandas >= 1.3.4",
        "pyfiglet >= 0.8.post1",
        "PyYAML",
        "bokeh >= 2.3.1",
        "scipy >= 1.7.1",
        "yfinance >= 0.1.67",
        "finta >= 1.3",
        "v20 >= 3.0.25.0",
        "ib_insync >= 0.9.70",
        "tqdm>=4.64.0",
        "importlib-resources",
        ],
    setup_requires=[
            "setuptools_git",
            "setuptools_scm",
        ],
    package_data={'': ['data/*.js']},
)
