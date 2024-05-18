import re


def valid_email(email):
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    if re.fullmatch(regex, email):
        return True
    return False


def valid_password(password):
    if len(password) >= 10:
        return True
    return False


def valid_username(username):
    if len(username) > 0:
        return True
    return False
