"""Health monitoring for PGSD database connections."""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any

from ..exceptions.database import DatabaseHealthError
from ..models.database import (
    PoolHealth,
)
from .connector import DatabaseConnector
from .pool import ConnectionPool


class HealthMonitor:
    """Health monitoring for database connections and pools."""

    def __init__(self, check_interval: int = 60):
        """Initialize health monitor.

        Args:
            check_interval: Health check interval in seconds
        """
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)

        # Health check history
        self._health_history: List[Dict[str, Any]] = []
        self._max_history_size = 100

        # Performance metrics
        self._metrics = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "average_response_time": 0.0,
            "last_check_time": None,
            "longest_response_time": 0.0,
            "shortest_response_time": float("inf"),
        }

    async def check_connection_health(
        self, connector: DatabaseConnector
    ) -> Dict[str, Any]:
        """Check health of a single connection.

        Args:
            connector: Database connector to check

        Returns:
            Dictionary with health check results
        """
        start_time = time.time()

        health_result = {
            "connection_id": connector.connection_id,
            "timestamp": datetime.utcnow().isoformat(),
            "is_healthy": False,
            "response_time_ms": 0,
            "checks": {
                "connection_test": False,
                "version_check": False,
                "permissions_check": False,
                "query_test": False,
            },
            "errors": [],
            "warnings": [],
        }

        try:
            # 1. Basic connection test
            try:
                health_result["checks"][
                    "connection_test"
                ] = await connector.test_connection()
                if not health_result["checks"]["connection_test"]:
                    health_result["errors"].append("Connection test failed")
            except Exception as e:
                health_result["errors"].append(f"Connection test error: {str(e)}")

            # 2. Version check
            try:
                version = await connector.get_version()
                health_result["checks"]["version_check"] = True
                health_result["version"] = str(version)

                # Check if version is supported
                from .version import VersionManager

                version_manager = VersionManager()
                if not version_manager.is_version_supported(version):
                    health_result["warnings"].append(
                        f"PostgreSQL version {version} may not be fully supported"
                    )
            except Exception as e:
                health_result["errors"].append(f"Version check error: {str(e)}")

            # 3. Permissions check
            try:
                permissions = await connector.check_permissions()
                health_result["checks"][
                    "permissions_check"
                ] = permissions.has_required_permissions()

                if not permissions.has_required_permissions():
                    missing = permissions.get_missing_permissions()
                    health_result["errors"].append(
                        f"Missing permissions: {', '.join(missing)}"
                    )

                health_result["accessible_schemas"] = len(
                    permissions.accessible_schemas
                )

            except Exception as e:
                health_result["errors"].append(f"Permissions check error: {str(e)}")

            # 4. Query test
            try:
                result = await connector.execute_query("SELECT 1 as test")
                health_result["checks"]["query_test"] = (
                    len(result) > 0 and result[0].get("test") == 1
                )

                if not health_result["checks"]["query_test"]:
                    health_result["errors"].append("Query test failed")
            except Exception as e:
                health_result["errors"].append(f"Query test error: {str(e)}")

            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            health_result["response_time_ms"] = round(response_time, 2)

            # Determine overall health
            required_checks = ["connection_test", "query_test"]
            health_result["is_healthy"] = all(
                health_result["checks"][check] for check in required_checks
            )

            # Performance warnings
            if response_time > 5000:  # 5 seconds
                health_result["warnings"].append(
                    f"Slow response time: {response_time:.2f}ms"
                )

            # Update metrics
            self._update_metrics(response_time, health_result["is_healthy"])

            # Log health check result
            log_level = logging.INFO if health_result["is_healthy"] else logging.WARNING
            self.logger.log(
                log_level,
                "Connection health check completed",
                extra={
                    "connection_id": connector.connection_id,
                    "is_healthy": health_result["is_healthy"],
                    "response_time_ms": health_result["response_time_ms"],
                    "error_count": len(health_result["errors"]),
                    "warning_count": len(health_result["warnings"]),
                },
            )

        except Exception as e:
            health_result["errors"].append(f"Health check failed: {str(e)}")
            health_result["is_healthy"] = False

            self.logger.error(
                "Health check failed",
                extra={"connection_id": connector.connection_id, "error": str(e)},
            )

        # Add to history
        self._add_to_history(health_result)

        return health_result

    async def check_pool_health(self, pool: ConnectionPool) -> PoolHealth:
        """Check health of connection pool.

        Args:
            pool: Connection pool to check

        Returns:
            Pool health information
        """
        try:
            # Get basic pool health
            pool_health = pool.health_check()

            # Add additional checks
            start_time = time.time()

            # Test getting and returning connection
            try:
                test_connector = pool.get_connection(timeout=5)
                test_result = await test_connector.test_connection()
                pool.return_connection(test_connector)

                connection_test_time = (time.time() - start_time) * 1000

                self.logger.debug(
                    "Pool connection test completed",
                    extra={
                        "test_passed": test_result,
                        "test_time_ms": connection_test_time,
                    },
                )

            except Exception as e:
                self.logger.warning(
                    "Pool connection test failed", extra={"error": str(e)}
                )

            return pool_health

        except Exception as e:
            self.logger.error("Pool health check failed", extra={"error": str(e)})
            raise DatabaseHealthError(
                f"Pool health check failed: {str(e)}", original_error=e
            )

    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of health check results.

        Returns:
            Dictionary with health summary
        """
        if not self._health_history:
            return {
                "total_checks": 0,
                "healthy_percentage": 0.0,
                "average_response_time": 0.0,
                "recent_errors": [],
                "trends": {},
            }

        # Calculate statistics from recent history
        recent_checks = self._health_history[-50:]  # Last 50 checks

        healthy_count = sum(1 for check in recent_checks if check["is_healthy"])
        total_checks = len(recent_checks)

        avg_response_time = (
            sum(check["response_time_ms"] for check in recent_checks) / total_checks
            if total_checks > 0
            else 0.0
        )

        # Get recent errors
        recent_errors = []
        for check in recent_checks[-10:]:  # Last 10 checks
            if check["errors"]:
                recent_errors.extend(check["errors"])

        # Calculate trends
        trends = self._calculate_trends(recent_checks)

        return {
            "total_checks": self._metrics["total_checks"],
            "successful_checks": self._metrics["successful_checks"],
            "failed_checks": self._metrics["failed_checks"],
            "healthy_percentage": (
                (healthy_count / total_checks) * 100 if total_checks > 0 else 0.0
            ),
            "average_response_time": round(avg_response_time, 2),
            "longest_response_time": self._metrics["longest_response_time"],
            "shortest_response_time": (
                self._metrics["shortest_response_time"]
                if self._metrics["shortest_response_time"] != float("inf")
                else 0.0
            ),
            "last_check_time": self._metrics["last_check_time"],
            "recent_errors": recent_errors[-5:],  # Last 5 errors
            "trends": trends,
        }

    def _update_metrics(self, response_time: float, is_healthy: bool):
        """Update health metrics.

        Args:
            response_time: Response time in milliseconds
            is_healthy: Whether the check was successful
        """
        self._metrics["total_checks"] += 1
        self._metrics["last_check_time"] = datetime.utcnow().isoformat()

        if is_healthy:
            self._metrics["successful_checks"] += 1
        else:
            self._metrics["failed_checks"] += 1

        # Update response time metrics
        if response_time > self._metrics["longest_response_time"]:
            self._metrics["longest_response_time"] = response_time

        if response_time < self._metrics["shortest_response_time"]:
            self._metrics["shortest_response_time"] = response_time

        # Calculate moving average
        total_time = self._metrics["average_response_time"] * (
            self._metrics["total_checks"] - 1
        )
        self._metrics["average_response_time"] = (
            total_time + response_time
        ) / self._metrics["total_checks"]

    def _add_to_history(self, health_result: Dict[str, Any]):
        """Add health check result to history.

        Args:
            health_result: Health check result to add
        """
        self._health_history.append(health_result)

        # Trim history if it gets too large
        if len(self._health_history) > self._max_history_size:
            self._health_history = self._health_history[-self._max_history_size :]

    def _calculate_trends(self, recent_checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate health trends from recent checks.

        Args:
            recent_checks: List of recent health check results

        Returns:
            Dictionary with trend information
        """
        if len(recent_checks) < 2:
            return {}

        # Calculate response time trend
        response_times = [check["response_time_ms"] for check in recent_checks]

        # Simple linear trend calculation
        mid_point = len(response_times) // 2
        first_half_avg = (
            sum(response_times[:mid_point]) / mid_point if mid_point > 0 else 0
        )
        second_half_avg = sum(response_times[mid_point:]) / (
            len(response_times) - mid_point
        )

        response_time_trend = (
            "improving"
            if second_half_avg < first_half_avg
            else "degrading" if second_half_avg > first_half_avg else "stable"
        )

        # Calculate health trend
        health_statuses = [check["is_healthy"] for check in recent_checks]

        first_half_healthy = (
            sum(health_statuses[:mid_point]) / mid_point if mid_point > 0 else 0
        )
        second_half_healthy = sum(health_statuses[mid_point:]) / (
            len(health_statuses) - mid_point
        )

        health_trend = (
            "improving"
            if second_half_healthy > first_half_healthy
            else "degrading" if second_half_healthy < first_half_healthy else "stable"
        )

        return {
            "response_time_trend": response_time_trend,
            "health_trend": health_trend,
            "response_time_change": round(second_half_avg - first_half_avg, 2),
            "health_rate_change": round(
                (second_half_healthy - first_half_healthy) * 100, 2
            ),
        }

    def get_health_alerts(self) -> List[Dict[str, Any]]:
        """Get health alerts based on recent checks.

        Returns:
            List of health alerts
        """
        alerts = []

        if not self._health_history:
            return alerts

        recent_checks = self._health_history[-10:]  # Last 10 checks

        # Check for consecutive failures
        consecutive_failures = 0
        for check in reversed(recent_checks):
            if not check["is_healthy"]:
                consecutive_failures += 1
            else:
                break

        if consecutive_failures >= 3:
            alerts.append(
                {
                    "type": "consecutive_failures",
                    "severity": "high",
                    "message": f"Connection has failed {consecutive_failures} consecutive health checks",
                    "count": consecutive_failures,
                }
            )

        # Check for slow response times
        recent_response_times = [check["response_time_ms"] for check in recent_checks]
        avg_response_time = sum(recent_response_times) / len(recent_response_times)

        if avg_response_time > 2000:  # 2 seconds
            alerts.append(
                {
                    "type": "slow_response",
                    "severity": "medium",
                    "message": f"Average response time is high: {avg_response_time:.2f}ms",
                    "avg_response_time": avg_response_time,
                }
            )

        # Check for error patterns
        error_counts = {}
        for check in recent_checks:
            for error in check["errors"]:
                error_type = error.split(":")[0]  # Get error type
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

        for error_type, count in error_counts.items():
            if count >= 3:
                alerts.append(
                    {
                        "type": "recurring_error",
                        "severity": "medium",
                        "message": f"Recurring error: {error_type} (occurred {count} times)",
                        "error_type": error_type,
                        "count": count,
                    }
                )

        return alerts

    def clear_history(self):
        """Clear health check history."""
        self._health_history.clear()
        self._metrics = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "average_response_time": 0.0,
            "last_check_time": None,
            "longest_response_time": 0.0,
            "shortest_response_time": float("inf"),
        }

        self.logger.info("Health check history cleared")

    def export_health_data(self) -> Dict[str, Any]:
        """Export health data for analysis.

        Returns:
            Dictionary with all health data
        """
        return {
            "metrics": self._metrics.copy(),
            "history": self._health_history.copy(),
            "summary": self.get_health_summary(),
            "alerts": self.get_health_alerts(),
            "export_time": datetime.utcnow().isoformat(),
        }
