# py_uboot_env

A Python package for reading, modifying, and writing U-Boot environment files.

## Installation

You can install the package from PyPI:

```bash
pip install py_uboot_env
```

Or directly from the repository:

```bash
pip install git+https://github.com/cubix-mx/py-uboot-env.git
```

## Usage

### As a Python Library

```python
from py_uboot_env import load_env

# Load an environment from a file
env = load_env("/path/to/u-boot.env")

# Get an environment variable
value = env.get("bootcmd")

# Set an environment variable
env.set("bootcmd", "run bootscript")

# Delete an environment variable
env.delete("unused_var")

# Save the environment back to a file
env.save("/path/to/u-boot.env")
```

### Command Line Tool

The package provides a command-line tool `uboot-env` with multiple subcommands:

- `edit`: Edit a U-Boot environment file with your default editor
- `dump`: Dump the contents of a U-Boot environment file
- `graph`: Generate a DOT graph of dependencies in the environment
- `get`: Get a specific variable from the environment
- `set`: Set a variable in the environment
- `delete`: Delete a variable from the environment

Example usage:

```bash
# Edit a U-Boot environment file
uboot-env edit /path/to/u-boot.env

# Dump a U-Boot environment file
uboot-env dump /path/to/u-boot.env

# Generate a DOT graph of dependencies
uboot-env graph /path/to/u-boot.env > env.dot

# Get a variable from the environment
uboot-env get /path/to/u-boot.env bootcmd

# Set a variable in the environment
uboot-env set /path/to/u-boot.env bootcmd "run bootscript"

# Delete a variable from the environment
uboot-env delete /path/to/u-boot.env unused_var
```

## License

This project is licensed under the terms of the MIT license.
