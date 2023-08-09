import os
import json
from typing import List

from nexus import ( NEXUS_ENDPOINT, fetch_project_config,
                   set_environment, fetch_resource, get_headers,
                   NexusAttributes)
from context import get_project_context, Context


def find_dict_diffs(dict0: dict, dict1: dict, to_skip: list = [],
                    diffs: dict = {}):
    keys = set(dict0.keys()).union(set(dict1.keys()))
    for key in keys:
        if key not in to_skip:
            value0 = dict0.get(key)
            value1 = dict1.get(key)
            if isinstance(value0, dict) and isinstance(value1, dict):
                diffs[key] = {}
                find_dict_diffs(value0, value1, to_skip, diffs=diffs[key])
            elif value0 != value1:
                diffs[key] = {'0': value0, '1': value1}


def get_project_and_context(bucket: str) -> tuple:
    """Get the project configuration and its context.
    
    Arguments
    ---------
    bucket : str
        The name of the project int the format: '{org}/{proj}'
    
    Returns
    -------
    A tuple with a dictionary containing the JSON payload of project 
    configuration and the context, instance of the class Context.
    """
    config = fetch_project_config(bucket)
    context = get_project_context(config)
    return config, context


def get_resource_and_context(resource_id: str, bucket: str,
                             endpoint: str, headers: dict) -> tuple:
    """Get the project configuration and its context.
    
    Returns
    -------
    A tuple with a dictionary containing the JSON payload of project 
    configuration and the context, instance of the class Context.
    """
    resource = fetch_resource(resource_id, bucket, endpoint, headers)
    if resource['@context'] == 'https://bbp.neuroshapes.org':
        context_resource = fetch_resource('https://neuroshapes.org', 'neurosciencegraph/datamodels',
                                          endpoint, headers)
        context = Context(context_resource)
    else:
        # Try to get the context from the same bucket
        context_resource = fetch_resource(resource['@context'], bucket,
                                          endpoint, headers)
        context = Context(context_resource)
    return resource, context 


def get_config_diffs(id0: str, id1: str,
                     bucket0: str, bucket1: str, token: str,
                     headers: dict = None,
                     endpoint0: str = NEXUS_ENDPOINT,
                     endpoint1: str = NEXUS_ENDPOINT):
    """Inspect the resource content and the project configuration to find discrepancies
    
    Arguments
    ---------
    id0, id1 : str
        Nexus ids of the resources being compared
    bucket0, bucket1 : str
        The bucket where the resources exist, constructed as `organization/project`   
    endpoint0, endpoint1 : str
        Deployment of Nexus, default to production endpoint
    headers : dict
        Headers in a json form to be used when fetching data from Nexus

    Returns
    -------
    diffs: dict
        Dictionary containing two sets of differences, the `context_diffs`
        covering conflicts caused by the the context values, `config_diffs`
        where the discrepancies in the project configurations are given if any,
        `resource_diffs` contains differences in values of attributes, and
        `prefix_diffs` contains differences in the attributes ids due to a context
        difference.
    """
    if headers is None:
        headers = get_headers(token) 
    if endpoint0 == endpoint1:
        # set environment once
        set_environment(token, endpoint0)
        config0, context0 = get_project_and_context(bucket0)
        res0, res_context0 = get_resource_and_context(id0, bucket0, endpoint0, headers)
        config1, context1 = get_project_and_context(bucket1)
        res1, res_context1 = get_resource_and_context(id1, bucket1, endpoint1, headers)
    else:
        # set environment for each call
        set_environment(token, endpoint0)
        config0, context0 = get_project_and_context(bucket0)
        res0, res_context0 = get_resource_and_context(id0, bucket0, endpoint0, headers)
        set_environment(token, endpoint1)
        config1, context1 = get_project_and_context(bucket1)
        res1, res_context1 = get_resource_and_context(id1, bucket1, endpoint1, headers)

    # Find the differences
    config_diffs = {}
    find_dict_diffs(config0, config1, NexusAttributes.project_metadata, config_diffs)
    # Project context differences
    context_diffs = {}
    find_dict_diffs(context0.document, context1.document, diffs=context_diffs)
    # Resource differences
    resource_diffs = {}
    find_dict_diffs(res0, res1, diffs=resource_diffs)
    prefix_diffs = {}
    if res_context0 != res_context1:
        # check possible differences in prefixes
        attrs = set(res0.keys()).union(set(res1.keys()))
        for attr in attrs:
            if attr in res0 and attr in res1:
                prefix0 = res_context0.resolve(attr)
                prefix1 = res_context1.resolve(attr)
                if prefix0 != prefix1:
                    prefix_diffs[attr] = {'0': prefix0, '1': prefix1}
    return dict(config_diffs=config_diffs, context_diffs=context_diffs,
                resource_diffs=resource_diffs, prefix_diffs=prefix_diffs)


if __name__ == "__main__":
    TOKEN = os.environ['NEXUS_TOKEN']
    id0 = "https://bbp.epfl.ch/neurosciencegraph/data/neuronmorphologies/0993c0e9-e83a-4571-a4f0-7a1ee738d0b4"
    bucket0 = "public/sscx"
    id1 = "https://bbp.epfl.ch/neurosciencegraph/data/e248278d-e370-4e3d-95f4-c3ec975770b2"
    bucket1 = "bbp-external/seu"
    result = get_config_diffs(id0, id1, bucket0, bucket1, token=TOKEN)
    fname = f"{id0.split('/')[-1]}-{id1.split('/')[-1]}-config-diffs.json"
    with open(fname, 'w') as ofile:
        json.dump(result, ofile, indent=2)
    