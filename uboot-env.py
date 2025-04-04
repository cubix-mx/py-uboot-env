#!/usr/bin/python3

import os
import re
import io
import sys
import struct
import argparse
import binascii
import tempfile
import subprocess
from textwrap import indent
from itertools import chain
from collections import namedtuple


UBootEnv = namedtuple('UBootEnv', ('content', 'env_size', 'header_size'))


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    if parser.prog == 'edit-env':
        parser.add_argument(
            'filename', help="The U-Boot environment file to edit")
    elif parser.prog == 'dump-env':
        parser.add_argument(
            'filename', help="The U-Boot environment file to dump")
    elif parser.prog == 'dot-env':
        parser.add_argument(
            'filename', help="The U-Boot environment file to graph")
    else:
        print("What am I?!", file=sys.stderr)
        return 1

    config = parser.parse_args(args)
    try:
        env = load_env(config.filename)
        if parser.prog == 'edit-env':
            env = edit_env(env)
            dump_env(env, config.filename)
        elif parser.prog == 'dump-env':
            print(format_env(env))
        elif parser.prog == 'dot-env':
            print(dot_env(env))
    except Exception as exc:
        if int(os.environ.get('DEBUG', '0')):
            raise
        print(str(exc), file=sys.stderr)
        return 1
    else:
        return 0


def load_env(filename):
    with io.open(filename, 'rb') as env_file:
        env = env_file.read()
    env_size = len(env)
    if env_size not in (0x1f000, 0x2000, 0x4000, 0x8000, 0x20000, 0x40000):
        raise ValueError("invalid environment size: {}".format(env_size))

    header_size = 4
    if binascii.crc32(env[header_size:]) != struct.unpack('<L', env[:4])[0]:
        header_size = 5
        if binascii.crc32(env[header_size:]) != struct.unpack('<L', env[:4])[0]:
            raise ValueError("invalid CRC in environment header")

    return UBootEnv(env_size=env_size, header_size=header_size, content={
        key: value
        for entry in env[header_size:].rstrip(b'\xff').split(b'\x00')
        if b'=' in entry
        for key, value in (entry.decode('ascii').split('=', 1),)
    })


def dump_env(env, filename):
    s = b'\x00' * env.header_size  # CRC + optional "redundand" count
    s += b''.join(  # env
        '{key}={value}'.format(key=key, value=value).encode('ascii') + b'\x00'
        for key, value in sorted(env.content.items())
    )
    s += b'\x00'  # env terminator
    s += b'\xff' * (env.env_size - len(s))  # padding
    s = bytearray(s)
    s[:4] = struct.pack('<L', binascii.crc32(s[env.header_size:]))
    with io.open(filename, 'wb') as env_file:
        env_file.write(s)


def format_env(env):
    return '\n'.join(
        '{key}={value}'.format(key=key, value=value)
        for key, value in sorted(env.content.items())
    )


def edit_env(env):
    with tempfile.NamedTemporaryFile('w+', encoding='ascii') as f:
        f.write(format_env(env))
        f.flush()
        try:
            subprocess.run(['editor', f.name], check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("editor exited with non-zero code; "
                               "leaving env alone")
        f.seek(0)
        return env._replace(content={
            key: value
            for entry in f.read().strip().split('\n')
            if '=' in entry
            for key, value in (entry.split('=', 1),)
        })


def dot_env(env):
    reads = {}
    writes = {}
    runs = {}
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
    edge [style=dotted, color="#999999"];
{reads}
    /* Writes */
    edge [style=dashed, color="#999999"];
{writes}
    /* Runs */
    edge [style=solid, color=black];
{runs}
}}
""".format(
        vars=indent('\n'.join(
            '{key};'.format(key=key)
            for keys in chain(reads.values(), writes.values())
            for key in keys
            if key not in runs
        ), prefix=' '*4),
        commands=indent('\n'.join(
            '{key};'.format(key=key)
            for key in runs
        ), prefix=' '*4),
        reads=indent('\n'.join(
            '{target}->{key};'.format(target=target, key=key)
            for key, targets in reads.items()
            for target in targets
        ), prefix=' '*4),
        writes=indent('\n'.join(
            '{key}->{target};'.format(target=target, key=key)
            for key, targets in writes.items()
            for target in targets
        ), prefix=' '*4),
        runs=indent('\n'.join(
            '{key}->{choice} [label="{index}{opt}"];'.format(
                choice=choice, key=key,
                index='' if len(targets) == 1 and len(choices - {None}) == 1 else index,
                opt='?' if None in choices else '')
            for key, targets in runs.items()
            for index, choices in enumerate(targets, start=1)
            for choice in choices
            if choice is not None
        ), prefix=' '*4)
    )


def parse_key(env, key, reads, writes, runs):
    # This is a horribly crude parser of U-Boot's scripting language; please
    # read the code and understand its limitations before relying on this!
    if key in runs:
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


def parse_value(s):
    for cmd in split_cmd(s):
        if cmd:
            yield cmd.split()


def split_cmd(s):
    in_str = False
    start = 0
    for i, c in enumerate(s):
        if in_str:
            if c == '"':
                in_str = False
        elif c == ';':
            yield s[start:i]
            start = i + 1
        elif c == '"':
            in_str = True
    yield s[start:]


if __name__ == '__main__':
    sys.exit(main())