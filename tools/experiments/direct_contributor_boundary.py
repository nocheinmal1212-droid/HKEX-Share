"""Experimental selected-logical-source dispatcher. No fixture keys or semantic answers.

This is not a production IR consumer. A request has an explicitly bound source snapshot,
literal source IDs, a selected projection, and separately persisted transport outcomes.
"""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path

VERSION = 'direct-contributor-attempt-v1'
MAX_CONTEXT_BYTES = 24000
MAX_IDS = 64
MAX_RESPONSE_BYTES = 131072
REASONS = ['supported_direct_breakdown', 'missing_evidence', 'ambiguous_relationship',
           'incompatible_context', 'unknown_context']


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('duplicate JSON key')
            result[k] = v
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def project(source, request, selected_ids):
    return {'operation': request['operation'], 'container_id': request['container_id'],
            'target_id': request['target_id'], 'candidate_ids': deepcopy(request['candidate_ids']),
            'evidence': [deepcopy(i) for i in source['items'] if i['id'] in selected_ids],
            'limitations': deepcopy(source['limitations'])}


def freeze(source, request, identity, *, selected_ids=None):
    source, request = deepcopy(source), deepcopy(request)
    selected_ids = deepcopy(selected_ids if selected_ids is not None else [i['id'] for i in source['items']])
    payload = project(source, request, selected_ids)
    return {'version': VERSION, 'identity': deepcopy(identity), 'request': request,
            'selected_ids': selected_ids, 'payload': payload, 'payload_sha256': sha(encode(payload))}


def outcome(state, reason, **extra):
    return {'state': state, 'reason': reason, **extra}


def precheck(source, trusted_identity, job):
    if (job.get('version') != VERSION or job.get('identity') != trusted_identity
            or trusted_identity.get('evidence_sha256') != sha(encode(source))):
        return outcome('rejected_input', 'source_binding_mismatch')
    ids = [i['id'] for i in source['items']]
    if len(ids) != len(set(ids)):
        return outcome('rejected_input', 'duplicate_id')
    request = job['request']
    if (set(request) != {'operation', 'container_id', 'target_id', 'candidate_ids'}
            or request['operation'] != 'select_direct_addends'
            or not isinstance(request['target_id'], str) or not request['target_id']):
        return outcome('rejected_input', 'invalid_request')
    if request['container_id'] != source['container_id']:
        return outcome('rejected_input', 'container_mismatch')
    target = request['target_id']
    if target not in ids:
        return outcome('precondition_abstention', 'target_absent')
    selected = job['selected_ids']
    if (not isinstance(selected, list) or len(selected) != len(set(selected))
            or not set(selected) <= set(ids)):
        return outcome('rejected_input', 'invalid_selection')
    if target not in selected:
        return outcome('rejected_input', 'target_not_selected')
    candidates = request['candidate_ids']
    if (not isinstance(candidates, list) or len(candidates) != len(set(candidates))
            or target in candidates or not set(candidates) <= set(selected)):
        return outcome('rejected_input', 'invalid_candidate_scope')
    target_item = next(i for i in source['items'] if i['id'] == target)
    if target_item.get('content_state') == 'unsupported' or target_item.get('text') is None:
        return outcome('precondition_abstention', 'unsupported_target_evidence')
    if target_item['text'] == '':
        return outcome('precondition_abstention', 'target_text_blank')
    if not candidates:
        return outcome('precondition_abstention', 'no_candidates')
    for item in source['items']:
        if item['id'] in selected and not set(item.get('header_refs', [])) <= set(selected):
            return outcome('rejected_input', 'header_not_selected')
    payload = encode(job['payload'])
    if sha(payload) != job['payload_sha256']:
        return outcome('rejected_input', 'request_hash_mismatch')
    if project(source, request, selected) != job['payload']:
        return outcome('rejected_input', 'projection_preservation_failure')
    if len(payload) > MAX_CONTEXT_BYTES or len(selected) > MAX_IDS:
        return outcome('rejected_input', 'context_limit_exceeded')
    return outcome('eligible', 'preconditions_met')


def output_schema(job):
    return {'type': 'object', 'additionalProperties': False,
            'required': ['action', 'target_id', 'contributor_ids', 'support_ids', 'reason'],
            'properties': {
                'action': {'type': 'string', 'enum': ['select', 'abstain']},
                'target_id': {'type': 'string', 'enum': [job['request']['target_id']]},
                'contributor_ids': {'type': 'array', 'items': {'type': 'string', 'enum': sorted(job['request']['candidate_ids'])}},
                'support_ids': {'type': 'array', 'items': {'type': 'string', 'enum': sorted(job['selected_ids'])}},
                'reason': {'type': 'string', 'enum': REASONS}}}


def postcheck(job, output):
    if not isinstance(output, dict) or set(output) != {'action', 'target_id', 'contributor_ids', 'support_ids', 'reason'}:
        return outcome('invalid_output', 'invalid_output_shape')
    if output['action'] not in ('select', 'abstain') or output['reason'] not in REASONS:
        return outcome('invalid_output', 'invalid_vocabulary')
    if output['target_id'] != job['request']['target_id']:
        return outcome('invalid_output', 'wrong_target')
    for field in ['contributor_ids', 'support_ids']:
        values = output[field]
        if not isinstance(values, list) or any(not isinstance(i, str) for i in values):
            return outcome('invalid_output', 'invalid_id_array')
        if len(values) != len(set(values)):
            return outcome('invalid_output', 'duplicate_output_id')
        if not set(values) <= set(job['selected_ids']):
            return outcome('invalid_output', 'unknown_id')
    if not set(output['contributor_ids']) <= set(job['request']['candidate_ids']):
        return outcome('invalid_output', 'id_outside_requested_scope')
    if output['action'] == 'abstain':
        if output['contributor_ids'] or output['reason'] == 'supported_direct_breakdown':
            return outcome('invalid_output', 'inconsistent_abstention')
        return outcome('model_abstention', 'model_abstained')
    if not output['contributor_ids'] or not output['support_ids'] or output['reason'] != 'supported_direct_breakdown':
        return outcome('invalid_output', 'inconsistent_selection')
    return outcome('structure_accepted', 'semantic_correctness_unverified')


def interpret_response(job, response):
    if response['transport_status'] != 'received':
        return outcome('transport_failure', response['transport_status'])
    if response['http_status'] != 200:
        return outcome('transport_failure', 'http_error', http_status=response['http_status'])
    raw = response['body']
    if len(raw) > MAX_RESPONSE_BYTES:
        return outcome('incomplete_response', 'response_too_large')
    try:
        envelope = parse(raw)
        choices = envelope['choices']
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise ValueError('one choice required')
        choice = choices[0]
        if choice.get('finish_reason') != 'stop':
            return outcome('incomplete_response', 'truncated' if choice.get('finish_reason') == 'length' else 'incomplete_response')
        message = choice['message']
        if not isinstance(message, dict):
            raise ValueError('message required')
        if message.get('refusal'):
            return outcome('model_refusal', 'refusal')
        if message.get('tool_calls'):
            return outcome('invalid_output', 'unexpected_response_mode')
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return outcome('invalid_output', 'malformed_response')
    try:
        output = parse(message['content'])
    except (ValueError, TypeError, KeyError):
        return outcome('invalid_output', 'malformed_json')
    return {**postcheck(job, output), 'model_output': output}


class Store:
    """Exclusive immutable writes. Completion is only a fully parseable result.json."""
    def __init__(self, directory):
        self.directory = Path(directory)

    def write(self, name, data):
        with (self.directory / name).open('xb') as stream:
            stream.write(data)
            stream.flush()

    def read(self, name):
        return (self.directory / name).read_bytes()


def dispatch(source, trusted_identity, job, transport, store, configuration):
    """One attempt, zero retries. Persistence failure is also returned to the caller."""
    source, job, configuration = deepcopy(source), deepcopy(job), deepcopy(configuration)
    request_bytes = encode(job)
    common = {'version': VERSION, 'source_identity': deepcopy(trusted_identity),
              'request_sha256': sha(request_bytes), 'configuration': configuration,
              'configuration_sha256': sha(encode(configuration)), 'model_calls': 0}
    try:
        store.write('source.json', encode(source))
        store.write('request.json', request_bytes)
    except OSError:
        return {**common, **outcome('persistence_failure', 'request_not_persisted'), 'persisted': False}
    gate = precheck(source, trusted_identity, job)
    if store.read('request.json') != request_bytes:
        gate = outcome('rejected_input', 'request_hash_mismatch')
    if gate['state'] != 'eligible':
        result = {**common, **gate}
    else:
        try:
            store.write('started.json', encode(common))
        except OSError:
            return {**common, **outcome('persistence_failure', 'request_not_persisted'), 'persisted': False}
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
        response_record = {k: v for k, v in response.items() if k != 'body'}
        if raw is not None:
            response_record.update(body_base64=base64.b64encode(raw).decode(), body_sha256=sha(raw))
        try:
            store.write('response.json', encode(response_record))
        except OSError:
            return {**common, **outcome('persistence_failure', 'result_not_persisted'), 'persisted': False}
        result = {**common, **interpret_response(job, response),
                  'response_record_sha256': sha(encode(response_record))}
        if sent != job['payload']:
            result.update(state='invalid_output', reason='scope_not_redefined')
    try:
        store.write('result.json', encode(result))
    except OSError:
        return {**common, **outcome('persistence_failure', 'result_not_persisted'), 'persisted': False}
    return {**result, 'persisted': True}


def replay(directory):
    directory = Path(directory)
    try:
        result = parse((directory / 'result.json').read_bytes())
    except FileNotFoundError:
        return outcome('incomplete_attempt', 'completion_unknown', model_calls=0,
                       historical_model_calls=None)
    except (ValueError, TypeError):
        return outcome('incomplete_attempt', 'invalid_terminal_record', model_calls=0)
    if sha((directory / 'request.json').read_bytes()) != result['request_sha256']:
        return outcome('incomplete_attempt', 'request_hash_mismatch', model_calls=0)
    if 'response_record_sha256' in result:
        if sha((directory / 'response.json').read_bytes()) != result['response_record_sha256']:
            return outcome('incomplete_attempt', 'response_hash_mismatch', model_calls=0)
    return {**result, 'historical_model_calls': result['model_calls'], 'model_calls': 0}
