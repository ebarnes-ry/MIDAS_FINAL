import signal
import time
import ast
import sympy
from typing import Dict, Any

def validate_execution_environment() -> Dict[str, Any]:
    """
    Runs a series of checks to validate that the environment supports
    the security and functionality requirements of the SafeExecutor.

    Returns:
        A dictionary summarizing the status of each check.
    """
    print("--- Running Environment Validation for Verification Pipeline ---")
    checks = {
        "signal_support": _check_signal_support(),
        "resource_limits": _check_resource_limits(),
        "sympy_version": _check_sympy_version(),
        "ast_parsing": _check_ast_parsing(),
    }

    overall_status = all(check["status"] for check in checks.values())
    checks["overall_status"] = {
        "status": overall_status,
        "message": "Environment is fully configured for safe execution." if overall_status else "Environment has configuration issues."
    }
    print(f"--- Validation Complete. Overall Status: {'OK' if overall_status else 'FAIL'} ---")
    return checks

def _check_signal_support() -> Dict[str, Any]:
    """Checks if SIGALRM is available for enforcing timeouts."""
    try:
        signal.signal(signal.SIGALRM, lambda s, f: None)
        signal.alarm(0)
        return {"status": True, "message": "SIGALRM support is available for timeouts."}
    except (AttributeError, ValueError):
        return {"status": False, "message": "SIGALRM not available. Timeouts will not be enforced."}

def _check_resource_limits() -> Dict[str, Any]:
    """Checks if the 'resource' module is available for memory limiting."""
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        return {"status": True, "message": "Resource module is available for memory limits.", "details": f"Current limit (soft/hard): {soft}/{hard}"}
    except ImportError:
        return {"status": False, "message": "Resource module not available. Memory limits will not be enforced."}

def _check_sympy_version() -> Dict[str, Any]:
    """Verifies that a compatible version of SymPy is installed."""
    try:
        version = sympy.__version__
        major, minor, _ = map(int, version.split('.'))
        if major >= 1 and minor >= 9:
            return {"status": True, "message": f"SymPy version {version} is compatible."}
        else:
            return {"status": False, "message": f"SymPy version {version} is too old. Recommend >= 1.9."}
    except Exception as e:
        return {"status": False, "message": f"Could not determine SymPy version: {e}"}

def _check_ast_parsing() -> Dict[str, Any]:
    """Ensures the 'ast' module can parse code."""
    try:
        ast.parse("x = 1 + 1")
        return {"status": True, "message": "AST parsing is functional."}
    except Exception as e:
        return {"status": False, "message": f"AST parsing failed: {e}"}

if __name__ == '__main__':
    # Allows running this file directly to check the current environment.
    results = validate_execution_environment()
    import json
    print(json.dumps(results, indent=2))