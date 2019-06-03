from utils import auth, gluster_cmd_to_http_response
from gluster.cli import georep
from flask import Blueprint, request

georep_api = Blueprint('georep_api', __name__)


@georep_api.route("/<mastervol>/<slavehost>/<slavevol>", methods=["POST"])
@auth
def api_georep_create(mastervol, slavehost, slavevol):
    data = request.get_json() or {}
    return gluster_cmd_to_http_response(georep.create, mastervol, slavehost, slavevol, **data)


@georep_api.route("/<mastervol>/<slavehost>/<slavevol>/start", methods=["POST"])
@auth
def api_georep_start(mastervol, slavehost, slavevol):
    data = request.get_json() or {}
    return gluster_cmd_to_http_response(georep.start, mastervol, slavehost, slavevol, **data)


@georep_api.route("/<mastervol>/<slavehost>/<slavevol>/stop", methods=["POST"])
@auth
def api_georep_stop(mastervol, slavehost, slavevol):
    data = request.get_json() or {}
    return gluster_cmd_to_http_response(georep.stop, mastervol, slavehost, slavevol, **data)


@georep_api.route("/<mastervol>/<slavehost>/<slavevol>", methods=["DELETE"])
@auth
def api_georep_delete(mastervol, slavehost, slavevol):
    data = request.get_json() or {}
    return gluster_cmd_to_http_response(georep.delete, mastervol, slavehost, slavevol, **data)


@georep_api.route("/<mastervol>/<slaveuser>/<slavehost>/<slavevol>/config", methods=["GET"])
@auth
def api_georep_config_get(mastervol, slaveuser, slavehost, slavevol):
    pass


@georep_api.route("/<mastervol>/<slaveuser>/<slavehost>/<slavevol>/config",
                  methods=["POST"])
@auth
def api_georep_config_set(mastervol, slaveuser, slavehost, slavevol):
    pass


@georep_api.route("/<mastervol>/<slaveuser>/<slavehost>/<slavevol>/config",
                  methods=["DELETE"])
@auth
def api_georep_config_reset(mastervol, slaveuser, slavehost, slavevol):
    pass


# Multiple routes will go to same function, Status can be fetched with or
# without Volume names
@georep_api.route("", methods=["GET"])
@georep_api.route("/<mastervol>", methods=["GET"])
@georep_api.route("/<mastervol>/<slaveuser>/<slavehost>/<slavevol>", methods=["GET"])
@auth
def api_georep_status(mastervol=None, slaveuser=None, slavehost=None, slavevol=None):
    return gluster_cmd_to_http_response(georep.status, mastervol, slaveuser, slavehost, slavevol)


@georep_api.route("/<mastervol>/<slaveuser>/<slavehost>/<slavevol>/checkpoint",
                  methods=["POST"])
@auth
def api_checkpoint_set(mastervol, slaveuser, slavehost, slavevol):
    pass


@georep_api.route("/<mastervol>/<slaveuser>/<slavehost>/<slavevol>/checkpoint",
                  methods=["GET"])
@auth
def api_checkpoint_get(mastervol, slaveuser, slavehost, slavevol):
    pass


@georep_api.route("/<mastervol>/<slaveuser>/<slavehost>/<slavevol>/checkpoint",
                  methods=["DELETE"])
@auth
def api_checkpoint_del(mastervol, slaveuser, slavehost, slavevol):
    pass


@georep_api.route("/<mastervol>/<slavehost>/<slavevol>/pause", methods=["POST"])
@auth
def api_georep_pause(mastervol, slavehost, slavevol):
    data = request.get_json() or {}
    return gluster_cmd_to_http_response(georep.pause, mastervol, slavehost, slavevol, **data)


@georep_api.route("/<mastervol>/<slavehost>/<slavevol>/resume", methods=["POST"])
@auth
def api_georep_resume(mastervol, slavehost, slavevol):
    data = request.get_json() or {}
    return gluster_cmd_to_http_response(georep.resume, mastervol, slavehost, slavevol, **data)
