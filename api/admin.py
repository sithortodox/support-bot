from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(prefix="/api/v1", tags=["Admin"])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        new_project = await db.create_project(
            name=project.name,
            description=project.description,
            system_prompt=project.system_prompt
        )
        
        return ProjectResponse(
            id=new_project.id,
            name=new_project.name,
            description=new_project.description,
            is_active=new_project.is_active
        )

@app.get("/projects")
async def list_projects():
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        projects = await db.get_active_projects()
        
        return [
            {"id": p.id, "name": p.name, "is_active": p.is_active}
            for p in projects
        ]

@app.post("/users/{telegram_id}/role")
async def set_user_role(telegram_id: int, role: str):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    if role not in ["user", "admin", "moderator"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        user = await db.set_user_role(telegram_id, role)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"status": "ok", "user_id": user.id, "role": user.role}
