# Installation

nzssdt-2023 requires Python, and at the time of writing supports the following versions:

[![python](https://img.shields.io/pypi/pyversions/nzssdt-2023.svg)](https://pypi.org/project/nzssdt-2023/)

For easy package installation, either [pip][] or [poetry][] is recommended.

## Stable release

A stable release of the Solvis package can be installed from the Python Package
Index (PyPI).


### Using pip

```console
$ pip install nzssdt-2023
```

### Adding to a poetry project

```console
$ poetry add nzssdt-2023
```

## From source code

The source code for `nzssdt-2023` can be downloaded from the [Github repository][].

You can clone down the public repository with:

```console
$ git clone https://github.com/GNS-Science/nzssdt-2023.git
```

Once you have a copy of the source, you can install the package into your
Python environment:

```console
$ pip install .
```

Or with Poetry (using `--all-extras` to install all extra dependencies is
recommended for development):
```console
$ poetry install --all-extras
```

[poetry]: https://python-poetry.org/
[pip]: https://pip.pypa.io
[Python installation guide]: http://docs.python-guide.org/en/latest/starting/installation/
[Github repository]: https://github.com/GNS-Science/nzssdt-2023
