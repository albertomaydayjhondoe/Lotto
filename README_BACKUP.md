# Backup & Restore Documentation

## Overview

This document describes the backup and restore procedures for the Stakazo platform, including PostgreSQL database snapshots and Memory Vault cold exports.

**Status:** Phase 1 (STUB Mode)  
**Last Updated:** 2025-11-28

---

## Backup Types

### 1. PostgreSQL Daily Snapshots

**Frequency:** Daily (02:00 UTC)  
**Retention:** 30 days  
**Storage:** Cloud Storage (encrypted)  
**Script:** `scripts/backup_postgres.sh`

#### What's Backed Up
- All database tables
- Indices
- Sequences
- Schema

#### Excluded
- Temporary tables
- Session data (Redis)
- Application logs (separate retention)

---

### 2. Memory Vault Monthly Cold Export

**Frequency:** Monthly (1st day, 03:00 UTC)  
**Retention:** 12 months  
**Format:** TAR.GZ + AES-256 encryption  
**Storage:** Off-site cold storage  
**Script:** `scripts/backup_memory_vault.sh`

#### What's Backed Up
- `ml_features/` - Machine learning feature vectors
- `audits/` - Audit logs and compliance records
- `campaign_history/` - Historical campaign metadata
- `clips_metadata/` - Enriched clip metadata
- `orchestrator_runs/` - Orchestrator execution logs

---

## Running Backups

### Manual PostgreSQL Backup

```bash
# Development/staging (STUB mode)
cd /workspaces/stakazo
./scripts/backup_postgres.sh --manual

# Production (requires environment variables)
export DB_HOST=your-db-host
export DB_USER=your-db-user
export PGPASSWORD=your-db-password
export DB_NAME=stakazo_prod
export BACKUP_DIR=/backups/postgres
./scripts/backup_postgres.sh --daily
```

### Manual Memory Vault Backup

```bash
# Development/staging (STUB mode)
cd /workspaces/stakazo
./scripts/backup_memory_vault.sh --manual

# Production (requires Google Drive API credentials)
export VAULT_ROOT=gdrive:/stakazo/memory_vault/
export BACKUP_DIR=/backups/memory_vault
export KMS_KEY_ID=your-kms-key-id
./scripts/backup_memory_vault.sh --monthly
```

---

## Restore Procedures

### PostgreSQL Restore

**Restore Time Target:** < 4 hours

#### Steps

1. **Stop application services**
   ```bash
   systemctl stop stakazo-api
   systemctl stop stakazo-workers
   ```

2. **Verify backup integrity**
   ```bash
   cd /backups/postgres
   sha256sum -c postgres_backup_YYYYMMDD_HHMMSS.sql.gz.sha256
   ```

3. **Decompress backup**
   ```bash
   gunzip postgres_backup_YYYYMMDD_HHMMSS.sql.gz
   ```

4. **Restore to database**
   ```bash
   # CAUTION: This will drop and recreate the database
   psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS stakazo_prod;"
   psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c "CREATE DATABASE stakazo_prod;"
   psql -h ${DB_HOST} -U ${DB_USER} -d stakazo_prod < postgres_backup_YYYYMMDD_HHMMSS.sql
   ```

5. **Run migrations (if needed)**
   ```bash
   cd /workspaces/stakazo/backend
   alembic upgrade head
   ```

6. **Verify data integrity**
   ```bash
   psql -h ${DB_HOST} -U ${DB_USER} -d stakazo_prod -c "SELECT COUNT(*) FROM campaigns;"
   psql -h ${DB_HOST} -U ${DB_USER} -d stakazo_prod -c "SELECT COUNT(*) FROM clips;"
   ```

7. **Restart services**
   ```bash
   systemctl start stakazo-api
   systemctl start stakazo-workers
   ```

---

### Memory Vault Restore

**Restore Time Target:** < 24 hours

#### Steps

1. **Verify backup integrity**
   ```bash
   cd /backups/memory_vault
   sha256sum -c memory_vault_YYYYMM.tar.gz.enc.sha256
   ```

2. **Decrypt backup**
   ```bash
   # STUB mode (development)
   cp memory_vault_YYYYMM.tar.gz.enc memory_vault_YYYYMM.tar.gz
   
   # PRODUCTION mode
   openssl enc -aes-256-cbc -d -salt -pbkdf2 \
     -in memory_vault_YYYYMM.tar.gz.enc \
     -out memory_vault_YYYYMM.tar.gz \
     -pass file:/path/to/kms-key
   ```

3. **Extract archive**
   ```bash
   mkdir -p /tmp/vault_restore
   tar xzf memory_vault_YYYYMM.tar.gz -C /tmp/vault_restore
   ```

4. **Upload to Google Drive** (production)
   ```bash
   # Use Google Drive API to restore folder structure
   # Or use rclone:
   rclone sync /tmp/vault_restore gdrive:stakazo/memory_vault/
   ```

5. **Rebuild database index**
   ```bash
   cd /workspaces/stakazo/backend
   python -c "from app.memory_vault.rebuild_index import rebuild; rebuild()"
   ```

6. **Verify restoration**
   ```bash
   # Check file counts
   python -c "from app.memory_vault.storage import storage; print(storage.list_files('ml_features'))"
   ```

---

## Restore Testing Schedule

**Frequency:** Quarterly (Q1, Q2, Q3, Q4)  
**Environment:** Staging  
**Duration:** ~4 hours for full test

### Test Checklist

- [ ] Restore PostgreSQL backup to staging
- [ ] Verify database integrity (record counts, schema)
- [ ] Restore Memory Vault backup to staging
- [ ] Verify file counts and checksums
- [ ] Run application smoke tests
- [ ] Measure restore time (document actual vs target)
- [ ] Document any issues or improvements
- [ ] Update this README with findings

### Q1 2025 Test Results
*To be completed*

### Q2 2025 Test Results
*To be completed*

### Q3 2025 Test Results
*To be completed*

### Q4 2025 Test Results
*To be completed*

---

## Automation

### Cron Jobs (Production)

Add to crontab:

```cron
# PostgreSQL daily backup at 02:00 UTC
0 2 * * * /path/to/scripts/backup_postgres.sh --daily >> /var/log/stakazo/backup_postgres.log 2>&1

# Memory Vault monthly backup on 1st day at 03:00 UTC
0 3 1 * * /path/to/scripts/backup_memory_vault.sh --monthly >> /var/log/stakazo/backup_vault.log 2>&1
```

### Monitoring Alerts

Set up alerts for:
- Backup failure (email + Slack)
- Backup size anomaly (> 50% deviation)
- Backup duration exceeded (> 2x average)
- Disk space low (< 20% free in backup directory)

---

## Security Considerations

### Encryption

- **PostgreSQL backups:** Encrypted at rest in cloud storage
- **Memory Vault backups:** AES-256 with KMS-managed keys
- **Transmission:** TLS 1.3 for all transfers

### Access Control

- Backup scripts run with dedicated service account
- Minimal permissions (write to backup dir, read from DB)
- KMS keys rotated quarterly
- Access audited in CloudTrail/equivalent

### Compliance

- GDPR: Backups include personal data, same retention applies
- HIPAA: N/A (no health data)
- SOC 2: Backup logs retained for audit

---

## Troubleshooting

### PostgreSQL Backup Fails

**Symptom:** Script exits with error  
**Common Causes:**
- Database connection timeout
- Disk space full
- Permission denied

**Solution:**
```bash
# Check database connectivity
psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -c "SELECT version();"

# Check disk space
df -h ${BACKUP_DIR}

# Check permissions
ls -la ${BACKUP_DIR}
```

### Memory Vault Backup Size Anomaly

**Symptom:** Backup size is significantly larger/smaller than expected  
**Investigation:**
```bash
# Compare with previous backup
ls -lh /backups/memory_vault/

# Check vault contents
du -sh /tmp/stakazo_memory_vault/*

# Investigate specific folders
find /tmp/stakazo_memory_vault/ml_features -type f -mtime -30 | wc -l
```

---

## Phase 2 Enhancements

- [ ] Incremental backups (reduce storage costs)
- [ ] Point-in-time recovery (PITR)
- [ ] Cross-region replication
- [ ] Automated restore testing (monthly)
- [ ] Backup compression optimization
- [ ] Backup deduplication
- [ ] Cloud-native backup solutions (AWS Backup, etc)

---

## Contact

**Backup Admin:** devops@stakazo.com  
**On-Call:** Use PagerDuty for emergencies  
**Documentation:** https://docs.stakazo.com/backups
