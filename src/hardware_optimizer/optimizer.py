"""
Hardware Optimizer for adjusting system parameters based on detected hardware
"""

import logging
from typing import Dict, Any, Optional
from .hardware_detector import hardware_detector

logger = logging.getLogger(__name__)


class HardwareOptimizer:
    """Optimizes system settings based on detected hardware"""

    def __init__(self):
        self.detector = hardware_detector
        self._optimization_cache: Dict[str, Any] = {}

    def get_system_profile(self) -> Dict[str, Any]:
        """
        Get a comprehensive system profile

        Returns:
            Dictionary with hardware info and optimization recommendations
        """
        # Use cached value if available and recent (within 5 minutes)
        cache_key = "system_profile"
        if cache_key in self._optimization_cache:
            cached_time, cached_data = self._optimization_cache[cache_key]
            if (time.time() - cached_time) < 300:  # 5 minutes
                return cached_data

        profile = {
            "hardware": self.detector.get_summary(),
            "recommendations": self.detector.get_optimization_recommendations(),
            "constraints": self._get_system_constraints(),
            "optimization_level": self._determine_optimization_level()
        }

        # Cache the result
        self._optimization_cache[cache_key] = (time.time(), profile)
        return profile

    def _get_system_constraints(self) -> Dict[str, Any]:
        """Identify system constraints that might affect performance"""
        constraints = []

        if self.detector.is_low_memory_system():
            constraints.append("low_memory")

        if self.detector.is_low_storage_system():
            constraints.append("low_storage")

        if not self.detector.is_gpu_available():
            constraints.append("no_gpu")

        # Check for thermal throttling (simplified)
        # In a real implementation, we'd check actual temperatures
        # if hasattr(psutil, "sensors_temperatures"):
        #     temps = psutil.sensors_temperatures()
        #     if temps:
        #         for name, entries in temps.items():
        #             for entry in entries:
        #                 if entry.current > 80:  # Arbitrary threshold
        #                     constraints.append("thermal_throttling")
        #                     break

        return {
            "identified": constraints,
            "severity": "high" if len(constraints) > 2 else "medium" if len(constraints) > 0 else "low"
        }

    def _determine_optimization_level(self) -> str:
        """Determine how aggressively to optimize based on hardware"""
        # Start with baseline
        level = "moderate"

        # Increase aggressiveness for high-end systems
        if not self.detector.is_low_memory_system(8.0) and self.detector.is_gpu_available():
            vram_gb = self.detector.get_total_vram() / 1024
            if vram_gb >= 8:
                level = "aggressive"

        # Decrease aggressiveness for constrained systems
        if self.detector.is_low_memory_system(4.0) or self.detector.is_low_storage_system(10.0):
            level = "conservative"

        return level

    def get_optimal_batch_size(self, base_size: int = 32) -> int:
        """
        Get optimal batch size for processing

        Args:
            base_size: Base batch size to adjust

        Returns:
            Optimized batch size
        """
        recommendations = self.detector.get_optimization_recommendations()
        return recommendations["compute"]["recommended_batch_size"]

    def get_optimal_worker_count(self) -> int:
        """Get optimal number of worker processes/threads"""
        recommendations = self.detector.get_optimization_recommendations()
        return recommendations["compute"]["recommended_workers"]

    def get_optimal_cache_size_mb(self) -> int:
        """Get optimal cache size in megabytes"""
        recommendations = self.detector.get_optimization_recommendations()
        return recommendations["memory"]["max_cache_size_mb"]

    def should_use_gpu(self) -> bool:
        """Check if GPU should be used for computation"""
        recommendations = self.detector.get_optimization_recommendations()
        return recommendations["compute"]["use_gpu"]

    def get_memory_optimization_flags(self) -> Dict[str, bool]:
        """Get memory-related optimization flags"""
        recommendations = self.detector.get_optimization_recommendations()
        return {
            "use_memory_mapping": recommendations["memory"]["use_memory_mapping"],
            "prefer_memory_views": not self.detector.is_low_memory_system(2.0),
            "garbage_collection_aggressive": self.detector.is_low_memory_system(4.0)
        }

    def get_io_optimization_flags(self) -> Dict[str, bool]:
        """Get I/O-related optimization flags"""
        recommendations = self.detector.get_optimization_recommendations()
        return {
            "use_async_io": True,  # Generally beneficial
            "buffer_size": min(65536, max(4096, self.detector.get_available_vram() * 1024)),
            "prefer_temp_files": recommendations["storage"]["prefer_temp_files"]
        }

    def apply_optimizations_to_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply hardware-based optimizations to a configuration dictionary

        Args:
            config: Configuration dictionary to optimize

        Returns:
            Optimized configuration dictionary
        """
        optimized = config.copy()
        profile = self.get_system_profile()

        # Apply batch size optimization
        if "batch_size" in optimized:
            # Only override if not explicitly set to a high value
            if optimized["batch_size"] < self.get_optimal_batch_size():
                optimized["batch_size"] = self.get_optimal_batch_size()
        else:
            optimized["batch_size"] = self.get_optimal_batch_size()

        # Apply worker count optimization
        if "num_workers" in optimized:
            optimal_workers = self.get_optimal_worker_count()
            if optimized["num_workers"] > optimal_workers * 1.5:  # Don't reduce too much
                optimized["num_workers"] = optimal_workers
        elif "num_workers" not in optimized:
            optimized["num_workers"] = self.get_optimal_worker_count()

        # Apply cache size optimization
        if "cache_size_mb" in optimized:
            optimal_cache = self.get_optimal_cache_size_mb()
            if optimized["cache_size_mb"] > optimal_cache * 1.5:
                optimized["cache_size_mb"] = optimal_cache
        elif "cache_size_mb" not in optimized:
            optimized["cache_size_mb"] = self.get_optimal_cache_size_mb()

        # Apply GPU usage
        if "use_gpu" in optimized:
            # Only disable GPU if explicitly set to False and we have one
            if optimized["use_gpu"] is False and not self.should_use_gpu():
                pass  # Keep as False
            elif optimized["use_gpu"] is True and not self.should_use_gpu():
                optimized["use_gpu"] = False  # Override incorrect setting
        else:
            optimized["use_gpu"] = self.should_use_gpu()

        # Apply memory optimization flags
        mem_opts = self.get_memory_optimization_flags()
        for key, value in mem_opts.items():
            if key not in optimized:
                optimized[key] = value

        # Apply I/O optimization flags
        io_opts = self.get_io_optimization_flags()
        for key, value in io_opts.items():
            if key not in optimized:
                optimized[key] = value

        # Add hardware info to config for reference
        optimized["_hardware_profile"] = {
            "cpu_cores": self.detector.system_info["cpu_count_logical"],
            "memory_gb": round(self.detector.system_info["memory_total"] / (1024**3), 1),
            "gpu_count": len(self.detector.system_info["gpu_info"]),
            "optimization_level": profile["optimization_level"]
        }

        return optimized

    def clear_cache(self):
        """Clear the optimization cache"""
        self._optimization_cache.clear()
        logger.info("Cleared hardware optimization cache")


# Global optimizer instance
hardware_optimizer = HardwareOptimizer()