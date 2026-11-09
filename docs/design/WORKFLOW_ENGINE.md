# Workflow Engine Architecture

**Document**: Visual Workflow & Task Execution Engine
**Version**: 1.0
**Status**: Design Phase

## Overview

The Workflow Engine enables users to visually compose complex AI and data pipelines without writing code. It supports:

- **Visual Node-based Programming**: Drag-and-drop node builder
- **Distributed Execution**: Multi-node parallel workflows
- **Event-driven**: Async task queue with progress tracking
- **Versioning**: Workflow versions and history
- **Scheduling**: One-time and recurring execution
- **Error Handling**: Retry logic, fallbacks, notifications
- **Results Storage**: Persistent output tracking

## Workflow Data Model

### Workflow Definition (JSON)

```json
{
  "id": "uuid",
  "name": "Model Fine-tuning Pipeline",
  "version": 1,
  "nodes": [
    {
      "id": "node-1",
      "type": "dataset_loader",
      "label": "Load Training Data",
      "config": {
        "storage_path": "s3://bucket/dataset.parquet",
        "format": "parquet",
        "sample_size": 1000
      },
      "position": { "x": 100, "y": 100 }
    },
    {
      "id": "node-2",
      "type": "python_code",
      "label": "Preprocess",
      "config": {
        "code": "import pandas as pd\ndf = inputs['data']\ndf['normalized'] = (df - df.mean()) / df.std()\noutputs['data'] = df"
      },
      "position": { "x": 300, "y": 100 }
    },
    {
      "id": "node-3",
      "type": "fine_tune",
      "label": "Fine-tune Llama 3",
      "config": {
        "model": "meta-llama/Llama-2-7b-hf",
        "training_params": {
          "learning_rate": 2e-5,
          "num_epochs": 3,
          "batch_size": 8
        },
        "lora": true
      },
      "position": { "x": 500, "y": 100 }
    },
    {
      "id": "node-4",
      "type": "save_output",
      "label": "Save Model",
      "config": {
        "storage_path": "s3://bucket/models/",
        "format": "huggingface"
      },
      "position": { "x": 700, "y": 100 }
    }
  ],
  "edges": [
    { "from": "node-1", "to": "node-2" },
    { "from": "node-2", "to": "node-3" },
    { "from": "node-3", "to": "node-4" }
  ],
  "metadata": {
    "created_by": "user123",
    "created_at": "2026-05-28T10:00:00Z",
    "description": "Fine-tune Llama 3 on custom dataset"
  }
}
```

## Node Types

### Input Nodes

```python
class DatasetLoaderNode:
    """Load dataset from storage"""
    inputs = []
    outputs = ['data']
    config_schema = {
        'storage_path': str,
        'format': Enum['csv', 'parquet', 'json', 'huggingface'],
        'sample_size': Optional[int]
    }
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        # Load from S3/storage
        return {'data': pd.read_parquet(config['storage_path'])}

class ModelNode:
    """Load pre-trained model"""
    inputs = []
    outputs = ['model']
    config_schema = {
        'model_name': str,  # 'meta-llama/Llama-2-7b', etc.
        'source': Enum['huggingface', 'local', 'custom_url']
    }
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        model = await load_model_from_huggingface(config['model_name'])
        return {'model': model}

class TextInputNode:
    """User text input"""
    inputs = []
    outputs = ['text']
    config_schema = {'default_value': str}
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        # Prompt user or use default
        return {'text': config.get('default_value', '')}

class ImageInputNode:
    """Image upload"""
    inputs = []
    outputs = ['image']
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        # Will be filled by user via UI
        return {'image': PIL.Image.open(config['image_path'])}
```

### Processing Nodes

```python
class PythonCodeNode:
    """Execute Python code"""
    inputs = ['*']
    outputs = ['*']
    config_schema = {'code': str}
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        # Exec user code with inputs available
        namespace = {'inputs': inputs, 'outputs': {}}
        exec(config['code'], namespace)
        return namespace['outputs']

class FineTuneNode:
    """Fine-tune LLM"""
    inputs = ['data', 'model']
    outputs = ['trained_model']
    config_schema = {
        'learning_rate': float,
        'num_epochs': int,
        'batch_size': int,
        'lora': bool,
        'gradient_checkpointing': bool
    }
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        # Fine-tune model on data
        trainer = Trainer(...)
        trained_model = await trainer.train(inputs['data'], config)
        return {'trained_model': trained_model}

class InferenceNode:
    """Run inference"""
    inputs = ['model', 'input_data']
    outputs = ['predictions']
    config_schema = {
        'batch_size': int,
        'device': Enum['cuda', 'cpu']
    }
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        predictions = await self._infer(inputs['model'], inputs['input_data'])
        return {'predictions': predictions}

class TransformNode:
    """Data transformation"""
    inputs = ['data']
    outputs = ['transformed_data']
    config_schema = {
        'operation': Enum['normalize', 'augment', 'filter', 'aggregate'],
        'params': Dict
    }

class ParallelNode:
    """Execute multiple nodes in parallel"""
    inputs = ['*']
    outputs = ['*']
    config_schema = {
        'nodes': List[str]  # Node IDs to run in parallel
    }
    
    async def execute(self, inputs: Dict, config: Dict) -> Dict:
        # Fanout execution to multiple nodes
        pass

class LoopNode:
    """Iterate over data"""
    inputs = ['items', 'operation_node']
    outputs = ['results']
    config_schema = {
        'iterate_over': str,  # 'items'
        'apply_node': str,
        'parallel': bool
    }
```

### Output Nodes

```python
class SaveToStorageNode:
    """Save output to S3/storage"""
    inputs = ['data']
    outputs = []
    config_schema = {
        'storage_path': str,
        'format': str,
        'compression': Optional[str]
    }

class DeployInferenceNode:
    """Deploy model as inference endpoint"""
    inputs = ['model']
    outputs = ['endpoint_url']
    config_schema = {
        'framework': Enum['vllm', 'triton', 'fastapi'],
        'replicas': int,
        'enable_autoscaling': bool
    }

class NotifyNode:
    """Send notification"""
    inputs = ['message']
    outputs = []
    config_schema = {
        'channel': Enum['email', 'slack', 'webhook'],
        'recipient': str
    }

class VisualizationNode:
    """Display results"""
    inputs = ['data']
    outputs = []
    config_schema = {
        'chart_type': Enum['scatter', 'line', 'histogram', 'heatmap'],
        'title': str
    }
```

## Execution Engine

### Workflow DAG

```python
# lib/workflow_dag.py
class WorkflowDAG:
    """Directed Acyclic Graph for workflows"""
    
    def __init__(self, definition: Dict):
        self.nodes = {n['id']: n for n in definition['nodes']}
        self.edges = definition['edges']
        self._validate()
    
    def _validate(self):
        """Validate DAG for cycles and correctness"""
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for edge in self.edges:
                if edge['from'] == node_id:
                    neighbor = edge['to']
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    raise ValueError("Workflow contains cycle")
    
    def topological_sort(self) -> List[str]:
        """Return node IDs in execution order"""
        visited = set()
        stack = []
        
        def dfs(node_id):
            visited.add(node_id)
            
            for edge in self.edges:
                if edge['from'] == node_id:
                    neighbor = edge['to']
                    if neighbor not in visited:
                        dfs(neighbor)
            
            stack.append(node_id)
        
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)
        
        return stack[::-1]
    
    def get_node_inputs(self, node_id: str) -> List[str]:
        """Get nodes that feed into this node"""
        return [e['from'] for e in self.edges if e['to'] == node_id]
    
    def get_node_outputs(self, node_id: str) -> List[str]:
        """Get nodes this node feeds into"""
        return [e['to'] for e in self.edges if e['from'] == node_id]
```

### Task Execution

```python
# services/workflow_executor.py
class WorkflowExecutor:
    """Executes workflow on GPU session"""
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        session: WorkspaceSession,
        input_overrides: Optional[Dict] = None
    ) -> WorkflowRun:
        """Execute workflow and track progress"""
        
        run = WorkflowRun(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            session_id=session.id,
            status='pending',
            created_at=datetime.utcnow()
        )
        
        # Queue execution task
        task = execute_workflow_task.delay(
            str(workflow.id),
            str(run.id),
            str(session.id),
            input_overrides or {}
        )
        
        run.celery_task_id = task.id
        db.session.add(run)
        await db.session.commit()
        
        return run
    
    async def execute_node(
        self,
        node: Dict,
        inputs: Dict,
        session: WorkspaceSession,
        run_id: str
    ) -> Any:
        """Execute single workflow node"""
        
        node_type = node['type']
        config = node.get('config', {})
        
        # Get appropriate handler
        handler = NODE_HANDLERS.get(node_type)
        if not handler:
            raise ValueError(f"Unknown node type: {node_type}")
        
        try:
            # Execute handler
            result = await handler.execute(inputs, config, session)
            
            # Emit progress
            await event_bus.publish(f"workflow.node_completed.{run_id}", {
                "node_id": node['id'],
                "result": result,
                "timestamp": datetime.utcnow()
            })
            
            return result
            
        except Exception as e:
            await event_bus.publish(f"workflow.node_failed.{run_id}", {
                "node_id": node['id'],
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            raise
```

### Celery Task

```python
# tasks/workflow_tasks.py
@celery_app.task(bind=True, max_retries=2)
def execute_workflow_task(
    self,
    workflow_id: str,
    run_id: str,
    session_id: str,
    input_overrides: Dict
):
    """Execute workflow in Celery worker"""
    
    try:
        # Load workflow and session
        workflow = db.session.query(Workflow).get(workflow_id)
        run = db.session.query(WorkflowRun).get(run_id)
        session = db.session.query(WorkspaceSession).get(session_id)
        
        if not all([workflow, run, session]):
            raise ValueError("Workflow/run/session not found")
        
        run.status = 'running'
        run.started_at = datetime.utcnow()
        db.session.commit()
        
        # Parse DAG
        dag = WorkflowDAG(workflow.definition)
        nodes_by_id = {n['id']: n for n in workflow.definition['nodes']}
        
        # Execute nodes in topological order
        node_results = {}
        
        for node_id in dag.topological_sort():
            node = nodes_by_id[node_id]
            
            # Gather inputs from previous nodes
            inputs = {}
            for input_node_id in dag.get_node_inputs(node_id):
                # Get outputs from that node
                inputs.update(node_results.get(input_node_id, {}))
            
            # Apply input overrides
            inputs.update(input_overrides.get(node_id, {}))
            
            # Execute node
            try:
                result = asyncio.run(
                    execute_node_in_session(node, inputs, session)
                )
                node_results[node_id] = result
            except Exception as e:
                logger.error(f"Node {node_id} failed: {e}")
                raise
        
        # Mark run as completed
        run.status = 'completed'
        run.completed_at = datetime.utcnow()
        run.result = node_results
        db.session.commit()
        
    except Exception as e:
        run.status = 'failed'
        run.error_message = str(e)
        run.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

## Workflow Scheduling

```python
# Scheduling via APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

class WorkflowScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
    
    def schedule_workflow(
        self,
        workflow_id: str,
        cron_expression: str,
        input_params: Dict
    ):
        """Schedule workflow to run on schedule"""
        
        def run_workflow():
            execute_workflow_task.delay(workflow_id, None, input_params)
        
        self.scheduler.add_job(
            run_workflow,
            'cron',
            **parse_cron(cron_expression),
            id=f'workflow-{workflow_id}'
        )
    
    def start(self):
        self.scheduler.start()
```

## Frontend Builder UI

### Canvas Rendering

```typescript
// components/Workflow/WorkflowCanvas.tsx
export function WorkflowCanvas({ workflowId }: { workflowId: string }) {
  const store = useWorkflowStore();
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Render nodes and edges
  const render = () => {
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    
    // Draw edges
    for (const edge of store.edges) {
      const fromNode = store.nodes.find(n => n.id === edge.from);
      const toNode = store.nodes.find(n => n.id === edge.to);
      
      ctx.beginPath();
      ctx.moveTo(fromNode.x + 150, fromNode.y + 50);
      ctx.lineTo(toNode.x, toNode.y);
      ctx.stroke();
    }
    
    // Draw nodes
    for (const node of store.nodes) {
      ctx.fillStyle = node.selected ? '#6366f1' : '#1e293b';
      ctx.fillRect(node.x, node.y, 150, 100);
      
      ctx.fillStyle = '#fff';
      ctx.fillText(node.label, node.x + 10, node.y + 50);
    }
  };
  
  // Handle interactions
  const handleMouseDown = (e: MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    const x = (e.clientX - rect!.left - pan.x) / zoom;
    const y = (e.clientY - rect!.top - pan.y) / zoom;
    
    // Check for node click
    for (const node of store.nodes) {
      if (x > node.x && x < node.x + 150 && y > node.y && y < node.y + 100) {
        store.selectNode(node.id);
        // Start dragging
      }
    }
  };
  
  useEffect(() => {
    const interval = setInterval(render, 16);
    return () => clearInterval(interval);
  }, [store.nodes, store.edges, zoom, pan]);
  
  return (
    <div className="workflow-builder">
      <canvas
        ref={canvasRef}
        width={1200}
        height={800}
        onMouseDown={handleMouseDown}
      />
      <NodePalette onNodeAdd={store.addNode} />
      <PropertiesPanel selectedNode={store.selectedNode} />
    </div>
  );
}
```

## API Endpoints

```
GET    /api/v1/workflows              - List workflows
POST   /api/v1/workflows              - Create workflow
GET    /api/v1/workflows/{id}         - Get workflow details
PUT    /api/v1/workflows/{id}         - Update workflow
POST   /api/v1/workflows/{id}/run     - Execute workflow
GET    /api/v1/workflows/{id}/runs    - List runs
GET    /api/v1/workflow-runs/{id}     - Get run status
```

## Next Steps

- Review [GPU Scheduler](GPU_SCHEDULER.md)
- See [Backend Architecture](../architecture/02-BACKEND_ARCHITECTURE.md)
