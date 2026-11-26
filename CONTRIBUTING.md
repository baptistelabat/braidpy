# Contributing

Contributions are welcome: a bug, a machine, a sinnet or a pattern to add, a
page of the documentation to mend.

## Setting up

The [developer guide](docs/source/developer_guide.md) says how: clone the
repository, `make install-uv`, `pre-commit install`. The rules braidpy is
written by are in [CLAUDE.md](CLAUDE.md), the same for a person and for an
assistant.

## Before opening a pull request

```sh
make lint && make typecheck && make test && make duplicates
```

`make test` runs the quick tests CI runs on every push. A test that takes
seconds is marked `@pytest.mark.slow`. Say what changed for the person using
braidpy in `CHANGELOG.md`'s unreleased section.

## What to ask first

Open an issue before a pull request that changes the API of an existing
function, adds a dependency, or writes a second version of something braidpy
already has: it keeps one implementation of everything, and
[`braidpy.tools`](docs/source/ai_assistants.md) is the front door other
things are built on.
