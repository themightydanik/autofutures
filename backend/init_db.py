# backend/init_db.py
import asyncio
import sys
from database.database import init_db, check_db_connection, get_db_context
from database.models import User
from services.auth_service import AuthService

async def create_admin():
    """Create default admin user"""
    with get_db_context() as db:
        auth_service = AuthService(db)
        try:
            admin = await auth_service.create_admin_user(
                username="admin",
                password="Admin123!Change",  # ИЗМЕНИТЕ СРАЗУ!
                email="admin@autofutures.com"
            )
            print(f"✅ Admin created: {admin['username']}")
            print(f"📧 Email: {admin['email']}")
            print(f"🔒 Password: Admin123!Change")
            print(f"\n⚠️  ВАЖНО: Смените пароль после первого входа!")
        except ValueError as e:
            print(f"ℹ️  Admin already exists or error: {str(e)}")
        except Exception as e:
            print(f"❌ Admin creation failed: {str(e)}")

def main():
    print("=" * 60)
    print("🔧 AutoFutures Database Initialization")
    print("=" * 60)
    
    # Check connection
    print("\n1️⃣  Checking database connection...")
    if not check_db_connection():
        print("❌ Database connection failed!")
        print("\nТroubleshooting:")
        print("  - Check MySQL is running: docker-compose ps mysql")
        print("  - Check credentials in .env file")
        print("  - Check DATABASE_URL in config.py")
        sys.exit(1)
    print("✅ Database connected")
    
    # Create tables
    print("\n2️⃣  Creating database tables...")
    try:
        init_db()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        sys.exit(1)
    
    # Create admin
    print("\n3️⃣  Creating admin user...")
    asyncio.run(create_admin())
    
    print("\n" + "=" * 60)
    print("🎉 Database initialized successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start backend: python main.py")
    print("  2. Login as admin to test")
    print("  3. Change admin password immediately!")
    print("\n")

if __name__ == "__main__":
    main()
