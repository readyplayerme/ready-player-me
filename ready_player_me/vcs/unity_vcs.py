"""Wrapper for Unity Version Control (cm)."""
import contextlib
import logging
import socket
import subprocess
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from collections.abc import Generator

VALID_RESPONSE: int = 200
__api_url = "http://localhost:9090/api/v1"


class CommandNotFoundError(Exception):
    """Raised when a CLI command is not found."""


@contextlib.contextmanager
def cm_api() -> "Generator":
    """Context manager to start and stop the cm REST API.

    Can be used as a function decorator or as `with cm_api():`.
    """
    # Check if cm api is already running, i.e. the port is already in use.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", 9090))
    if result == 0:
        # Port is already in use, do not start another subprocess.
        yield
        return

    try:
        # Start the cm API to listen for requests.
        subprocess_obj = subprocess.Popen(["cm", "api"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    except FileNotFoundError as err:
        raise CommandNotFoundError("Command cm not found. Please install Unity Version Control.") from err
    try:
        yield
    finally:
        # Send <Enter> to the subprocess to close it.
        subprocess_obj.communicate(input=b"\n")


@cm_api()
def get_repos(repo_name: str = "") -> list:
    """Get a list of all remote repositories or only the given one.

    :param repo_name: Name of the repository to find. Defaults to "" to list all.
    :return: A list of repositories.
    """
    url = f"{__api_url}/repos/{repo_name}"
    req = requests.get(url, timeout=5)
    if req.status_code == VALID_RESPONSE:
        response = req.json()
        return response if isinstance(response, list) else [response]
    logging.error("The repository list could not be retrieved.")
    return []


@cm_api()
def get_wkspaces(wkspace: str = "") -> list:
    """Get a list of all workspaces or only the given one.

    :param wkspace: Name of the workspace to find. Defaults to "" to list all.
    :return: A list of workspaces.
    """
    url = f"{__api_url}/wkspaces/{wkspace}"
    req = requests.get(url, timeout=5)
    if req.status_code is VALID_RESPONSE:
        response = req.json()
        return response if isinstance(response, list) else [response]
    logging.error("Workspace list could not be retrieved.")
    return []


def get_wkspace_remote(wkspace_path: str) -> str:
    """Get the remote url of a workspace.

    :param wkspace_path: Path to the workspace folder.
    :return: Remote url of the workspace. Empty if not found.
    """
    try:
        result = subprocess.run(["cm", "wi", wkspace_path], capture_output=True, text=True)
    except FileNotFoundError as err:
        raise CommandNotFoundError("Command cm not found. Please install Unity Version Control.") from err
    if result.returncode == 0:
        return result.stdout.strip().lstrip("Branch ")
    logging.warning("Workspace remote could not be retrieved. Probably not a workspace!")
    return ""


def find_workspace(repo_url: str) -> dict | None:
    """Find a workspace that points to the given repo url."""
    if workspaces := get_wkspaces():
        return next(
            (wkspace for wkspace in workspaces if get_wkspace_remote(wkspace["path"]).endswith(repo_url)),
            None,
        )
    return None


def get_wkspace_path(wkspace_name: str) -> str:
    """Get the local folder path of a workspace.

    If given an empty string, returns the path of the first workspace found.

    :param wkspace_name: Name of the local workspace to find. Can also be the repository name.
    :return: Folder Path of the workspace or empty string if it was not found.
    """
    # First try to find the workspace by name.
    try:
        wkspaces = get_wkspaces(wkspace_name)
    except (requests.RequestException, CommandNotFoundError) as err:
        logging.error(err)
        return ""
    try:
        return wkspaces[0]["path"]
    except IndexError:
        # If the workspace was not found, try to find it by repo url. Takes longer.
        try:
            wkspace = find_workspace(f"{wkspace_name}@Wolf3D@cloud")
            if not wkspace:
                logging.error("Local workspace not found.")
                return ""
            return wkspace["path"]
        except (requests.RequestException, CommandNotFoundError) as err:
            logging.error(err)
            return ""


if __name__ == "__main__":
    print(get_wkspace_path("wardrobe"))
