"""
Hardware Detection for system optimization
"""

import platform
import psutil
import subprocess
import json
import re
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class HardwareDetector:
    """Detects system hardware capabilities"""

    def __init__(self):
        self.system_info = self._gather_system_info()

    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather comprehensive system information"""
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": self._get_disk_usage(),
            "gpu_info": self._get_gpu_info(),
            "battery": self._get_battery_info() if hasattr(psutil, "sensors_battery") else None,
            "boot_time": psutil.boot_time()
        }
        return info

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        disk_usage = psutil.disk_usage('/')
        return {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "percentage": (disk_usage.used / disk_usage.total) * 100
        }

    def _get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get GPU information"""
        gpus = []

        # Try to get GPU info using various methods
        try:
            # For NVIDIA GPUs using nvidia-smi
            if self._is_linux() or self._is_windows():
                try:
                    output = subprocess.check_output(
                        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used",
                         "--format=csv,noheader,nounits"],
                        stderr=subprocess.DEVNULL,
                        universal_newlines=True
                    )
                    for line in output.strip().split('\n'):
                        if line:
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 4:
                                gpus.append({
                                    "vendor": "NVIDIA",
                                    "name": parts[0],
                                    "driver_version": parts[1],
                                    "memory_total_mb": int(parts[2]),
                                    "memory_used_mb": int(parts[3]),
                                    "memory_free_mb": int(parts[2]) - int(parts[3])
                                })
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass

            # For AMD GPUs on Linux
            if self._is_linux():
                try:
                    output = subprocess.check_output(
                        ["rocm-smi", "--showproductname", "--showvram"],
                        stderr=subprocess.DEVNULL,
                        universal_newlines=True
                    )
                    # Parse ROCm output (simplified)
                    lines = output.strip().split('\n')
                    for line in lines:
                        if 'GPU' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                gpus.append({
                                    "vendor": "AMD",
                                    "name": parts[0].strip(),
                                    "vram_info": parts[1].strip()
                                })
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass

        except Exception as e:
            logger.debug(f"Error getting GPU info: {e}")

        # If we couldn't get specific GPU info, try to get basic info from OpenCL or similar
        if not gpus:
            # Try using PyOpenCL or similar if available
            # For now, we'll just note that we couldn't get detailed GPU info
            pass

        return gpus

    def _is_linux(self) -> bool:
        """Check if running on Linux"""
        return platform.system() == "Linux"

    def _is_windows(self) -> bool:
        """Check if running on Windows"""
        return platform.system() == "Windows"

    def _is_macos(self) -> bool:
        """Check if running on macOS"""
        return platform.system() == "Darwin"

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the hardware"""
        return {
            "cpu": {
                "physical_cores": self.system_info["cpu_count_physical"],
                "logical_cores": self.system_info["cpu_count_logical"],
                "architecture": self.system_info["architecture"]
            },
            "memory": {
                "total_gb": round(self.system_info["memory_total"] / (1024**3), 2),
                "available_gb": round(self.system_info["memory_available"] / (1024**3), 2)
            },
            "storage": {
                "total_gb": round(self.system_info["disk_usage"]["total"] / (1024**3), 2),
                "free_gb": round(self.system_info["disk_usage"]["free"] / (1024**3), 2),
                "usage_percent": self.system_info["disk_usage"]["percentage"]
            },
            "gpu": {
                "count": len(self.system_info["gpu_info"]),
                "details": self.system_info["gpu_info"]
            },
            "platform": {
                "system": self.system_info["platform"],
                "release": self.system_info["platform_release"],
                "version": self.system_info["platform_version"]
            }
        }

    def is_gpu_available(self) -> bool:
        """Check if any GPU is available"""
        return len(self.system_info["gpu_info"]) > 0

    def get_total_vram(self) -> int:
        """Get total VRAM across all GPUs in MB"""
        return sum(gpu.get("memory_total_mb", 0) for gpu in self.system_info["gpu_info"])

    def get_available_vram(self) -> int:
        """Get available VRAM across all GPUs in MB"""
        return sum(gpu.get("memory_free_mb", 0) for gpu in self.system_info["gpu_info"])

    def is_low_memory_system(self, threshold_gb: float = 4.0) -> bool:
        """Check if system has low memory"""
        total_gb = self.system_info["memory_total"] / (1024**3)
        return total_gb < threshold_gb

    def is_low_storage_system(self, threshold_gb: float = 20.0) -> bool:
        """Check if system has low storage"""
        free_gb = self.system_info["disk_usage"]["free"] / (1024**3)
        return free_gb < threshold_gb

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """
        Get optimization recommendations based on hardware

        Returns:
            Dictionary with recommendations for various subsystems
        """
        recommendations = {
            "compute": {
                "recommended_batch_size": self._recommend_batch_size(),
                "recommended_workers": self._recommend_worker_count(),
                "use_gpu": self.is_gpu_available()
            },
            "memory": {
                "use_memory_mapping": not self.is_low_memory_system(2.0),
                "max_cache_size_mb": self._recommend_cache_size()
            },
            "storage": {
                "use_ssd_optimizations": True,  # Assume SSD for now
                "prefer_temp_files": not self.is_low_storage_system(5.0)
            },
            "overall_performance": self._get_performance_tier()
        }
        return recommendations

    def _recommend_batch_size(self) -> int:
        """Recommend batch size based on available memory and GPU"""
        # Base batch size
        base_batch = 32

        # Adjust based on available memory
        available_gb = self.system_info["memory_available"] / (1024**3)
        if available_gb < 4:
            base_batch = max(4, base_batch // 4)
        elif available_gb < 8:
            base_batch = max(8, base_batch // 2)
        elif available_gb > 32:
            base_batch = min(512, base_batch * 2)

        # Adjust based on GPU VRAM if available
        if self.is_gpu_available():
            vram_gb = self.get_total_vram() / 1024  # Convert MB to GB
            if vram_gb < 4:
                base_batch = max(4, base_batch // 2)
            elif vram_gb > 12:
                base_batch = min(1024, base_batch * 2)

        return base_batch

    def _recommend_worker_count(self) -> int:
        """Recommend number of worker processes/threads"""
        # Don't exceed logical CPU cores
        max_workers = self.system_info["cpu_count_logical"]

        # Reduce if memory is limited
        available_gb = self.system_info["memory_available"] / (1024**3)
        if available_gb < 2:
            max_workers = max(1, max_workers // 4)
        elif available_gb < 4:
            max_workers = max(2, max_workers // 2)

        return max_workers

    def _recommend_cache_size(self) -> int:
        """Recommend cache size in MB"""
        # Use up to 25% of available memory, but cap at reasonable limits
        available_mb = self.system_info["memory_available"] / (1024**2)
        cache_size = min(2048, max(256, int(available_mb * 0.25)))
        return cache_size

    def _get_performance_tier(self) -> str:
        """Determine overall performance tier"""
        score = 0

        # CPU score (0-30 points)
        cpu_score = min(30, self.system_info["cpu_count_logical"] * 2)
        score += cpu_score

        # Memory score (0-30 points)
        memory_gb = self.system_info["memory_total"] / (1024**3)
        if memory_gb >= 32:
            memory_score = 30
        elif memory_gb >= 16:
            memory_score = 25
        elif memory_gb >= 8:
            memory_score = 20
        elif memory_gb >= 4:
            memory_score = 15
        elif memory_gb >= 2:
            memory_score = 10
        else:
            memory_score = 5
        score += memory_score

        # GPU score (0-20 points)
        if self.is_gpu_available():
            gpu_score = 20  # Simplified - could be more detailed based on GPU model/vram
            score += gpu_score
        else:
            score += 0  # No GPU points

        # Storage score (0-20 points) - based on available space
        free_gb = self.system_info["disk_usage"]["free"] / (1024**3)
        if free_gb >= 100:
            storage_score = 20
        elif free_gb >= 50:
            storage_score = 15
        elif free_gb >= 20:
            storage_score = 10
        elif free_gb >= 10:
            storage_score = 5
        else:
            storage_score = 0
        score += storage_score

        # Determine tier
        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"


# Global hardware detector instance
hardware_detector = HardwareDetector()