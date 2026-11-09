"""
Workflow Executor - DAG-based workflow execution engine
"""

import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session
from enum import Enum

from models import Workflow

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Workflow node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowNode:
    """Represents a single node in a workflow"""
    
    def __init__(
        self,
        node_id: str,
        node_type: str,
        config: Dict[str, Any],
        depends_on: List[str] = None,
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.config = config
        self.depends_on = depends_on or []
        self.status = NodeStatus.PENDING
        self.output = None
        self.error = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def duration_seconds(self) -> float:
        """Get execution duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


class WorkflowDAG:
    """Directed acyclic graph for workflow execution"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.nodes: Dict[str, WorkflowNode] = {}
        self.run_id = str(uuid.uuid4())
    
    def add_node(
        self,
        node_id: str,
        node_type: str,
        config: Dict[str, Any],
        depends_on: List[str] = None,
    ) -> WorkflowNode:
        """Add a node to the DAG"""
        node = WorkflowNode(node_id, node_type, config, depends_on)
        self.nodes[node_id] = node
        return node
    
    def get_executable_nodes(self) -> List[WorkflowNode]:
        """Get nodes that are ready to execute (all dependencies met)"""
        executable = []
        for node in self.nodes.values():
            if node.status == NodeStatus.PENDING:
                # Check if all dependencies are completed
                deps_complete = all(
                    self.nodes[dep].status == NodeStatus.COMPLETED
                    for dep in node.depends_on
                )
                if deps_complete:
                    executable.append(node)
        return executable
    
    def topological_sort(self) -> List[List[WorkflowNode]]:
        """Sort nodes into execution layers"""
        layers = []
        processed = set()
        
        while len(processed) < len(self.nodes):
            layer = []
            for node in self.nodes.values():
                if node.node_id not in processed:
                    # Check if all deps are processed
                    if all(dep in processed for dep in node.depends_on):
                        layer.append(node)
            
            if not layer:
                break  # Cycle detected
            
            layers.append(layer)
            processed.update(n.node_id for n in layer)
        
        return layers
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DAG to dictionary for storage/transmission"""
        return {
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "config": node.config,
                    "depends_on": node.depends_on,
                    "status": node.status.value,
                    "output": node.output,
                    "error": node.error,
                }
                for node_id, node in self.nodes.items()
            }
        }


class WorkflowExecutor:
    """Executes workflow DAGs"""
    
    def __init__(self):
        self.node_handlers: Dict[str, Callable] = {}
        self.running_workflows: Dict[str, WorkflowDAG] = {}
    
    def register_node_handler(
        self,
        node_type: str,
        handler: Callable,
    ) -> None:
        """
        Register a handler for a node type.
        
        Args:
            node_type: Type of node (e.g., 'execute_command', 'process_file')
            handler: Async callable that executes the node
        """
        self.node_handlers[node_type] = handler
        logger.info(f"Registered handler for node type: {node_type}")
    
    async def execute_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
    ) -> Any:
        """
        Execute a single workflow node.
        
        Args:
            node: WorkflowNode to execute
            context: Execution context (environment variables, previous outputs)
        
        Returns:
            Node output
        """
        try:
            node.status = NodeStatus.RUNNING
            node.started_at = datetime.utcnow()
            
            # Get handler
            handler = self.node_handlers.get(node.node_type)
            if not handler:
                raise ValueError(f"No handler for node type: {node.node_type}")
            
            # Execute
            logger.info(f"Executing node {node.node_id} ({node.node_type})")
            output = await handler(node.config, context)
            
            node.status = NodeStatus.COMPLETED
            node.output = output
            
            logger.info(f"Node {node.node_id} completed successfully")
            
            return output
        
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            logger.error(f"Node {node.node_id} failed: {e}")
            raise
        
        finally:
            node.completed_at = datetime.utcnow()
    
    async def execute_dag(
        self,
        dag: WorkflowDAG,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow DAG.
        
        Args:
            dag: WorkflowDAG to execute
            context: Execution context
        
        Returns:
            Execution results
        """
        context = context or {}
        self.running_workflows[dag.run_id] = dag
        
        try:
            logger.info(f"Starting workflow execution: {dag.run_id}")
            
            # Get topological sort
            layers = dag.topological_sort()
            
            # Execute layer by layer
            for layer_idx, layer in enumerate(layers):
                logger.info(f"Executing layer {layer_idx + 1}/{len(layers)}")
                
                # Execute all nodes in layer in parallel
                tasks = [
                    self.execute_node(node, context)
                    for node in layer
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update context with outputs
                for node, result in zip(layer, results):
                    if not isinstance(result, Exception):
                        context[f"output_{node.node_id}"] = node.output
                
                # Check for failures
                failures = [r for r in results if isinstance(r, Exception)]
                if failures:
                    logger.error(f"Layer {layer_idx} had {len(failures)} failures")
                    # Decide whether to continue or fail
                    # For now, continue to allow partial execution
            
            # Compile results
            results = {
                "run_id": dag.run_id,
                "workflow_id": dag.workflow_id,
                "status": "completed",
                "outputs": {
                    node_id: node.output
                    for node_id, node in dag.nodes.items()
                    if node.status == NodeStatus.COMPLETED
                },
                "errors": {
                    node_id: node.error
                    for node_id, node in dag.nodes.items()
                    if node.error
                },
                "duration_seconds": sum(
                    node.duration_seconds()
                    for node in dag.nodes.values()
                ),
            }
            
            logger.info(f"Workflow {dag.run_id} completed")
            
            return results
        
        finally:
            del self.running_workflows[dag.run_id]
    
    def get_workflow_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get status of running or completed workflow"""
        dag = self.running_workflows.get(run_id)
        if dag:
            return dag.to_dict()
        return None
    
    def cancel_workflow(self, run_id: str) -> bool:
        """Cancel a running workflow"""
        dag = self.running_workflows.get(run_id)
        if dag:
            # Mark all pending/running nodes as cancelled
            for node in dag.nodes.values():
                if node.status in (NodeStatus.PENDING, NodeStatus.RUNNING):
                    node.status = NodeStatus.SKIPPED
            return True
        return False


# Default executor instance
_executor: Optional[WorkflowExecutor] = None


def get_executor() -> WorkflowExecutor:
    """Get or create the default executor"""
    global _executor
    if _executor is None:
        _executor = WorkflowExecutor()
    return _executor


# Built-in node handlers

async def execute_command_handler(config: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Execute a shell command"""
    command = config.get("command", "")
    # Would actually execute the command
    return f"Output of: {command}"


async def process_file_handler(config: Dict[str, Any], context: Dict[str, Any]) -> Dict:
    """Process a file"""
    file_path = config.get("path", "")
    operation = config.get("operation", "")
    # Would actually process the file
    return {"file": file_path, "operation": operation, "processed": True}


async def http_request_handler(config: Dict[str, Any], context: Dict[str, Any]) -> Dict:
    """Make an HTTP request"""
    url = config.get("url", "")
    method = config.get("method", "GET")
    # Would actually make the request
    return {"url": url, "method": method, "status": 200}


# Register built-in handlers
def register_builtin_handlers():
    """Register built-in node handlers"""
    executor = get_executor()
    executor.register_node_handler("execute_command", execute_command_handler)
    executor.register_node_handler("process_file", process_file_handler)
    executor.register_node_handler("http_request", http_request_handler)


# Initialize
register_builtin_handlers()
