#!/usr/bin/env python3
"""Static source review; does not execute MG5, LHAPDF, or a generator."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source.pdf_backend import review_backend, BackendReviewError

def write_fresh(path,payload):
    path=Path(path)
    if not path.parent.is_dir() or path.parent.resolve()!=path.parent.absolute():
        raise BackendReviewError("OUTPUT_PARENT_MISSING_OR_REDIRECTED:"+str(path.parent))
    with path.open("x",encoding="utf-8") as stream:
        json.dump(payload,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--mg5-root",type=Path,required=True)
    parser.add_argument("--lhapdf-prefix",type=Path,required=True)
    parser.add_argument("--pdf-root",type=Path,required=True)
    parser.add_argument("--phase12-readback",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--alpha-output",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        for path in [args.output,args.alpha_output]:
            if path.exists() or path.is_symlink(): raise BackendReviewError("REFUSE_OUTPUT_OVERWRITE:"+str(path))
        if args.output.absolute()==args.alpha_output.absolute(): raise BackendReviewError("OUTPUT_PATHS_MUST_DIFFER")
        backend,alpha=review_backend(args.mg5_root,args.lhapdf_prefix,args.pdf_root,args.phase12_readback,args.repo)
        write_fresh(args.output,backend);write_fresh(args.alpha_output,alpha)
        print(json.dumps({"status":backend["status"],"actual_MG5_binding":backend["actual_MG5_binding"],
            "alpha_diagnostic_pass":alpha["diagnostic"]["strict_diagnostic_pass"],"new_ME_calls":0,
            "new_integrals":0,"native_PDF_calls_this_audit":0,"output":str(args.output),"alpha_output":str(args.alpha_output)}))
        return 0
    except (BackendReviewError,OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({"status":"BLOCKED_PHASE13_PDF_BACKEND","reason":str(error),"new_ME_calls":0,
            "new_integrals":0,"native_PDF_calls_this_audit":0}))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
