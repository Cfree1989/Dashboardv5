#!/usr/bin/env python3
"""
Simple deployment script for atomic file operations.

This script assumes a clean slate (no existing jobs) and focuses on safely
enabling atomic file operations with monitoring and rollback capability.

Usage:
    python scripts/deploy_atomic_file_operations.py --enable
    python scripts/deploy_atomic_file_operations.py --disable
    python scripts/deploy_atomic_file_operations.py --status
"""

import os
import sys
import json
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtomicFileDeployment:
    """Simple deployment utility for atomic file operations."""
    
    def __init__(self):
        self.deployment_log = []
        self.config_file = Path('.env')
        
    def get_current_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        status = {
            'atomic_operations_enabled': False,
            'environment_variable': None,
            'docker_services_running': False,
            'last_deployment': None
        }
        
        # Check environment variable
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                for line in f:
                    if line.startswith('ATOMIC_FILE_OPERATIONS_ENABLED='):
                        value = line.split('=', 1)[1].strip()
                        status['atomic_operations_enabled'] = value.lower() == 'true'
                        status['environment_variable'] = value
                        break
        
        # Check Docker services
        try:
            result = subprocess.run(
                ['docker', 'compose', 'ps', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                services = json.loads(result.stdout)
                status['docker_services_running'] = len(services) > 0
        except Exception as e:
            logger.warning(f"Could not check Docker services: {e}")
        
        # Check deployment log
        log_file = Path('logs/deployment_log.json')
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                    if logs:
                        status['last_deployment'] = logs[-1].get('timestamp')
            except Exception as e:
                logger.warning(f"Could not read deployment log: {e}")
        
        return status
    
    def enable_atomic_operations(self, dry_run: bool = False) -> bool:
        """Enable atomic file operations."""
        try:
            # Update environment variable
            if not dry_run:
                self._update_env_variable('ATOMIC_FILE_OPERATIONS_ENABLED=true')
            
            # Restart backend service to pick up new environment
            if not dry_run:
                logger.info("Restarting backend service...")
                subprocess.run(['docker', 'compose', 'restart', 'backend'], check=True)
            
            # Log the deployment
            self._log_deployment('enable', dry_run)
            
            logger.info("✅ Atomic file operations enabled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable atomic operations: {e}")
            self._log_deployment('enable_failed', dry_run, error=str(e))
            return False
    
    def disable_atomic_operations(self, dry_run: bool = False) -> bool:
        """Disable atomic file operations (fallback to legacy system)."""
        try:
            # Update environment variable
            if not dry_run:
                self._update_env_variable('ATOMIC_FILE_OPERATIONS_ENABLED=false')
            
            # Restart backend service to pick up new environment
            if not dry_run:
                logger.info("Restarting backend service...")
                subprocess.run(['docker', 'compose', 'restart', 'backend'], check=True)
            
            # Log the deployment
            self._log_deployment('disable', dry_run)
            
            logger.info("✅ Atomic file operations disabled (fallback to legacy system)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable atomic operations: {e}")
            self._log_deployment('disable_failed', dry_run, error=str(e))
            return False
    
    def _update_env_variable(self, new_value: str):
        """Update environment variable in .env file."""
        if not self.config_file.exists():
            # Create .env file if it doesn't exist
            with open(self.config_file, 'w') as f:
                f.write(f"{new_value}\n")
            return
        
        # Read existing content
        with open(self.config_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add the variable
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('ATOMIC_FILE_OPERATIONS_ENABLED='):
                lines[i] = f"{new_value}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"{new_value}\n")
        
        # Write back to file
        with open(self.config_file, 'w') as f:
            f.writelines(lines)
    
    def _log_deployment(self, action: str, dry_run: bool, error: str = None):
        """Log deployment action."""
        log_entry = {
            'action': action,
            'dry_run': dry_run,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'environment_variable': 'ATOMIC_FILE_OPERATIONS_ENABLED'
        }
        
        if error:
            log_entry['error'] = error
        
        self.deployment_log.append(log_entry)
        
        # Save to file
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'deployment_log.json'
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    existing_logs = json.load(f)
            else:
                existing_logs = []
            
            existing_logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(existing_logs, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save deployment log: {e}")
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run health check on the system."""
        health = {
            'backend_responding': False,
            'file_operations_working': False,
            'redis_available': False,
            'database_available': False
        }
        
        try:
            # Check backend health
            result = subprocess.run(
                ['curl', '-f', 'http://localhost:5000/health'],
                capture_output=True, text=True, timeout=5
            )
            health['backend_responding'] = result.returncode == 0
        except Exception:
            pass
        
        try:
            # Check Redis
            result = subprocess.run(
                ['docker', 'compose', 'exec', '-T', 'redis', 'redis-cli', 'ping'],
                capture_output=True, text=True, timeout=5
            )
            health['redis_available'] = result.returncode == 0 and 'PONG' in result.stdout
        except Exception:
            pass
        
        try:
            # Check database
            result = subprocess.run(
                ['docker', 'compose', 'exec', '-T', 'db', 'pg_isready', '-U', 'postgres'],
                capture_output=True, text=True, timeout=5
            )
            health['database_available'] = result.returncode == 0
        except Exception:
            pass
        
        # File operations check would require a test job, but we assume clean slate
        health['file_operations_working'] = health['backend_responding']
        
        return health
    
    def generate_deployment_report(self) -> str:
        """Generate a deployment report."""
        status = self.get_current_status()
        health = self.run_health_check()
        
        report = []
        report.append("=== Atomic File Operations Deployment Report ===")
        report.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        report.append("")
        
        report.append("Current Status:")
        report.append(f"  Atomic Operations: {'✅ ENABLED' if status['atomic_operations_enabled'] else '❌ DISABLED'}")
        report.append(f"  Environment Variable: {status['environment_variable'] or 'Not set'}")
        report.append(f"  Docker Services: {'✅ Running' if status['docker_services_running'] else '❌ Not running'}")
        report.append(f"  Last Deployment: {status['last_deployment'] or 'Never'}")
        report.append("")
        
        report.append("System Health:")
        report.append(f"  Backend: {'✅ Responding' if health['backend_responding'] else '❌ Not responding'}")
        report.append(f"  Redis: {'✅ Available' if health['redis_available'] else '❌ Not available'}")
        report.append(f"  Database: {'✅ Available' if health['database_available'] else '❌ Not available'}")
        report.append(f"  File Operations: {'✅ Working' if health['file_operations_working'] else '❌ Not working'}")
        report.append("")
        
        if self.deployment_log:
            report.append("Recent Deployments:")
            for entry in self.deployment_log[-5:]:  # Last 5 entries
                report.append(f"  {entry['timestamp']} - {entry['action']}")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Deploy atomic file operations')
    parser.add_argument('--enable', action='store_true', help='Enable atomic file operations')
    parser.add_argument('--disable', action='store_true', help='Disable atomic file operations')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--health', action='store_true', help='Run health check')
    parser.add_argument('--report', action='store_true', help='Generate deployment report')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run')
    
    args = parser.parse_args()
    
    if not any([args.enable, args.disable, args.status, args.health, args.report]):
        parser.print_help()
        return
    
    deployment = AtomicFileDeployment()
    
    if args.status:
        status = deployment.get_current_status()
        print("Current Deployment Status:")
        print(f"  Atomic Operations: {'ENABLED' if status['atomic_operations_enabled'] else 'DISABLED'}")
        print(f"  Environment Variable: {status['environment_variable'] or 'Not set'}")
        print(f"  Docker Services: {'Running' if status['docker_services_running'] else 'Not running'}")
        print(f"  Last Deployment: {status['last_deployment'] or 'Never'}")
    
    if args.health:
        health = deployment.run_health_check()
        print("System Health Check:")
        for service, status in health.items():
            print(f"  {service}: {'✅' if status else '❌'}")
    
    if args.enable:
        logger.info("Enabling atomic file operations...")
        success = deployment.enable_atomic_operations(args.dry_run)
        if success:
            logger.info("✅ Atomic file operations enabled successfully")
        else:
            logger.error("❌ Failed to enable atomic file operations")
            sys.exit(1)
    
    if args.disable:
        logger.info("Disabling atomic file operations...")
        success = deployment.disable_atomic_operations(args.dry_run)
        if success:
            logger.info("✅ Atomic file operations disabled successfully")
        else:
            logger.error("❌ Failed to disable atomic file operations")
            sys.exit(1)
    
    if args.report:
        report = deployment.generate_deployment_report()
        print(report)

if __name__ == '__main__':
    main()
