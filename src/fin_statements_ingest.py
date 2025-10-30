#!/usr/bin/env python3
"""
Main entry point for FinPulse financial data ingestion.
This replaces the old monolithic script with the new modular approach.
"""

from finpulse.main import main

if __name__ == "__main__":
    main()