"""
Code sanitization utilities for safe code execution.

This module provides validation and sanitization for Python and JavaScript code
to prevent malicious operations like file system access, network calls,
process spawning, etc.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class SanitizationResult:
    """Result of code sanitization check."""

    is_safe: bool
    violations: List[str]

    @property
    def error_message(self) -> Optional[str]:
        if self.is_safe:
            return None
        return "Code contains potentially dangerous operations: " + "; ".join(
            self.violations
        )


# Python dangerous patterns
PYTHON_DANGEROUS_IMPORTS = [
    # System/OS access
    r"\bimport\s+os\b",
    r"\bfrom\s+os\s+import\b",
    r"\bimport\s+sys\b",
    r"\bfrom\s+sys\s+import\b",
    r"\bimport\s+subprocess\b",
    r"\bfrom\s+subprocess\s+import\b",
    r"\bimport\s+shutil\b",
    r"\bfrom\s+shutil\s+import\b",
    r"\bimport\s+pathlib\b",
    r"\bfrom\s+pathlib\s+import\b",
    # Code execution
    r"\bimport\s+exec\b",
    r"\bimport\s+eval\b",
    r"\bimport\s+compile\b",
    r"\bimport\s+code\b",
    r"\bfrom\s+code\s+import\b",
    r"\bimport\s+ast\b",
    r"\bfrom\s+ast\s+import\b",
    r"\bimport\s+importlib\b",
    r"\bfrom\s+importlib\s+import\b",
    r"\b__import__\s*\(",
    # Network access
    r"\bimport\s+socket\b",
    r"\bfrom\s+socket\s+import\b",
    r"\bimport\s+requests\b",
    r"\bfrom\s+requests\s+import\b",
    r"\bimport\s+urllib\b",
    r"\bfrom\s+urllib\b",
    r"\bimport\s+httplib\b",
    r"\bimport\s+http\.client\b",
    r"\bimport\s+ftplib\b",
    r"\bimport\s+smtplib\b",
    r"\bimport\s+telnetlib\b",
    r"\bimport\s+aiohttp\b",
    r"\bfrom\s+aiohttp\s+import\b",
    r"\bimport\s+httpx\b",
    r"\bfrom\s+httpx\s+import\b",
    # File access
    r"\bimport\s+io\b",
    r"\bfrom\s+io\s+import\b",
    r"\bimport\s+tempfile\b",
    r"\bfrom\s+tempfile\s+import\b",
    r"\bimport\s+glob\b",
    r"\bfrom\s+glob\s+import\b",
    r"\bimport\s+fileinput\b",
    # Process/threading
    r"\bimport\s+multiprocessing\b",
    r"\bfrom\s+multiprocessing\s+import\b",
    r"\bimport\s+threading\b",
    r"\bfrom\s+threading\s+import\b",
    r"\bimport\s+concurrent\b",
    r"\bfrom\s+concurrent\b",
    # Dangerous built-ins
    r"\bimport\s+ctypes\b",
    r"\bfrom\s+ctypes\s+import\b",
    r"\bimport\s+pickle\b",
    r"\bfrom\s+pickle\s+import\b",
    r"\bimport\s+marshal\b",
    r"\bimport\s+shelve\b",
    # Introspection/reflection that could be dangerous
    r"\bimport\s+inspect\b",
    r"\bfrom\s+inspect\s+import\b",
    r"\bimport\s+gc\b",
    r"\bfrom\s+gc\s+import\b",
    # Database access (prevent data exfiltration)
    r"\bimport\s+sqlite3\b",
    r"\bimport\s+psycopg2\b",
    r"\bimport\s+pymysql\b",
    r"\bimport\s+pymongo\b",
    r"\bimport\s+redis\b",
]

PYTHON_DANGEROUS_FUNCTIONS = [
    # Built-in dangerous functions
    (r"\bexec\s*\(", "exec() function"),
    (r"\beval\s*\(", "eval() function"),
    (r"\bcompile\s*\(", "compile() function"),
    (r"\bopen\s*\(", "open() function - file access"),
    (r"\bgetattr\s*\(", "getattr() function"),
    (r"\bsetattr\s*\(", "setattr() function"),
    (r"\bdelattr\s*\(", "delattr() function"),
    (r"\bglobals\s*\(", "globals() function"),
    (r"\blocals\s*\(", "locals() function"),
    (r"\bvars\s*\(", "vars() function"),
    (r"\bdir\s*\(", "dir() function"),
    (r"\b__builtins__", "__builtins__ access"),
    (r"\b__class__", "__class__ access"),
    (r"\b__subclasses__", "__subclasses__ access"),
    (r"\b__mro__", "__mro__ access"),
    (r"\b__bases__", "__bases__ access"),
    (r"\b__globals__", "__globals__ access"),
    (r"\b__code__", "__code__ access"),
    # System commands
    (r"\.system\s*\(", "system() call"),
    (r"\.popen\s*\(", "popen() call"),
    (r"\.spawn\s*\(", "spawn() call"),
    (r"\.call\s*\(", "subprocess call()"),
    (r"\.run\s*\(", "subprocess run()"),
    (r"\.Popen\s*\(", "Popen() call"),
    # Exit functions
    (r"\bexit\s*\(", "exit() function"),
    (r"\bquit\s*\(", "quit() function"),
    (r"\b_exit\s*\(", "_exit() function"),
]

# JavaScript dangerous patterns
JAVASCRIPT_DANGEROUS_PATTERNS = [
    # Node.js modules
    (r'\brequire\s*\(\s*[\'"]fs[\'"]', "fs module - file system access"),
    (r'\brequire\s*\(\s*[\'"]child_process[\'"]', "child_process module"),
    (r'\brequire\s*\(\s*[\'"]os[\'"]', "os module"),
    (r'\brequire\s*\(\s*[\'"]path[\'"]', "path module"),
    (r'\brequire\s*\(\s*[\'"]net[\'"]', "net module - network access"),
    (r'\brequire\s*\(\s*[\'"]http[\'"]', "http module"),
    (r'\brequire\s*\(\s*[\'"]https[\'"]', "https module"),
    (r'\brequire\s*\(\s*[\'"]dgram[\'"]', "dgram module - UDP"),
    (r'\brequire\s*\(\s*[\'"]dns[\'"]', "dns module"),
    (r'\brequire\s*\(\s*[\'"]cluster[\'"]', "cluster module"),
    (r'\brequire\s*\(\s*[\'"]worker_threads[\'"]', "worker_threads module"),
    (r'\brequire\s*\(\s*[\'"]vm[\'"]', "vm module"),
    (r'\brequire\s*\(\s*[\'"]repl[\'"]', "repl module"),
    (r'\brequire\s*\(\s*[\'"]readline[\'"]', "readline module"),
    (r'\brequire\s*\(\s*[\'"]tls[\'"]', "tls module"),
    (r'\brequire\s*\(\s*[\'"]crypto[\'"]', "crypto module"),
    (r'\brequire\s*\(\s*[\'"]zlib[\'"]', "zlib module"),
    # ES6 imports for Node modules
    (r'\bimport\s+.*\s+from\s+[\'"]fs[\'"]', "fs module import"),
    (r'\bimport\s+.*\s+from\s+[\'"]child_process[\'"]', "child_process import"),
    (r'\bimport\s+.*\s+from\s+[\'"]os[\'"]', "os module import"),
    (r'\bimport\s+.*\s+from\s+[\'"]net[\'"]', "net module import"),
    (r'\bimport\s+.*\s+from\s+[\'"]http[\'"]', "http module import"),
    (r'\bimport\s+.*\s+from\s+[\'"]https[\'"]', "https module import"),
    # Dangerous global functions/objects
    (r"\bprocess\.", "process object access"),
    (r"\bglobal\.", "global object access"),
    (r"\b__dirname\b", "__dirname access"),
    (r"\b__filename\b", "__filename access"),
    (r"\bBuffer\s*\(", "Buffer constructor"),
    (r"\bBuffer\.alloc", "Buffer allocation"),
    # Code execution
    (r"\beval\s*\(", "eval() function"),
    (r"\bFunction\s*\(", "Function constructor"),
    (r'\bsetTimeout\s*\([^,]*[\'"`]', "setTimeout with string code"),
    (r'\bsetInterval\s*\([^,]*[\'"`]', "setInterval with string code"),
    # Fetch/network (if available)
    (r"\bfetch\s*\(", "fetch() - network access"),
    (r"\bXMLHttpRequest\b", "XMLHttpRequest"),
    (r"\bWebSocket\b", "WebSocket access"),
]

# Common patterns for both languages
COMMON_DANGEROUS_PATTERNS = [
    (r"\benv\b", "environment variable access"),
    (r"\.env\b", ".env file access"),
    (r"password", "potential password handling"),
    (r"secret", "potential secret handling"),
    (r"api[_-]?key", "potential API key handling"),
    (r"private[_-]?key", "potential private key handling"),
]

# Maximum code length
MAX_CODE_LENGTH = 10000  # 10KB


def sanitize_python_code(code: str) -> SanitizationResult:
    """
    Validate Python code for dangerous patterns.

    Args:
        code: The Python code to validate

    Returns:
        SanitizationResult with safety status and any violations found
    """
    violations = []

    # Check code length
    if len(code) > MAX_CODE_LENGTH:
        violations.append(
            f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
        )
        return SanitizationResult(is_safe=False, violations=violations)

    # Check for dangerous imports
    for pattern in PYTHON_DANGEROUS_IMPORTS:
        match = re.search(pattern, code, re.IGNORECASE)
        if match:
            violations.append(f"Dangerous import detected: {match.group(0).strip()}")

    # Check for dangerous functions
    for pattern, description in PYTHON_DANGEROUS_FUNCTIONS:
        if re.search(pattern, code, re.IGNORECASE):
            violations.append(f"Dangerous operation: {description}")

    return SanitizationResult(is_safe=len(violations) == 0, violations=violations)


def sanitize_javascript_code(code: str) -> SanitizationResult:
    """
    Validate JavaScript code for dangerous patterns.

    Args:
        code: The JavaScript code to validate

    Returns:
        SanitizationResult with safety status and any violations found
    """
    violations = []

    # Check code length
    if len(code) > MAX_CODE_LENGTH:
        violations.append(
            f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
        )
        return SanitizationResult(is_safe=False, violations=violations)

    # Check for dangerous patterns
    for pattern, description in JAVASCRIPT_DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            violations.append(f"Dangerous operation: {description}")

    return SanitizationResult(is_safe=len(violations) == 0, violations=violations)


def sanitize_code(code: str, language: str) -> SanitizationResult:
    """
    Validate code for the specified language.

    Args:
        code: The code to validate
        language: The programming language ('python' or 'javascript')

    Returns:
        SanitizationResult with safety status and any violations found
    """
    if language.lower() == "python":
        return sanitize_python_code(code)
    elif language.lower() in ("javascript", "js"):
        return sanitize_javascript_code(code)
    else:
        return SanitizationResult(
            is_safe=False, violations=[f"Unsupported language: {language}"]
        )


# Allowed modules for Python (whitelist approach - optional stricter mode)
PYTHON_ALLOWED_IMPORTS = {
    "json",
    "math",
    "random",
    "datetime",
    "collections",
    "itertools",
    "functools",
    "re",
    "string",
    "decimal",
    "fractions",
    "statistics",
    "copy",
    "pprint",
    "textwrap",
    "difflib",
    "enum",
    "dataclasses",
    "typing",
    "abc",
    "numbers",
    "operator",
    "heapq",
    "bisect",
    "array",
    "weakref",
    "types",
    "hashlib",  # For data hashing only
    "base64",
    "binascii",
    "html",
    "xml.etree.ElementTree",  # Safe XML parsing
    "csv",  # String-based, not file-based
    "uuid",
    "time",  # For time.sleep and timestamps
}


def get_allowed_imports_python() -> set:
    """Return the set of allowed Python imports."""
    return PYTHON_ALLOWED_IMPORTS.copy()


def extract_imports(code: str, language: str) -> List[str]:
    """
    Extract all import statements from code.

    Args:
        code: The code to analyze
        language: The programming language

    Returns:
        List of imported module names
    """
    imports = []

    if language.lower() == "python":
        # Match 'import x' and 'from x import y'
        import_pattern = r"^\s*import\s+([\w.]+)"
        from_pattern = r"^\s*from\s+([\w.]+)\s+import"

        for line in code.split("\n"):
            match = re.match(import_pattern, line)
            if match:
                imports.append(match.group(1))
            match = re.match(from_pattern, line)
            if match:
                imports.append(match.group(1))

    elif language.lower() in ("javascript", "js"):
        # Match require('x') and import x from 'x'
        require_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]"
        import_pattern = r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]"

        imports.extend(re.findall(require_pattern, code))
        imports.extend(re.findall(import_pattern, code))

    return imports
