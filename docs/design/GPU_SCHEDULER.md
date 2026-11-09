# GPU Scheduler Design

**Document**: Intelligent GPU Allocation & Scheduling
**Version**: 1.0
**Status**: Design Phase

## Overview

The GPU Scheduler intelligently allocates GPU resources across multiple cloud providers and local nodes. It optimizes for:

- **Cost**: Minimize hourly GPU spending
- **Performance**: Select fastest GPUs
- **Availability**: Find available GPUs
- **Latency**: Minimize network latency
- **Failover**: Smart provider selection for recovery

## Scheduling Algorithm

### Multi-Objective Optimization

```python
# services/scheduler_service.py
class GPUScheduler:
    """Intelligent GPU scheduling"""
    
    # Weights for different optimization objectives
    WEIGHTS = {
        'cost': 0.3,
        'performance': 0.25,
        'availability': 0.25,
        'latency': 0.2
    }
    
    async def allocate_gpu(
        self,
        workspace: Workspace,
        requirements: GPURequirements,
        constraints: Optional[GPUConstraints] = None
    ) -> GPUAllocation:
        """
        Find and allocate optimal GPU.
        
        Args:
            workspace: Workspace requesting GPU
            requirements: GPU requirements (VRAM, compute capability, etc.)
            constraints: Optional constraints (budget, providers, regions)
        
        Returns:
            GPU allocation with provider info
        """
        
        # 1. Collect GPU inventory from all providers
        inventory = await self._collect_inventory()
        
        # 2. Filter by requirements and constraints
        candidates = self._filter_candidates(
            inventory,
            requirements,
            constraints
        )
        
        if not candidates:
            raise NoGPUAvailableError(
                f"No GPUs matching requirements: {requirements}"
            )
        
        # 3. Score each candidate
        scores = {
            gpu.id: self._score_gpu(gpu, requirements, workspace)
            for gpu in candidates
        }
        
        # 4. Select best
        best_id = max(scores, key=scores.get)
        best_gpu = next(g for g in candidates if g.id == best_id)
        
        # 5. Allocate and return
        allocation = GPUAllocation(
            gpu=best_gpu,
            provider=best_gpu.provider,
            timestamp=datetime.utcnow()
        )
        
        return allocation
    
    async def _collect_inventory(self) -> List[GPU]:
        """
        Collect GPU inventory from all providers.
        Uses caching and parallelization.
        """
        
        # Check cache first
        cached = await cache.get('gpu_inventory')
        if cached and (datetime.utcnow() - cached['updated_at']).seconds < 300:
            return cached['gpus']
        
        # Parallel queries to all providers
        providers = provider_manager.get_all_providers()
        
        tasks = [
            provider.get_available_gpus()
            for provider in providers
        ]
        
        # Execute with timeout per provider
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )
        
        # Collect results
        inventory = []
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                logger.error(f"Provider {provider.name} query failed: {result}")
                continue
            
            for gpu in result:
                gpu.provider = provider.name
                inventory.append(gpu)
        
        # Cache for 5 minutes
        await cache.set(
            'gpu_inventory',
            {
                'gpus': inventory,
                'updated_at': datetime.utcnow()
            },
            ttl=300
        )
        
        return inventory
    
    def _filter_candidates(
        self,
        inventory: List[GPU],
        requirements: GPURequirements,
        constraints: Optional[GPUConstraints]
    ) -> List[GPU]:
        """Filter GPUs by hard requirements"""
        
        candidates = []
        
        for gpu in inventory:
            # Hard requirements (must meet all)
            if gpu.vram_gb < requirements.min_vram_gb:
                continue
            
            if requirements.gpu_models and gpu.model not in requirements.gpu_models:
                continue
            
            if gpu.cuda_capability < requirements.min_cuda_capability:
                continue
            
            # Constraints (optional)
            if constraints:
                if constraints.max_hourly_cost:
                    hourly_cost = gpu.hourly_cost_cents / 100.0
                    if hourly_cost > constraints.max_hourly_cost:
                        continue
                
                if constraints.allowed_providers:
                    if gpu.provider not in constraints.allowed_providers:
                        continue
                
                if constraints.allowed_regions:
                    if gpu.region not in constraints.allowed_regions:
                        continue
            
            candidates.append(gpu)
        
        return candidates
    
    def _score_gpu(
        self,
        gpu: GPU,
        requirements: GPURequirements,
        workspace: Workspace
    ) -> float:
        """
        Score GPU suitability.
        
        Returns score 0-1 (higher = better)
        """
        
        score = 0.0
        
        # Factor 1: Cost (normalized, cheaper = higher score)
        # Assume average cost is $1/hour, range 0.25-5
        normalized_cost = gpu.hourly_cost_cents / 100.0
        cost_score = 1.0 / (1 + (normalized_cost / 1.0) ** 2)
        score += cost_score * self.WEIGHTS['cost']
        
        # Factor 2: Performance (compute capability)
        # Higher compute capability = higher score
        performance_score = gpu.cuda_capability / 10.0  # Max 9.0
        score += performance_score * self.WEIGHTS['performance']
        
        # Factor 3: Availability (inverse utilization)
        # Less utilized = higher score
        availability_score = 1.0 - gpu.utilization
        score += availability_score * self.WEIGHTS['availability']
        
        # Factor 4: Latency (inverse network latency)
        # Lower latency = higher score
        # Assume average latency 50ms, range 1-500ms
        latency_ms = gpu.latency_ms or 50
        latency_score = 1.0 / (1 + (latency_ms / 50.0))
        score += latency_score * self.WEIGHTS['latency']
        
        # Bonus: Match exact VRAM request (avoid over-provisioning)
        if abs(gpu.vram_gb - requirements.min_vram_gb) < 2:
            score *= 1.05
        
        # Penalty: Local Docker (only use if no cloud option)
        if gpu.provider == 'local_docker' and any(
            g.provider != 'local_docker' for g in inventory
        ):
            score *= 0.5
        
        return score
```

## Data Structures

```python
# schemas/gpu.py
from dataclasses import dataclass

@dataclass
class GPU:
    """GPU specification from provider"""
    id: str
    model: str
    vram_gb: int
    cuda_version: str
    cuda_capability: float  # 7.0, 8.0, 8.9, 9.0
    provider: str
    available: bool
    utilization: float  # 0.0-1.0
    temperature: Optional[int]
    power_usage_w: Optional[int]
    hourly_cost_cents: int
    region: Optional[str]
    latency_ms: Optional[int]  # Network latency from backend

@dataclass
class GPURequirements:
    """GPU requirements for workload"""
    min_vram_gb: int = 4
    gpu_models: Optional[List[str]] = None  # Specific models
    min_cuda_capability: float = 7.0
    prefer_multi_gpu: bool = False
    num_gpus: int = 1

@dataclass
class GPUConstraints:
    """Constraints on GPU selection"""
    max_hourly_cost: Optional[float] = None
    allowed_providers: Optional[List[str]] = None
    allowed_regions: Optional[List[str]] = None
    exclude_providers: Optional[List[str]] = None

@dataclass
class GPUAllocation:
    """Allocated GPU for session"""
    gpu: GPU
    provider: str
    session_id: Optional[str] = None
    allocated_at: datetime = None
    expires_at: Optional[datetime] = None
```

## Failover & Recovery

### Session Recovery Flow

```python
async def handle_gpu_failure(session_id: str):
    """Recover from GPU failure"""
    
    session = await db.get_session(session_id)
    workspace = session.workspace
    
    logger.warning(f"GPU session {session_id} failed on {session.provider}")
    
    # 1. Get latest checkpoint
    checkpoint = await checkpoint_service.get_latest(session_id)
    if not checkpoint:
        logger.error(f"No checkpoint for session {session_id}, cannot recover")
        session.status = 'failed'
        await db.save(session)
        return
    
    # 2. Select alternate provider
    requirements = GPURequirements(
        min_vram_gb=session.gpu.vram_gb,
        min_cuda_capability=session.gpu.cuda_capability
    )
    
    constraints = GPUConstraints(
        exclude_providers=[session.provider]  # Avoid same provider
    )
    
    try:
        allocation = await scheduler.allocate_gpu(
            workspace,
            requirements,
            constraints
        )
    except NoGPUAvailableError:
        # Fallback: use any provider
        allocation = await scheduler.allocate_gpu(workspace, requirements)
    
    # 3. Provision new session
    provider = provider_manager.get_provider(allocation.provider)
    
    try:
        new_session = await provider.restore_session(
            checkpoint_id=checkpoint.id,
            gpu=allocation.gpu
        )
    except Exception as e:
        logger.error(f"Recovery failed: {e}")
        session.status = 'recovery_failed'
        await db.save(session)
        return
    
    # 4. Update session record
    session.provider = allocation.provider
    session.provider_session_id = new_session.provider_session_id
    session.gpu_model = allocation.gpu.model
    session.vram_gb = allocation.gpu.vram_gb
    session.status = 'recovered'
    session.updated_at = datetime.utcnow()
    
    await db.save(session)
    
    logger.info(f"Session {session_id} recovered on {allocation.provider}")
```

## Cost Optimization

### Cost Tracking

```python
class CostTracker:
    """Track and optimize GPU costs"""
    
    async def estimate_workflow_cost(
        self,
        workflow: Workflow,
        session_config: SessionConfig
    ) -> float:
        """Estimate cost to run workflow"""
        
        # Get GPU requirements from workflow
        requirements = self._extract_requirements(workflow)
        
        # Allocate GPU (dry run)
        allocation = await scheduler.allocate_gpu(
            workspace,
            requirements
        )
        
        # Estimate execution time
        estimated_runtime_hours = self._estimate_runtime(workflow)
        
        # Calculate cost
        hourly_cost = allocation.gpu.hourly_cost_cents / 100.0
        total_cost = hourly_cost * estimated_runtime_hours
        
        return total_cost
    
    async def optimize_gpu_selection(
        self,
        workspace: Workspace,
        budget: float
    ) -> List[GPU]:
        """Find GPUs within budget"""
        
        inventory = await scheduler._collect_inventory()
        
        # Calculate time available at each GPU rate
        affordable_gpus = []
        
        for gpu in inventory:
            hourly_cost = gpu.hourly_cost_cents / 100.0
            if hourly_cost <= budget:
                affordable_gpus.append(gpu)
        
        # Sort by performance per dollar
        affordable_gpus.sort(
            key=lambda g: g.cuda_capability / (g.hourly_cost_cents / 100.0),
            reverse=True
        )
        
        return affordable_gpus
```

## Metrics & Monitoring

```python
# Monitor scheduler health
@app.get("/api/v1/scheduler/status")
async def get_scheduler_status():
    """Get scheduler metrics"""
    
    return {
        'gpu_inventory': {
            'total': len(await scheduler._collect_inventory()),
            'available': len([g for g in inventory if g.available]),
            'by_provider': aggregate_by_provider(inventory)
        },
        'active_allocations': await db.count_active_sessions(),
        'allocation_success_rate': await metrics.get_success_rate(),
        'average_allocation_time_ms': await metrics.get_avg_allocation_time(),
        'providers_status': {
            name: await provider.get_health_status()
            for name, provider in provider_manager.get_all_providers().items()
        }
    }
```

## Next Steps

- See [Session Persistence](SESSION_PERSISTENCE.md)
- Review [Backend Architecture](../architecture/02-BACKEND_ARCHITECTURE.md)
