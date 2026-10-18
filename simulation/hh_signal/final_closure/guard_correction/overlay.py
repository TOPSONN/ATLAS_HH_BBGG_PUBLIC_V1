"""Exact reversible Route-A guard proposal for the frozen finite LO process."""
import difflib,hashlib
from pathlib import Path
from ..stop92_diagnostic import overlay as diagnostic
ORIGINAL_SHA256=diagnostic.ORIGINAL_SHA256
DIAGNOSTIC_SHA256='f235b6030461f4e71f4cb6563ef816201e775ad4c6255d337839ad6584571bc2'
REN_OLD=diagnostic.PREDICATES[1]
REN_NEW=('if(scale.le.0d0.or.MU_R.le.0d0.or.\n     $ abs(scale/q-1d0).gt.1d-10)',
 'POINT92_RENORMALIZATION_SCALE',[
 ('q_GeV','q'),('native_scale_GeV','scale'),('model_MU_R_GeV','MU_R'),
 ('native_scale_over_q','scale/q'),('relative_mismatch','abs(scale/q-1d0)')])
PREDICATES=(diagnostic.PREDICATES[0],REN_NEW,*diagnostic.PREDICATES[2:])
DECL_OLD='      real*8 p(0:3,nexternal),g1,g2,q,a,expected\n'
DECL_NEW=DECL_OLD+'      integer hi_i,hi_j\n'
MOMENTUM_FINITE=('      do hi_j=1,2\n      do hi_i=0,3\n'
    '      call finite(p(hi_i,hi_j))\n      enddo\n      enddo\n')
FINITE_OLD='      call finite(g2)\n'
FINITE_NEW=FINITE_OLD+('      call finite(scale)\n'
    '      call finite(q2fact(1))\n      call finite(q2fact(2))\n')

def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def once(text,old,new):
    if text.count(old)!=1:raise ValueError('UNIQUE_CORRECTION_REGION_REQUIRED')
    return text.replace(old,new)
def corrected(original):
    proposed=diagnostic.candidate(original)
    proposed=once(proposed,DECL_OLD,DECL_NEW+MOMENTUM_FINITE)
    proposed=once(proposed,FINITE_OLD,FINITE_NEW)
    return once(proposed,diagnostic.block(*REN_OLD),diagnostic.block(*REN_NEW))
def restore(proposed):
    proposed=once(proposed,diagnostic.block(*REN_NEW),diagnostic.block(*REN_OLD))
    proposed=once(proposed,FINITE_NEW,FINITE_OLD)
    proposed=once(proposed,DECL_NEW+MOMENTUM_FINITE,DECL_OLD)
    return diagnostic.restore(proposed)
def diff(before,after,name='native_checks.f'):
    return ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
        fromfile='frozen/'+name,tofile='proposed/'+name))
def source():
    original=(Path(__file__).resolve().parents[1]/'integration_runtime/native_checks.f').read_text()
    proposed=corrected(original)
    if restore(proposed)!=original:raise ValueError('REVERSAL_FAILED')
    return proposed
