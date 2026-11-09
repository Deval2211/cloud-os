"""
GPU Scheduler - Multi-objective GPU allocation and optimization
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import asyncio

from provider_sdk import provider_manager, GPU

logger = logging.getLogger(__name__)


@dataclass
class GPURequirements:
    """GPU requirements for a session"""
    min_vram_gb: int = 8
    min_cuda_version: str = "11.0"
    gpu_model: Optional[str] = None
    quantity: int = 1
    
    # Preferences
    preferred_providers: List[str] = field(default_factory=lambda: ["runpod", "local_docker"])
    preferred_regions: List[str] = field(default_factory=list)


@dataclass
class GPUConstraints:
    """Constraints for GPU allocation"""
    max_hourly_cost_usd: float = 100.0
    max_latency_ms: int = 500
    required_gpu_models: List[str] = field(default_factory=list)
    exclude_providers: List[str] = field(default_factory=list)
    required_regions: List[str] = field(default_factory=list)


@dataclass
class AllocationScore:
    """Scoring for GPU allocation"""
    gpu: GPU
    provider: str
    total_score: float
    cost_score: float
    performance_score: float
    latency_score: float
    availability_score: float


class GPUScheduler:
    """Multi-objective GPU allocation scheduler"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def allocate_gpu(
        self,
        requirements: GPURequirements,
        constraints: GPUConstraints,
    ) -> tuple[Optional[GPU], str]:
        """
        Find and allocate best GPU matching requirements and constraints.
        
        Returns:
            Tuple of (GPU, provider_name) or (None, None) if no match found
        """
        try:
            # Discover all available GPUs
            all_gpus = await provider_manager.discover_all_gpus({
                "model": requirements.gpu_model,
                "min_vram_gb": requirements.min_vram_gb,
            })
            
            if not all_gpus:
                self.logger.warning("No GPUs available matching requirements")
                return None, None
            
            # Score each GPU
            scores: List[AllocationScore] = []
            
            for gpu in all_gpus:
                # Check constraints
                if not self._meets_constraints(gpu, constraints):
                    continue
                
                # Get provider for this GPU
                provider = gpu.provider
                
                # Score this GPU
                score = await self._score_gpu(gpu, provider, requirements, constraints)
                scores.append(score)
            
            if not scores:
                self.logger.warning("No GPUs meet constraints")
                return None, None
            
            # Sort by score (highest first)
            scores.sort(key=lambda s: s.total_score, reverse=True)
            best = scores[0]
            
            self.logger.info(
                f"Selected GPU {best.gpu.model} on {best.provider} "
                f"with score {best.total_score:.2f}"
            )
            
            return best.gpu, best.provider
        
        except Exception as e:
            self.logger.error(f"GPU allocation failed: {e}")
            return None, None
    
    def _meets_constraints(self, gpu: GPU, constraints: GPUConstraints) -> bool:
        """Check if GPU meets all constraints"""
        
        # Cost constraint
        hourly_cost = gpu.hourly_cost_cents / 100.0
        if hourly_cost > constraints.max_hourly_cost_usd:
            return False
        
        # Provider constraint
        if gpu.provider in constraints.exclude_providers:
            return False
        
        # GPU model constraint
        if constraints.required_gpu_models and gpu.model not in constraints.required_gpu_models:
            return False
        
        # Region constraint
        if constraints.required_regions and gpu.region not in constraints.required_regions:
            return False
        
        return True
    
    async def _score_gpu(
        self,
        gpu: GPU,
        provider: str,
        requirements: GPURequirements,
        constraints: GPUConstraints,
    ) -> AllocationScore:
        """Score a GPU based on multi-objective criteria"""
        
        # Cost score (lower is better, normalize to 0-1)
        hourly_cost = gpu.hourly_cost_cents / 100.0
        cost_ratio = hourly_cost / max(constraints.max_hourly_cost_usd, 0.01)
        cost_score = max(0, 1 - cost_ratio)
        
        # Performance score (VRAM and compute capability)
        perf_base = min(gpu.vram_gb / 80.0, 1.0)  # Normalize to 80GB max
        cuda_cap_score = float(gpu.cuda_capability.replace(".", "")) / 90.0  # Normalize
        performance_score = (perf_base + cuda_cap_score) / 2.0
        
        # Availability score (inversely proportional to utilization)
        availability_score = 1.0 - gpu.utilization
        
        # Latency score (default to good, would use ping in production)
        latency_score = 0.95
        if gpu.region:
            # Would use actual latency measurement here
            latency_score = 0.9
        
        # Weight scores
        weights = {
            "cost": 0.3,
            "performance": 0.3,
            "availability": 0.2,
            "latency": 0.2,
        }
        
        total_score = (
            weights["cost"] * cost_score +
            weights["performance"] * performance_score +
            weights["availability"] * availability_score +
            weights["latency"] * latency_score
        )
        
        return AllocationScore(
            gpu=gpu,
            provider=provider,
            total_score=total_score,
            cost_score=cost_score,
            performance_score=performance_score,
            latency_score=latency_score,
            availability_score=availability_score,
        )
    
    async def get_allocations_for_comparison(
        self,
        requirements: GPURequirements,
        constraints: GPUConstraints,
        top_n: int = 3,
    ) -> List[AllocationScore]:
        """Get top N GPU allocation options for user selection"""
        try:
            # Discover GPUs
            all_gpus = await provider_manager.discover_all_gpus({
                "model": requirements.gpu_model,
                "min_vram_gb": requirements.min_vram_gb,
            })
            
            # Score and filter
            scores: List[AllocationScore] = []
            for gpu in all_gpus:
                if not self._meets_constraints(gpu, constraints):
                    continue
                
                score = await self._score_gpu(
                    gpu,
                    gpu.provider,
                    requirements,
                    constraints
                )
                scores.append(score)
            
            # Sort and return top N
            scores.sort(key=lambda s: s.total_score, reverse=True)
            return scores[:top_n]
        
        except Exception as e:
            self.logger.error(f"Failed to get allocations: {e}")
            return []
