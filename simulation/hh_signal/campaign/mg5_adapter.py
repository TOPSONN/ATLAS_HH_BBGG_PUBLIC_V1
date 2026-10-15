"""Fixed reviewed MG5 model/export driver in a private source copy."""
import sys,json
from pathlib import Path

def main():
    root=Path(sys.argv[1]).resolve();target=Path(sys.argv[2]).resolve()
    require= lambda ok,msg: None if ok else (_ for _ in ()).throw(RuntimeError(msg))
    require(target.parent==root.parent,'export output must share private build parent')
    sys.path.insert(0,str(root))
    import madgraph
    require(Path(madgraph.MG5DIR).resolve()==root,'wrong MG5 imported')
    from madgraph.interface.master_interface import MasterCmd
    cmd=MasterCmd()
    def no_install(*args,**kw):raise RuntimeError('INSTALLATION_NOT_AUTHORIZED')
    cmd.do_install=no_install
    for line in ['set auto_update 0 --no_save','set automatic_html_opening False --no_save',
       'set nb_core 1 --no_save','set run_mode 0 --no_save','set output_dependencies internal --no_save',
       'set ninja None --no_save','set collier None --no_save','set samurai None --no_save','set golem None --no_save',
       'set fortran_compiler x86_64-conda-linux-gnu-gfortran --no_save',
       'set cpp_compiler x86_64-conda-linux-gnu-g++ --no_save','import model loop_sm',
       'generate g g > h h [noborn=QCD]']:
        cmd.exec_cmd(line,precmd=True)
    amps=cmd._curr_amps
    require(len(amps)==1 and len(amps[0].get('born_diagrams'))==0 and
            len(amps[0].get('loop_diagrams'))==16,'actual full mass production diagrams differ')
    cmd.exec_cmd('output '+target.name+' -nojpeg',precmd=True)
    cmd.exec_cmd('generate g g > h h [sqrvirt=QCD]',precmd=True)
    cmd.exec_cmd('output standalone matrix_element',precmd=True)
    print('PASS_ACTUAL_LOOP_INDUCED_MADEVENT_EXPORT_16_DIAGRAMS_ZERO_EVENTS')

if __name__=='__main__':main()
