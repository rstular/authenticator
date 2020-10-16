import json
import logging
import logging.handlers
import sys

import redis
import uwsgi

from flask import Flask


def load_json_file(json_file):
    with open(json_file, "r") as f:
        data = f.read()
    return json.loads(data)

class AuthApp(Flask):
    realms = None
    redis_obj = None
    logger = None

    def __init__(self, *args):
        # Load app configuration
        app_config = load_json_file(uwsgi.opt["app-config-file"])
        # Load authentication realms
        self.realms = load_json_file(uwsgi.opt["app-realms-file"])

        # Configure redis connection
        redis_config = app_config["redis"]
        self.redis_obj = redis.Redis(host=redis_config["host"], port=redis_config["port"], db=redis_config["database_id"])


        # Configure logging
        self.logger = logging.getLogger(app_config["logging"]["name"])
        self.logger.setLevel(logging.DEBUG)

        # Configure stdout log handler
        stdout_config = app_config["logging"]["stdout"]
        if stdout_config["enable"]:
            handler = logging.StreamHandler(sys.stdout)

            level = logging.getLevelName(stdout_config["level"])
            handler.setLevel(level)

            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(forwardedip)s - %(realip)s - %(component)s - %(originalhost)s - %(user)s - %(message)s - %(useragent)s")
            handler.formatter = formatter

            self.logger.addHandler(handler)

        # Configure rsyslog log handler
        rsyslog_config = app_config["logging"]["rsyslog"]
        if rsyslog_config["enable"]:
            handler = logging.handlers.SysLogHandler(address=(rsyslog_config["host"], rsyslog_config["port"]), facility="daemon")

            level = logging.getLevelName(rsyslog_config["level"])
            handler.setLevel(level)

            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(forwardedip)s - %(realip)s - %(component)s - %(originalhost)s - %(user)s - %(message)s - %(useragent)s")
            handler.formatter = formatter

            self.logger.addHandler(handler)
        super().__init__(*args)
    
    def log(self, level, message, request, user="None"):
        ORIGINAL_URI = request.environ["X-Original-Uri"] if "X-Original-Uri" in request.environ else None
        ORIGINAL_HOST = request.environ["X-Original-Host"] if "X-Original-Host" in request.environ else None
        REAL_USER_IP = request.environ["X-Real-Ip"] if "X-Real-Ip" in request.environ else None
        FORWARDED_IP = request.environ["X-Forwarded-For"] if "X-Forwarded-For" in request.environ else None
        USER_AGENT = request.headers["User-Agent"] if "User-Agent" in request.headers else None

        log_level = logging.getLevelName(level)

        self.logger.log(log_level, message, extra={
            "realip": REAL_USER_IP,
            "forwardedip": FORWARDED_IP,
            "component": request.path,
            "originalhost": ORIGINAL_HOST,
            "user": user,
            "useragent": USER_AGENT
        })

