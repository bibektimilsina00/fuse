import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlmodel import Session, select
from src.database import engine as db_engine
from src.worker import celery_app
from src.workflows.models import Workflow, WorkflowNode

logger = logging.getLogger(__name__)

@celery_app.task(name="src.workflows.engine.check_scheduled_workflows")
def check_scheduled_workflows():
    """
    Scans all active workflows for schedule triggers and executes them if due.
    """
    from src.workflows.engine.executor import execute_workflow_task
    
    logger.debug("Checking for scheduled workflows...")
    
    with Session(db_engine) as session:
        # Get all trigger nodes of type 'schedule.cron' belonging to 'active' workflows
        # We use a join to ensure we only get nodes from active workflows
        statement = select(WorkflowNode).join(Workflow).where(
            WorkflowNode.node_type == "schedule.cron",
            Workflow.status == "active"
        )
        
        trigger_nodes = session.exec(statement).all()
        now = datetime.utcnow()
        triggered_count = 0
        
        for node in trigger_nodes:
            try:
                # spec contains the configuration (V2 structure)
                spec = node.spec or {}
                config = spec.get("config", {})
                
                interval = config.get("interval", 15)
                frequency = config.get("frequency", "seconds")
                
                # Retrieve last run time from spec
                last_run_str = spec.get("last_run_at")
                if last_run_str:
                    try:
                        last_run_at = datetime.fromisoformat(last_run_str)
                    except ValueError:
                        last_run_at = datetime.min
                else:
                    last_run_at = datetime.min
                
                # Calculate if it's due
                delta = timedelta(seconds=0)
                if frequency == "seconds":
                    delta = timedelta(seconds=interval)
                elif frequency == "minutes":
                    delta = timedelta(minutes=interval)
                elif frequency == "hours":
                    delta = timedelta(hours=interval)
                elif frequency == "days":
                    delta = timedelta(days=interval)
                
                if now >= last_run_at + delta:
                    logger.info(f"Triggering workflow {node.workflow_id} (Node: {node.node_id})")
                    
                    # Update last_run_at immediately in the database
                    # This prevents double-triggering if the heartbeat runs again before execution starts
                    new_spec = dict(spec)
                    new_spec["last_run_at"] = now.isoformat()
                    node.spec = new_spec
                    session.add(node)
                    session.commit()
                    
                    # Execute workflow
                    trigger_data = {
                        "source": "schedule",
                        "triggered_at": now.isoformat(),
                        "node_id": node.node_id,
                        "interval": interval,
                        "frequency": frequency
                    }
                    
                    execute_workflow_task.delay(str(node.workflow_id), trigger_data)
                    triggered_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing schedule node {node.id}: {e}")
                continue
                
    if triggered_count > 0:
        logger.info(f"Scheduled check complete. Triggered {triggered_count} workflows.")
    return triggered_count
