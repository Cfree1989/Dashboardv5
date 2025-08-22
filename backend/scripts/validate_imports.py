#!/usr/bin/env python3
"""
Import Validation Script
Task 2.2: Add Import Validation

This script validates import patterns and detects potential circular dependencies
in the services layer and business logic packages.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import importlib
import warnings

class ImportValidator:
    """Validates import patterns and detects circular dependencies"""
    
    def __init__(self, project_root: str = "app"):
        self.project_root = Path(project_root)
        self.import_graph: Dict[str, Set[str]] = {}
        self.circular_deps: List[List[str]] = []
        self.import_issues: List[str] = []
        
    def scan_directory(self, directory: str) -> None:
        """Scan a directory for Python files and build import graph"""
        dir_path = self.project_root / directory
        if not dir_path.exists():
            print(f"⚠️  Directory {dir_path} does not exist")
            return
            
        for py_file in dir_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            module_path = str(py_file.relative_to(self.project_root)).replace(os.sep, ".").replace(".py", "")
            self._analyze_file(py_file, module_path)
    
    def _analyze_file(self, file_path: Path, module_path: str) -> None:
        """Analyze a single Python file for imports"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = self._extract_imports(tree, module_path)
            
            if imports:
                self.import_graph[module_path] = imports
                
        except Exception as e:
            self.import_issues.append(f"Error parsing {file_path}: {e}")
    
    def _extract_imports(self, tree: ast.AST, current_module: str) -> Set[str]:
        """Extract import statements from AST"""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        
        # Filter to only include internal app imports
        return {imp for imp in imports if imp.startswith('app.')}
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                self.circular_deps.append(cycle)
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.import_graph.get(node, set()):
                dfs(neighbor)
                
            rec_stack.remove(node)
            path.pop()
        
        for node in self.import_graph:
            if node not in visited:
                dfs(node)
        
        return self.circular_deps
    
    def validate_import_patterns(self) -> List[str]:
        """Validate import patterns and best practices"""
        issues = []
        
        for module, imports in self.import_graph.items():
            # Check for wildcard imports
            if any('*' in imp for imp in imports):
                issues.append(f"⚠️  {module}: Contains wildcard imports")
            
            # Check for relative imports in wrong context
            if module.startswith('app.services') and any(imp.startswith('app.business_logic') for imp in imports):
                issues.append(f"⚠️  {module}: Services importing business_logic (potential circular dependency)")
        
        return issues
    
    def test_imports(self) -> List[str]:
        """Test actual imports to catch runtime issues"""
        issues = []
        test_modules = [
            'app.services',
            'app.business_logic',
            'app.services.orchestration.job_orchestration_service',
            'app.business_logic.job_lifecycle',
            'app.business_logic.shared_services',
            'app.business_logic.analytics'
        ]
        
        # Add current directory to Python path
        current_dir = Path.cwd()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        for module_name in test_modules:
            try:
                importlib.import_module(module_name)
                print(f"✅ {module_name}: Imports successfully")
            except Exception as e:
                error_msg = f"❌ {module_name}: Import failed - {e}"
                issues.append(error_msg)
                print(error_msg)
        
        return issues

def main():
    """Main validation function"""
    print("🔍 Import Validation Script")
    print("=" * 50)
    
    validator = ImportValidator()
    
    # Scan key directories
    print("\n📁 Scanning directories...")
    validator.scan_directory("services")
    validator.scan_directory("business_logic")
    
    # Detect circular dependencies
    print("\n🔄 Detecting circular dependencies...")
    circular_deps = validator.detect_circular_dependencies()
    
    if circular_deps:
        print("❌ Circular dependencies detected:")
        for cycle in circular_deps:
            print(f"   {' -> '.join(cycle)}")
    else:
        print("✅ No circular dependencies detected")
    
    # Validate import patterns
    print("\n📋 Validating import patterns...")
    pattern_issues = validator.validate_import_patterns()
    
    if pattern_issues:
        print("⚠️  Import pattern issues:")
        for issue in pattern_issues:
            print(f"   {issue}")
    else:
        print("✅ Import patterns look good")
    
    # Test actual imports
    print("\n🧪 Testing actual imports...")
    import_issues = validator.test_imports()
    
    if import_issues:
        print("❌ Import test issues:")
        for issue in import_issues:
            print(f"   {issue}")
    else:
        print("✅ All import tests passed")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
    print(f"   Circular Dependencies: {len(circular_deps)}")
    print(f"   Pattern Issues: {len(pattern_issues)}")
    print(f"   Import Test Issues: {len(import_issues)}")
    print(f"   Total Issues: {len(circular_deps) + len(pattern_issues) + len(import_issues)}")
    
    if not (circular_deps or pattern_issues or import_issues):
        print("🎉 All validations passed!")
        return 0
    else:
        print("⚠️  Issues found - review and fix as needed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
