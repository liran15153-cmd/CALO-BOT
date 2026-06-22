from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    ".pytest-tmp",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
EXCLUDED_FILES = {".env", ".env.local", "package-lock.json"}
TEXT_SUFFIXES = {
    ".css",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".log",
    ".md",
    ".mjs",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}


@dataclass(frozen=True)
class SecretFinding:
    path: str
    line: int
    kind: str


POSTGRES_PASSWORD_URL_PATTERN = re.compile(
    r"\bpostgres(?:ql)?://[^:\s/@]+:(?P<password>[^@\s]+)@[^ \n\r\t]+"
)

PATTERNS = (
    ("supabase_secret_key", re.compile(r"\bsb_secret_[A-Za-z0-9_-]{24,}\b")),
    ("legacy_service_role_jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("postgres_password_url", POSTGRES_PASSWORD_URL_PATTERN),
)


def find_secret_findings(path: str, text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in PATTERNS:
            match = pattern.search(line)
            if match and not _finding_is_safe_placeholder(kind, line, match):
                findings.append(SecretFinding(path=path, line=line_number, kind=kind))
    return findings


def scan_repo(root: Path) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for path in root.rglob("*"):
        if not path.is_file() or _skip_path(root, path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(find_secret_findings(str(path.relative_to(root)), text))
    return findings


def _skip_path(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    if path.name in EXCLUDED_FILES:
        return True
    if path.suffix.lower() in TEXT_SUFFIXES:
        return False
    return path.name in {".gitignore", "README"}


def _finding_is_safe_placeholder(kind: str, line: str, match: re.Match[str]) -> bool:
    if kind == "postgres_password_url":
        return _is_placeholder_secret(match.group("password"))
    lowered = line.lower()
    return "<project-ref>" in lowered or "placeholder" in lowered


def _is_placeholder_secret(value: str) -> bool:
    normalized = value.strip(" '\"<>[]{}").lower()
    return normalized in {
        "password",
        "changeme",
        "change-me",
        "example",
        "example-password",
        "placeholder",
        "your-password",
        "your_password",
        "db-password",
        "db_password",
    } or normalized.startswith("your_") or normalized.startswith("your-")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repo text files for committed secrets.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    findings = scan_repo(root)
    if not findings:
        print("Secret scan passed: no secret-like values found.")
        return 0
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.kind}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
