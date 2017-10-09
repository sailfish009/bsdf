# Contributing to BSDF

There are several ways that you can contribute to BSDF. From contributing
bugs in the [issue tracker](https://gitlab.com/almarklein/bsdf/issues), to
providing fixes and improvements, or even contributing new implementations.

## Organization of the code

Since BSDF is designed to be simple, implementations are usually
restricted to a single module. The [BSDF Gitlab repo](https://gitlab.com/almarklein/bsdf)
contains implementations for several languages, organized in sub
directories. This allows testing each implementation using a "test
service", and ensures compatibility between the different
implementations.


## Development dependencies

The tooling around BSDF is implemented in Python. For development, you
need Python 3.x and the invoke library (`pip install invoke`).

To run tasks such as tests, run `invoke` from the root repo to get
started.


## Workflow

To start contributing an enhancement or new implementation, please start
by making an issue to start the discussion. The actual code will be
contributed via pull requests.

It is expected that each implementation will be more or less maintained by
its own group of contributors.


## Code of conduct

BSDF does not have an official code of conduct yet, but let's just say
that we expect respect from and towards all contributors, and will not
tolerate discrimination or trolling.
