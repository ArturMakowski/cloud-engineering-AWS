<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of Contents

- [aws-python](#aws-python)
  - [Quick start](#quick-start)
  - [Developing/Contributing](#developingcontributing)
    - [System requirements](#system-requirements)
    - [Installing the dev dependencies](#installing-the-dev-dependencies)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# aws-python

## Quick start

```bash
pip install aws-python
```

```python
from fastapi import ...
```

## Developing/Contributing

### System requirements

You will need the following installed on your machine to develop on this codebase

- `make` AKA `cmake`, e.g. `sudo apt-get update -y; sudo apt-get install cmake -y`
- Python 3.7+, ideally using `pyenv` to easily change between Python versions
- `git`

### Installing the dev dependencies

```bash
# clone the repo
git clone https://github.com/<your github username>/aws-python.git

# install the dev dependencies
make install

# run the tests
make test
```
