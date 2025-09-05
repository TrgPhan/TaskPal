#!/usr/bin/env python3
"""
PostgreSQL Setup Script for TaskPal
This script helps you set up PostgreSQL database for TaskPal
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create PostgreSQL database and user for TaskPal"""
    
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',  # Default PostgreSQL superuser
        'password': input("Enter PostgreSQL 'postgres' user password: "),
        'database': 'postgres'  # Connect to default database first
    }
    
    # TaskPal database configuration
    TASKPAL_CONFIG = {
        'dbname': 'taskpal_db',
        'username': 'taskpal_user',
        'password': 'taskpal_password'
    }
    
    try:
        print("🔌 Connecting to PostgreSQL...")
        
        # Connect to PostgreSQL server
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL successfully!")
        
        # Create database
        print(f"📁 Creating database '{TASKPAL_CONFIG['dbname']}'...")
        cursor.execute(f"DROP DATABASE IF EXISTS {TASKPAL_CONFIG['dbname']}")
        cursor.execute(f"CREATE DATABASE {TASKPAL_CONFIG['dbname']}")
        print(f"✅ Database '{TASKPAL_CONFIG['dbname']}' created!")
        
        # Create user
        print(f"👤 Creating user '{TASKPAL_CONFIG['username']}'...")
        cursor.execute(f"DROP USER IF EXISTS {TASKPAL_CONFIG['username']}")
        cursor.execute(f"CREATE USER {TASKPAL_CONFIG['username']} WITH PASSWORD '{TASKPAL_CONFIG['password']}'")
        print(f"✅ User '{TASKPAL_CONFIG['username']}' created!")
        
        # Grant privileges
        print("🔑 Granting privileges...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {TASKPAL_CONFIG['dbname']} TO {TASKPAL_CONFIG['username']}")
        cursor.execute(f"ALTER USER {TASKPAL_CONFIG['username']} CREATEDB")
        print("✅ Privileges granted!")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 PostgreSQL setup completed successfully!")
        print(f"📊 Database: {TASKPAL_CONFIG['dbname']}")
        print(f"👤 User: {TASKPAL_CONFIG['username']}")
        print(f"🔗 Connection URL: postgresql://{TASKPAL_CONFIG['username']}:{TASKPAL_CONFIG['password']}@localhost:5432/{TASKPAL_CONFIG['dbname']}")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_connection():
    """Test connection to TaskPal database"""
    try:
        print("\n🧪 Testing connection to TaskPal database...")
        
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='taskpal_user',
            password='taskpal_password',
            database='taskpal_db'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Connection successful!")
        print(f"📊 PostgreSQL Version: {version[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TaskPal PostgreSQL Setup")
    print("=" * 40)
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
        print("✅ psycopg2 is installed")
    except ImportError:
        print("❌ psycopg2 not found. Please install it first:")
        print("   pip install psycopg2-binary")
        sys.exit(1)
    
    # Create database and user
    if create_database():
        # Test connection
        test_connection()
        
        print("\n📝 Next steps:")
        print("1. Create a .env file with your database credentials")
        print("2. Run: py -m flask db upgrade")
        print("3. Start your application: py main.py")
    else:
        print("\n❌ Setup failed. Please check your PostgreSQL installation.")
        sys.exit(1)
