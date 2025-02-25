import os
import subprocess
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='pos_startup.log'
)
logger = logging.getLogger(__name__)

def run_backup():
    """Run the MongoDB backup script"""
    try:
        logger.info("Starting MongoDB backup...")
        result = subprocess.run(['python', 'backup_mongodb.py'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        logger.info(f"Backup completed: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running backup: {str(e)}")
        return False

def start_flask_app():
    """Start the Flask application"""
    try:
        logger.info("Starting POS application...")
        
        # Use subprocess.Popen to start the process without waiting for it to complete
        process = subprocess.Popen(['python', 'app.py'], 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True)
        
        # Give the app a moment to start
        time.sleep(2)
        
        # Check if process is still running (which means it started successfully)
        if process.poll() is None:
            logger.info("POS application started successfully")
            print("POS application started successfully. Access it at http://localhost:5000")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Application failed to start: {stderr}")
            print(f"Application failed to start: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        print(f"Error starting application: {str(e)}")
        return False

def main():
    """Main startup function"""
    print("Starting POS System...")
    print("1. Running MongoDB backup to SQLite...")
    
    backup_success = run_backup()
    if backup_success:
        print("Backup completed successfully!")
    else:
        print("Backup failed, but we'll continue with local SQLite database.")
    
    print("2. Starting Flask application...")
    start_flask_app()

if __name__ == "__main__":
    main()
