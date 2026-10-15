"""Pinned native writer suppression plus independent event-output audit."""
import gzip,io,re
from pathlib import Path
from .contract import require,sha,lock

def subroutine(text,name):
    match=re.search(r'(?im)^      subroutine '+re.escape(name)+r'\b[^\n]*\n',text)
    require(match is not None,'MISSING_PINNED_SUBROUTINE:'+name)
    end=re.search(r'(?im)^      end\s*$',text[match.end():]);require(end is not None,'MISSING_SUBROUTINE_END')
    return match.start(),match.end()+end.end()

def suppress_writers(original):
    require(__import__('hashlib').sha256(original.encode()).hexdigest()==lock()['native_sources']['unwgt.f'],'UNREVIEWED_NATIVE_WRITER_SOURCE')
    # Keep unwgt and Zoom_Event untouched: their RNG/adaptation semantics must
    # not be silently replaced by a different integration algorithm.
    replacements={
        'clear_events':"""      subroutine clear_events
      implicit none
      include 'genps.inc'
      double precision twgt,maxwgt,swgt(maxevents)
      integer lun,nw,itmin
      common/to_unwgt/twgt,maxwgt,swgt,lun,nw,itmin
      nw=0
      maxwgt=0d0
      call hh_guard_count(3)
      end""",
        'store_events':"""      subroutine store_events(force_max_wgt,scale_to_xsec)
      implicit none
      double precision force_max_wgt
      logical scale_to_xsec
      integer th_nunwgt,neventswritten
      double precision th_maxwgt
      common/theoretical_unwgt_max/th_maxwgt,th_nunwgt
      common/to_eventswritten/neventswritten
C     Native final unweighting/serialization is entirely suppressed.
      th_maxwgt=0d0
      th_nunwgt=0
      neventswritten=0
      call hh_guard_count(2)
      end""",
        'write_leshouche':"""      subroutine write_leshouche(p,wgt,numproc,do_write_events)
      implicit none
      include 'nexternal.inc'
      double precision p(0:3,nexternal),wgt
      integer numproc
      logical do_write_events
C     No four-vectors, weights or candidate records are serialized.
      call hh_guard_count(1)
      end"""}
    for name,body in replacements.items():
        start,end=subroutine(original,name);original=original[:start]+body+original[end:]
    original+='\n'+(Path(__file__).parent/'src/writer_counters.f').read_text()
    require(not re.search(r'(?im)^\s*(?:open\s*\(|call write_event\b)',original),'UNSAFE_NATIVE_SAMPLE_WRITER')
    return original

def suppress_permanent_writer(original):
    require(__import__('hashlib').sha256(original.encode()).hexdigest()==lock()['native_sources']['rw_events.f'],'UNREVIEWED_PERMANENT_WRITER_SOURCE')
    # Retain other I/O helpers, but make every direct event-serialization call
    # fatal. Original continuation lines are irrelevant after body replacement.
    start,end=subroutine(original,'write_event')
    return original[:start]+"""      subroutine write_event
      implicit none
      write(*,*) 'HH_GUARD_PERMANENT_EVENT_WRITE_FORBIDDEN'
      stop 86
      end"""+original[end:]

def output_audit(root):
    root=Path(root);require(root.is_dir() and not root.is_symlink(),'UNSAFE_AUDIT_ROOT')
    files=[];events=0
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(),'OUTPUT_SYMLINK_FORBIDDEN')
        if not p.is_file():continue
        relative=p.relative_to(root).as_posix();lower=p.name.lower()
        require(p.stat().st_size<=64*1024**2,'UNREVIEWED_LARGE_OUTPUT')
        require(p.suffix.lower() not in ['.lhe','.root','.hepmc','.hepmc3'] and not
            lower.endswith(('.lhe.gz','.hepmc.gz','.hepmc3.gz')) and
            lower not in ['events.dat','unweighted_events','pythia8_events','tag_1_delphes_events.root'],'UNEXPECTED_PHYSICAL_EVENT_OUTPUT:'+relative)
        # Scan all non-binary text, even an unexpected extension or compressed
        # file. Known binary object/executable output is separately hash-bound.
        raw=p.read_bytes()
        if raw.startswith(b'\x1f\x8b'):
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:raw=stream.read(64*1024**2+1)
            require(len(raw)<=64*1024**2,'EXPANDED_OUTPUT_SIZE_CAP')
        count=len(re.findall(rb'<event(?:\s[^>]*)?>',raw,re.I));events+=count
        require(count==0 and b'<LesHouchesEvents' not in raw and b'HepMC::Asciiv' not in raw and
            not raw.startswith(b'root'),'EVENT_RECORD_IN_DISGUISED_OUTPUT:'+relative)
        require(b'\0' not in raw,'UNREVIEWED_BINARY_RUNTIME_OUTPUT:'+relative)
        files.append({'path':relative,'bytes':p.stat().st_size,'sha256':sha(p)})
    return {'status':'PASS_ZERO_RETAINED_OUTPUT_POSTCONDITION','retained_event_records':events,'files':files,
        'scope':'filesystem postcondition; not proof that native survey was executed or never wrote transient records'}

def publication_guard(root):
    proof=output_audit(root)
    require(not any(Path(r['path']).suffix.lower() in ['.pdf','.png'] for r in proof['files']),'UNAPPROVED_FIGURE')
    return proof

def workspace_envelope(root,immutable,writable):
    from .contract import validate_source_inventory
    root=Path(root).resolve();writable=Path(writable).resolve()
    require(writable.is_relative_to(root) and writable!=root,'UNSAFE_WRITABLE_ENVELOPE')
    validate_source_inventory(immutable,root);known={r['path'] for r in immutable}
    for p in root.rglob('*'):
        require(not p.is_symlink(),'WORKSPACE_SYMLINK')
        if p.is_file() and p.relative_to(root).as_posix() not in known:
            require(p.resolve().is_relative_to(writable),'UNEXPECTED_WRITE_OUTSIDE_RUNTIME:'+p.relative_to(root).as_posix())
    return publication_guard(writable)
