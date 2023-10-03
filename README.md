# GitHub Actions SDK

The GitHub Actions SDK builds on the Docker SDK to facilitate the transition of local code development to deploying code in a GitHub Action.

The SDK is particularly relevant to the development of Docker-based GitHub actions, which are containing a Python application. In this sense, it excludes JavaScript-based actions or Docker-based actions that do not bundle a Python application.

The SDK has been tested only on Windows.

# Prerequisites
- [Python](https://www.python.org/) or [Anaconda Python](https://www.anaconda.com/)

- [Docker](https://www.docker.com/)

- [Docker SDK for Python](https://docker-py.readthedocs.io/)

    via `pip`:
    ```
    $ pip install docker
    ```
    or via `conda`:
    ```
    $ conda install -c conda-forge docker-py
    ```

- GitHub Actions SDK
    ```
    $ git clone https://github.com/vliz-be-opsci/github-actions-sdk.git
    ```

# Usage

## Option 1: Run action code as a dockerized application

By default the GitHub Actions SDK will emulate an environment that closely resembles the environment in which the action will be executed on GitHub.

The GitHub Actions SDK can be called via

```
$ python gas.py
```

or explicitly specifying `mode=docker`

```
$ python gas.py -m docker
```

A CRLF to LF newline conversion is executed by default on Windows systems, though only on files with MIME type matching `text/*`. CRLF conversion can be disabled via `--disable-crlf2lf`.

```
$ python gas.py --disable-crlf2lf
```

## Option 2: Run action code as a native application

In the Python environment in which you installed `docker-py`, you can also install the required packages for your action. Doing so allows to run the action natively, without the need to build and run a docker container, thus increasing development speed.

```
$ python gas.py -m native
```

# Getting started with an example

This repository as a whole serves as an example. It hosts an action that reads a list of weather stations and retrieves the corresponding weather observations from the National Weather Service API in a format of choice (csv, json, html, ...).

The `action` folder contains all files necessary to bootstrap a GitHub action, with the action code being implemented in `action/action.py`.

The `github_repo_input` folder contains the files that would be present in the GitHub repository on which the action is acting.

The `environment_variables.json` contains the environment variables to be passed to the action, in this case `API_ENDPOINT` and `FILE_FORMAT` (i.e. output file format).

The `gas.py` file is the implementation of the GitHub Actions SDK. Running

```
$ python gas.py
```

will fire up a docker container, eventually creating the `github_repo_output` folder and the `docker.log` file.

The workflow file for this action, once deployed to GitHub, could look like this:

```yaml
on: [push]
jobs:
  job:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v3
      - name: weather-observations-action
        uses: vliz-be-opsci/weather-observations-action@main
        env:
          API_ENDPOINT: "https://api.weather.gov"
          FILE_FORMAT: "csv"
      - name: git-auto-commit-action
        uses: stefanzweifel/git-auto-commit-action@v4
```
