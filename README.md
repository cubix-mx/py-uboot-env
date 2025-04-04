# py-uboot-env

A Python package for manipulating U-Boot environment files with a modern API and convenient CLI tools.

[![PyPI version](https://img.shields.io/pypi/v/py-uboot-env.svg)](https://pypi.org/project/py-uboot-env/)
[![License](https://img.shields.io/github/license/cubix-mx/py-uboot-env.svg)](https://github.com/cubix-mx/py-uboot-env/blob/main/LICENSE)

## Overview

`py-uboot-env` provides functionality to read, modify, and write U-Boot environment files. It features both a programmer-friendly API and a versatile command-line interface.

### Features

- Command-line interface for common operations
- Support for both file paths and file handles
- Environment variable dependency analysis and visualization
- Built-in environment editor with your system's default text editor

## Installation

Install from PyPI:

```bash
pip install py-uboot-env
```

## API Usage

### Basic Usage

```python
from py_uboot_env import load_env

# Load an environment file
env = load_env('/path/to/uboot.env')

# Read values
bootcmd = env.get('bootcmd')
bootdelay = env.get('bootdelay', '3')  # With default value

# Modify values
env.set('bootdelay', '5')
env.delete('unused_var')

# Save changes
env.save('/path/to/uboot.env')
```

### Working with File Handles

```python
from py_uboot_env import load_env, dump_env
import io

# Create an in-memory file-like object
buffer = io.BytesIO()

# Create a new environment and save it to the buffer
env = load_env(existing_env_file)
env.set('new_variable', 'value')
dump_env(env, buffer)

# Rewind the buffer and read it back
buffer.seek(0)
updated_env = load_env(buffer)
```

## Command-Line Interface

`py-uboot-env` provides a single `uboot-env` command with multiple actions:

### Viewing Environment Variables

```bash
# Dump the entire environment
uboot-env dump /path/to/uboot.env

# Get a specific variable
uboot-env get /path/to/uboot.env bootcmd
```

### Modifying Environment Variables

```bash
# Set a variable
uboot-env set /path/to/uboot.env bootdelay 5

# Delete a variable
uboot-env delete /path/to/uboot.env unused_var
```

### Interactive Editing

Open the environment file in your default text editor:

```bash
uboot-env edit /path/to/uboot.env
```

### Dependency Analysis

Generate a GraphViz DOT representation of variable dependencies:

```bash
# Generate DOT output
uboot-env graph /path/to/uboot.env > uboot-deps.dot

# Generate a PDF using GraphViz (if installed)
uboot-env graph /path/to/uboot.env | dot -Tpdf -o uboot-deps.pdf
```

This analyzes which environment variables are read from, written to, or which commands are run by each variable, creating a visual dependency graph.

## Environment File Format

The package handles U-Boot environment files in their standard binary format, including:

- CRC32 checksums in the header
- Support for different environment sizes
- Proper handling of redundant environment blocks

## Development

### Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under The Unlicense - see the LICENSE file for details.

## Acknowledgments

- [U-Boot Project](https://www.denx.de/wiki/U-Boot)
- [Original code by Dave Jones](https://gist.github.com/waveform80/62f3cc34dc87b8c26e6febc7f28c404e) which served as the foundation for this package
