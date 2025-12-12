"""
SPRINT 13 - Human Observability & Cognitive Dashboard
Module: Observability Persistence

PostgreSQL schemas and persistence layer for observability data.

Tables:
- accounts_state_history
- accounts_metrics_history
- warmup_human_tasks
- audit_log (already exists from Sprint 12, extended here)
"""

import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# ============================================================================
# POSTGRESQL SCHEMAS
# ============================================================================

SQL_SCHEMA = """
-- SPRINT 13: Observability Persistence Schemas

-- 1. accounts_state_history
-- Tracks every state transition
CREATE TABLE IF NOT EXISTS accounts_state_history (
    id SERIAL PRIMARY KEY,
    account_id TEXT NOT NULL,
    previous_state TEXT,
    new_state TEXT NOT NULL,
    transition_reason TEXT,
    duration_in_prev_state_days INT,
    risk_snapshot JSONB,
    metrics_snapshot JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_account_state 
        FOREIGN KEY (account_id) 
        REFERENCES accounts(account_id) 
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_state_history_account 
    ON accounts_state_history(account_id);

CREATE INDEX IF NOT EXISTS idx_state_history_timestamp 
    ON accounts_state_history(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_state_history_new_state 
    ON accounts_state_history(new_state);


-- 2. accounts_metrics_history
-- Time-series metrics for each account
CREATE TABLE IF NOT EXISTS accounts_metrics_history (
    id SERIAL PRIMARY KEY,
    account_id TEXT NOT NULL,
    maturity_score FLOAT NOT NULL,
    risk_score FLOAT NOT NULL,
    readiness_score FLOAT NOT NULL,
    total_actions INT DEFAULT 0,
    action_diversity FLOAT DEFAULT 0.0,
    impressions INT DEFAULT 0,
    blocks INT DEFAULT 0,
    comments INT DEFAULT 0,
    followers INT DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_account_metrics 
        FOREIGN KEY (account_id) 
        REFERENCES accounts(account_id) 
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metrics_history_account 
    ON accounts_metrics_history(account_id);

CREATE INDEX IF NOT EXISTS idx_metrics_history_timestamp 
    ON accounts_metrics_history(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_metrics_history_risk 
    ON accounts_metrics_history(risk_score DESC);


-- 3. warmup_human_tasks
-- Human warmup task tracking
CREATE TABLE IF NOT EXISTS warmup_human_tasks (
    task_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    warmup_day INT NOT NULL,
    warmup_phase TEXT NOT NULL,
    description TEXT,
    required_actions JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    human_required BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    verification_result JSONB,
    
    CONSTRAINT fk_warmup_task_account 
        FOREIGN KEY (account_id) 
        REFERENCES accounts(account_id) 
        ON DELETE CASCADE,
    
    CONSTRAINT chk_status 
        CHECK (status IN ('pending', 'started', 'completed', 'failed', 'expired'))
);

CREATE INDEX IF NOT EXISTS idx_warmup_tasks_account 
    ON warmup_human_tasks(account_id);

CREATE INDEX IF NOT EXISTS idx_warmup_tasks_status 
    ON warmup_human_tasks(status);

CREATE INDEX IF NOT EXISTS idx_warmup_tasks_due_date 
    ON warmup_human_tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_warmup_tasks_created 
    ON warmup_human_tasks(created_at DESC);


-- 4. audit_log (extended from Sprint 12)
-- Already exists, but we ensure proper indices
CREATE INDEX IF NOT EXISTS idx_audit_account_timestamp 
    ON audit_log(account_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_event_type 
    ON audit_log(event_type);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
    ON audit_log(timestamp DESC);


-- 5. Retention policy (auto-cleanup old data)
-- Function to delete old records
CREATE OR REPLACE FUNCTION cleanup_old_observability_data()
RETURNS void AS $$
BEGIN
    -- Delete state history older than 90 days
    DELETE FROM accounts_state_history 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Delete metrics history older than 90 days
    DELETE FROM accounts_metrics_history 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Delete completed warmup tasks older than 30 days
    DELETE FROM warmup_human_tasks 
    WHERE status IN ('completed', 'failed', 'expired') 
    AND completed_at < NOW() - INTERVAL '30 days';
    
    -- Audit log cleanup (keep 6 months)
    -- (Only if using PostgreSQL audit_log, not JSONL)
    -- DELETE FROM audit_log WHERE timestamp < NOW() - INTERVAL '180 days';
    
    RAISE NOTICE 'Cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-observability', '0 2 * * *', 'SELECT cleanup_old_observability_data()');
"""


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class StateHistoryRecord:
    """State transition record"""
    account_id: str
    previous_state: Optional[str]
    new_state: str
    transition_reason: str
    duration_in_prev_state_days: int
    risk_snapshot: Dict
    metrics_snapshot: Dict
    timestamp: datetime


@dataclass
class MetricsHistoryRecord:
    """Metrics snapshot record"""
    account_id: str
    maturity_score: float
    risk_score: float
    readiness_score: float
    total_actions: int
    action_diversity: float
    impressions: int
    blocks: int
    comments: int
    followers: int
    engagement_rate: float
    timestamp: datetime


@dataclass
class WarmupTaskRecord:
    """Warmup task record"""
    task_id: str
    account_id: str
    warmup_day: int
    warmup_phase: str
    description: str
    required_actions: Dict
    status: str
    human_required: bool
    created_at: datetime
    due_date: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    verification_result: Optional[Dict]


# ============================================================================
# PERSISTENCE MANAGER
# ============================================================================

class ObservabilityPersistence:
    """
    Manages persistence of observability data.
    
    Features:
    - PostgreSQL write/read
    - CSV export
    - Retention policy
    - Batch operations
    """
    
    def __init__(self, db_connection=None, storage_path: str = "storage/observability"):
        """
        Initialize persistence manager.
        
        Args:
            db_connection: PostgreSQL connection (optional)
            storage_path: Path for CSV exports
        """
        self.db = db_connection
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ObservabilityPersistence initialized (storage: {self.storage_path})")
    
    # ========================================================================
    # STATE HISTORY
    # ========================================================================
    
    def record_state_transition(
        self,
        account_id: str,
        previous_state: Optional[str],
        new_state: str,
        transition_reason: str,
        duration_in_prev_state_days: int,
        risk_snapshot: Dict,
        metrics_snapshot: Dict
    ) -> bool:
        """
        Record state transition.
        
        Returns:
            True if recorded successfully
        """
        try:
            record = StateHistoryRecord(
                account_id=account_id,
                previous_state=previous_state,
                new_state=new_state,
                transition_reason=transition_reason,
                duration_in_prev_state_days=duration_in_prev_state_days,
                risk_snapshot=risk_snapshot,
                metrics_snapshot=metrics_snapshot,
                timestamp=datetime.now()
            )
            
            if self.db:
                # PostgreSQL insert
                import json
                cursor = self.db.cursor()
                cursor.execute("""
                    INSERT INTO accounts_state_history (
                        account_id, previous_state, new_state, transition_reason,
                        duration_in_prev_state_days, risk_snapshot, metrics_snapshot, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    account_id,
                    previous_state,
                    new_state,
                    transition_reason,
                    duration_in_prev_state_days,
                    json.dumps(risk_snapshot),
                    json.dumps(metrics_snapshot),
                    record.timestamp
                ))
                self.db.commit()
                logger.info(f"Recorded state transition: {account_id} {previous_state} → {new_state}")
                return True
            else:
                # Fallback: CSV append
                csv_file = self.storage_path / "state_history.csv"
                file_exists = csv_file.exists()
                
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow([
                            'account_id', 'previous_state', 'new_state', 'transition_reason',
                            'duration_days', 'risk_snapshot', 'metrics_snapshot', 'timestamp'
                        ])
                    
                    writer.writerow([
                        account_id,
                        previous_state or '',
                        new_state,
                        transition_reason,
                        duration_in_prev_state_days,
                        str(risk_snapshot),
                        str(metrics_snapshot),
                        record.timestamp.isoformat()
                    ])
                
                logger.info(f"Recorded state transition to CSV: {account_id}")
                return True
        
        except Exception as e:
            logger.error(f"Error recording state transition: {e}")
            return False
    
    def get_state_history(
        self,
        account_id: str,
        limit: int = 50
    ) -> List[StateHistoryRecord]:
        """
        Get state history for account.
        """
        try:
            if self.db:
                cursor = self.db.cursor()
                cursor.execute("""
                    SELECT account_id, previous_state, new_state, transition_reason,
                           duration_in_prev_state_days, risk_snapshot, metrics_snapshot, timestamp
                    FROM accounts_state_history
                    WHERE account_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (account_id, limit))
                
                rows = cursor.fetchall()
                return [
                    StateHistoryRecord(
                        account_id=row[0],
                        previous_state=row[1],
                        new_state=row[2],
                        transition_reason=row[3],
                        duration_in_prev_state_days=row[4],
                        risk_snapshot=row[5],
                        metrics_snapshot=row[6],
                        timestamp=row[7]
                    )
                    for row in rows
                ]
            else:
                # Fallback: read from CSV
                csv_file = self.storage_path / "state_history.csv"
                if not csv_file.exists():
                    return []
                
                records = []
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['account_id'] == account_id:
                            records.append(StateHistoryRecord(
                                account_id=row['account_id'],
                                previous_state=row['previous_state'] or None,
                                new_state=row['new_state'],
                                transition_reason=row['transition_reason'],
                                duration_in_prev_state_days=int(row['duration_days']),
                                risk_snapshot=eval(row['risk_snapshot']),
                                metrics_snapshot=eval(row['metrics_snapshot']),
                                timestamp=datetime.fromisoformat(row['timestamp'])
                            ))
                
                return records[-limit:]  # Last N records
        
        except Exception as e:
            logger.error(f"Error getting state history: {e}")
            return []
    
    # ========================================================================
    # METRICS HISTORY
    # ========================================================================
    
    def record_metrics_snapshot(
        self,
        account_id: str,
        maturity_score: float,
        risk_score: float,
        readiness_score: float,
        total_actions: int = 0,
        action_diversity: float = 0.0,
        impressions: int = 0,
        blocks: int = 0,
        comments: int = 0,
        followers: int = 0,
        engagement_rate: float = 0.0
    ) -> bool:
        """
        Record metrics snapshot.
        """
        try:
            record = MetricsHistoryRecord(
                account_id=account_id,
                maturity_score=maturity_score,
                risk_score=risk_score,
                readiness_score=readiness_score,
                total_actions=total_actions,
                action_diversity=action_diversity,
                impressions=impressions,
                blocks=blocks,
                comments=comments,
                followers=followers,
                engagement_rate=engagement_rate,
                timestamp=datetime.now()
            )
            
            if self.db:
                cursor = self.db.cursor()
                cursor.execute("""
                    INSERT INTO accounts_metrics_history (
                        account_id, maturity_score, risk_score, readiness_score,
                        total_actions, action_diversity, impressions, blocks, comments,
                        followers, engagement_rate, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    account_id,
                    maturity_score,
                    risk_score,
                    readiness_score,
                    total_actions,
                    action_diversity,
                    impressions,
                    blocks,
                    comments,
                    followers,
                    engagement_rate,
                    record.timestamp
                ))
                self.db.commit()
                return True
            else:
                # CSV fallback
                csv_file = self.storage_path / "metrics_history.csv"
                file_exists = csv_file.exists()
                
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow([
                            'account_id', 'maturity_score', 'risk_score', 'readiness_score',
                            'total_actions', 'action_diversity', 'impressions', 'blocks',
                            'comments', 'followers', 'engagement_rate', 'timestamp'
                        ])
                    
                    writer.writerow([
                        account_id, maturity_score, risk_score, readiness_score,
                        total_actions, action_diversity, impressions, blocks,
                        comments, followers, engagement_rate, record.timestamp.isoformat()
                    ])
                
                return True
        
        except Exception as e:
            logger.error(f"Error recording metrics snapshot: {e}")
            return False
    
    def get_metrics_history(
        self,
        account_id: str,
        days: int = 30
    ) -> List[MetricsHistoryRecord]:
        """
        Get metrics history for account (last N days).
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            if self.db:
                cursor = self.db.cursor()
                cursor.execute("""
                    SELECT account_id, maturity_score, risk_score, readiness_score,
                           total_actions, action_diversity, impressions, blocks, comments,
                           followers, engagement_rate, timestamp
                    FROM accounts_metrics_history
                    WHERE account_id = %s AND timestamp >= %s
                    ORDER BY timestamp ASC
                """, (account_id, cutoff))
                
                rows = cursor.fetchall()
                return [
                    MetricsHistoryRecord(
                        account_id=row[0],
                        maturity_score=row[1],
                        risk_score=row[2],
                        readiness_score=row[3],
                        total_actions=row[4],
                        action_diversity=row[5],
                        impressions=row[6],
                        blocks=row[7],
                        comments=row[8],
                        followers=row[9],
                        engagement_rate=row[10],
                        timestamp=row[11]
                    )
                    for row in rows
                ]
            else:
                # CSV fallback
                csv_file = self.storage_path / "metrics_history.csv"
                if not csv_file.exists():
                    return []
                
                records = []
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['account_id'] == account_id:
                            ts = datetime.fromisoformat(row['timestamp'])
                            if ts >= cutoff:
                                records.append(MetricsHistoryRecord(
                                    account_id=row['account_id'],
                                    maturity_score=float(row['maturity_score']),
                                    risk_score=float(row['risk_score']),
                                    readiness_score=float(row['readiness_score']),
                                    total_actions=int(row['total_actions']),
                                    action_diversity=float(row['action_diversity']),
                                    impressions=int(row['impressions']),
                                    blocks=int(row['blocks']),
                                    comments=int(row['comments']),
                                    followers=int(row['followers']),
                                    engagement_rate=float(row['engagement_rate']),
                                    timestamp=ts
                                ))
                
                return records
        
        except Exception as e:
            logger.error(f"Error getting metrics history: {e}")
            return []
    
    # ========================================================================
    # WARMUP TASKS
    # ========================================================================
    
    def create_warmup_task(
        self,
        task_id: str,
        account_id: str,
        warmup_day: int,
        warmup_phase: str,
        description: str,
        required_actions: Dict,
        due_date: Optional[datetime] = None
    ) -> bool:
        """
        Create warmup task record.
        """
        try:
            record = WarmupTaskRecord(
                task_id=task_id,
                account_id=account_id,
                warmup_day=warmup_day,
                warmup_phase=warmup_phase,
                description=description,
                required_actions=required_actions,
                status='pending',
                human_required=True,
                created_at=datetime.now(),
                due_date=due_date,
                started_at=None,
                completed_at=None,
                verification_result=None
            )
            
            if self.db:
                import json
                cursor = self.db.cursor()
                cursor.execute("""
                    INSERT INTO warmup_human_tasks (
                        task_id, account_id, warmup_day, warmup_phase, description,
                        required_actions, status, human_required, created_at, due_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    task_id, account_id, warmup_day, warmup_phase, description,
                    json.dumps(required_actions), 'pending', True,
                    record.created_at, due_date
                ))
                self.db.commit()
                return True
            else:
                # CSV fallback
                csv_file = self.storage_path / "warmup_tasks.csv"
                file_exists = csv_file.exists()
                
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow([
                            'task_id', 'account_id', 'warmup_day', 'warmup_phase',
                            'description', 'required_actions', 'status', 'created_at',
                            'due_date', 'completed_at'
                        ])
                    
                    writer.writerow([
                        task_id, account_id, warmup_day, warmup_phase,
                        description, str(required_actions), 'pending',
                        record.created_at.isoformat(),
                        due_date.isoformat() if due_date else '',
                        ''
                    ])
                
                return True
        
        except Exception as e:
            logger.error(f"Error creating warmup task: {e}")
            return False
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        verification_result: Optional[Dict] = None
    ) -> bool:
        """
        Update task status (pending → started → completed/failed).
        """
        try:
            timestamp = datetime.now()
            
            if self.db:
                import json
                cursor = self.db.cursor()
                
                if status == 'started':
                    cursor.execute("""
                        UPDATE warmup_human_tasks
                        SET status = %s, started_at = %s
                        WHERE task_id = %s
                    """, (status, timestamp, task_id))
                elif status in ('completed', 'failed'):
                    cursor.execute("""
                        UPDATE warmup_human_tasks
                        SET status = %s, completed_at = %s, verification_result = %s
                        WHERE task_id = %s
                    """, (status, timestamp, json.dumps(verification_result) if verification_result else None, task_id))
                else:
                    cursor.execute("""
                        UPDATE warmup_human_tasks
                        SET status = %s
                        WHERE task_id = %s
                    """, (status, task_id))
                
                self.db.commit()
                return True
            else:
                # CSV fallback (rewrite file)
                csv_file = self.storage_path / "warmup_tasks.csv"
                if not csv_file.exists():
                    return False
                
                rows = []
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['task_id'] == task_id:
                            row['status'] = status
                            if status in ('completed', 'failed'):
                                row['completed_at'] = timestamp.isoformat()
                        rows.append(row)
                
                with open(csv_file, 'w', newline='') as f:
                    if rows:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
                
                return True
        
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False
    
    def get_pending_tasks(self, account_id: Optional[str] = None) -> List[WarmupTaskRecord]:
        """
        Get all pending warmup tasks (optionally filtered by account).
        """
        try:
            if self.db:
                cursor = self.db.cursor()
                
                if account_id:
                    cursor.execute("""
                        SELECT task_id, account_id, warmup_day, warmup_phase, description,
                               required_actions, status, human_required, created_at, due_date,
                               started_at, completed_at, verification_result
                        FROM warmup_human_tasks
                        WHERE account_id = %s AND status = 'pending'
                        ORDER BY due_date ASC
                    """, (account_id,))
                else:
                    cursor.execute("""
                        SELECT task_id, account_id, warmup_day, warmup_phase, description,
                               required_actions, status, human_required, created_at, due_date,
                               started_at, completed_at, verification_result
                        FROM warmup_human_tasks
                        WHERE status = 'pending'
                        ORDER BY due_date ASC
                    """)
                
                rows = cursor.fetchall()
                return [
                    WarmupTaskRecord(
                        task_id=row[0],
                        account_id=row[1],
                        warmup_day=row[2],
                        warmup_phase=row[3],
                        description=row[4],
                        required_actions=row[5],
                        status=row[6],
                        human_required=row[7],
                        created_at=row[8],
                        due_date=row[9],
                        started_at=row[10],
                        completed_at=row[11],
                        verification_result=row[12]
                    )
                    for row in rows
                ]
            else:
                # CSV fallback
                csv_file = self.storage_path / "warmup_tasks.csv"
                if not csv_file.exists():
                    return []
                
                records = []
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['status'] == 'pending':
                            if account_id is None or row['account_id'] == account_id:
                                records.append(WarmupTaskRecord(
                                    task_id=row['task_id'],
                                    account_id=row['account_id'],
                                    warmup_day=int(row['warmup_day']),
                                    warmup_phase=row['warmup_phase'],
                                    description=row['description'],
                                    required_actions=eval(row['required_actions']),
                                    status=row['status'],
                                    human_required=True,
                                    created_at=datetime.fromisoformat(row['created_at']),
                                    due_date=datetime.fromisoformat(row['due_date']) if row['due_date'] else None,
                                    started_at=None,
                                    completed_at=None,
                                    verification_result=None
                                ))
                
                return records
        
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []
    
    # ========================================================================
    # CSV EXPORT
    # ========================================================================
    
    def export_to_csv(self, table_name: str, output_file: str) -> bool:
        """
        Export table to CSV file.
        
        Args:
            table_name: Table to export (state_history, metrics_history, warmup_tasks)
            output_file: Output CSV file path
        """
        try:
            if not self.db:
                logger.warning("No database connection, CSV export not available")
                return False
            
            cursor = self.db.cursor()
            
            # Get table data
            table_map = {
                'state_history': 'accounts_state_history',
                'metrics_history': 'accounts_metrics_history',
                'warmup_tasks': 'warmup_human_tasks'
            }
            
            db_table = table_map.get(table_name)
            if not db_table:
                logger.error(f"Unknown table: {table_name}")
                return False
            
            cursor.execute(f"SELECT * FROM {db_table} ORDER BY timestamp DESC LIMIT 10000")
            rows = cursor.fetchall()
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Write CSV
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
            
            logger.info(f"Exported {len(rows)} rows to {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    def cleanup_old_data(self, days: int = 90) -> bool:
        """
        Cleanup data older than N days.
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            if self.db:
                cursor = self.db.cursor()
                
                # Delete old state history
                cursor.execute("""
                    DELETE FROM accounts_state_history 
                    WHERE timestamp < %s
                """, (cutoff,))
                
                # Delete old metrics history
                cursor.execute("""
                    DELETE FROM accounts_metrics_history 
                    WHERE timestamp < %s
                """, (cutoff,))
                
                # Delete old completed tasks
                cursor.execute("""
                    DELETE FROM warmup_human_tasks 
                    WHERE status IN ('completed', 'failed', 'expired') 
                    AND completed_at < %s
                """, (cutoff,))
                
                self.db.commit()
                logger.info(f"Cleaned up data older than {days} days")
                return True
            else:
                logger.info("Cleanup not available without database connection")
                return False
        
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_persistence_instance: Optional[ObservabilityPersistence] = None


def get_persistence() -> ObservabilityPersistence:
    """Get global persistence instance"""
    global _persistence_instance
    if _persistence_instance is None:
        _persistence_instance = ObservabilityPersistence()
    return _persistence_instance


def set_persistence(instance: ObservabilityPersistence):
    """Set global persistence instance"""
    global _persistence_instance
    _persistence_instance = instance


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SQL_SCHEMA",
    "StateHistoryRecord",
    "MetricsHistoryRecord",
    "WarmupTaskRecord",
    "ObservabilityPersistence",
    "get_persistence",
    "set_persistence",
]
