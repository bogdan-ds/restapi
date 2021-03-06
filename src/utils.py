# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 Red Hat, Inc. <http://www.redhat.com>
#  This file is part of GlusterFS.
#
#  This file is licensed to you under your choice of the GNU Lesser
#  General Public License, version 3 or any later version (LGPLv3 or
#  later), or the GNU General Public License, version 2 (GPLv2), in all
#  cases as published by the Free Software Foundation.
#

import json
from functools import wraps
import os
import logging
import fcntl

import jwt
from flask import request
from gluster.cli import GlusterCmdException

from conf import (DEFAULT_CONFIG_FILE,
                  CUSTOM_CONFIG_FILE,
                  APPS_FILE)

_config = {}
_log_level = {}

REQUIRED_CLAIMS = ["iss", "iat", "exp", "qsh"]
DEFAULT_CONTENT_TYPE = {"Content-Type": "application/json; charset=utf-8"}


# Init Logger instance
logger = logging.getLogger(__name__)


def boolify(inp):
    if inp in ["1", "True", "true", "Yes", "yes"]:
        return True
    return False


def http_response_error(err, status=401):
    out = {"error": err, "errno": -1, "output": ""}
    return (json.dumps(out),
            status,
            DEFAULT_CONTENT_TYPE)


def get_config(item, default_value=None):
    if not _config:
        load_config()
    return _config.get(item, default_value)


def load_config():
    """
    Load/Reload the config from REST Config files. This function will
    be triggered during init and when SIGUSR2.
    """
    global _config
    _config = {}
    if os.path.exists(DEFAULT_CONFIG_FILE):
        _config = json.load(open(DEFAULT_CONFIG_FILE))
    if os.path.exists(CUSTOM_CONFIG_FILE):
        _config.update(json.load(open(CUSTOM_CONFIG_FILE)))


def load_log_level():
    """
    Reads log_level from Config file and sets accordingly. This function will
    be triggered during init and when SIGUSR2.
    """
    global logger, _log_level
    new_log_level = _config.get("log_level", "INFO")
    if _log_level != new_log_level:
        logger.setLevel(getattr(logging, new_log_level.upper()))
        _log_level = new_log_level.upper()


def load_all():
    load_config()
    load_log_level()


def get_qsh(method, path, args):
    pass


def get_app_secret(iss):
    if not os.path.exists(APPS_FILE):
        return None

    with open(APPS_FILE) as f:
        apps = json.load(f)
        data = apps.get(iss, None)

    return data


def auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _config.get("auth-enabled"):
            return func(*args, **kwargs)

        # Collect Authorization header, validate if format is different
        # than "Bearer <TOKEN>"
        auth_header = request.headers.get("Authorization", "").strip()
        auth_header_parts = ["", ""]
        if auth_header != "":
            auth_header_parts = auth_header.split(" ")
            if len(auth_header_parts) != 2 or \
               auth_header_parts[0].lower() != "bearer":
                return http_response_error(
                    "Authorization header format must be Bearer <TOKEN>",
                    status=401)

        try:
            payload_data = jwt.decode(auth_header_parts[1], verify=False)
        except jwt.DecodeError:
            return http_response_error("Invalid Token", status=401)

        # Check for required claims
        for claim_name in REQUIRED_CLAIMS:
            if payload_data.get(claim_name, None) is not None:
                return http_response_error(
                    "Token missing {0} Claim".format(claim_name),
                    status=401)

        # Claims["qsh"] is SHA256 hash generated by Client, this will
        # change wrt URL,Method and parameters. Generate qsh by using
        # User inputs, this will be compared with Claims["qsh"]
        qsh = get_qsh(request.method, request.path, request.args)

        if qsh != payload_data.get("qsh"):
            return http_response_error(
                "Invalid qsh claim in token",
                status=401)

        try:
            app_secret = get_app_secret(payload_data.get("iss"))
            if app_secret is None:
                return http_response_error("Invalid App Id", status=401)

            jwt.decode(auth_header_parts[1], key=app_secret)
        except jwt.ExpiredSignatureError:
            return http_response_error("Expired Token", status=401)
        except jwt.DecodeError:
            return http_response_error("Invalid Token", status=401)
            pass

        # All Success, Call the actual Function
        return func(*args, **kwargs)

    return wrapper


def gluster_cmd_to_http_response(func, *args, **kwargs):
    out = {"output": "", "error": "", "errno": 0}
    status_code = kwargs.get("success_status_code", 200)
    try:
        out["output"] = func(*args, **kwargs)
    except GlusterCmdException as e:
        # e.message is a tuple, contains (rc, out, err)
        out["errno"] = e.message[0]
        out["error"] = e.message[2]
        status_code = 500

    return (json.dumps(out),
            status_code,
            DEFAULT_CONTENT_TYPE)


class LockedOpen(object):

    def __init__(self, filename, *args, **kwargs):
        self.filename = filename
        self.open_args = args
        self.open_kwargs = kwargs
        self.fileobj = None

    def __enter__(self):
        """
        If two processes compete to update a file, The first process
        gets the lock and the second process is blocked in the fcntl.flock()
        call. When first process replaces the file and releases the lock,
        the already open file descriptor in the second process now points
        to a  "ghost" file(not reachable by any path name) with old contents.
        To avoid that conflict, check the fd already opened is same or
        not. Open new one if not same
        """
        f = open(self.filename, *self.open_args, **self.open_kwargs)
        while True:
            fcntl.flock(f, fcntl.LOCK_EX)
            fnew = open(self.filename, *self.open_args, **self.open_kwargs)
            if os.path.sameopenfile(f.fileno(), fnew.fileno()):
                fnew.close()
                break
            else:
                f.close()
                f = fnew
        self.fileobj = f
        return f

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.fileobj.close()
