introspector
============

A tool to automatically and interactively generate configuration files for `open311-adapter`.

Discovery and config generation is currently supported for the following backends:

 - Confirm on Demand

## Installation

Docker is the simplest way to run this code. There is a wrapper script that runs
the container correctly:

```bash
$ wget https://raw.githubusercontent.com/mysociety/open311-introspector/main/script/introspector.sh
$ chmod +x introspector.sh
```

Alternatively you can install and run locally. Requirements:

 - Python 3.8+
 - Poetry
 - lxml

```bash
$ git clone git@github.com:mysociety/open311-introspector.git
$ cd open311-introspector
$ poetry install
```

## Creating a new configuration

By default configuration files are created in `configs` in the current directory.
Set the `INTROSPECTOR_CONFIG_PATH` envvar if you want to put them elsewhere (eg
in your `open311-adapter`'s `conf` directory so you don't need to copy them manually.)

To create a new, empty, configuration file you must choose a backend and a council name and pass that to the `new` sub-command.

For example, to create a new Confirm config file for Borsetshire:

```bash
$ ./introspector.sh new confirm borsetshire
```
(NB this assumes you're running via Docker; if you're running locally replace
`./inspector.sh` with `poetry run introspector`)

This will create `council-borsetshire_confirm.yml` in the config directory.
This file will not yet have any values for any of the config keys, so the next
thing to do is generate the values interactively.

To get started with Confirm you'll need three initial values:

 - username
 - password
 - tenant/database ID

Everything else will be optional or introspected from the Confirm API.

```bash
$ ./introspector.sh generate borsetshire
```

Follow the prompts to fill out the config file, which is written when the script exits.

You can run this command as many times as required, it won't delete any config values
from the existing file. By default you'll only be prompted to fill in blank values -
if you want to change an existing value or see all the values from the config, run:

```bash
$ ./introspector.sh generate --update borsetshire
```
