from app.database import engine, Base, User
from sqlalchemy import text

def reset_users_table():
    print("Dropping users table...")
    try:
        # We use raw SQL to be sure, or SQLAlchemy metadata
        # Base.metadata.drop_all(bind=engine) # This drops everything
        # Let's just drop the users table
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.commit()
        print("Users table dropped.")
        
        print("Recreating tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables recreated with new schema.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_users_table()
