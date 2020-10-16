import secrets

import requests

from flask import Flask, request, jsonify, make_response
from flask_script import Manager, Server

from auth_app import AuthApp


app = AuthApp(__name__)

@app.route("/api/auth/verify/<realm>", methods=["GET"])
def handle_auth(realm):

    if realm not in app.realms:
        app.log("WARN", "Invalid realm ({})".format(realm), request)
        return jsonify({"success": False, "message": "Invalid realm"}), 401
    realm_config = app.realms[realm]

    if not "auth_username" in request.cookies or not "auth_token" in request.cookies:
        app.log("INFO", "Missing authentication cookies", request)
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    USERNAME = request.cookies["auth_username"]
    TOKEN = request.cookies["auth_token"]

    key_name = "{}_{}".format(realm_config["prefix"], USERNAME)
    stored_token_val = app.redis_obj.get(key_name)

    if not stored_token_val is None:
        stored_token_val = stored_token_val.decode()

    if stored_token_val == TOKEN:
        app.log("INFO", "User token authenticated", request, USERNAME)
        return jsonify({"success": True}), 200
    else:
        app.log("WARN", "Invalid authentication token", request, USERNAME)
        resp = make_response(jsonify({"success": False, "message": "Invalid token"}))
        resp.status_code = 401
        resp.delete_cookie("auth_token", domain=".{}".format(realm_config["domain"]))
        resp.delete_cookie("auth_username", domain=".{}".format(realm_config["domain"]))
        return resp

@app.route("/api/auth/login/<realm>", methods=["POST"])
def handle_login(realm):
    
    # Check if realm is valid
    if realm not in app.realms:
        app.log("WARN", "Invalid realm ({})".format(realm), request)
        return jsonify({"success": False, "message": "Invalid realm"}), 401
    # Load realm config
    realm_config = app.realms[realm]

    # Load credentials
    data = None
    # Check whether credentials are in URL form or JSON form
    if len(request.form) != 0:
        data = request.form
    if not request.json is None:
        data = request.json
    # Check whether post body exists
    if data is None:
        app.log("INFO", "No credentials provided", request)
        return jsonify({"success": False, "message": "Credentials not provided"}), 400
    # Check whether credentials are present
    if not "username" in data or not "password" in data:
        app.log("INFO", "No credentials provided", request)
        return jsonify({"success": False, "message": "Credentials not provided"}), 400

    # Authenticate against endpoint
    r = requests.post(realm_config["auth_endpoint"], json={"username": data["username"], "password": data["password"]})
    response_json = r.json()
    # Handle authentication failure
    if response_json["success"] != True:
        # Check if GimB servers are down
        if response_json["errorcode"] == "auth_ldap_noconnect_all":
            app.log("ERROR", "Moodle upstream error (auth_ldap_noconnect_all)", request, data["username"])
            return jsonify({"success": False, "message": "GimB servers unreachable (GimB's fault)"}), 502

        app.log("WARN", "Authentication failed", request, data["username"])
        return jsonify({"success": False, "message": "Bad credentials"}), 401
    
    # Handle successful authentication
    app.log("INFO", "User authenticated", request, data["username"])
    # Generate the token
    token = hex(secrets.randbits(realm_config["token"]["length"]))[2:]

    key_name = "{}_{}".format(realm_config["prefix"], data["username"])
    app.redis_obj.set(name=key_name, value=token, ex=realm_config["token"]["expiration"])

    resp = make_response(jsonify({"success": True, "redirect": realm_config["redirect"]}))
    resp.status_code = 200
    resp.set_cookie("auth_username", value=data["username"], max_age=realm_config["token"]["expiration"], domain=".{}".format(realm_config["domain"]), httponly=True)
    resp.set_cookie("auth_token", value=token, max_age=realm_config["token"]["expiration"], domain=".{}".format(realm_config["domain"]), httponly=True)
    return resp

@app.route("/api/auth/logout/<realm>", methods=["GET", "POST"])
def handle_logout(realm):

    if realm not in app.realms:
        app.log("WARN", "Invalid realm ({})".format(realm), request)
        return jsonify({"success": False, "message": "Invalid realm"}), 401
    realm_config = app.realms[realm]

    if "auth_token" in request.cookies and "auth_username" in request.cookies:
        USERNAME = request.cookies["auth_username"]
        TOKEN = request.cookies["auth_token"]

        key_name = "{}_{}".format(realm_config["prefix"], USERNAME)

        stored_token_val = app.redis_obj.get(key_name)
        if not stored_token_val is None:
            stored_token_val = stored_token_val.decode()

        if stored_token_val == TOKEN:
            app.redis_obj.delete(key_name)

        app.log("INFO", "User logged out", request, USERNAME)


    resp = make_response("Logged out successfully. <a href=\"{}\">Go back.</a>".format(realm_config["logout_redirect"]))
    if "auth_token" in request.cookies:
        resp.delete_cookie("auth_token", domain=".{}".format(realm_config["domain"]))
    if "auth_username" in request.cookies:
        resp.delete_cookie("auth_username", domain=".{}".format(realm_config["domain"]))
    resp.headers["Location"] = realm_config["logout_redirect"]
    resp.status_code = 302
    return resp


if __name__ == "__main__":
    app.run(host="localhost", port=3001, debug=True)
