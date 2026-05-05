"""
Rooms Router — 스터디룸 API

Phase 1에서는 목록 조회만.
상세 조회는 Phase 2에서 description, capacity 추가 후 만든다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.services import room_service

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("/", response_model=list[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    """
    스터디룸 전체 목록

    GET /rooms
    로그인 불필요
    """
    return room_service.get_rooms(db)


@router.post("/", response_model=RoomResponse)
def create_room(
    request: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 가능합니다")
    return room_service.create_room(db, request)


@router.patch("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    request: RoomUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 가능합니다")
    try:
        return room_service.update_room(db, room_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 가능합니다")
    try:
        room_service.delete_room(db, room_id)
        return {"message": "스터디룸이 삭제되었습니다"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
