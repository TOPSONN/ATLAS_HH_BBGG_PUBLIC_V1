"""Generate/reverse a failure-only diagnostic overlay on the exact frozen guard."""
import difflib,hashlib,re
from pathlib import Path

ORIGINAL_SHA256='5cbe786a92c872cdbcd43440f8c5b8894b6d27da1ec883c66fc4ba6d402dabfb'
PREDICATES=(
 ('if(q.le.0d0.or.g1.lt.0d0.or.g2.lt.0d0)', 'POINT92_Q_OR_PDF',
  [('q_GeV','q'),('g1_dimensionless','g1'),('g2_dimensionless','g2'),('native_scale_GeV','scale')]),
 ('if(abs(MU_R/q-1d0).gt.1d-10)', 'POINT92_RENORMALIZATION_SCALE',
  [('q_GeV','q'),('MU_R_GeV','MU_R'),('native_scale_GeV','scale'),('MU_R_over_q','MU_R/q'),('relative_mismatch','abs(MU_R/q-1d0)')]),
 ('if(any(abs(q2fact/q**2-1d0).gt.1d-10))', 'POINT92_FACTORIZATION_SCALE',
  [('q_GeV','q'),('q2fact1_GeV2','q2fact(1)'),('q2fact2_GeV2','q2fact(2)'),('QF1_squared_over_q2','q2fact(1)/q**2'),
   ('QF2_squared_over_q2','q2fact(2)/q**2'),('native_scale_GeV','scale')]),
 ('if(a.le.0d0)', 'POINT92_ALPHA_NONPOSITIVE',
  [('q_GeV','q'),('alpha_actual','a'),('MU_R_GeV','MU_R'),('native_scale_GeV','scale')]),
 ('if(abs(a/expected-1d0).gt.1d-10)', 'POINT92_ALPHA_RUNNING_MISMATCH',
  [('q_GeV','q'),('alpha_actual','a'),('alpha_expected','expected'),('relative_mismatch','abs(a/expected-1d0)'),('native_scale_GeV','scale')]),
)

def block(predicate,identifier,fields):
    # Exactly one formatted record: the unchanged supervisor terminates as soon
    # as it sees HI_FAILURE, so a later scalar line would not be reliable.
    lines=['      '+predicate+' then',"      write(*,'(A,"+str(len(fields))+"(A,ES25.16E3))')",
           "     $ 'HI_FAILURE POINT92 "+identifier+"',"]
    for index,(label,value) in enumerate(fields):
        lines.append("     $ ' "+label+"=',"+value+(',' if index+1<len(fields) else ''))
    lines+=['      flush(6)','      stop 92','      endif']
    return '\n'.join(lines)+'\n'

def candidate(original):
    if hashlib.sha256(original.encode()).hexdigest()!=ORIGINAL_SHA256:raise ValueError('FROZEN_GUARD_DRIFT')
    result=original
    for predicate,identifier,fields in PREDICATES:
        old='      '+predicate+' stop 92\n'
        if result.count(old)!=1:raise ValueError('PREDICATE_NOT_UNIQUE:'+identifier)
        result=result.replace(old,block(predicate,identifier,fields))
    return result

def restore(proposed):
    result=proposed
    for predicate,identifier,fields in PREDICATES:
        new=block(predicate,identifier,fields)
        if result.count(new)!=1:raise ValueError('OVERLAY_BLOCK_DRIFT:'+identifier)
        result=result.replace(new,'      '+predicate+' stop 92\n')
    if hashlib.sha256(result.encode()).hexdigest()!=ORIGINAL_SHA256:raise ValueError('SUCCESS_PATH_OR_GUARD_CHANGED')
    return result

def exact_point(text):
    start=text.index('      subroutine hi_point(')
    match=re.search(r'^      end\s*$',text[start:],re.M|re.I)
    if match is None:raise ValueError('POINT_END_MISSING')
    end=start+match.end()+1
    return text[start:end]

def diff(original,proposed):
    return ''.join(difflib.unified_diff(original.splitlines(True),proposed.splitlines(True),
        fromfile='frozen/native_checks.f',tofile='proposed/native_checks_diagnostic.f'))
