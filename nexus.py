import requests
from typing import List
from urllib.parse import quote_plus
import nexussdk as nxs

from context import get_project_context


NEXUS_ENDPOINT= "https://bbp.epfl.ch/nexus/v1"


def get_headers(token: str, content_type: str = 'application/json',
                    accept: str = 'application/json') -> dict:
    headers = {'Content-type': content_type,
               'Accept': accept,
               'Authorization': f"Bearer {token}"}
    return headers


def set_environment(token: str, endpoint: str):
    nxs.config.set_environment(endpoint)
    nxs.config.set_token(token)


def fetch_resource(resource_id: str, bucket: str,
                   endpoint: str, headers: dict) -> dict:
    """Fetch a resource from Nexus using its id
    
    Arguments
    ---------
    resource_id : str
        The id of the resource
    bucket : str
        The name of the project int the format: '{org}/{proj}'
    endpoint: str
    
    Returns
    -------
    A dictionary containing the JSON payload of project configuration
    """
    url_base = f"{endpoint}/resources/{bucket}"
    url = "/".join((url_base, "_", quote_plus(resource_id), "source"))
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    resource = response.json()
    return resource


def fetch_project_config(bucket: str) -> dict: 
    """Get the project configuration.
    
    Arguments
    ---------
    bucket : str
        The name of the project int the format: '{org}/{proj}'
    
    Returns
    -------
    A dictionary containing the JSON payload of project configuration
    """
    org, proj = bucket.split('/')
    return nxs.projects.fetch(org, proj)
