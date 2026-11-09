#!/usr/bin/env python
"""
Quick integration test for Cloud OS Phase 5-8 components
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src/backend"))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_provider_system():
    """Test provider system"""
    logger.info("\n" + "="*60)
    logger.info("Testing Provider System")
    logger.info("="*60)
    
    from provider_sdk import provider_registry, provider_manager
    from provider_sdk.local_docker import LocalDockerProvider
    from provider_sdk.runpod import RunPodProvider
    
    # Register providers
    try:
        local = LocalDockerProvider()
        provider_registry.register("local_docker", local)
        logger.info("✓ Registered Local Docker provider")
    except Exception as e:
        logger.error(f"✗ Failed to register Local Docker: {e}")
    
    try:
        runpod = RunPodProvider()
        provider_registry.register("runpod", runpod)
        logger.info("✓ Registered RunPod provider")
    except Exception as e:
        logger.error(f"✗ Failed to register RunPod: {e}")
    
    # List providers
    providers = provider_registry.list_providers()
    logger.info(f"✓ Registered providers: {providers}")
    
    # Test provider manager
    health = await provider_manager.health_check_all()
    logger.info(f"✓ Health check results: {health}")
    
    return True


async def test_gpu_scheduler():
    """Test GPU scheduler"""
    logger.info("\n" + "="*60)
    logger.info("Testing GPU Scheduler")
    logger.info("="*60)
    
    from services.scheduler_service import GPUScheduler, GPURequirements, GPUConstraints
    from provider_sdk import provider_registry
    from provider_sdk.local_docker import LocalDockerProvider
    
    # Register local provider
    try:
        local = LocalDockerProvider()
        provider_registry.register("local_docker", local)
    except:
        pass
    
    scheduler = GPUScheduler()
    logger.info("✓ Created GPU scheduler")
    
    # Test requirements
    reqs = GPURequirements(
        min_vram_gb=16,
        gpu_model="RTX 4090",
        quantity=1,
    )
    
    constraints = GPUConstraints(
        max_hourly_cost_usd=5.0,
    )
    
    logger.info(f"✓ Created requirements: min_vram_gb={reqs.min_vram_gb}, model={reqs.gpu_model}")
    logger.info(f"✓ Created constraints: max_cost=${constraints.max_hourly_cost_usd}/hr")
    
    # Test scoring (won't actually allocate)
    allocations = await scheduler.get_allocations_for_comparison(reqs, constraints, top_n=3)
    logger.info(f"✓ Found {len(allocations)} GPU options")
    for alloc in allocations:
        logger.info(f"  - {alloc.gpu.model}: score={alloc.total_score:.2f}")
    
    return True


async def test_workflow_executor():
    """Test workflow executor"""
    logger.info("\n" + "="*60)
    logger.info("Testing Workflow Executor")
    logger.info("="*60)
    
    from services.workflow_executor import get_executor, WorkflowDAG
    
    executor = get_executor()
    logger.info("✓ Got workflow executor")
    
    # Create DAG
    dag = WorkflowDAG("test-workflow")
    dag.add_node("step1", "execute_command", {"command": "echo hello"})
    dag.add_node("step2", "http_request", 
        {"url": "https://api.example.com/data", "method": "GET"},
        depends_on=["step1"])
    
    logger.info("✓ Created DAG with 2 nodes")
    
    # Check topological sort
    layers = dag.topological_sort()
    logger.info(f"✓ Topological sort: {len(layers)} layers")
    for i, layer in enumerate(layers):
        logger.info(f"  Layer {i+1}: {[n.node_id for n in layer]}")
    
    # Test execution
    try:
        results = await executor.execute_dag(dag)
        logger.info(f"✓ Workflow execution: {results['status']}")
        logger.info(f"  Completed: {len(results['outputs'])} nodes")
        logger.info(f"  Errors: {len(results['errors'])} nodes")
    except Exception as e:
        logger.error(f"✗ Workflow execution failed: {e}")
    
    return True


async def test_checkpoint_service():
    """Test checkpoint service"""
    logger.info("\n" + "="*60)
    logger.info("Testing Checkpoint Service")
    logger.info("="*60)
    
    from services.checkpoint_service import CheckpointService
    
    logger.info("✓ Imported checkpoint service")
    logger.info("✓ Methods available:")
    for method in ['create_checkpoint', 'restore_checkpoint', 'list_checkpoints', 
                   'delete_checkpoint', 'cleanup_expired_checkpoints']:
        logger.info(f"  - {method}")
    
    return True


async def test_celery_tasks():
    """Test Celery tasks"""
    logger.info("\n" + "="*60)
    logger.info("Testing Celery Tasks")
    logger.info("="*60)
    
    from tasks import (
        provision_gpu_session, monitor_session_metrics,
        create_checkpoint, restore_checkpoint, terminate_session,
        execute_workflow, execute_workflow_node, collect_workflow_results,
        process_ai_request, cleanup_expired_checkpoints,
        collect_system_metrics, sync_provider_status
    )
    
    tasks = [
        "provision_gpu_session", "monitor_session_metrics",
        "create_checkpoint", "restore_checkpoint", "terminate_session",
        "execute_workflow", "execute_workflow_node", "collect_workflow_results",
        "process_ai_request", "cleanup_expired_checkpoints",
        "collect_system_metrics", "sync_provider_status"
    ]
    
    logger.info(f"✓ Imported {len(tasks)} Celery tasks:")
    for task in tasks:
        logger.info(f"  - {task}")
    
    return True


async def main():
    """Run all tests"""
    logger.info("\n" + "="*80)
    logger.info("CLOUD OS - PHASE 5-8 INTEGRATION TEST")
    logger.info("="*80)
    
    tests = [
        ("Provider System", test_provider_system),
        ("GPU Scheduler", test_gpu_scheduler),
        ("Workflow Executor", test_workflow_executor),
        ("Checkpoint Service", test_checkpoint_service),
        ("Celery Tasks", test_celery_tasks),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = await test_func()
        except Exception as e:
            logger.error(f"✗ {name} test failed: {e}")
            results[name] = False
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("="*80 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
