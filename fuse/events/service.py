import logging
import uuid
from typing import Any, Dict, List
from sqlmodel import Session, select
from fuse.database import engine as db_engine
from fuse.workflows.models import Workflow, WorkflowNode
from fuse.workflows.engine.core import WorkflowEngine

logger = logging.getLogger(__name__)

class EventService:
    @staticmethod
    def dispatch(event_type: str, payload: Dict[str, Any]):
        """
        Dispatch an event to matching active workflows.
        
        Args:
            event_type: Type of event (e.g., 'datatables.row_created')
            payload: Event data
        """
        logger.info(f"Dispatching event {event_type} with payload: {payload}")
        
        with Session(db_engine) as session:
            # Find all nodes of type 'core.data_table.trigger' in active workflows
            # We match the node_type exactly as defined in our package system
            statement = (
                select(WorkflowNode, Workflow)
                .join(Workflow)
                .where(Workflow.status == "active")
                .where(WorkflowNode.node_type == "core.data_table.trigger")
            )
            results = session.exec(statement).all()
            
            triggered_count = 0
            for node, workflow in results:
                config = node.spec.get("config", {})
                
                # Match event type (created, updated, deleted)
                config_event = config.get("event_type")
                config_table_id = config.get("table_id")
                
                # payload['table_id'] is a UUID usually from datatables service
                event_leaf = event_type.split('.')[-1]
                
                if config_event and config_event != "any" and config_event != event_leaf:
                    continue
                    
                if config_table_id and str(config_table_id) != str(payload.get("table_id")):
                    continue
                
                logger.info(f"Event Logic matched! Triggering workflow: {workflow.id}")
                WorkflowEngine.start_execution(workflow.id, payload)
                triggered_count += 1
                
            if triggered_count > 0:
                logger.info(f"Dispatched {event_type} to {triggered_count} workflows.")

event_service = EventService()
