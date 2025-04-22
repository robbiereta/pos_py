@echo off
@echo Stopping POS System Service...
net stop POSSystemService
@echo Uninstalling POS System Service...
python c:\Users\usuario\Documents\pos_py\pos_service.py remove
@echo Service uninstalled.
pause
