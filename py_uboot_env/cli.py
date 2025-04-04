#!/usr/bin/python3
"""
Command line interface for U-Boot environment tools.

Provides commands for editing, dumping, and analyzing U-Boot environment files.
"""

import os
import sys
import re
import io
import argparse
import tempfile
import subprocess
from textwrap import indent
from itertools import chain
from collections import defaultdict
from typing import Dict, Set, List, Optional, Union, Any, Tuple

from .uboot_env import UBootEnv, load_env, dump_env, format_env


def main(args=None):
    """Main entry point for the command line interface."""
    if args is None:
        args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        description="U-Boot environment file manipulation tool",
        prog="uboot-env"
    )
    
    # Create subparsers for different actions
    subparsers = parser.add_subparsers(
        dest='action',
        help='Action to perform',
        required=True
    )
    
    # Edit command
    edit_parser = subparsers.add_parser(
        'edit', 
        help='Edit a U-Boot environment file with your default editor'
    )
    edit_parser.add_argument(
        'filename', 
        help="The U-Boot environment file to edit"
    )
    
    # Dump command
    dump_parser = subparsers.add_parser(
        'dump', 
        help='Dump the contents of a U-Boot environment file'
    )
    dump_parser.add_argument(
        'filename', 
        help="The U-Boot environment file to dump"
    )
    
    # Graph command
    graph_parser = subparsers.add_parser(
        'graph', 
        help='Generate a DOT graph of dependencies in the environment'
    )
    graph_parser.add_argument(
        'filename', 
        help="The U-Boot environment file to graph"
    )
    
    # Get command
    get_parser = subparsers.add_parser(
        'get', 
        help='Get a specific variable from the environment'
    )
    get_parser.add_argument(
        'filename', 
        help="The U-Boot environment file"
    )
    get_parser.add_argument(
        'variable', 
        help="The variable name to get"
    )
    
    # Set command
    set_parser = subparsers.add_parser(
        'set', 
        help='Set a variable in the environment'
    )
    set_parser.add_argument(
        'filename', 
        help="The U-Boot environment file"
    )
    set_parser.add_argument(
        'variable', 
        help="The variable name to set"
    )
    set_parser.add_argument(
        'value', 
        help="The value to set"
    )
    
    # Delete command
    delete_parser = subparsers.add_parser(
        'delete', 
        help='Delete a variable from the environment'
    )
    delete_parser.add_argument(
        'filename', 
        help="The U-Boot environment file"
    )
    delete_parser.add_argument(
        'variable', 
        help="The variable name to delete"
    )
    
    config = parser.parse_args(args)
    
    try:
        # All commands require loading the environment first
        env = load_env(config.filename)
        
        if config.action == 'edit':
            env = edit_env(env)
            dump_env(env, config.filename)
            print(f"Environment saved to {config.filename}")
        
        elif config.action == 'dump':
            print(format_env(env))
        
        elif config.action == 'graph':
            print(dot_env(env))
        
        elif config.action == 'get':
            value = env.get(config.variable)
            if value is None:
                print(f"Variable '{config.variable}' not found in environment", file=sys.stderr)
                return 1
            print(value)
        
        elif config.action == 'set':
            env.set(config.variable, config.value)
            dump_env(env, config.filename)
            print(f"Variable '{config.variable}' set to '{config.value}'")
            print(f"Environment saved to {config.filename}")
        
        elif config.action == 'delete':
            if config.variable not in env.content:
                print(f"Variable '{config.variable}' not found in environment", file=sys.stderr)
                return 1
            env.delete(config.variable)
            dump_env(env, config.filename)
            print(f"Variable '{config.variable}' deleted")
            print(f"Environment saved to {config.filename}")
        
    except Exception as exc:
        if int(os.environ.get('DEBUG', '0')):
            raise
        print(str(exc), file=sys.stderr)
        return 1
    else:
        return 0


def edit_env(env: UBootEnv) -> UBootEnv:
    """
    Edit a U-Boot environment using an external editor.
    
    Args:
        env: UBootEnv object to edit
        
    Returns:
        UBootEnv: The edited environment
        
    Raises:
        RuntimeError: If the editor exits with a non-zero code
    """
    with tempfile.NamedTemporaryFile('w+', encoding='ascii') as f:
        f.write(format_env(env))
        f.flush()
        try:
            subprocess.run(['editor', f.name], check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("Editor exited with non-zero code; "
                               "leaving env alone")
        f.seek(0)
        content = {}
        for entry in f.read().strip().split('\n'):
            if '=' in entry:
                key, value = entry.split('=', 1)
                content[key] = value
        
        return UBootEnv(content=content, env_size=env.env_size, header_size=env.header_size)


def dot_env(env: UBootEnv) -> str:
    """
    Generate a GraphViz DOT representation of dependencies in the environment.
    
    Args:
        env: UBootEnv object to analyze
        
    Returns:
        str: The DOT representation
    """
    reads: Dict[str, Set[str]] = {}
    writes: Dict[str, Set[str]] = {}
    runs: Dict[str, List[Set[str]]] = {}
    
    parse_key(env, 'bootcmd', reads, writes, runs)
    
    return """\
digraph env {{
    graph [rankdir=TB];
    node [fontname="Arial", fontsize=10];
    edge [fontname="Arial", fontsize=10];
    /* Vars */
    node [style=filled, color="#2fa6da"];
{vars}
    /* Commands */
    node [shape=rect, style="filled,rounded", color="#ff5733"];
{commands}
    /* Reads */
    edge [color="#2fa6da"];
{reads}
    /* Writes */
    edge [color="#ff5733"];
{writes}
    /* Runs */
    edge [color="#66cc66"];
{runs}
}}""".format(
        vars=indent('\n'.join(
            '"{key}";'.format(key=key)
            for key in sorted(chain(
                reads.keys(), reads.values(),
                writes.keys(), writes.values()))
        ), prefix=' '*4),
        commands=indent('\n'.join(
            '"{key}";'.format(key=key)
            for key in runs
        ), prefix=' '*4),
        reads=indent('\n'.join(
            '"{target}"->"{key}";'.format(target=target, key=key)
            for key, targets in reads.items()
            for target in targets
        ), prefix=' '*4),
        writes=indent('\n'.join(
            '"{key}"->"{target}";'.format(target=target, key=key)
            for key, targets in writes.items()
            for target in targets
        ), prefix=' '*4),
        runs=indent('\n'.join(
            '"{key}"->"{choice}" [label="{index}{opt}"];'.format(
                choice=choice, key=key,
                index='' if len(targets) == 1 and len(choices - {None}) == 1 else index,
                opt='?' if None in choices else '')
            for key, targets in runs.items()
            for index, choices in enumerate(targets, start=1)
            for choice in choices
            if choice is not None
        ), prefix=' '*4)
    )


def parse_key(env: UBootEnv, key: str, reads: Dict[str, Set[str]], 
             writes: Dict[str, Set[str]], runs: Dict[str, List[Set[str]]]) -> None:
    """
    Parse a key in the environment to find dependencies.
    
    Args:
        env: UBootEnv object to analyze
        key: Key to parse
        reads: Dictionary of keys read from
        writes: Dictionary of keys written to
        runs: Dictionary of commands run
    """
    # Skip if already processed
    if key in runs:
        return
    
    # Check if key exists
    if key not in env.content:
        return
        
    var_re = re.compile(r'\$(\{)?(?P<var>\w+)(?(1)\})')
    run_stack = []
    run_choices = None
    
    for cmd in parse_value(env.content[key]):
        if cmd[0] in {'then', 'do'}:
            del cmd[0]
        if cmd[0] == 'if':
            run_stack.append(run_choices)
            run_choices = {None}
            del cmd[0]
        elif cmd[0] == 'elif':
            del cmd[0]
        elif cmd[0] == 'else':
            run_choices.remove(None)
            del cmd[0]
        elif cmd[0] == 'fi':
            if run_choices - {None}:
                runs.setdefault(key, []).append(run_choices)
            run_choices = run_stack.pop()
        
        if cmd:
            if cmd[0] == 'run':
                target = ''.join(cmd[1:])
                if var_re.search(target):
                    target_re = re.compile(var_re.sub('.*', target))
                    run_stack.append(run_choices)
                    run_choices = set()
                    for target in env.content:
                        if target_re.match(target):
                            run_choices.add(target)
                            parse_key(env, target, reads, writes, runs)
                    runs.setdefault(key, []).append(run_choices)
                    run_choices = run_stack.pop()
                else:
                    if run_choices is None:
                        runs.setdefault(key, []).append({target})
                    else:
                        run_choices.add(target)
                    parse_key(env, target, reads, writes, runs)
            elif cmd[0] == 'for':
                writes.setdefault(key, set()).add(cmd[1])
            elif cmd[0] == 'load':
                writes.setdefault(key, set()).add('filesize')
            elif cmd[0] in {'setexpr', 'setenv'}:
                writes.setdefault(key, set()).add(cmd[1])
            elif cmd[0:1] == ['env', 'default']:
                writes.setdefault(key, set()).add(cmd[2])
            elif cmd[0:1] == ['env', 'export']:
                writes.setdefault(key, set()).add('filesize')
            elif cmd[0:2] == ['fdt', 'get', 'value']:
                writes.setdefault(key, set()).add(cmd[-1])
        
        for part in cmd:
            match = var_re.search(part)
            if match:
                reads.setdefault(key, set()).add(match.group('var'))


def parse_value(s: str) -> List[List[str]]:
    """
    Parse a value into a list of commands.
    
    Args:
        s: String to parse
        
    Returns:
        List of commands
    """
    result = []
    for cmd in split_cmd(s):
        if cmd:
            result.append(cmd.split())
    return result


def split_cmd(s: str) -> List[str]:
    """
    Split a command string into individual commands.
    
    Args:
        s: String to split
        
    Returns:
        List of command strings
    """
    result = []
    in_str = False
    start = 0
    for i, c in enumerate(s):
        if in_str:
            if c == '"':
                in_str = False
        elif c == ';':
            result.append(s[start:i])
            start = i + 1
        elif c == '"':
            in_str = True
    result.append(s[start:])
    return result


if __name__ == '__main__':
    sys.exit(main())
