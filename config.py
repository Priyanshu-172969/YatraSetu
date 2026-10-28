import os
from dotenv import load_dotenv

# Load environment variables from a local .env file if it exists
load_dotenv()

class Config:
    """Application and MySQL configuration settings."""
    
    # MySQL Database Connection Settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'yatrasetu_db')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')

    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'yatrasetu-default-session-key-dev')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

    @classmethod
    def get_db_config(cls, include_database=True):
        """
        Returns a dictionary suitable for mysql.connector.connect().
        If include_database is False, connects to the MySQL server without selecting a database.
        """
        config = {
            'host': cls.MYSQL_HOST,
            'port': cls.MYSQL_PORT,
            'user': cls.MYSQL_USER,
            'password': cls.MYSQL_PASSWORD,
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': False,  # Manual commit for explicit transaction control
        }
        if include_database:
            config['database'] = cls.MYSQL_DATABASE
        return config
