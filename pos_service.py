import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import logging
import os
import sys
from config import MONGODB_URI, DB_NAME
from db import get_db

logging.basicConfig(
    filename='c:\\logs\\pos_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class POSService(win32serviceutil.ServiceFramework):
    _svc_name_ = "POSSystemService"
    _svc_display_name_ = "POS System Service"
    _svc_description_ = "Background service for POS system operations"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        logging.info("POS Service started")
        
        # Initialize database connection
        try:
            db = get_db()
            logging.info("Connected to database successfully")
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            return

        while self.is_running:
            # Add your POS system background tasks here
            logging.info("POS Service is running...")
            
            # Check for pending tasks or perform periodic operations
            try:
                # Example: Check for unprocessed sales or pending invoices
                # self.process_pending_tasks(db)
                pass
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")

            # Wait for a while before next iteration or listen for stop signal
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
            if rc == win32event.WAIT_OBJECT_0:
                break

        logging.info("POS Service stopped")

    def process_pending_tasks(self, db):
        # Implement your background tasks here
        # For example, process pending sales, generate invoices, etc.
        pass

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(POSService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(POSService)
