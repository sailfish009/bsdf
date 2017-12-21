# The BSDF Command Line Interface

BSDF has a command line interface (CLI) for performing simple tasks, such as
inspecting, converting and creating BSDF files. The CLI is part of the
Python implementation, so `pip install bsdf` to start using it.

## Using the CLI

After installation, depending on your Python setup, the CLI may be
available as the `bsdf` command. If this is the case, you can run:
```bash
$ bsdf ...
```

If this is not the case, or if you want to target a specific Python version,
use:

```bash
$ python -m bsdf ...
```

## Getting help

To get started, run the help command:

```bash
$ bsdf help
```

which yields:

```
Command line interface for the Binary Structured Data Format.
See http://bsdf.io for more information on BSDF.

usage: bsdf command [options]

Available commands:
  convert - Convert one format into another (e.g. JSON to BSDF).
  create  - Create a BSDF file from data obtained by evaluation Python code.
  help    - Show the help text.
  info    - Print meta information about the given BSDF file.
  version - Print the version of the current Python implementation.
  view    - View the content of a given BSDF file.

Run 'bsdf help command' or 'bsdf command --help' to learn more.
```

Dive deeper using e.g.
```bash
$ bsdf help view
```

## Example

```
$ bsdf create foo.bsdf '["xx", 4, None, [3, 4, 5]*3]'
```

```
$ bsdf info foo.bsdf
BSDF info for: C:\dev\pylib\bsdf\python\foo.bsdf
  file_name:     foo.bsdf
  file_size:     45
  file_mtime:    2017-12-21 15:21:41
  is_valid:      true
  file_version:  2.1
```

```
$ bsdf view foo.bsdf
[ list with 4 elements
  'xx'
  4
  null
  [ list with 9 elements
    3
    4
    5
    3
    4
    5
    3
    4
    5
  ]
]
```

```
$ bsdf view foo.bsdf --depth=1
[ list with 4 elements
  'xx'
  4
  null
  [ list with 9 elements ]
]
```
