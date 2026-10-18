"""Generate/reverse the exact future builder diff; do not import or run it."""
import ast,hashlib
from pathlib import Path
from .overlay import once,diff
HERE=Path(__file__).resolve().parent
# Set from the unchanged production builder, not from a reconstructed template.
BUILDER_ORIGINAL_SHA256='13f2210057ebdce2eac67048523aaa6f3b2a5e73351ada67069bb25a4cfb3d0d'
REGIONS=(
 ('from .overlay import apply\n','from .overlay import apply\nfrom ..guard_correction.overlay import source as corrected_guard_source\nfrom ..guard_correction.review_contract import (validate_build_approval,\n    full_source_identity,guard_descriptor,SCHEMA,binary_identity,\n    verify_dependency_sources,verify_compiler)\n'),
 ('def prepare(root):\n','def prepare(root, *, build_review=None):\n    require(isinstance(build_review,dict),"SEPARATE_BUILD_APPROVAL_REQUIRED")\n    validate_build_approval(build_review,build_review.get("revision"),full_source_identity())\n    check_revision(build_review["revision"])\n'),
 ("    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran'\n", "    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran'\n    verify_compiler(compiler)\n"),
 ("        old=REPO/f'simulation/hh_signal/config_lock/evidence/seed_{seed}/cards'", "        verify_dependency_sources(process)\n        old=REPO/f'simulation/hh_signal/config_lock/evidence/seed_{seed}/cards'"),
 ("        flags=[compiler,'-O0'", "        corrected_guard=sub/'native_checks_corrected.f'\n        corrected_guard.write_text(corrected_guard_source())\n        require(sha(corrected_guard)==guard_descriptor()['native_guard_sha256'],'CORRECTED_GUARD_BYTES_DRIFT')\n        flags=[compiler,'-O0'"),
 ("files=[HERE/'observers.f90',HERE/'native_checks.f',sub/'native_io_only.f90']", "files=[HERE/'observers.f90',corrected_guard,sub/'native_io_only.f90']"),
 ("'physics_contract_sha256':PHYSICS_SHA,'source_identity':sources(),'replicas':replicas,'ceilings':CAPS,", "'schema':SCHEMA,'approved_build_source_revision':build_review['revision'],\n        'guard_correction':guard_descriptor(),\n        'physics_contract_sha256':PHYSICS_SHA,'source_identity':full_source_identity(),'replicas':replicas,'ceilings':CAPS,"),
 ("    save(root/'review_build.json',manifest);return manifest", "    manifest['immutable_binary_identity']=binary_identity(manifest)\n    save(root/'review_build.json',manifest);return manifest"),
)
def candidate(original):
    if hashlib.sha256(original.encode()).hexdigest()!=BUILDER_ORIGINAL_SHA256:raise ValueError('BUILDER_BASE_DRIFT')
    result=original
    for old,new in REGIONS:result=once(result,old,new)
    ast.parse(result);return result
def restore(proposed):
    for old,new in reversed(REGIONS):proposed=once(proposed,new,old)
    if hashlib.sha256(proposed.encode()).hexdigest()!=BUILDER_ORIGINAL_SHA256:raise ValueError('BUILDER_UNDECLARED_CHANGE')
    return proposed
def source():
    # Preserve the exact published proposal after activation changes build.py.
    proposed=(HERE/'build_corrected_proposal.py').read_text()
    return candidate(restore(proposed))
