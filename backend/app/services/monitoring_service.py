"""
Comprehensive monitoring service for the 3D Print Management System.
Provides metrics collection, health monitoring, and performance tracking.
"""

import time
import psutil
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class MonitoringService:
    """Comprehensive monitoring service for system health and performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history = []
        self.max_history_size = 1000  # Keep last 1000 metrics
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': time.time() - self.start_time,
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 2)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'process': {
                    'memory_mb': round(process_memory.rss / (1024**2), 2),
                    'cpu_percent': process_cpu,
                    'threads': process.num_threads(),
                    'open_files': len(process.open_files()),
                    'connections': len(process.connections())
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e)}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            from app import request_count, error_count, performance_metrics
            
            # Calculate error rate
            error_rate = (error_count / max(request_count, 1)) * 100
            
            # Get top slow endpoints
            slow_endpoints = []
            for path, metrics in performance_metrics.items():
                if metrics['count'] > 0:
                    slow_endpoints.append({
                        'path': path,
                        'count': metrics['count'],
                        'avg_duration_ms': round(metrics['avg_duration'] * 1000, 2),
                        'error_count': metrics['error_count'],
                        'error_rate': round((metrics['error_count'] / metrics['count']) * 100, 2)
                    })
            
            # Sort by average duration (slowest first)
            slow_endpoints.sort(key=lambda x: x['avg_duration_ms'], reverse=True)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'requests': {
                    'total': request_count,
                    'errors': error_count,
                    'error_rate_percent': round(error_rate, 2)
                },
                'performance': {
                    'slow_endpoints': slow_endpoints[:10],  # Top 10 slowest
                    'total_endpoints': len(performance_metrics)
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return {'error': str(e)}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance and health metrics"""
        try:
            from app import db
            from app.models.job import Job
            from app.models.payment import Payment
            from app.models.event import Event
            
            start_time = time.time()
            
            # Test database connectivity
            db.session.execute('SELECT 1')
            db.session.commit()
            connectivity_time = time.time() - start_time
            
            # Get table statistics
            job_count = Job.query.count()
            payment_count = Payment.query.count()
            event_count = Event.query.count()
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_jobs = Job.query.filter(Job.created_at >= yesterday).count()
            recent_events = Event.query.filter(Event.timestamp >= yesterday).count()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'connectivity': {
                    'status': 'healthy',
                    'response_time_ms': round(connectivity_time * 1000, 2)
                },
                'tables': {
                    'jobs': job_count,
                    'payments': payment_count,
                    'events': event_count
                },
                'recent_activity': {
                    'jobs_last_24h': recent_jobs,
                    'events_last_24h': recent_events
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'connectivity': {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            }
    
    def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage system metrics"""
        try:
            storage_path = os.environ.get('STORAGE_PATH', 'storage')
            
            if not os.path.exists(storage_path):
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'not_found',
                    'error': f'Storage path {storage_path} does not exist'
                }
            
            # Get storage directory info
            total_size = 0
            file_count = 0
            directory_count = 0
            
            for root, dirs, files in os.walk(storage_path):
                directory_count += len(dirs)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except (OSError, IOError):
                        continue
            
            # Get disk usage for storage directory
            disk_usage = psutil.disk_usage(storage_path)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'healthy',
                'path': storage_path,
                'files': {
                    'count': file_count,
                    'directories': directory_count,
                    'total_size_gb': round(total_size / (1024**3), 2)
                },
                'disk': {
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'percent_used': round((disk_usage.used / disk_usage.total) * 100, 2)
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect storage metrics: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def get_redis_metrics(self) -> Dict[str, Any]:
        """Get Redis performance and health metrics"""
        try:
            import redis
            from rq import Queue
            
            # Get Redis connection
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
            redis_client = redis.from_url(redis_url)
            
            # Test connectivity
            start_time = time.time()
            redis_client.ping()
            connectivity_time = time.time() - start_time
            
            # Get Redis info
            info = redis_client.info()
            
            # Get RQ queue metrics
            queue = Queue(connection=redis_client)
            job_count = len(queue)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'connectivity': {
                    'status': 'healthy',
                    'response_time_ms': round(connectivity_time * 1000, 2)
                },
                'redis': {
                    'version': info.get('redis_version', 'unknown'),
                    'uptime_seconds': info.get('uptime_in_seconds', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_mb': round(info.get('used_memory', 0) / (1024**2), 2),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                },
                'rq': {
                    'queue_size': job_count
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'connectivity': {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            }
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            # Collect all metrics
            system_metrics = self.get_system_metrics()
            app_metrics = self.get_application_metrics()
            db_metrics = self.get_database_metrics()
            storage_metrics = self.get_storage_metrics()
            redis_metrics = self.get_redis_metrics()
            
            # Determine overall health
            health_checks = {
                'system': 'healthy' if 'error' not in system_metrics else 'unhealthy',
                'database': db_metrics.get('connectivity', {}).get('status', 'unknown'),
                'storage': storage_metrics.get('status', 'unknown'),
                'redis': redis_metrics.get('connectivity', {}).get('status', 'unknown')
            }
            
            # Overall health is healthy only if all components are healthy
            overall_health = 'healthy' if all(status == 'healthy' for status in health_checks.values()) else 'degraded'
            
            # Store metrics in history
            metrics_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_health': overall_health,
                'health_checks': health_checks,
                'system': system_metrics,
                'application': app_metrics,
                'database': db_metrics,
                'storage': storage_metrics,
                'redis': redis_metrics
            }
            
            self.metrics_history.append(metrics_entry)
            
            # Keep only recent history
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            return {
                'status': overall_health,
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': time.time() - self.start_time,
                'health_checks': health_checks,
                'components': {
                    'system': system_metrics,
                    'application': app_metrics,
                    'database': db_metrics,
                    'storage': storage_metrics,
                    'redis': redis_metrics
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect comprehensive health: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for the specified number of hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter history by timestamp
            recent_metrics = []
            for entry in self.metrics_history:
                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                if entry_time >= cutoff_time:
                    recent_metrics.append(entry)
            
            return recent_metrics
        except Exception as e:
            logger.error(f"Failed to get metrics history: {e}")
            return []
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on thresholds"""
        alerts = []
        
        try:
            # Get current metrics
            system_metrics = self.get_system_metrics()
            app_metrics = self.get_application_metrics()
            
            # Check CPU usage
            if 'cpu' in system_metrics and system_metrics['cpu']['percent'] > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'warning',
                    'message': f"High CPU usage: {system_metrics['cpu']['percent']}%",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check memory usage
            if 'memory' in system_metrics and system_metrics['memory']['percent'] > 85:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'warning',
                    'message': f"High memory usage: {system_metrics['memory']['percent']}%",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check disk usage
            if 'disk' in system_metrics and system_metrics['disk']['percent'] > 90:
                alerts.append({
                    'type': 'high_disk',
                    'severity': 'critical',
                    'message': f"High disk usage: {system_metrics['disk']['percent']}%",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check error rate
            if 'requests' in app_metrics and app_metrics['requests']['error_rate_percent'] > 5:
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'critical',
                    'message': f"High error rate: {app_metrics['requests']['error_rate_percent']}%",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check slow endpoints
            if 'performance' in app_metrics:
                for endpoint in app_metrics['performance']['slow_endpoints'][:3]:  # Top 3 slowest
                    if endpoint['avg_duration_ms'] > 1000:  # Over 1 second
                        alerts.append({
                            'type': 'slow_endpoint',
                            'severity': 'warning',
                            'message': f"Slow endpoint {endpoint['path']}: {endpoint['avg_duration_ms']}ms avg",
                            'timestamp': datetime.utcnow().isoformat()
                        })
        
        except Exception as e:
            logger.error(f"Failed to generate performance alerts: {e}")
            alerts.append({
                'type': 'alert_generation_error',
                'severity': 'error',
                'message': f"Failed to generate alerts: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return alerts

# Global monitoring service instance
monitoring_service = MonitoringService()
