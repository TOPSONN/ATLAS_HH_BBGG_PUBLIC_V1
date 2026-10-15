#!/usr/bin/env python3
"""Isolated native loop export. Fixed commands only; never launch/install."""
import json
from pathlib import Path
import sys

def main():
    root=Path(sys.argv[1]).resolve()
    output=root.parent/'standalone'
    sys.path.insert(0,str(root))
    import madgraph
    from madgraph.interface.master_interface import MasterCmd
    require_root = Path(madgraph.MG5DIR).resolve() == root
    if not require_root: raise RuntimeError('WRONG_SCRATCH_MG5_IMPORT')
    cmd=MasterCmd()
    def blocked(*args,**kwargs): raise RuntimeError('INSTALL_OR_EVENT_GENERATION_FORBIDDEN')
    # Dispatcher-level guard as well as a fixed instruction stream.
    cmd.do_install=blocked
    cmd.do_launch=blocked
    cmd.do_shell=blocked
    setup=['set auto_update 0 --no_save','set automatic_html_opening False --no_save',
           'set nb_core 1 --no_save','set run_mode 0 --no_save',
           'set fortran_compiler x86_64-conda-linux-gnu-gfortran --no_save',
           'set cpp_compiler x86_64-conda-linux-gnu-g++ --no_save',
           'set output_dependencies internal --no_save', 'set ninja None --no_save',
           'set collier None --no_save','set samurai None --no_save','set golem None --no_save',
           'import model loop_sm']
    for line in setup: cmd.exec_cmd(line)
    inspections={}
    for option in ('noborn','sqrvirt'):
        cmd.exec_cmd('generate g g > h h ['+option+'=QCD]')
        model=cmd._curr_model
        rows=[]
        for amp in cmd._curr_amps:
            for kind in ('born_diagrams','loop_diagrams','loop_UVCT_diagrams'):
                for d in amp.get(kind):
                    vertices=[]
                    for v in d.get('vertices'):
                        vid=v.get('id')
                        inter=model.get_interaction(vid) if vid>0 else None
                        vertices.append({'interaction_id':vid,
                            'pdgs':[p.get('pdg_code') for p in inter.get('particles')] if inter else [],
                            'leg_pdgs':[p.get('id') for p in v.get('legs')],
                            'couplings':str(inter.get('couplings')) if inter else '',
                            'orders':dict(inter.get('orders')) if inter else {}})
                    tree_vertices=[]
                    if kind=='loop_diagrams':
                        structure_ids={sid for tag in d.get('tag') for sid in tag[1]}
                        for sid in sorted(structure_ids):
                            for v in amp.get('structure_repository')[sid].get('vertices'):
                                vid=v.get('id')
                                inter=model.get_interaction(vid) if vid>0 else None
                                tree_vertices.append({'interaction_id':vid,
                                    'pdgs':[p.get('pdg_code') for p in inter.get('particles')] if inter else [],
                                    'couplings':str(inter.get('couplings')) if inter else ''})
                    rows.append({'kind':kind,'vertices':vertices,'tree_vertices':tree_vertices,'orders':dict(d.get('orders')),
                                 'CT_vertices':str(d.get('CT_vertices')) if kind=='loop_diagrams' else ''})
        inspections[option]={'interface':cmd.current_interface,'model':model.get('name'),
            'processes':[a.get('process').nice_string() for a in cmd._curr_amps],'diagrams':rows}
    if inspections['noborn']['diagrams'] != inspections['sqrvirt']['diagrams']:
        raise RuntimeError('NOBORN_SQRVIRT_DIAGRAM_MISMATCH')
    (root.parent/'diagram_inspection.json').write_text(json.dumps(inspections,indent=2)+'\n')
    cmd.exec_cmd('output standalone '+str(output))
    print('PASS_NATIVE_STANDALONE_EXPORT_ZERO_EVENTS')

if __name__=='__main__': main()
