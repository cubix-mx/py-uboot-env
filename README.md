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

### Testing

The package includes a comprehensive test suite to ensure functionality and reliability.

#### Running Tests Locally

To run the test suite locally, first install pytest:

```bash
pip install pytest
```

Then run the tests:

```bash
python -m pytest
```

For more detailed output, use the verbose flag:

```bash
python -m pytest -v
```

#### Continuous Integration

This project uses GitHub Actions for continuous integration testing:

- Tests automatically run on every push and pull request
- Tests run on multiple operating systems (Linux, Windows, macOS)
- Tests run across multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Every release requires all tests to pass before publication to PyPI

#### Test Coverage

The test suite covers:

- **Core Functionality**: Tests for the `UBootEnv` class methods (`get`, `set`, `delete`, `save`) and utility functions (`load_env`, `dump_env`, `format_env`).
- **Error Handling**: Tests for handling invalid environment sizes and CRC errors.
- **CLI Commands**: Tests for all environment manipulation commands (`dump`, `get`, `set`, `delete`, `edit`).
- **Integration Tests**: End-to-end workflows for both API and CLI usage patterns.

### Publishing to PyPI

This package uses GitHub Actions to automatically publish to PyPI when a new release is created. To publish a new version:

1. Update the version number in `pyproject.toml`
2. Merge your changes to the `main` branch
3. Create a new [GitHub Release](https://github.com/cubix-mx/py-uboot-env/releases/new) with a tag that matches the version (e.g., `v1.1.3`)

**Important Notes:**
- The version in `pyproject.toml` MUST be updated before creating a release tag, or PyPI will reject the publication.
- The GitHub Action workflow will only publish to PyPI when a tag is pushed, not on regular commits.
- The version tag should match the version in `pyproject.toml`.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under The Unlicense - see the LICENSE file for details.

## Acknowledgments

- [U-Boot Project](https://www.denx.de/wiki/U-Boot)
- [Original code by Dave Jones](https://gist.github.com/waveform80/62f3cc34dc87b8c26e6febc7f28c404e) which served as the foundation for this package
