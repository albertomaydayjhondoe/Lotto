"""
Job Dispatcher
Maps job types to their handlers
"""
from typing import Dict, Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Job
from app.worker.handlers import run_cut_analysis
from app.e2b.dispatcher import dispatch_e2b_job, should_use_e2b_dispatcher


# Dispatch table: job_type -> handler function
DISPATCH_TABLE: Dict[str, Callable] = {
    "cut_analysis": run_cut_analysis,
    "cut_analysis_e2b": dispatch_e2b_job,  # E2B simulation
    # Add more handlers here as they're implemented:
    # "generate_variants": run_generate_variants,
    # "publish_to_platform": run_publish_to_platform,
}


async def dispatch_job(job: Job, db: AsyncSession) -> Dict[str, Any]:
    """
    Dispatch a job to its appropriate handler.
    
    Args:
        job: Job to process
        db: Database session
        
    Returns:
        Handler result dictionary
        
    Raises:
        KeyError: If job_type is not in DISPATCH_TABLE
        Exception: Any exception raised by the handler
    """
    if job.job_type not in DISPATCH_TABLE:
        raise KeyError(f"Unknown job_type: {job.job_type}. Available types: {list(DISPATCH_TABLE.keys())}")
    
    handler = DISPATCH_TABLE[job.job_type]
    result = await handler(job, db)
    
    return result


def is_job_type_supported(job_type: str) -> bool:
    """
    Check if a job type has a registered handler.
    
    Args:
        job_type: Job type string
        
    Returns:
        True if handler exists, False otherwise
    """
    return job_type in DISPATCH_TABLE
