#!/usr/bin/env python3
"""Inspect bounded Phase8 histogram metadata/CSV without PyROOT; read-only, no event loop."""
import argparse,csv,json,math,sys
from pathlib import Path

KEYS=("dataset_id","stage","observable","normalization_mode")
SUMMARY=("dataset_id","stage","observable","normalization_mode","status","dimension","root_path","unit","actual_source_count","N_original","raw_defined_event_count","sumw","sumw2","sum_absw","underflow","overflow","missing_count","invalid_count","weight_scope","normalization_scale","BR_applications","yield_scope","numerical_content_sha256")

def require(ok,reason):
    if not ok:raise ValueError(reason)

def load_histograms(path):
    with Path(path).open(encoding="utf-8") as stream:value=json.load(stream)
    require(isinstance(value,dict) and value.get("schema_version")==1,"UNSUPPORTED_HISTOGRAM_MANIFEST")
    rows=value.get("histograms");require(isinstance(rows,list) and rows,"NO_HISTOGRAM_METADATA")
    seen=set()
    for row in rows:
        require(all(isinstance(row.get(k),str) for k in KEYS),"MALFORMED_HISTOGRAM_IDENTITY")
        identity=tuple(row[k] for k in KEYS);require(identity not in seen,"DUPLICATE_HISTOGRAM_IDENTITY");seen.add(identity)
        require(row.get("status") in ("DEFINED","UNDEFINED_ILL_CONDITIONED_OR_EMPTY_SHAPE"),"UNSUPPORTED_HISTOGRAM_STATUS")
    return value,rows

def select(rows,selectors):
    for name,value in selectors.items():
        if value is not None:require(any(row[name]==value for row in rows),"UNKNOWN_"+name.upper())
    return [row for row in rows if all(value is None or row[name]==value for name,value in selectors.items())]

def bins(path,selected,bin_x=None,bin_y=None,flow="all",limit=40):
    allowed={tuple(row[k] for k in KEYS) for row in selected if row["status"]=="DEFINED"}
    output=[];matched=0
    with Path(path).open(encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        require(set(KEYS+("dimension","bin_x","bin_y","content","sumw2","flow")).issubset(reader.fieldnames or []),"UNSUPPORTED_HISTOGRAM_CSV")
        for row in reader:
            if tuple(row[k] for k in KEYS) not in allowed:continue
            try:x=int(row["bin_x"]);y=int(row["bin_y"]);dimension=int(row["dimension"])
            except ValueError as error:raise ValueError("INVALID_BIN_IDENTITY") from error
            if bin_x is not None and x!=bin_x or bin_y is not None and y!=bin_y:continue
            if flow!="all" and row["flow"]!=("REGULAR" if flow=="regular" else "FLOW"):continue
            try:content=float(row["content"]);square=float(row["sumw2"])
            except ValueError as error:raise ValueError("INVALID_BIN_CONTENT") from error
            require(dimension in (1,2) and x>=0 and y>=0 and math.isfinite(content) and math.isfinite(square) and square>=0,"INVALID_BIN_CONTENT")
            matched+=1
            if len(output)<limit:output.append({**row,"dimension":dimension,"bin_x":x,"bin_y":y,"content":content,"sumw2":square})
    return output,matched

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,required=True);p.add_argument("--csv",type=Path)
    p.add_argument("--dataset");p.add_argument("--stage");p.add_argument("--observable");p.add_argument("--normalization")
    p.add_argument("--list",action="store_true",help="List matching histogram metadata; default unless --bins or --bin is used")
    p.add_argument("--bins",action="store_true");p.add_argument("--bin",type=int,dest="bin_x");p.add_argument("--bin-y",type=int)
    p.add_argument("--flow",choices=["all","regular","flow"],default="all");p.add_argument("--limit",type=int,default=40)
    a=p.parse_args(argv)
    try:
        require(1<=a.limit<=1000,"LIMIT_MUST_BE_1_TO_1000")
        require(a.bin_x is None or a.bin_x>=0,"BIN_MUST_BE_NONNEGATIVE");require(a.bin_y is None or a.bin_y>=0,"BIN_Y_MUST_BE_NONNEGATIVE")
        manifest,rows=load_histograms(a.manifest)
        selectors=dict(zip(KEYS,(a.dataset,a.stage,a.observable,a.normalization)))
        selected=select(rows,selectors);require(selected,"NO_MATCHING_HISTOGRAM")
        result={"status":"READ_ONLY_NUMERICAL_INSPECTION","validation_scope":"Metadata/CSV inspection only; use native phase8_analyze validate for actual ROOT readback and content digest validation.",
                "evidence_class":manifest.get("evidence_class","UNSPECIFIED"),"matching_histograms":len(selected),
                "reported_histograms":min(a.limit,len(selected)),"histograms":[{k:row[k] for k in SUMMARY if k in row} for row in selected[:a.limit]],
                "aggregate_numerical_content_sha256":manifest.get("numerical_histogram_content_sha256")}
        if a.bins or a.bin_x is not None or a.bin_y is not None:
            csv_path=a.csv or a.manifest.with_name("phase8_histograms.csv")
            if any(row["status"]=="DEFINED" for row in selected):
                values,count=bins(csv_path,selected,a.bin_x,a.bin_y,a.flow,a.limit)
                result.update({"matching_bin_rows":count,"reported_bin_rows":len(values),"bins":values})
            else:result.update({"matching_bin_rows":0,"bins":[],"bin_status":"NO_DEFINED_SHAPE; undefined is not zero"})
        print(json.dumps(result,indent=2,allow_nan=False));return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as error:
        print(json.dumps({"status":"FAILED_HISTOGRAM_INSPECTION","reason":str(error)}),file=sys.stderr);return 2

if __name__=="__main__":raise SystemExit(main())
