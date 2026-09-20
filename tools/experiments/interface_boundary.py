"""Experimental typed request boundary; no accounting interpretation or fixture imports."""
from copy import deepcopy


def decision(stage, state, reason):
    return {'stage': stage, 'state': state, 'reason': reason}


def precheck(request):
    if not isinstance(request, dict) or set(request) != {'operation', 'target_id', 'evidence'}:
        return decision('input_validation', 'rejected', 'invalid_request_shape')
    op, target, evidence = request['operation'], request['target_id'], request['evidence']
    if op not in ('select_unique_total', 'classify_target'):
        return decision('input_validation', 'rejected', 'unsupported_operation')
    if op == 'classify_target' and (not isinstance(target, str) or not target):
        return decision('input_validation', 'rejected', 'required_target_id_missing')
    if op == 'select_unique_total' and target is not None:
        return decision('input_validation', 'rejected', 'unexpected_target_id')
    if not isinstance(evidence, list):
        return decision('input_validation', 'rejected', 'invalid_evidence_shape')
    ids = set()
    for item in evidence:
        if (not isinstance(item, dict) or set(item) != {'id', 'text'}
                or not isinstance(item['id'], str) or not item['id'] or not isinstance(item['text'], str)):
            return decision('input_validation', 'rejected', 'invalid_evidence_item')
        if item['id'] in ids:
            return decision('input_validation', 'rejected', 'duplicate_evidence_id')
        ids.add(item['id'])
    if not evidence:
        return decision('precondition', 'abstained', 'no_evidence')
    if op == 'classify_target' and target not in ids:
        return decision('precondition', 'abstained', 'target_missing')
    return decision('precondition', 'eligible', 'preconditions_met')


def user_payload(request):
    if precheck(request)['state'] != 'eligible':
        raise ValueError('Cannot construct a model request from ineligible input')
    instruction = ('Select the total label from the supplied evidence.'
                   if request['operation'] == 'select_unique_total' else
                   'Classify ' + request['target_id'] + ' as a total label if supported by the supplied evidence.')
    return {'instruction': instruction, 'evidence': deepcopy(request['evidence'])}


def postcheck(request, output):
    if precheck(request)['state'] != 'eligible':
        raise ValueError('Output validation requires eligible input')
    if not isinstance(output, dict) or set(output) != {'action', 'evidence_id', 'role'}:
        return decision('output_validation', 'rejected', 'invalid_output_shape')
    if output['action'] == 'abstain':
        if output['evidence_id'] is not None or output['role'] is not None:
            return decision('output_validation', 'rejected', 'abstention_fields_must_be_null')
    elif output['action'] == 'label':
        if not isinstance(output['evidence_id'], str) or output['role'] != 'total_label':
            return decision('output_validation', 'rejected', 'invalid_label_fields')
        if output['evidence_id'] not in {e['id'] for e in request['evidence']}:
            return decision('output_validation', 'rejected', 'returned_id_not_in_evidence')
        if request['operation'] == 'classify_target' and output['evidence_id'] != request['target_id']:
            return decision('output_validation', 'rejected', 'selected_id_differs_from_requested_target')
    else:
        return decision('output_validation', 'rejected', 'invalid_action')
    return decision('output_validation', 'accepted', 'structure_and_target_valid')


def dispatch(request, transport):
    frozen_request = deepcopy(request)
    gate = precheck(frozen_request)
    if gate['state'] != 'eligible':
        return {**gate, 'model_calls': 0, 'model_output': None}
    output = transport(user_payload(frozen_request))
    raw_output = deepcopy(output)
    return {**postcheck(frozen_request, raw_output), 'model_calls': 1, 'model_output': raw_output}
