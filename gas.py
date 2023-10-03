import argparse
import docker
import json
import logging
import mimetypes
import os
import platform
import shutil
from pathlib import Path
from subprocess import check_call

ROOT_PATH = Path(__file__).parent
CACHE_PATH = ROOT_PATH / ".gas_cache"
ENVIRONMENT = json.load(open(ROOT_PATH / "environment_variables.json"))
SHUTIL_IGNORE_PATTERNS = [".git"]

def create_gas_cache():
    logger.debug("creating .gas_cache")
    shutil.copytree(
        ROOT_PATH / "action",
        CACHE_PATH / "action",
        ignore=shutil.ignore_patterns(*SHUTIL_IGNORE_PATTERNS),
    )
    shutil.copytree(
        ROOT_PATH / "github_repo_input",
        CACHE_PATH / "github_repo_input",
        ignore=shutil.ignore_patterns(*SHUTIL_IGNORE_PATTERNS),
    )

def clean_gas_cache():
    logger.debug("cleaning .gas_cache")
    if (ROOT_PATH / "github_repo_output").exists():
        shutil.rmtree(
            ROOT_PATH / "github_repo_output"
        )
    shutil.copytree(
        ROOT_PATH / ".gas_cache/github_repo_input",
        ROOT_PATH / "github_repo_output",
    )
    shutil.rmtree(
        ROOT_PATH / ".gas_cache"
    )

def mime_type_match(mime_type):
    if not mime_type:
        return False
    if mime_type.startswith("text/"):
        return True
    if mime_type == "application/x-sh":
        return True

def crlf2lf(force=False): 
    if force or platform.system() == "Windows":
        logger.debug("converting crlf to lf")
        for dirpath, _, filenames in os.walk(ROOT_PATH / ".gas_cache"): 
            for filename in filenames:
                file_path = Path(dirpath) / filename
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type_match(mime_type):
                    with open(file_path, "rb") as f:
                        buffer = f.read().replace(b"\r\n", b"\n")
                    with open(file_path, "wb") as f:
                        f.write(buffer)

def run_native_action():
    action_path = ROOT_PATH / ".gas_cache/action/action.py"
    github_workspace_path = ROOT_PATH / ".gas_cache/github_repo_input"
    os.environ["GITHUB_WORKSPACE"] =  str(github_workspace_path)
    for key, value in ENVIRONMENT.items():
        os.environ[key] = value
    check_call(f"python {action_path}")

def run_dockerized_action(client):
    logger.debug("building docker image")
    client.images.build(
        tag="action_image",
        path=str(ROOT_PATH / ".gas_cache/action"),
        forcerm=True
    )
    logger.debug("running docker container")
    console = client.containers.run(
        name="action_container",
        image="action_image",
        environment = ENVIRONMENT,
        volumes = {
            ROOT_PATH / ".gas_cache/github_repo_input": {
                "bind": "/github/workspace",
                "mode": "rw",
            },
        },
        stdout=True,
        stderr=True,
    )
    logger.debug("generating docker.log")
    with open(ROOT_PATH / "docker.log", "w", encoding="utf-8") as f:
        f.write(console.decode("utf-8"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log-level", nargs="?", default="INFO")
    parser.add_argument("-m", "--mode", nargs="?", default="docker")
    parser.add_argument("-r", "--repo", nargs="?", default="NULL")
    parser.add_argument("--disable-crlf2lf", action="store_true")
    parser.add_argument("--force-crlf2lf", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    logger = logging.getLogger(__name__)

    try:
        clean_gas_cache()
    except FileNotFoundError:
        logger.debug(".gas_cache not found, continuing")

    create_gas_cache()

    if args.mode == "native":
        try:
            run_native_action()
        finally:
            clean_gas_cache()

    elif args.mode == "docker":
        try:
            if not args.disable_crlf2lf:
                crlf2lf(args.force_crlf2lf)
            client = docker.from_env()
            run_dockerized_action(client)
        finally:
            try:
                client.containers.get("action_container").remove()
                client.images.get("action_image").remove()
            except NameError:
                raise RuntimeError("docker client not found, please verify whether docker daemon is running")
            finally:
                clean_gas_cache()

    elif args.mode == "deploy":
        try:
            repository_path = CACHE_PATH / "repository"
            check_call(f"git clone {args.repo} {repository_path}")
            # TODO empty the repository, except .git folder
            shutil.copytree(
                ROOT_PATH / "action",
                repository_path,
                ignore=shutil.ignore_patterns(*SHUTIL_IGNORE_PATTERNS),
                dirs_exist_ok=True
            )
            os.chdir(repository_path)
            check_call("git add .")
            check_call("git status")
            check_call("git update-index --chmod=+x entrypoint.sh") # TODO: check if this can be handled by CHMOD in Dockerfile
            check_call("git ls-files --stage")
            # TODO: if not dry run
            check_call('git commit -m "initialize via github-actions-sdk"')
            check_call("git push")
        finally:
            ...
            # TODO clean_gas_cache()?

    else:
        try:
            clean_gas_cache()
        finally:
            raise AssertionError(f"invalid mode: {args.mode}")