"""Read-only, source-bound MG5/LHAPDF review; never executes either package."""
from __future__ import annotations
import ast
import hashlib
import json
import math
from pathlib import Path

SET_NAME = "NNPDF30_lo_as_0130_nf_4"
INFO_SHA256 = "85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162"
MEMBER_SHA256 = "e3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e"
READBACK_SHA256 = "13b49445a86537ec68e31d48c1438276b8d8d05f233df91f79ae166d72cb7b55"
ALPHA_RECEIPT_SHA256 = "c800618d3f03a0e03b0c8560875715306b4a15f2bef2607796dc759375c4a671"
FLAVOURS = [-4,-3,-2,-1,1,2,3,4,21]

class BackendReviewError(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise BackendReviewError(reason)

def identity(path):
    """Hash bytes, not normalized text, and reject an identity changing mid-read."""
    p=Path(path)
    require(p.is_file(), "MISSING_REGULAR_INPUT:"+str(p))
    resolved=p.resolve(strict=True)
    before=p.stat()
    digest=hashlib.sha256()
    with p.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024), b""):
            digest.update(chunk)
    after=p.stat()
    require(p.resolve(strict=True)==resolved and
            (before.st_size,before.st_mtime_ns,before.st_ino)==
            (after.st_size,after.st_mtime_ns,after.st_ino), "INPUT_CHANGED_DURING_READ:"+str(p))
    return {"path":str(p),"resolved_path":str(resolved),"bytes":after.st_size,
            "sha256":digest.hexdigest()}

def compare_identity(path, expected):
    actual=identity(path)
    require(isinstance(expected,dict),"MALFORMED_EXPECTED_IDENTITY")
    for key in ["sha256","bytes","resolved_path"]:
        require(key in expected and actual[key]==expected[key], "INPUT_IDENTITY_MISMATCH:"+str(path)+":"+key)
    return actual

def witness(path, anchors):
    record=identity(path)
    lines=Path(path).read_text(encoding="utf-8").splitlines()
    result=[]
    for anchor in anchors:
        matches=[n for n,line in enumerate(lines,1) if anchor in line]
        require(bool(matches),"SOURCE_WITNESS_MISSING:"+str(path)+":"+anchor)
        result.append({"anchor":anchor,"line_numbers":matches})
    record["witnesses"]=result
    return record

def parse_info(text):
    """Small data-only parser for the fixed, one-line public metadata format."""
    out={}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        require(":" in line,"MALFORMED_METADATA_LINE")
        key,value=line.split(":",1); key=key.strip();value=value.strip()
        require(key and key not in out,"DUPLICATE_METADATA_KEY:"+key)
        try: out[key]=ast.literal_eval(value)
        except (ValueError,SyntaxError): out[key]=value
    return out

def alpha_diagnostic(info, native_alpha):
    require(info.get("MZ")==4.1799998,"WRONG_ALPHA_REFERENCE_SCALE")
    require(info.get("AlphaS_MZ")==0.2544023564420006,"WRONG_DECLARED_ALPHA_REFERENCE")
    require(info.get("AlphaS_Type")=="ipol","WRONG_ALPHA_TYPE")
    require(type(info.get("AlphaS_OrderQCD")) is int and info["AlphaS_OrderQCD"]==0,"WRONG_ALPHA_ORDER")
    qs,vs=info.get("AlphaS_Qs"),info.get("AlphaS_Vals")
    require(isinstance(qs,list) and isinstance(vs,list) and len(qs)==len(vs)==50,"INVALID_ALPHA_KNOTS")
    require(all(type(v) in [int,float] and math.isfinite(v) and v>0 for v in qs+vs),"INVALID_ALPHA_KNOT_VALUE")
    require(all(a<=b for a,b in zip(qs,qs[1:])),"UNORDERED_ALPHA_KNOTS")
    q=info["MZ"];declared=info["AlphaS_MZ"]
    require(type(native_alpha) in [float,int] and math.isfinite(native_alpha) and native_alpha>0,"INVALID_NATIVE_ALPHA")
    require(native_alpha==0.254403024565842,"HISTORICAL_NATIVE_ALPHA_CHANGED")
    bracket=[{"Q_GeV":a,"alpha_s":b} for a,b in zip(qs,vs) if a in [max(v for v in qs if v<q),min(v for v in qs if v>q)]]
    delta=abs(native_alpha-declared);relative=delta/declared
    return {"Q_reference_GeV":q,"declared_alpha_s":declared,"historical_native_alpha_s":native_alpha,
        "absolute_difference":delta,"relative_difference":relative,"strict_diagnostic_tolerance":1e-6,
        "strict_diagnostic_pass":relative<=1e-6,"historical_diagnostic_must_remain_false":True,
        "reference_is_exact_knot":q in qs,"table_node_count":len(qs),"table_bracket":bracket,
        "duplicate_Q_knots_GeV":sorted({a for a,b in zip(qs,qs[1:]) if a==b}),
        "ipol_table_pairs":[{"Q_GeV":a,"alpha_s":b} for a,b in zip(qs,vs)],
        "official_accuracy_bound":None,"official_accuracy_status":"UNKNOWN",
        "difference_cause":"CONSISTENT_WITH_DISTINCT_DECLARATION_AND_TABULATED_INTERPOLATION; NOT_A_PROVEN_ERROR_BOUND_OR_COMPLETE_CAUSAL_DECOMPOSITION",
        "diagnostic_is_official_accuracy_test":False}

def validate_metadata(info, member_header, native):
    expected={"SetIndex":263400,"DataVersion":2,"NumMembers":101,"Particle":2212,
        "OrderQCD":0,"FlavorScheme":"variable","NumFlavors":4,"AlphaS_OrderQCD":0,"AlphaS_Type":"ipol"}
    for key,value in expected.items():
        require(info.get(key)==value and type(info.get(key)) is type(value),"METADATA_MISMATCH:"+key)
    require(info.get("Flavors")==FLAVOURS,"FLAVOUR_LIST_MISMATCH")
    require(5 not in info["Flavors"] and -5 not in info["Flavors"],"BOTTOM_PDF_FORBIDDEN")
    require(member_header=={"PdfType":"central","Format":"lhagrid1"},"MEMBER_OVERRIDE_OR_HEADER_MISMATCH")
    require(native.get("native_flavours")==FLAVOURS and native.get("bottom_active") is False,"NATIVE_BOTTOM_OR_FLAVOURS_MISMATCH")
    require(native.get("native_LHAPDF_ID")==263400,"NATIVE_MEMBER_ID_MISMATCH")
    require(native.get("reader_version")=="6.5.6","NATIVE_VERSION_MISMATCH")
    require(native.get("native_file_resolution_checked") is True,"UNVERIFIED_HISTORICAL_MEMBER_RESOLUTION")
    require(native.get("selected_member_resolution")=="EXCLUSIVE_EXTERNAL_MEMBER; BUILTIN_METADATA_FALLBACK_OBSERVED_AND_NO_SAME_NAME_INSTALLED_SET","UNVERIFIED_HISTORICAL_FALLBACK")
    for key in ["MG5_parser_executed","matching_validated","physical_component_validated","installed_directory_writes"]:
        require(native.get(key) is False,"HISTORICAL_SCOPE_MISMATCH:"+key)
    for key in ["new_ME_calls","new_integrals","new_hard_events","new_Pythia_events","new_Delphes_events"]:
        require(type(native.get(key)) is int and native[key]==0,"HISTORICAL_PHYSICS_COUNTER_MISMATCH:"+key)
    require(native.get("interpolation_errors")==0 and native.get("nonfinite_errors")==0,"HISTORICAL_READBACK_ERROR")
    require(isinstance(native.get("finite_pdf_points"),list) and len(native["finite_pdf_points"])==4 and native.get("finite_xfx_values")==36,"HISTORICAL_NATIVE_POINT_COUNT_MISMATCH")
    for key in ["MCharm","MBottom","MTop"]:
        require(key in info,"MISSING_THRESHOLD_MASS:"+key)
    # The fixed member has no override. Keep fallback keys explicit; never call them ME pole masses.
    thresholds={}
    for name,pdg in [("Charm",4),("Bottom",5),("Top",6)]:
        mass_key="M"+name
        pdf_key=next(k for k in ["Threshold"+name,mass_key] if k in info)
        alpha_key=next(k for k in ["AlphaS_Threshold"+name,"Threshold"+name,"AlphaS_M"+name,mass_key] if k in info)
        thresholds[name]={"pdf_threshold_GeV":info[pdf_key],"pdf_source_key":pdf_key,
            "alpha_threshold_GeV":info[alpha_key],"alpha_source_key":alpha_key,
            "activation_permitted_by_max4":pdg<=4,"ME_pole_mass_inference":False}
    require(info.get("AlphaS_FlavorScheme",info["FlavorScheme"])=="variable","ALPHA_SCHEME_MISMATCH")
    require(info.get("AlphaS_NumFlavors",info["NumFlavors"])==4,"ALPHA_MAX_FLAVOURS_MISMATCH")
    return thresholds

def verify_historical_closure(native):
    before=native.get("raw_inputs_and_dependencies_before");after=native.get("raw_inputs_and_dependencies_after")
    require(isinstance(before,dict) and len(before)==10 and before==after,"HISTORICAL_DEPENDENCY_IDENTITY_UNSTABLE")
    dependencies={str(path):compare_identity(path,expected) for path,expected in before.items()}
    sources=native.get("source_sha256")
    require(isinstance(sources,dict) and len(sources)==5,"MALFORMED_HISTORICAL_SOURCE_IDENTITIES")
    checked_sources={}
    for path,expected in sources.items():
        record=identity(path);require(record["sha256"]==expected,"HISTORICAL_READER_SOURCE_DRIFT:"+path)
        checked_sources[path]=record
    return dependencies,checked_sources

MG5_WITNESSES={
 "pdf_makefile":("Template/LO/Source/PDF/makefile",["ifdef lhapdf","ifeq ($(lhapdfsubversion),1)","PDF  += pdf_lhapdf62.o"]),
 "make_opts":("Template/LO/Source/make_opts",["ifneq ($(lhapdf),)","alfas_functions=alfas_functions_lhapdf","alfas_functions=alfas_functions"]),
 "backend62":("Template/Common/Source/PDF/pdf_lhapdf62.cc",["LHAPDF::lookupPDF(lhaid)","LHAPDF::mkPDF(setname, mem)","activeMember()->xfxQ(ipart_copy, x, q)","activeMember()->alphasQ(Q)","get_entry_as<int>(\"AlphaS_OrderQCD\")","my_par.find(\"DEFAULT\")","id = value[0];"]),
 "interface":("madgraph/interface/common_run_interface.py",["def link_lhapdf(","lhalib = 'libLHAPDF.a'","self.make_opts_var['lhapdfsubversion'] = lhapdf_version.split('.',2)[1]","self.install_lhapdf_pdfset(pdfsets_dir, pdfset)","files.cp(pjoin(pdfsets_dir, pdfset)"]),
 "exporter":("madgraph/iolibs/export_v4.py",['template = open(pjoin(MG5DIR, "madgraph", "iolibs", "template_files", "pdf_wrap_lhapdf.f")']),
 "pdf_wrapper":("madgraph/iolibs/template_files/pdf_wrap_lhapdf.f",["data zmass/91.188d0/","value(1)=lhaid","if (pdlabel.eq.'lhapdf') then","nloop=nloop+1","asmz=alphasPDF(zmass)","LHAPath='./PDFsets'","LHAPath='lib/PDFsets'"]),
 "alpha_wrapper":("Template/LO/Source/alfas_functions_lhapdf.f",["DOUBLE PRECISION FUNCTION ALPHAS(Q)","ALPHAS=alphasPDF(Q)"]),
 "density_wrapper":("Template/LO/Source/PDF/pdg2pdf_lhapdf6.f",["call evolvepart(ipart,x,xmu,pdg2pdf)","pdg2pdf=pdg2pdf/x"]),
 "run_card":("madgraph/various/banner.py",['self.add_param("lhaid", 230000',"if self['pdlabel'] == 'lhapdf':","self.get_default('lhaid', log_level=20)"]),
}
LHAPDF_WITNESSES={
 "version_header":("include/LHAPDF/Version.h",['#define LHAPDF_VERSION "6.5.6"',"#define LHAPDF_VERSION_CODE 60506"]),
 "alpha_header":("include/LHAPDF/AlphaS.h",["class AlphaS_Ipol","return alphasQ2(q*q)","_interpolateCubic","subgrid boundary (for the same Q values)"]),
 "pdf_header":("include/LHAPDF/PDF.h",["_alphas.reset( mkAlphaS(info()) )","return _alphas->alphasQ2(q2)","double alphasQ(double q) const"]),
 "factory_header":("include/LHAPDF/Factories.h",["AlphaS* mkAlphaS(const Info& info)"]),
 "config_tool":("bin/lhapdf-config",['echo "6.5.6"',"--libdir","--datadir","--cppflags"]),
}

def review_backend(mg5_root, lhapdf_prefix, pdf_root, phase12_readback, repo):
    """Static mapping and current-byte closure of an actual historical standalone run."""
    mg5_root,lhapdf_prefix,pdf_root,phase12_readback,repo=map(Path,[mg5_root,lhapdf_prefix,pdf_root,phase12_readback,repo])
    old=phase12_readback/"pdf_member_readback.json";old_alpha=phase12_readback/"pdf_alpha_reference_checks.json"
    old_id=identity(old);old_alpha_id=identity(old_alpha)
    require(old_id["sha256"]==READBACK_SHA256,"HISTORICAL_NATIVE_RECEIPT_SHA_MISMATCH")
    require(old_alpha_id["sha256"]==ALPHA_RECEIPT_SHA256,"HISTORICAL_ALPHA_RECEIPT_SHA_MISMATCH")
    for filename,expected in [(old.name,READBACK_SHA256),(old_alpha.name,ALPHA_RECEIPT_SHA256)]:
        require(identity(repo/"analysis/phase12/evidence"/filename)["sha256"]==expected,"PUBLISHED_HISTORICAL_RECEIPT_MISMATCH:"+filename)
    native=json.loads(old.read_text());native_alpha=json.loads(old_alpha.read_text())
    require(native.get("evidence_class")=="ACTUAL_ISOLATED_PDF_READBACK" and native.get("status")=="PASS_ISOLATED_NATIVE_PDF_INTERFACE_WITH_LIMITS","UNACCEPTED_HISTORICAL_NATIVE_RECEIPT")
    dependencies,old_sources=verify_historical_closure(native)
    setdir=pdf_root/SET_NAME
    require(setdir.is_dir() and setdir.resolve()==setdir,"MISSING_OR_REDIRECTED_EXTERNAL_SET")
    info_path=setdir/(SET_NAME+".info");member_path=setdir/(SET_NAME+"_0000.dat")
    info_id=identity(info_path);member_id=identity(member_path)
    require(info_id["sha256"]==INFO_SHA256 and info_id["bytes"]==2345,"EXACT_PDF_INFO_IDENTITY_MISMATCH")
    require(member_id["sha256"]==MEMBER_SHA256 and member_id["bytes"]==683592,"EXACT_PDF_MEMBER_IDENTITY_MISMATCH")
    for item in [info_id,member_id]:
        require(item["path"] in dependencies and item==dependencies[item["path"]],"EXTERNAL_PDF_NOT_HISTORICALLY_NATIVE_BOUND")
    info=parse_info(info_path.read_text())
    with member_path.open() as stream:
        head=[]
        for line in stream:
            if line.strip()=="---": break
            require(len(head)<32,"EXCESSIVE_MEMBER_HEADER")
            head.append(line)
    member_header=parse_info("".join(head))
    thresholds=validate_metadata(info,member_header,native)
    native_value=native.get("alpha_reference_diagnostic",{}).get("native_alpha_at_declared_Q")
    diagnostic=alpha_diagnostic(info,native_value)
    require(diagnostic["strict_diagnostic_pass"] is False,"STRICT_DIAGNOSTIC_WAS_PROMOTED")
    require(native["alpha_reference_diagnostic"].get("within_strict_diagnostic_tolerance") is False,"HISTORICAL_DIAGNOSTIC_CHANGED")
    require(native_alpha.get("reference_diagnostic")==native["alpha_reference_diagnostic"],"HISTORICAL_ALPHA_RECEIPTS_DISAGREE")
    require(native["alpha_reference_diagnostic"].get("strict_diagnostic_relative_tolerance")==1e-6,"HISTORICAL_DIAGNOSTIC_TOLERANCE_CHANGED")
    source_records={key:witness(mg5_root/filename,anchors) for key,(filename,anchors) in MG5_WITNESSES.items()}
    source_records.update({"lhapdf_"+key:witness(lhapdf_prefix/filename,anchors) for key,(filename,anchors) in LHAPDF_WITNESSES.items()})
    source_records["legacy_6_1_backend_not_selected_for_6_5_6"]=identity(mg5_root/"Template/Common/Source/PDF/pdf_lhapdf6.cc")
    version=identity(mg5_root/"VERSION")
    require("version = 3.5.16" in (mg5_root/"VERSION").read_text(),"MG5_VERSION_MISMATCH")
    source_records["mg5_version"]=version
    so=identity(lhapdf_prefix/"lib/libLHAPDF.so")
    require(so["path"] in dependencies and so==dependencies[so["path"]],"LIBRARY_NOT_HISTORICALLY_NATIVE_BOUND")
    static=lhapdf_prefix/"lib/libLHAPDF.a"
    static_record=identity(static) if static.exists() else {"path":str(static),"exists":False,"sha256":None,"status":"ABSENT"}
    installed_same_name=lhapdf_prefix/"share/LHAPDF"/SET_NAME
    require(not installed_same_name.exists() and not installed_same_name.is_symlink(),"ACCIDENTAL_SAME_NAME_INSTALLED_FALLBACK")
    require(len(native.get("observed_data_paths",[]))==2 and native["observed_data_paths"][0]==str(pdf_root),"HISTORICAL_DATA_PATH_MISMATCH")
    raw_after={key:compare_identity(key,record) for key,record in dependencies.items()}
    for record in source_records.values(): compare_identity(record["path"],record)
    scope={"MG5_parser_executed":False,"MG5_process_enumerated":False,"MG5_compiled_or_linked":False,
        "native_PDF_calls_this_audit":0,"new_ME_calls":0,"new_integrals":0,"new_hard_events":0,
        "new_Pythia_events":0,"new_Delphes_events":0,"installed_directory_writes":False,
        "historical_readback_reused":True,"current_raw_dependencies_rehashed":True}
    backend={"schema_version":1,"evidence_class":"HISTORICAL_SOURCE_AUDIT",
        "status":"PASS_STATIC_BACKEND_MAPPING_WITH_LIMITS","actual_MG5_binding":"UNVERIFIED_NOT_EXECUTED",
        "symbolic_parser_PDF_dependency":"NOT_NEEDED_FOR_SYMBOLIC_SCOPE",
        "numerical_ME_backend_readiness":"BLOCKED_UNVERIFIED_LINK_AND_RUNTIME_SELECTION",
        "set_name":SET_NAME,"member":0,"lhaid":263400,"data_version":2,
        "PDF_order_QCD":0,"PDF_flavour_scheme":"variable","PDF_maximum_flavours":4,
        "native_flavours_historical":native["native_flavours"],"bottom_pdf_active":False,
        "native_reader_version_historical":native["reader_version"],"external_pdf_identities":[info_id,member_id],
        "phase12_native_receipt":old_id,"phase12_alpha_receipt":old_alpha_id,
        "historical_observed_UTC":native["observed_UTC"],"historical_native_point_count":4,
        "historical_native_xfx_value_count":36,"new_native_measurement":False,
        "historical_dependencies_current_before":dependencies,"historical_dependencies_current_after":raw_after,
        "historical_reader_sources_current":old_sources,"source_identities_and_witnesses":source_records,
        "lhapdf_library":so,"lhapdf_static_library":static_record,
        "static_library_expectation_satisfied":static.exists(),
        "static_library_absence_interpretation":"MG5_LINK_LHAPDF_TRIES_LIBLHAPDF_A; DYNAMIC_LIB_SUCCESS_DOES_NOT_PROVE_GENERATED_PROCESS_LINK; NO_LINK_ATTEMPTED",
        "mapping":{"selected_source_for_LHAPDF_6_5_6":"Template/Common/Source/PDF/pdf_lhapdf62.cc",
            "legacy_source_scope":"pdf_lhapdf6.cc ONLY lhapdfsubversion==1 branch",
            "ID_to_member":"pdfset DEFAULT value[0] -> lookupPDF(lhaid) -> PDFSetHandler -> mkPDF(setname,member)",
            "density":"pdg2pdf -> evolvepart -> activeMember.xfxQ -> divide by x",
            "alpha_order":"GetOrderAs reads AlphaS_OrderQCD; pdfwrap increments nloop by one",
            "alpha_selection_condition":"nonempty make variable lhapdf selects alfas_functions_lhapdf",
            "alpha_evaluation":"ALPHAS(Q) -> alphasPDF(Q) -> alphaspdfm_(set1,Q) -> activeMember.alphasQ(Q)",
            "MG5_asmz_initialization_Q_GeV":91.188,
            "MG5_asmz_initialization_value":None,"MG5_asmz_value_status":"NOT_EXECUTED; NOT_PDF_METADATA_REFERENCE_VALUE"},
        "future_binding_requirements":["EXACT pdlabel/lhaid and both beam PDF settings, not RunCard defaults",
            "Generated make_opts, compiler/link evidence and actual loaded library identity",
            "Exact process-local lib/PDFsets info/member hashes and all effective search paths",
            "Disable install_lhapdf_pdfset/network/install fallback and preserve original prefixes",
            "Member-specific density and alpha readback through authorized MG5-linked executable"],
        "same_name_installed_set_present":False,"historical_resolution":native["selected_member_resolution"],
        "current_pdf_path":str(setdir),"thresholds":thresholds,"scope":scope}
    alpha={"schema_version":1,"evidence_class":"HISTORICAL_SOURCE_AUDIT",
        "status":"REVIEWED_IPOL_REFERENCE_DIAGNOSTIC_FALSE","diagnostic":diagnostic,
        "alpha_flavour_scheme":"variable","alpha_flavour_scheme_source_key":"FlavorScheme",
        "alpha_maximum_flavours":4,"alpha_maximum_flavours_source_key":"NumFlavors",
        "alpha_order_QCD":0,"alpha_type":"ipol","thresholds":thresholds,
        "member_header_override_keys":[],"member_specific_alpha_interface":"activeMember()->alphasQ(Q)",
        "implementation_evidence":"Installed LHAPDF 6.5.6 AlphaS.h declares Q2 tables, repeated-boundary subgrids, cubic interpolation and log(Q2) knot lookup. Compiled AlphaS.cc body absent from installed package; no independent exact interpolation reproduction claimed.",
        "reference_semantics":"MZ and AlphaS_MZ are this set's declared pair at 4.1799998 GeV; the set name 0130 is not used as an input value. In ipol evaluation the tables are distinct from the declaration; no equality at an off-knot reference is guaranteed by inspected interface.",
        "domains":{"PDF_alpha_s":{"value_at_reference":native_value,"source":"PHASE12_NATIVE04_REUSED_CURRENT_HASH_CLOSURE"},
            "ME_coupling_alpha_s":{"value":None,"binding":"UNVERIFIED_NOT_EXECUTED","conditional_source_mapping":"ALPHAS(Q) delegates only if reviewed LHAPDF object and link selected"},
            "ISR_alpha_s":{"value":None,"binding":"UNVERIFIED_NOT_EXECUTED"},
            "FSR_alpha_s":{"value":None,"binding":"UNVERIFIED_NOT_EXECUTED"}},
        "MG5_asmz_reference_Q_GeV":91.188,"MG5_asmz_value":None,
        "historical_91_1876_value_is_not_ME_asmz":True,"phase12_native_receipt":old_id,
        "source_identities_and_witnesses":source_records,"public_primary_documentation":[
            {"url":"https://www.lhapdf.org/classLHAPDF_1_1AlphaS__Ipol.html","version_displayed":"6.5.6","role":"IPOL_INTERFACE_AND_SUBGRID_SEMANTICS"},
            {"url":"https://www.lhapdf.org/config.html","version_displayed":"6.5.6","role":"MEMBER_SET_GLOBAL_CASCADE_AND_ALPHA_KEYS"}],"scope":scope}
    return backend,alpha
