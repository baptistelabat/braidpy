# braidpy for AI assistants

An AI assistant can already read braidpy: its modules say in plain English
what they do and why, and its functions are typed. What it lacks is a short
way in. braidpy has some fifty modules, and the answer to "is this braid the
same as that one?" or "how do I make it on a kumihimo disk?" is spread across
several of them. So there is now one front door, kept as readable for a
person as for an assistant, and an MCP server that offers it as tools.

## The front door: `braidpy.tools`

A handful of questions, each a function taking and giving only text, numbers,
lists and dicts — JSON as it is:

| Function | Answers |
|---|---|
| {func}`~braidpy.tools.list_braids` | the braids braidpy knows by name, by what makes them |
| {func}`~braidpy.tools.describe_braid` | a braid word's strands, permutation, purity, closure, normal form |
| {func}`~braidpy.tools.compare_braids` | whether two words make the same braid, and how unlike they are |
| {func}`~braidpy.tools.similar_braids` | the catalogue's braids nearest one, with every way of making each |
| {func}`~braidpy.tools.ways_to_make` | a kumihimo disk's moves, a lace machine's punchcard, Ashley's stand |
| {func}`~braidpy.tools.make_braid` | a braid made as Braid Studio makes it, told in words |
| {func}`~braidpy.tools.studio_link` | the Braid Studio link that shows a braid in 3D |

```python
from braidpy import tools

tools.describe_braid("1 -2")["permutation"]  # [2, 3, 1]
tools.compare_braids("1 2 3 -6 -5 -4", "3 2 1 -4 -5 -6", n_strands=7)
# {'same_braid': True, 'distance': 0.0}: the flat sinnet of 7, read backwards
tools.ways_to_make("1 -2 -2 1")["ashley"]["a_sinnet"]  # False: one strand a space
```

None of them computes anything of its own: each asks the module that knows
and says which, so there is still one implementation of everything. Every
answer naming a braid carries a Braid Studio link, so an assistant can hand a
person something to look at rather than a list of numbers.

## The MCP server: `braidpy-mcp`

The [Model Context Protocol](https://modelcontextprotocol.io) is how an
assistant — Claude, or any other client — is given tools. braidpy's is the
front door's functions, as they are: the docstring a person reads is the
description the assistant is given.

```sh
pip install "braidpy[mcp]"
claude mcp add braidpy -- braidpy-mcp      # Claude Code; other clients alike
```

It runs on the assistant's machine, over stdio, and needs nothing else. The
catalogue of braids by topology, which
{func}`~braidpy.tools.similar_braids` uses, takes a minute or so to make: the
server starts making it as it starts.

## What else would help, and what would not

- **Restructuring: not needed.** The modules are many but each is one idea,
  and their names say which. Moving them would break every link and import
  for little gain; the front door is the short way in, and the rest stays as
  it is. If anything, a few old modules could gain the plain docstrings the
  newer ones have.
- **An `llms.txt`** beside the documentation: a page listing the
  documentation's pages in a sentence each, the convention for telling an
  assistant where to read. Cheap, and useful to assistants that browse.
- **A command line**, `braidpy describe "1 -2"` printing JSON: the front
  door again, for shell scripts and for assistants that run commands rather
  than call tools.
- **MCP resources**: the catalogues as documents an assistant can read whole,
  rather than tools it calls. Worth adding if assistants turn out to list the
  catalogue often.
- **A hosted server**, so an assistant needs nothing installed: possible, but
  a service to run and pay for; the local one costs nothing.
