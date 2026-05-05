"""
Room 스키마 — 스터디룸 응답 형태

Phase 1에서는 목록 조회만 한다.
스터디룸은 관리자가 Supabase에서 직접 넣어두는 방식.
"""

from datetime import datetime
from pydantic import BaseModel


class RoomResponse(BaseModel):
    """스터디룸 응답"""
    id: int
    name: str
    capacity: int
    created_at: datetime


class RoomCreate(BaseModel):
    """스터디룸 생성 요청"""
    name: str
    capacity: int


class RoomUpdate(BaseModel):
    """스터디룸 수정 요청 (부분 수정 허용)"""
    name: str | None = None
    capacity: int | None = None
