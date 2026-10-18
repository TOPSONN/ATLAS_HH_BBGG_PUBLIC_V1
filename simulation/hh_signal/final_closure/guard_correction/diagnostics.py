"""Versioned scalar receipt reader; old diagnostic schemas stay unchanged."""
import re
from ..stop92_diagnostic.diagnostics import parse_record as old_parse,MAX_RECORD_BYTES
from .overlay import REN_NEW,REN_OLD

def parse_record(record):
    if len(record.encode('ascii'))>MAX_RECORD_BYTES or '\n' in record or '\r' in record:
        raise ValueError('DIAGNOSTIC_SERIALIZATION_BOUND')
    if ' POINT92_RENORMALIZATION_SCALE ' not in record:return old_parse(record)
    keys=tuple(re.findall(r'\s+([A-Za-z0-9_]+)=',record))
    if keys!=tuple(k for k,_ in REN_NEW[2]):raise ValueError('CORRECTED_RENORMALIZATION_SCHEMA_REQUIRED')
    # Reuse the independently tested numeric/bounds parser with an exact,
    # position-preserving field-name adapter. Never relabel a model ratio as
    # the physical native ratio in the returned scientific record.
    original=record
    for (new,_),(old,_) in zip(REN_NEW[2],REN_OLD[2]):
        original=original.replace(' '+new+'=', ' FIELD_'+old+'=')
    original=original.replace(' FIELD_',' ')
    parsed=old_parse(original)
    parsed['scalars']={new:parsed['scalars'][old] for (new,_),(old,_) in zip(REN_NEW[2],REN_OLD[2])}
    parsed['record_bytes']=len(record.encode('ascii'));parsed['schema']='SCIENTIFIC_ROUTE_A_V1'
    return parsed
