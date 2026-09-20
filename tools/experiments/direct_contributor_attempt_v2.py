"""Versioned commit protocol for experimental logical-source attempts.

The frozen v1 request/semantic boundary is reused without changing historical runs.
Only a valid completion record with all matching artifacts authorizes replay.
"""
import base64
from copy import deepcopy
import os
from pathlib import Path

from direct_contributor_boundary import encode, freeze, interpret_response, outcome, parse, precheck, sha

VERSION = 'direct-contributor-attempt-v2'
COMPLETION = 'completion.json'


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)

    def write(self, name, data):
        with (self.directory / name).open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    def read(self, name):
        return (self.directory / name).read_bytes()


def incomplete(reason):
    return outcome('incomplete_attempt', reason, model_calls=0, historical_model_calls=None)


def dispatch(source, trusted_identity, job, transport, store, configuration):
    """Single-owner fresh directory; no retries, cleanup, overwrites or inferred commits."""
    source, job, configuration = deepcopy(source), deepcopy(job), deepcopy(configuration)
    common = {'version': VERSION, 'source_identity': deepcopy(trusted_identity),
              'source_snapshot_sha256': sha(encode(source)),
              'request_sha256': sha(encode(job)), 'configuration': configuration,
              'configuration_sha256': sha(encode(configuration)), 'model_calls': 0}
    artifacts = {}

    def save(name, value):
        raw = encode(value)
        store.write(name, raw)
        # Save expected bytes only after write/flush/close returned successfully.
        artifacts[name] = raw

    def failure(reason):
        return {**common, **outcome('persistence_failure', reason), 'persisted': False}

    # A reused directory refers to its previous attempt; never dispatch into it.
    try:
        store.read(COMPLETION)
    except FileNotFoundError:
        pass
    except OSError:
        return failure('completion_preflight_failed')
    else:
        return {**common, **outcome('attempt_conflict', 'completion_already_exists'), 'persisted': False}
    try:
        save('source.json', source)
        save('request.json', job)
        if any(store.read(name) != raw for name, raw in artifacts.items()):
            return failure('snapshot_readback_mismatch')
    except FileExistsError:
        return {**common, **outcome('attempt_conflict', 'snapshot_already_exists'), 'persisted': False}
    except OSError:
        return failure('request_not_persisted')
    gate = precheck(source, trusted_identity, job)
    if gate['state'] != 'eligible':
        result = {**common, **gate}
    else:
        try:
            save('started.json', common)
            if store.read('started.json') != artifacts['started.json']:
                return failure('start_readback_mismatch')
        except OSError:
            return failure('request_not_persisted')
        common['model_calls'] = 1
        sent = deepcopy(job['payload'])
        try:
            response = transport(sent)
        except TimeoutError:
            response = {'transport_status': 'timeout'}
        except OSError:
            response = {'transport_status': 'transport_error'}
        except Exception:
            response = {'transport_status': 'transport_exception'}
        raw = response.get('body')
        record = {k: v for k, v in response.items() if k != 'body'}
        if raw is not None:
            record.update(body_base64=base64.b64encode(raw).decode(), body_sha256=sha(raw))
        try:
            save('response.json', record)
        except OSError:
            return failure('result_not_persisted')
        result = {**common, **interpret_response(job, response),
                  'response_record_sha256': sha(artifacts['response.json'])}
        if sent != job['payload']:
            result.update(state='invalid_output', reason='scope_not_redefined')
    try:
        save('result.json', result)
        if any(store.read(name) != raw for name, raw in artifacts.items()):
            return failure('artifact_readback_mismatch')
    except OSError:
        return failure('result_not_persisted')
    marker = {'version': VERSION, 'artifacts': {name: sha(raw) for name, raw in artifacts.items()}}
    try:
        store.write(COMPLETION, encode(marker))
        if store.read(COMPLETION) != encode(marker):
            raise OSError('completion readback mismatch')
    except OSError:
        # The marker may have reached storage before the exception. Replay must resolve it.
        return {**common, **outcome('commit_unknown', 'completion_not_confirmed'), 'persisted': None}
    return {**result, 'persisted': True}


def replay(directory):
    """Read-only: v1/uncommitted/partial/tampered attempts never become completed v2 attempts."""
    store = Store(directory)
    try:
        marker = parse(store.read(COMPLETION))
    except FileNotFoundError:
        return incomplete('completion_unknown')
    except (OSError, ValueError, TypeError):
        return incomplete('invalid_completion_record')
    if (not isinstance(marker, dict) or set(marker) != {'version', 'artifacts'}
            or marker['version'] != VERSION or not isinstance(marker['artifacts'], dict)):
        return incomplete('invalid_completion_record')
    hashes = marker['artifacts']
    base = {'source.json', 'request.json', 'result.json'}
    dispatched = base | {'started.json', 'response.json'}
    if set(hashes) not in (base, dispatched):
        return incomplete('invalid_artifact_inventory')
    if any(not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
           for v in hashes.values()):
        return incomplete('invalid_artifact_hash')
    try:
        # Inventory names are checked BEFORE any path is dereferenced.
        raw = {name: store.read(name) for name in hashes}
        if any(sha(data) != hashes[name] for name, data in raw.items()):
            return incomplete('artifact_hash_mismatch')
        values = {name: parse(data) for name, data in raw.items()}
        if any(not isinstance(v, dict) for v in values.values()):
            return incomplete('invalid_artifact_record')
        result = values['result.json']
        if result['version'] != VERSION:
            return incomplete('unsupported_attempt_version')
        calls = result['model_calls']
        if type(calls) is not int or calls not in (0, 1) or (set(hashes) == dispatched) != (calls == 1):
            return incomplete('invalid_dispatch_inventory')
        if (result['request_sha256'] != hashes['request.json']
                or result['source_snapshot_sha256'] != hashes['source.json']
                or result['configuration_sha256'] != sha(encode(result['configuration']))):
            return incomplete('invalid_result_binding')
        if calls:
            started = values['started.json']
            if (started['version'] != VERSION or started['model_calls'] != 0
                    or any(started[k] != result[k] for k in ('request_sha256', 'source_identity', 'source_snapshot_sha256',
                                                           'configuration', 'configuration_sha256'))
                    or result['response_record_sha256'] != hashes['response.json']):
                return incomplete('invalid_dispatch_binding')
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return incomplete('missing_or_invalid_artifact')
    return {**result, 'historical_model_calls': calls, 'model_calls': 0}
