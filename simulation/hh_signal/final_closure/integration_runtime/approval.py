"""Out-of-band human review, never a JSON/flag/environment authorization.

The operator must first have the human's explicit approval in the trusted
conversation. A second, controlling-terminal confirmation binds its exact
scope. This is an operator boundary, not protection against arbitrary Python
code execution or a hostile account owner. No receipt can create this object.
"""
import hashlib,json,os,re,time
from .contract import require,identity,PHYSICS_SHA,SEEDS,CAPS

_SEAL=object()
CONSUMED={'58d39888a024028e32f3071db9215c0db6fe0a89',
 '79f779ef6d96340681242f86afe06bc90975728d','1f3c5fc4efa141a0e3e6831aa3b44c0e6bd32ee7',
 '4b1635073b6b1cd3096ee268a3c7858dea3da3b1','1b0b34bb0ee57b7ea8b073ffa49262b5e434cf00'}

class HumanReview:
    def __init__(self,seal,scope):
        require(seal is _SEAL,'NO_FILE_OR_FLAG_CAN_ISSUE_HUMAN_APPROVAL')
        self._seal=seal;self.scope=json.loads(json.dumps(scope));self.pid=os.getpid()
        self.digest=identity(self.scope)

def scope(action,revision,root,source_identity,*,full_receipt=None,binary_identity=None):
    require(action in ['BUILD_ONLY','BINARY_REVIEW','PHYSICAL_RESTART'],'UNKNOWN_REVIEW_ACTION')
    require(re.fullmatch('[0-9a-f]{40}',revision or '') and revision not in CONSUMED,'CONSUMED_OR_UNCORRECTED_REVISION')
    profile={}
    if action=='BUILD_ONLY':
        from ..resource_closure.backend import load_profile
        profile={'full_build_resource_profile':load_profile('BUILD_ONLY')}
    return {**profile,'action':action,'revision':revision,'output':str(root),'source_binding_identity':identity(source_identity),
        'physics_contract_sha256':PHYSICS_SHA,'seeds':list(SEEDS),'ceilings':CAPS,
        'FULL_BUILD_RECEIPT_IDENTITY':full_receipt,'IMMUTABLE_BINARY_SOURCE_IDENTITY':binary_identity}

def confirm(expected):
    """Only invoke after a separate explicit human decision; never auto-answer.

    No --approve switch, piped stdin, authorization JSON or env variable is read.
    A binary review and physical restart are distinct confirmations/digests.
    """
    # A tty is not seekable: separate read/write streams avoid BufferedRandom.
    with open('/dev/tty','w',encoding='utf-8',buffering=1) as output,open('/dev/tty','r',encoding='utf-8') as input_stream:
        require(os.isatty(output.fileno()) and os.isatty(input_stream.fileno()),'CONTROLLING_HUMAN_TERMINAL_REQUIRED')
        require(os.fstat(output.fileno()).st_rdev==os.fstat(input_stream.fileno()).st_rdev,'HUMAN_TERMINAL_DEVICE_MISMATCH')
        challenge='APPROVE '+expected['action']+' '+identity(expected)
        output.write('\nEXTERNAL HUMAN APPROVAL OF THIS EXACT SCOPE IS REQUIRED:\n'+json.dumps(expected,indent=2)+'\n'+challenge+'\n> ')
        answer=input_stream.readline(256).rstrip('\n')
        require(answer==challenge,'EXPLICIT_HUMAN_SCOPE_CONFIRMATION_REQUIRED')
    return HumanReview(_SEAL,expected)

def verify(review,expected):
    require(type(review) is HumanReview and review._seal is _SEAL and review.pid==os.getpid(),
        'SEPARATE_HUMAN_REVIEW_REQUIRED_NOT_EDITABLE_DATA')
    require(review.digest==identity(review.scope)==identity(expected),'STALE_OR_WRONG_HUMAN_REVIEW_SCOPE')
    return {'status':'EXTERNAL_OPERATOR_REVIEW_SCOPE_BOUND','scope':expected,'scope_sha256':review.digest}


def confirm_fd(expected,fd):
    """Future isolated worker: the actual caller's pinned human TTY descriptor.

    This reads a manual challenge in this PID. It accepts no answer argument,
    approval file, flag or environment variable. Never invoke in automated tests.
    """
    import stat
    require(type(fd) is int and fd>=3 and os.isatty(fd),'PINNED_HUMAN_TERMINAL_REQUIRED')
    info=os.fstat(fd)
    require(stat.S_ISCHR(info.st_mode) and info.st_rdev!=0,'HUMAN_TERMINAL_DEVICE_REQUIRED')
    challenge='APPROVE '+expected['action']+' '+identity(expected)
    message='\nEXTERNAL HUMAN APPROVAL OF THIS EXACT SCOPE IS REQUIRED:\n'+json.dumps(expected,indent=2)+'\n'+challenge+'\n> '
    os.write(fd,message.encode('utf-8'))
    raw=bytearray()
    while len(raw)<256:
        byte=os.read(fd,1)
        if not byte or byte==b'\n':break
        raw.extend(byte)
    require(bytes(raw)==challenge.encode('ascii'),'EXPLICIT_HUMAN_SCOPE_CONFIRMATION_REQUIRED')
    return HumanReview(_SEAL,expected)
