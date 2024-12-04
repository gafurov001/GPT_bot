import re


def validate_full_name(name):
    pattern = r"^[A-Za-z]+(?:['A-Za-z]+)?(?: [A-Za-z]+(?:['A-Za-z]+)?)?$"

    if re.match(pattern, name) and len(name.split()) > 1:
        return True
    return False