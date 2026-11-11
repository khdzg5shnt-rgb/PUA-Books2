"""Read one explicit request without retaining conversation data."""
import json
import sys
from pathlib import Path

MAX_INPUT_BYTES = 1024 * 1024


def validate_fact_values(values, config):
    """Validate supplied fields without including their values in errors."""
    defaults = config['defaults']
    if not isinstance(values, dict):
        raise ValueError('facts must be an object')
    if set(values) - set(defaults):
        raise ValueError('Unknown fact fields; use system/router.json defaults')
    for name, value in values.items():
        if type(value) is not type(defaults[name]):
            raise ValueError('Wrong type for ' + name)
        if name in config['enums'] and value not in config['enums'][name]:
            raise ValueError('Unknown value for ' + name)
    if values.get('consecutive_low_rounds', 0) < 0:
        raise ValueError('consecutive_low_rounds must be nonnegative')


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key; provide one current value')
        value[key] = item
    return value


def _invalid_constant(_value):
    raise ValueError('Non-finite JSON number is not allowed')


def read_request(path):
    """Use '-' for stdin. Never save, log, or include input text in errors."""
    if str(path) == '-':
        data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        with Path(path).open('rb') as handle:
            data = handle.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError('Request exceeds the one-megabyte input limit')
    try:
        return json.loads(data.decode('utf-8-sig'), object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('Request must be valid UTF-8 JSON') from error
