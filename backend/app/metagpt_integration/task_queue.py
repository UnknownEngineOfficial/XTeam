"""
Redis-backed Async Task Queue Module

This module provides a Redis-backed task queue for managing long-running
agent workflows asynchronously. It includes job enqueueing, processing,
status tracking, and a worker loop for consuming jobs.

Features:
- Async job enqueueing with priority support
- Job status tracking (pending, running, completed, failed)
- Worker loop for processing jobs
- Retry logic with exponential backoff
- Job result caching
- Dead letter queue for failed jobs
"""

import json
import asyncio
import logging
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import Settings


logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class JobPriority(int, Enum):
    """Job priority levels (higher number = higher priority)."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class Job:
    """
    Represents a job in the task queue.
    
    Attributes:
        job_id: Unique job identifier
        job_type: Type of job (e.g., 'workflow', 'deployment')
        payload: Job data/parameters
        status: Current job status
        priority: Job priority level
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        result: Job result data
        error: Error message if job failed
        retry_count: Number of retries attempted
        max_retries: Maximum number of retries allowed
        timeout_seconds: Job timeout in seconds
        tags: Optional tags for job categorization
    """

    def __init__(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: int = 3600,
        tags: Optional[List[str]] = None,
        job_id: Optional[str] = None,
    ):
        """Initialize a new job."""
        self.job_id = job_id or str(uuid4())
        self.job_type = job_type
        self.payload = payload
        self.status = JobStatus.PENDING
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.retry_count = 0
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "payload": self.payload,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create job from dictionary."""
        job = cls(
            job_type=data["job_type"],
            payload=data["payload"],
            priority=JobPriority(data.get("priority", JobPriority.NORMAL.value)),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 3600),
            tags=data.get("tags", []),
            job_id=data.get("job_id"),
        )
        job.status = JobStatus(data.get("status", JobStatus.PENDING.value))
        if data.get("started_at"):
            job.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            job.completed_at = datetime.fromisoformat(data["completed_at"])
        job.result = data.get("result")
        job.error = data.get("error")
        job.retry_count = data.get("retry_count", 0)
        return job

    def mark_running(self) -> None:
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: Dict[str, Any]) -> None:
        """Mark job as completed with result."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def mark_failed(self, error: str) -> None:
        """Mark job as failed with error message."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def mark_timeout(self) -> None:
        """Mark job as timed out."""
        self.status = JobStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        self.error = f"Job timed out after {self.timeout_seconds} seconds"

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry count and mark as retrying."""
        self.retry_count += 1
        self.status = JobStatus.RETRYING
        self.error = None


class TaskQueue:
    """
    Redis-backed async task queue for managing long-running jobs.
    
    Provides methods for:
    - Enqueueing jobs with priority
    - Processing jobs with worker loop
    - Tracking job status
    - Handling retries and timeouts
    - Managing dead letter queue
    """

    def __init__(self, settings: Settings):
        """
        Initialize task queue.
        
        Args:
            settings: Application settings with Redis configuration
        """
        self.settings = settings
        self.redis: Optional[Redis] = None
        self.queue_key = "task_queue"
        self.job_prefix = "job:"
        self.status_prefix = "job_status:"
        self.result_prefix = "job_result:"
        self.dlq_key = "task_queue:dlq"  # Dead Letter Queue
        self.processing_key = "task_queue:processing"
        self.job_handlers: Dict[str, Callable] = {}

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = await redis.from_url(
                self.settings.redis_queue_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis.ping()
            logger.info("Connected to Redis task queue")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis task queue")

    def register_handler(self, job_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific job type.
        
        Args:
            job_type: Type of job to handle
            handler: Async callable that processes the job
        """
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    async def enqueue_job(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: int = 3600,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Enqueue a new job.
        
        Args:
            job_type: Type of job
            payload: Job data/parameters
            priority: Job priority level
            max_retries: Maximum number of retries
            timeout_seconds: Job timeout in seconds
            tags: Optional tags for categorization
            
        Returns:
            Job ID
            
        Raises:
            RuntimeError: If Redis is not connected
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        job = Job(
            job_type=job_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            tags=tags,
        )

        # Store job data
        job_key = f"{self.job_prefix}{job.job_id}"
        await self.redis.set(job_key, json.dumps(job.to_dict()), ex=86400)  # 24h TTL

        # Add to queue with priority score (higher priority = lower score for sorted set)
        score = -priority.value  # Negative so higher priority comes first
        await self.redis.zadd(self.queue_key, {job.job_id: score})

        logger.info(f"Enqueued job {job.job_id} of type {job_type} with priority {priority.name}")
        return job.job_id

    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job object or None if not found
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        job_key = f"{self.job_prefix}{job_id}"
        job_data = await self.redis.get(job_key)

        if not job_data:
            return None

        return Job.from_dict(json.loads(job_data))

    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status or None if not found
        """
        job = await self.get_job(job_id)
        return job.status if job else None

    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job result.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job result or None if not available
        """
        job = await self.get_job(job_id)
        return job.result if job else None

    async def get_job_error(self, job_id: str) -> Optional[str]:
        """
        Get job error message.
        
        Args:
            job_id: Job ID
            
        Returns:
            Error message or None if no error
        """
        job = await self.get_job(job_id)
        return job.error if job else None

    async def _save_job(self, job: Job) -> None:
        """Save job state to Redis."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        job_key = f"{self.job_prefix}{job.job_id}"
        await self.redis.set(job_key, json.dumps(job.to_dict()), ex=86400)

    async def _process_job(self, job: Job) -> None:
        """
        Process a single job.
        
        Args:
            job: Job to process
        """
        handler = self.job_handlers.get(job.job_type)
        if not handler:
            error_msg = f"No handler registered for job type: {job.job_type}"
            logger.error(error_msg)
            job.mark_failed(error_msg)
            await self._save_job(job)
            return

        try:
            job.mark_running()
            await self._save_job(job)

            # Execute job with timeout
            result = await asyncio.wait_for(
                handler(job.payload),
                timeout=job.timeout_seconds,
            )

            job.mark_completed(result)
            logger.info(f"Job {job.job_id} completed successfully")

        except asyncio.TimeoutError:
            job.mark_timeout()
            logger.warning(f"Job {job.job_id} timed out")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Job {job.job_id} failed: {error_msg}")

            if job.can_retry():
                job.increment_retry()
                logger.info(f"Job {job.job_id} will be retried (attempt {job.retry_count}/{job.max_retries})")
            else:
                job.mark_failed(error_msg)
                logger.error(f"Job {job.job_id} exhausted retries")

        finally:
            await self._save_job(job)

    async def _handle_dead_letter(self, job: Job) -> None:
        """
        Move job to dead letter queue.
        
        Args:
            job: Failed job
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        dlq_entry = {
            "job_id": job.job_id,
            "job_type": job.job_type,
            "error": job.error,
            "failed_at": datetime.utcnow().isoformat(),
            "retry_count": job.retry_count,
        }

        await self.redis.lpush(self.dlq_key, json.dumps(dlq_entry))
        logger.warning(f"Job {job.job_id} moved to dead letter queue")

    async def process_job(self, job_id: str) -> None:
        """
        Process a specific job.
        
        Args:
            job_id: Job ID to process
        """
        job = await self.get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return

        await self._process_job(job)

        # Handle retries
        if job.status == JobStatus.RETRYING:
            # Re-enqueue with exponential backoff
            backoff_seconds = min(2 ** job.retry_count * 60, 3600)  # Max 1 hour
            await asyncio.sleep(backoff_seconds)
            score = -job.priority.value
            if self.redis:
                await self.redis.zadd(self.queue_key, {job.job_id: score})
                logger.info(f"Job {job.job_id} re-enqueued after {backoff_seconds}s backoff")

        # Handle dead letter
        elif job.status == JobStatus.FAILED:
            await self._handle_dead_letter(job)

    async def worker_loop(self, worker_id: int = 0, batch_size: int = 10) -> None:
        """
        Main worker loop for processing jobs.
        
        Continuously fetches jobs from queue and processes them.
        
        Args:
            worker_id: Worker identifier for logging
            batch_size: Number of jobs to process in each iteration
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        logger.info(f"Worker {worker_id} started")

        try:
            while True:
                try:
                    # Get next job(s) from queue (sorted by priority)
                    job_ids = await self.redis.zrange(
                        self.queue_key,
                        0,
                        batch_size - 1,
                    )

                    if not job_ids:
                        # No jobs available, wait before checking again
                        await asyncio.sleep(1)
                        continue

                    # Process each job
                    for job_id in job_ids:
                        try:
                            # Remove from queue
                            await self.redis.zrem(self.queue_key, job_id)

                            # Mark as processing
                            await self.redis.sadd(self.processing_key, job_id)

                            # Process job
                            await self.process_job(job_id)

                        except Exception as e:
                            logger.error(f"Error processing job {job_id}: {e}")

                        finally:
                            # Remove from processing set
                            await self.redis.srem(self.processing_key, job_id)

                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}")
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} stopped")
            raise

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        pending_count = await self.redis.zcard(self.queue_key)
        processing_count = await self.redis.scard(self.processing_key)
        dlq_count = await self.redis.llen(self.dlq_key)

        return {
            "pending_jobs": pending_count,
            "processing_jobs": processing_count,
            "dead_letter_queue_size": dlq_count,
            "total_jobs": pending_count + processing_count + dlq_count,
        }

    async def get_dead_letter_queue(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get dead letter queue entries.
        
        Args:
            limit: Maximum number of entries to retrieve
            
        Returns:
            List of failed job entries
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        dlq_entries = await self.redis.lrange(self.dlq_key, 0, limit - 1)
        return [json.loads(entry) for entry in dlq_entries]

    async def clear_queue(self) -> None:
        """Clear all jobs from queue."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        await self.redis.delete(self.queue_key)
        await self.redis.delete(self.processing_key)
        logger.warning("Task queue cleared")

    async def clear_dead_letter_queue(self) -> None:
        """Clear dead letter queue."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        await self.redis.delete(self.dlq_key)
        logger.warning("Dead letter queue cleared")

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled, False if not found or already processing
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Check if job is in queue
        removed = await self.redis.zrem(self.queue_key, job_id)

        if removed:
            job = await self.get_job(job_id)
            if job:
                job.mark_cancelled()
                await self._save_job(job)
            logger.info(f"Job {job_id} cancelled")
            return True

        return False


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


async def get_task_queue(settings: Settings) -> TaskQueue:
    """
    Get or create global task queue instance.
    
    Args:
        settings: Application settings
        
    Returns:
        TaskQueue instance
    """
    global _task_queue

    if _task_queue is None:
        _task_queue = TaskQueue(settings)
        await _task_queue.connect()

    return _task_queue


async def close_task_queue() -> None:
    """Close global task queue instance."""
    global _task_queue

    if _task_queue:
        await _task_queue.disconnect()
        _task_queue = None
