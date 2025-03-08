from enum import Enum

import pytz


class ResponseCode(Enum):
    SUCCESS = 200
    UNAUTHORIZED = 401
    SERVER_ERROR = 500
    VALIDATION_ERROR = 422
    NOT_FOUND = 404
    ALREADY_REPORTED = 208


MIN_LEN_PATH_PARTS = 2
LEN_OF_PARTS_GITHUB_URL = 2
TIMEZONE = pytz.timezone("Europe/Moscow")
