"""Independent role-bound attempts; immutable completion markers and read-only replay."""
import base64
from copy import deepcopy
import os
from pathlib import Path
import time
from .artifacts import encode, loads, sha, fingerprint, identity, require
from .semantic import validate_answer, VERSION as OPERATION_VERSION, PROMPT, SCHEMA

VERSION = 'paired-semantic-attempt-1.0.0'
CONFIGS = {
    'primary': {'model': 'google/gemini-3.8-flash', 'route': 'google-ai-studio', 'served_provider': 'Google AI Studio'},
    'research': {'model': 'deepseek/deepseek-v4.1-flash', 'route': 'together', 'served_provider': 'Together'},
}
for _role, _config in CONFIGS.items():
    _config.update(role=_role, temperature=0, max_tokens=4096, reasoning='native_default', deadline_seconds=60,
                   allow_fallbacks=False, require_parameters=True, max_price={'prompt':5,'completion':20,'request':0})
FILES = ('query.json', 'request.json', 'started.json', 'response.json', 'result.json', 'completion.json')


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)

    def write(self, name, value):
        with (self.directory / name).open('xb') as stream:
            stream.write(encode(value)); stream.flush(); os.fsync(stream.fileno())

    def read(self, name):
        return (self.directory / name).read_bytes()


def request(query, role, nonce):
    config = deepcopy(CONFIGS[role])
    payload = {'model': config['model'], 'temperature': config['temperature'], 'max_tokens': config['max_tokens'],
               'provider': {'only': [config['route']], 'allow_fallbacks': False, 'require_parameters': True, 'max_price': config['max_price']},
               'messages': [{'role': 'system', 'content': query['prompt']}, {'role': 'user', 'content': encode(query['context']).decode()}],
               'response_format': {'type': 'json_schema', 'json_schema': {'name': 'direct_contributor_headers', 'strict': True, 'schema': query['schema']}}}
    binding = {'version': VERSION, 'query_id': query['query_id'], 'query_sha256': fingerprint(query),
               'semantic_payload_sha256': fingerprint({'messages': payload['messages'], 'response_format': payload['response_format']}),
               'configuration': config, 'configuration_sha256': fingerprint(config), 'nonce': nonce, 'payload': payload}
    return {'attempt_id': identity('attempt', binding), **binding}


def interpret(query, req, response):
    result = {'state': response.get('transport_status', 'transport_error'), 'answer': None, 'served': None,
              'usage': None, 'cost': None, 'cost_status': 'unknown', 'revision': None}
    if result['state'] != 'ok':
        require(result['state'] in {'timeout', 'transport_error', 'unavailable', 'budget_exhausted'}, 'invalid transport status')
        return result
    try:
        body = loads(base64.b64decode(response['body_base64'], validate=True))
        result['served'] = {'model': body.get('model'), 'provider': body.get('provider'), 'id': body.get('id')}
        result['usage'] = body.get('usage')
        cost = (body.get('usage') or {}).get('cost')
        if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0:
            result.update(cost=str(cost), cost_status='reported')
        config = req['configuration']
        if body.get('model') != config['model'] or body.get('provider') != config['served_provider']:
            result['state'] = 'identity_mismatch'; return result
        choices = body['choices']
        require(len(choices) == 1, 'expected one choice')
        choice = choices[0]; message = choice['message']
        if message.get('refusal') or choice.get('finish_reason') == 'content_filter':
            result['state'] = 'refusal'; return result
        if choice.get('finish_reason') == 'length':
            result['state'] = 'truncation'; return result
        require(choice.get('finish_reason') == 'stop' and not message.get('tool_calls'), 'incomplete or tool output')
        answer = validate_answer(query, loads(message['content']))
        result.update(state='accepted' if answer['state'] == 'selected' else 'abstained', answer=answer)
    except (ValueError, KeyError, TypeError, AttributeError):
        result['state'] = 'invalid_output'
    return result


def dispatch(query, req, transport, store):
    """One fresh attempt. No retry after any write or transport failure, including unknown commits."""
    require(query['version'] == OPERATION_VERSION and query['prompt'] == PROMPT and query['schema'] == SCHEMA
            and query['query_id'] == identity('query', {k:v for k,v in query.items() if k != 'query_id'}), 'altered logical query')
    require(req == request(query, req['configuration']['role'], req['nonce']), 'request/configuration mismatch')
    artifacts = {}
    calls = 0
    def save(name, value):
        store.write(name, value)
        artifacts[name] = encode(value)  # only after close/fsync succeeds
    def failure(state):
        return {'state': state, 'attempt_id': req['attempt_id'], 'model_calls': calls}
    try:
        save('query.json', query); save('request.json', req)
        require(all(store.read(n) == b for n, b in artifacts.items()), 'snapshot readback mismatch')
        save('started.json', {'attempt_id': req['attempt_id'], 'request_sha256': fingerprint(req), 'unix_seconds': time.time()})
    except (OSError, ValueError):
        return failure('persistence_failure')
    start = time.monotonic()
    if query['gate'] != 'eligible':
        response = {'transport_status': 'unavailable', 'reason': 'source_prerequisite_' + query['gate']}
    else:
        calls = 1
        try:
            response = transport(deepcopy(req))
        except TimeoutError:
            response = {'transport_status': 'timeout'}
        except Exception:
            response = {'transport_status': 'transport_error'}
    if response.get('transport_status') in {'unavailable', 'budget_exhausted'}:
        calls = 0
    result = {'version': VERSION, 'attempt_id': req['attempt_id'], 'query_id': query['query_id'],
              'role': req['configuration']['role'], 'model_calls': calls, 'elapsed_seconds': time.monotonic() - start,
              'validation': interpret(query, req, response)}
    if query['gate'] != 'eligible':
        result['validation']['state'] = query['gate']
    try:
        save('response.json', response); save('result.json', result)
        require(all(store.read(n) == b for n, b in artifacts.items()), 'artifact readback mismatch')
    except (OSError, ValueError):
        return failure('persistence_failure')
    marker = {'version': VERSION, 'attempt_id': req['attempt_id'], 'artifacts': {n: sha(b) for n, b in artifacts.items()}}
    try:
        store.write('completion.json', marker)
        require(store.read('completion.json') == encode(marker), 'completion readback mismatch')
    except (OSError, ValueError):
        return failure('commit_unknown')
    return result


def replay(store, query, role, nonce):
    """Expected query/role/config are supplied by the consumer, never trusted from a completion."""
    req = request(query, role, nonce)
    incomplete = {'state': 'incomplete_attempt', 'attempt_id': req['attempt_id'], 'model_calls': 0}
    try:
        marker = loads(store.read('completion.json'))
        require(set(marker) == {'version', 'attempt_id', 'artifacts'} and marker['version'] == VERSION
                and marker['attempt_id'] == req['attempt_id'], 'invalid completion identity')
        require(set(marker['artifacts']) == set(FILES) - {'completion.json'}, 'invalid inventory')
        raw = {n: store.read(n) for n in marker['artifacts']}
        require(all(sha(b) == marker['artifacts'][n] for n,b in raw.items()), 'artifact corruption')
        values = {n: loads(b) for n,b in raw.items()}
        require(values['query.json'] == query and values['request.json'] == req, 'saved query/request mismatch')
        require(values['started.json']['attempt_id'] == req['attempt_id'] and values['started.json']['request_sha256'] == fingerprint(req), 'start binding mismatch')
        result = values['result.json']
        expected = interpret(query, req, values['response.json'])
        if query['gate'] != 'eligible': expected['state'] = query['gate']
        require(set(result) == {'version','attempt_id','query_id','role','model_calls','elapsed_seconds','validation'}, 'result fields')
        require(result['version'] == VERSION and result['attempt_id'] == req['attempt_id'] and result['query_id'] == query['query_id']
                and result['role'] == role and type(result['model_calls']) is int
                and result['model_calls'] == int(query['gate'] == 'eligible' and values['response.json'].get('transport_status') not in {'unavailable','budget_exhausted'}) and result['validation'] == expected, 'result binding mismatch')
        return {**result, 'historical_model_calls': result['model_calls'], 'model_calls': 0}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return incomplete
