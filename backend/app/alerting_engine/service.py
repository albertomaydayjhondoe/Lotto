"""
Alerting Service

CRUD operations for alert management.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, and_, func

from app.models.database import AlertEventModel
from .models import Alert, AlertCreate, AlertType, AlertSeverity


async def create_alert(db: AsyncSession, alert: AlertCreate) -> Alert:
    """
    Create a new alert and save to database.
    
    Args:
        db: Database session
        alert: Alert data to create
        
    Returns:
        Created Alert instance
    """
    alert_obj = Alert(
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        metadata=alert.metadata
    )
    
    # Create database record
    db_alert = AlertEventModel(
        id=str(alert_obj.id),
        alert_type=alert_obj.alert_type.value,
        severity=alert_obj.severity.value,
        message=alert_obj.message,
        alert_metadata=alert_obj.metadata,
        created_at=alert_obj.created_at,
        read=0
    )
    
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)
    
    return alert_obj


async def mark_alert_read(db: AsyncSession, alert_id: UUID) -> bool:
    """
    Mark an alert as read.
    
    Args:
        db: Database session
        alert_id: Alert ID to mark as read
        
    Returns:
        True if alert was marked, False if not found
    """
    query = (
        update(AlertEventModel)
        .where(AlertEventModel.id == str(alert_id))
        .values(read=1)
    )
    
    result = await db.execute(query)
    await db.commit()
    
    return result.rowcount > 0


async def get_alerts(
    db: AsyncSession, 
    unread_only: bool = False,
    limit: int = 100
) -> list[Alert]:
    """
    Get alerts from database.
    
    Args:
        db: Database session
        unread_only: Only return unread alerts
        limit: Maximum number of alerts to return
        
    Returns:
        List of Alert instances
    """
    query = select(AlertEventModel).order_by(desc(AlertEventModel.created_at)).limit(limit)
    
    if unread_only:
        query = query.where(AlertEventModel.read == 0)
    
    result = await db.execute(query)
    db_alerts = result.scalars().all()
    
    # Convert to Pydantic models
    alerts = []
    for db_alert in db_alerts:
        alert = Alert(
            id=UUID(db_alert.id),
            alert_type=AlertType(db_alert.alert_type),
            severity=AlertSeverity(db_alert.severity),
            message=db_alert.message,
            metadata=db_alert.alert_metadata or {},
            created_at=db_alert.created_at,
            read=bool(db_alert.read)
        )
        alerts.append(alert)
    
    return alerts


async def get_recent_alerts(db: AsyncSession, limit: int = 50) -> list[Alert]:
    """
    Get most recent alerts.
    
    Args:
        db: Database session
        limit: Maximum number of alerts to return
        
    Returns:
        List of recent Alert instances
    """
    return await get_alerts(db, unread_only=False, limit=limit)


async def check_duplicate_alert(
    db: AsyncSession,
    alert_type: AlertType,
    severity: AlertSeverity,
    minutes_window: int = 5
) -> bool:
    """
    Check if a similar alert was created recently.
    
    Args:
        db: Database session
        alert_type: Type of alert to check
        severity: Severity of alert to check
        minutes_window: Time window in minutes to check for duplicates
        
    Returns:
        True if duplicate exists, False otherwise
    """
    threshold = datetime.utcnow() - timedelta(minutes=minutes_window)
    
    query = select(func.count(AlertEventModel.id)).where(
        and_(
            AlertEventModel.alert_type == alert_type.value,
            AlertEventModel.severity == severity.value,
            AlertEventModel.created_at >= threshold
        )
    )
    
    result = await db.execute(query)
    count = result.scalar()
    
    return count > 0


async def get_unread_count(db: AsyncSession) -> int:
    """
    Get count of unread alerts.
    
    Args:
        db: Database session
        
    Returns:
        Number of unread alerts
    """
    query = select(func.count(AlertEventModel.id)).where(AlertEventModel.read == 0)
    result = await db.execute(query)
    return result.scalar() or 0
