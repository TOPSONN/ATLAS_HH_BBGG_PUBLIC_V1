# Coupling, mass and numerical conventions

SM κλ=κtop=1. Actual generated source binds GC_30=-6*i*lam*v, lam=MH²/(2v²),
GC_37=-i*yt/sqrt(2), yt=sqrt(2)*YUKAWA[6]/v. Both precision copies of GC_30
are rescaled for diagnostic κλ=-1,0,1,2 without changing MH. This is not an
arbitrary BSM production-model implementation.

MASS[6]=173 GeV; YUKAWA[6]=173 GeV independently. Varying MASS[6] to180 at
fixed Yukawa and identical 400 GeV momenta changes the actual matrix element.
YUKAWA[6]=0 and346 independently change it too; bottom loops remain when top
Yukawa is zero. MH125, MB4.7 and YUKAWA[5]=4.7 GeV; fixed input LO mass/Yukawa
conventions, no running-top-mass claim. EW inputs aEWM1=132.507, GF=1.16639e-5,
MZ=91.188 GeV derive MW. Higgs width0.00638233934 GeV is the retained model
baseline, not an adopted precision width.

Actual numerical alpha_s=0.118 fixed, mu_R=mHH/2, no PDF convolution and no mu_F
dependence in standalone ME. Proposed production mu_R=mu_F=mHH/2 requires a
reviewed user-scale implementation/readback. CTEQ6L1 is a built-in method
comparison candidate, not a precision PDF choice. PDF/alpha_s pairing must be
reviewed before a real pilot. No continuum/ZH/ttH fixed scale was reused.

HV lhv=1, real-mass model, CutTools OPP with OneLOop scalar integrals and QP
rescue. Fixed-point finiteness/pole residuals, repeatability, on-shell momentum,
Higgs exchange, threshold rejection and κλ quadratic closure are actually tested.
All raw numerical return codes/precision estimates/card hashes are retained.
