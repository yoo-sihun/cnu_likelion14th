"""
Reservation Service — 예약 비즈니스 로직

규칙:
- 같은 방에 시간이 겹치는 예약은 불가
- 예약 취소는 본인만 가능
- 시작 시간이 종료 시간보다 앞이어야 한다
- 과거 시간(이미 지난 start_time) 예약은 불가
- 예약 최대 4시간
- 예약 시간은 30분 단위로 설정해야 합니다
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.repositories import reservation_repo, room_repo
from app.schemas.reservation import ReservationCreate


def _as_utc(dt: datetime) -> datetime:
    """
    datetime 비교를 안전하게 하기 위한 유틸.
    - timezone-aware면 UTC로 변환
    - naive면 UTC로 간주(클라이언트가 TZ 없이 보낸 경우 대비)
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_reservations_by_room(db: Session, room_id: int):
    """특정 방의 예약 목록"""
    return reservation_repo.get_reservations_by_room(db, room_id)


def get_my_reservations(db: Session, user_id: int):
    """내 예약 목록"""
    return reservation_repo.get_reservations_by_user(db, user_id)

def _is_30min_slot(dt):
    return dt.second == 0 and dt.microsecond == 0 and dt.minute in (0, 30)


def create_reservation(db: Session, user_id: int, request: ReservationCreate):
    """
    예약 생성

    1. 스터디룸 존재 확인
    2. 시작 < 종료 시간 확인
    3. 시간 겹침 확인
    4. 예약 생성
    """
    # 1. 방이 존재하는지
    room = room_repo.get_room_by_id(db, request.room_id)
    if not room:
        raise ValueError("스터디룸을 찾을 수 없습니다")

    # 2. 시간대 정규화 (검증/DB 저장 기준을 UTC로 통일)
    now_utc = datetime.now(timezone.utc)
    start_utc = _as_utc(request.start_time)
    end_utc = _as_utc(request.end_time)

    # 2-1. 시간 유효성
    if start_utc >= end_utc:
        raise ValueError("시작 시간은 종료 시간보다 앞이어야 합니다")

    # 2-2. 과거 예약 방지
    if start_utc < now_utc:
        raise ValueError("과거 시간에는 예약할 수 없습니다")
    
    # 2-3. 예약 최대 4시간
    duration = end_utc - start_utc
    if duration > timedelta(hours=4):
        raise ValueError("예약은 최대 4시간까지 가능합니다")

    # 2-4. 30분 단위 예약
    if not _is_30min_slot(start_utc) or not _is_30min_slot(end_utc):
        raise ValueError("예약 시간은 30분 단위로 설정해야 합니다")
    

    # 3. 같은 방에 겹치는 예약이 있는지
    overlap = reservation_repo.get_overlapping_reservation(
        db, request.room_id, start_utc, end_utc
    )
    if overlap:
        raise ValueError("해당 시간에 이미 예약이 있습니다")

    # 4. 예약 생성
    new_reservation = Reservation(
        user_id=user_id,
        room_id=request.room_id,
        start_time=start_utc,
        end_time=end_utc,
    )
    return reservation_repo.create_reservation(db, new_reservation)


def cancel_reservation(db: Session, user_id: int, reservation_id: int):
    """
    예약 취소

    규칙: 본인 예약만 취소 가능
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise ValueError("예약을 찾을 수 없습니다")
    if reservation.user_id != user_id:
        raise PermissionError("본인의 예약만 취소할 수 있습니다")

    reservation_repo.delete_reservation(db, reservation)
