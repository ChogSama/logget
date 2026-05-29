# CRUD /items — dùng để test DB connection

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from server.database import get_db
from server.models import Item

router = APIRouter(prefix="/items", tags=["items"])


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str


# GET /items
@router.get("/")
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()


# GET /items/{id}
@router.get("/{item_id}")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


# POST /items
@router.post("/", status_code=201)
async def create_item(body: ItemCreate, db: AsyncSession = Depends(get_db)):
    item = Item(name=body.name)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


# PUT /items/{id}
@router.put("/{item_id}")
async def update_item(item_id: int, body: ItemUpdate, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item.name = body.name
    await db.commit()
    await db.refresh(item)
    return item


# DELETE /items/{id}
@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(item)
    await db.commit()