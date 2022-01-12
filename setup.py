from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

setup(
    name="gwwc-twitter-network",
    version="0.1",
    author="Faiz Surani, Tim Loderhose",
    description=("GWWC Twitter Network Analysis"),
    long_description=readme,
    url="https://github.com/ProbablyFaiz/gwwc-twitter-network",
    license=None,
    packages=["neta"],
)
