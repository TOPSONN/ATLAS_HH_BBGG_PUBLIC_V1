"""Execute one already-reserved MG5 run using an isolated release copy."""
import sys,os,runpy
from pathlib import Path

def main():
    root=Path(sys.argv[1]).resolve();driver=Path(sys.argv[2]).resolve()
    protected=[Path(p).resolve() for p in sys.argv[3:]]
    def forbidden(value):
        if not isinstance(value,(str,bytes,os.PathLike)):return False
        p=Path(os.fsdecode(value)).resolve()
        return any(p==r or p.is_relative_to(r) for r in protected)
    def audit(event,args):
        targets=[]
        if event=='open':
            p,mode,flags=args
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):targets=[p]
        elif event in ('os.remove','os.mkdir','os.rmdir','os.chmod','os.utime','os.truncate'):targets=args[:1]
        elif event=='os.rename':targets=args[:2]
        if any(forbidden(t) for t in targets):raise PermissionError('PINNED_INSTALLATION_WRITE_FORBIDDEN')
        if event=='socket.connect':raise PermissionError('GENERATOR_NETWORK_INSTALL_FORBIDDEN')
    sys.addaudithook(audit);sys.path.insert(0,str(root))
    import madgraph
    if Path(madgraph.MG5DIR).resolve()!=root:raise RuntimeError('wrong private MG5')
    madgraph.ReadWrite=False
    entry=root/'bin/mg5_aMC';sys.argv=[str(entry),str(driver)]
    runpy.run_path(str(entry),run_name='__main__')
if __name__=='__main__':main()
