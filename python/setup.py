from setuptools import setup, find_packages
import datetime
import os

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
RAIN_DIR = os.path.dirname(PYTHON_DIR)


def load_cargo_version():
    try:
        with open(os.path.abspath(os.path.join(RAIN_DIR, "Cargo.toml"))) as f:
            import re
            exp = re.compile('^version = "([^"]*)"$')
            for line in f:
                m = exp.search(line)
                if m:
                    return m.groups()[0]
    except:
        return "0.0"


def load_version():
    if "RAIN_VERSION" in os.environ and os.environ["RAIN_VERSION"]:
        return os.environ["RAIN_VERSION"]
    else:
        return load_cargo_version()


with open('requirements.txt') as reqs:
    requirements = [line for line in reqs.read().split('\n') if line]

now = datetime.datetime.now()

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='rain-python',
      version=load_version(),
      description='Distributed Computational Framework',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/substantic/rain',
      author='Stanislav Bohm, Vojtech Cima, Tomas Gavenciak',
      author_email='rain@substantic.net',
      license='MIT',
      packages=find_packages(),
      package_data={'rain': ['capnp/*.capnp']},
      install_requires=requirements)
