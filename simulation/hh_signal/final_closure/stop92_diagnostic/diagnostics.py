"""Strict bounded single-record scalar parser, independent of the runtime bridge."""
import math,re
from .overlay import PREDICATES
SCHEMAS={identifier:tuple(label for label,_ in fields) for _,identifier,fields in PREDICATES}
MAX_RECORD_BYTES=768

def parse_record(record):
    if '\n' in record or '\r' in record or len(record.encode('ascii'))>MAX_RECORD_BYTES:
        raise ValueError('DIAGNOSTIC_SERIALIZATION_BOUND')
    tokens=record.split()
    if len(tokens)<3 or tokens[:2]!=['HI_FAILURE','POINT92'] or tokens[2] not in SCHEMAS:
        raise ValueError('UNKNOWN_POINT92_IDENTIFIER')
    identifier=tokens[2]
    # ES25.16E3 creates spaces between '=' and its value. Labels must occur in
    # the exact reviewed order and no additional payload is accepted.
    tail=record[record.index(identifier)+len(identifier):]
    pairs=re.findall(r'\s+([A-Za-z0-9_]+)=\s*([^\s]+)',tail)
    rebuilt=''.join(' '+key+'='+value for key,value in pairs)
    if re.sub(r'\s+','',tail)!=re.sub(r'\s+','',rebuilt) or tuple(k for k,_ in pairs)!=SCHEMAS[identifier]:
        raise ValueError('UNREVIEWED_SCALAR_FIELDS')
    values={}
    for key,raw in pairs:
        if len(raw)>32 or not re.fullmatch(r'[+-]?(?:[0-9]+\.[0-9]+(?:[EeDd][+-][0-9]+)?|NaN|Infinity|Inf)',raw,re.I):
            raise ValueError('INVALID_SCALAR_TOKEN')
        value=float(raw.replace('D','E').replace('d','e'))
        # Do not silently turn an inherited nonfinite value into a finite zero.
        values[key]={'value':value,'representation':raw} if math.isfinite(value) else {'value':None,'nonfinite':raw}
    return {'identifier':identifier,'scalars':values,'record_bytes':len(record.encode('ascii')),
        'precision':'ES25.16E3 / binary64 scalar inputs; units encoded in labels','contains_event_vectors':False}
