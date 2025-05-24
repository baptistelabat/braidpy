# BraidPy

A Python library for working with braids.

## Features

- [x] Representation of braids
- [x] Braid operations and manipulations
- [x] Visualization capabilities
- [x] Mathematical properties and computations
- [] unreduced Burau matrix representation
- [] reduced Burau matrix representation
- [] Alexaner polynomial

## Usage

```python
from braidpy import Braid

# Create a braid
b = Braid([1, 2, -1])

# Perform operations
result = b * b.inverse()
```


## 🛠️ Installation
You can download the code directly from GitHub or using git:

```bash
git clone git@github.com:baptistelabat/braidpy.git
```

To install the required dependencies, follow the steps below:

1. Install `uv` by following the official [installation guide](https://docs.astral.sh/uv/getting-started/installation).
2. Alternatively, run the command from root of repository:  
   ```bash
   cd braidpy
   make install-uv
   ```

---

## Test
To launch the complete suite of tests, launch the following command:
```bash
uv run pytest tests
```
Alternatively, if you have make install, just run:
   ```bash
   make test
   ```


---

## 📜 Documentation
Documentation is available at:
https://braidpy.readthedocs.io/en/latest/

### Project Team:
Human: 
- **Baptiste Labat**
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?logo=linkedin&logoWidth=20&style=flat-square)](https://www.linkedin.com/in/baptiste-labat-01751138/)
[![GitHub](https://img.shields.io/badge/-GitHub-black?logo=github&logoWidth=20&style=flat-square)](https://github.com/baptistelabat)

Bot:
chatgpt
windsurf
---

## 🤝 Contributions

Contributions are welcome! Please open an issue or submit a pull request to suggest changes, report bugs, or propose new features.

Here are a few code guidelines:  
- We use english for code and comments.
- We use google style docstring.
- We use type hinting.  
Please be sure to install the pre-commit tool in order to check your code while commiting in order to keep a clean project history.
```bash
pre-commit install
```
Please have a look to makefile to find helpful commands.

## 📜 License
![License](https://img.shields.io/badge/license-MPL%202.0-brightgreen)

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](./LICENSE) file for details.

---

## 🖇️ References
https://dehornoy.lmno.cnrs.fr