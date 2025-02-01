# Mexican POS System with CFDI Support

## Overview
This Point of Sale (POS) system is designed for Mexican businesses, providing full support for CFDI (Comprobante Fiscal Digital por Internet) invoicing.

## Features
- Sales management
- Product inventory
- CFDI invoice generation
- Tax calculation
- Reporting

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in `.env`
3. Initialize database: `python setup_db.py`
4. Run the application: `python app.py`

## Configuration
Ensure you have your SAT (Servicio de Administración Tributaria) credentials configured for CFDI generation.
