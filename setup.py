from setuptools import setup, find_packages

setup(
    name="intelligent-query-router",
    version="0.1.0",
    description="Intelligent SQL query router with automatic backend selection",
    author="Aarush Ghosh",
    author_email="a66ghosh@uwaterloo.ca",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "sqlglot>=20.0.0",
        "pyarrow>=14.0.0",
        "pandas>=2.0.0",
        "duckdb>=0.9.0",
        "polars>=0.19.0",
        "pyspark>=3.5.0",
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "irouter=irouter.cli.main:cli",
        ],
    },
)