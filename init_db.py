# init_db.py
import asyncio
from app.db import init_db, engine
from app.models import Base

async def main():
    print("Initializing database and creating tables...")
    await init_db()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
