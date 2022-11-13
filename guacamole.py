#!/usr/bin/python

# Copyright: (c) 2020, Pablo Escobar <pablo.escobarlopez@unibas.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.parse import urlencode


URL_GET_TOKEN = "{url}/api/tokens"
URL_LIST_CONNECTIONS = "{url}/api/session/data/{datasource}/connectionGroups/\
{group}/tree?token={token}"
URL_LIST_CONNECTIONS_GROUPS = "{url}/api/session/data/{datasource}/connectionGroups/?token={token}"
URL_LIST_USERS = "{url}/api/session/data/{datasource}/users?token={token}"
URL_CONNECTION_DETAILS = "{url}/api/session/data/{datasource}/connections/{connection_id}/parameters?token={token}"

class GuacamoleError(Exception):
    pass


def guacamole_get_token(base_url, validate_certs, auth_username, auth_password):
    """
    Retun a dict with a token to authenticate with the API and a datasource.
    DataSource can be "postgresql" or "mysql" depending on how guacamole is configured.

    Example of what this function returns:
    {
        'authToken': 'AAAAABBBBBCCCCCDDDDD",
        'dataSource': 'postgresql'
    }
    """

    url_get_token = URL_GET_TOKEN.format(url=base_url)

    payload = {
        'username': auth_username,
        'password': auth_password
    }

    try:
        token = json.load(open_url(url_get_token, method='POST',
                                   validate_certs=validate_certs,
                                   data=urlencode(payload)))
    except ValueError as e:
        raise GuacamoleError(
            'API returned invalid JSON when trying to obtain access token from %s: %s'
            % (url_get_token, str(e)))
    except Exception as e:
        raise GuacamoleError('Could not obtain access token from %s: %s'
                             % (url_get_token, str(e)))
    try:
        return {
            'authToken': token['authToken'],
            'dataSource': token['dataSource'],
        }
    except KeyError:
        raise GuacamoleError(
            'Could not obtain access token from %s' % url_get_token)


def guacamole_get_connections(base_url, validate_certs, datasource, group, auth_token):
    """
    Return a list of dicts with all the connections registered in the guacamole server
    for the provided connections group and its sub-groups. Default connections group is ROOT
    """

    url_list_connections = URL_LIST_CONNECTIONS.format(
        url=base_url, datasource=datasource, group=group, token=auth_token)

    try:
        connections_group = json.load(open_url(url_list_connections, method='GET',
                                                           validate_certs=validate_certs))
    except ValueError as e:
        raise GuacamoleError(
            'API returned invalid JSON when trying to obtain list of connections from %s: %s'
            % (url_list_connections, str(e)))
    except Exception as e:
        raise GuacamoleError('Could not obtain list of guacamole connections from %s: %s'
                             % (url_list_connections, str(e)))


    all_connections = []

    if 'childConnections' in connections_group:
        all_connections = connections_group['childConnections']
  
    if 'childConnectionGroups' in connections_group:
        for group in connections_group['childConnectionGroups']:
            if 'childConnections' in group:
                all_connections = all_connections + group['childConnections']

    return all_connections


def guacamole_get_connections_group_id(base_url, validate_certs, datasource, group, auth_token):
    """
    Get the group numeric id from the group name.
    When working with a group different of the default one (ROOT) we have to map the group name
    to its numeric identifier because the API expects a group numeric id, not a group name
    """

    url_list_connections_groups = URL_LIST_CONNECTIONS_GROUPS.format(
        url=base_url, datasource=datasource, token=auth_token)

    try:
        connections_groups = json.load(open_url(url_list_connections_groups, method='GET',
                                                           validate_certs=validate_certs))
    except ValueError as e:
        raise GuacamoleError(
            'API returned invalid JSON when trying to obtain list of connections groups from %s: %s'
            % (url_list_connections_groups, str(e)))
    except Exception as e:
        raise GuacamoleError('Could not obtain list of guacamole connections groups from %s: %s'
                             % (url_list_connections_groups, str(e)))

    # find the numeric id for the group name
    for group_id, group_info in connections_groups.items():
        if group_info['name'] == group:
            group_numeric_id = group_info['identifier']

    try:
        group_numeric_id
    except NameError:
        raise GuacamoleError(
            'Could not find the numeric id for connections group %s. Does the group exists?' % (group))
    else:
        return group_numeric_id


def guacamole_get_users(base_url, validate_certs, datasource, auth_token):
    """
    Returns a dict with all the users registered in the guacamole server
    """

    url_list_users = URL_LIST_USERS.format(url=base_url, datasource=datasource, token=auth_token)

    try:
        guacamole_users = json.load(open_url(url_list_users, method='GET', validate_certs=validate_certs))
    except ValueError as e:
        raise GuacamoleError(
            'API returned invalid JSON when trying to obtain list of users from %s: %s'
            % (url_list_users, str(e)))
    except Exception as e:
        raise GuacamoleError('Could not obtain list of guacamole users from %s: %s'
                             % (url_list_users, str(e)))

    return guacamole_users

def guacamole_get_connection_details(base_url, validate_certs, datasource, connection_id, auth_token):
    """
    Return a dict with detailed connection parameters for a single connection.
    This function requires a connection id and provides more information than function guacamole_get_connections()
    """

    url_connection_details = URL_CONNECTION_DETAILS.format(
        url=base_url, datasource=datasource, connection_id=connection_id, token=auth_token)

    try:
        connection_details = json.load(open_url(url_connection_details, method='GET',
                                                validate_certs=validate_certs))
    except ValueError as e:
        raise GuacamoleError(
            'API returned invalid JSON when trying to obtain connection details from %s: %s'
            % (url_connection_details, str(e)))
    except Exception as e:
        raise GuacamoleError('Could not obtain connection details from %s: %s'
                             % (url_connection_details, str(e)))

    return connection_details

