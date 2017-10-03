# BSDF

Binary Structured Data Format

## Introduction


## Installation

Differs per implementation, but in general the `bsdf.xx` file can be included
in your project.


## Development

Since BSDF is designed to be simple, implementations are usually restricted
to a single module. This repo contains all "official" implementations,
organized in sub directories. This also makes it easier to test each
implementation using a "test service".

The tooling around BSDF is implemented in Python. For development, you
need Python 3.x and the invoke library (`pip install invoke`).

To run tests and run other tasks, run `invoke` from the root repo to
get started.

