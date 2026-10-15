#!/usr/bin/env python3
"""Local finite-mass signal campaign entry point (Linux/WSL)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.hh_signal.campaign.controller import main
if __name__=='__main__':main()
