import ast
import importlib.util
from pathlib import Path

APP_PACKAGE = "app"


def _find_app_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / APP_PACKAGE
        if candidate.is_dir():
            return candidate
    raise AssertionError("Unable to locate the app package root")


APP_ROOT = _find_app_root()
USE_CASES_ROOT = APP_ROOT / "use_cases"
ALLOWED_USE_CASES = {"auth", "favorites", "watch"}


def _iter_python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in root.rglob("*.py") if path.is_file()]


def _module_name(path: Path) -> str:
    relative = path.relative_to(APP_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return APP_PACKAGE
    return f"{APP_PACKAGE}." + ".".join(parts)


def _collect_imports(path: Path) -> set[str]:
    module_name = _module_name(path)
    if path.name == "__init__.py":
        package = module_name
    else:
        package = module_name.rpartition(".")[0]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                dotted = "." * node.level + (node.module or "")
                try:
                    base = importlib.util.resolve_name(dotted, package)
                except ImportError:
                    base = dotted.lstrip(".")
            else:
                base = node.module or ""
            if base:
                imports.add(base)
                for alias in node.names:
                    if alias.name != "*":
                        imports.add(f"{base}.{alias.name}")
    return imports


def _assert_no_imports(
    *, layer: str, roots: list[Path], forbidden_prefixes: list[str]
) -> None:
    violations: list[str] = []
    for root in roots:
        for path in _iter_python_files(root):
            module_name = _module_name(path)
            for imported in _collect_imports(path):
                for prefix in forbidden_prefixes:
                    if imported == prefix or imported.startswith(prefix + "."):
                        relative_path = path.relative_to(APP_ROOT)
                        violations.append(
                            f"{module_name} ({relative_path}) imports {imported}"
                        )
    assert not violations, (
        f"{layer} layer violates architecture contract:\n"
        + "\n".join(sorted(violations))
    )


def _collect_forbidden_imports(
    *, roots: list[Path], forbidden_prefixes: list[str]
) -> list[str]:
    violations: list[str] = []
    for root in roots:
        for path in _iter_python_files(root):
            module_name = _module_name(path)
            for imported in _collect_imports(path):
                for prefix in forbidden_prefixes:
                    if imported == prefix or imported.startswith(prefix + "."):
                        relative_path = path.relative_to(APP_ROOT)
                        violations.append(
                            f"{module_name} ({relative_path}) imports {imported}"
                        )
    return violations


def test_domain_has_no_external_imports() -> None:
    domain_root = APP_ROOT / "domain"
    violations: list[str] = []

    for path in _iter_python_files(domain_root):
        module_name = _module_name(path)
        for imported in _collect_imports(path):
            if imported.startswith(f"{APP_PACKAGE}.") and not imported.startswith(
                f"{APP_PACKAGE}.domain"
            ):
                relative_path = path.relative_to(APP_ROOT)
                violations.append(
                    f"{module_name} ({relative_path}) imports {imported}"
                )

    assert not violations, (
        "domain layer violates architecture contract:\n"
        + "\n".join(sorted(violations))
    )


def test_use_cases_do_not_import_transport_or_infrastructure() -> None:
    _assert_no_imports(
        layer="use_cases",
        roots=[USE_CASES_ROOT / name for name in sorted(ALLOWED_USE_CASES)],
        forbidden_prefixes=[
            f"{APP_PACKAGE}.routers",
            f"{APP_PACKAGE}.api",
            f"{APP_PACKAGE}.crud",
            f"{APP_PACKAGE}.infrastructure",
        ],
    )


def test_use_cases_only_allowed_modules() -> None:
    unexpected = [
        path.name
        for path in USE_CASES_ROOT.iterdir()
        if path.is_dir()
        and not path.name.startswith("__")
        and path.name not in ALLOWED_USE_CASES
    ]
    assert not unexpected, f"Unexpected use cases modules found: {sorted(unexpected)}"


def test_favorites_use_cases_do_not_import_infrastructure() -> None:
    _assert_no_imports(
        layer="favorites",
        roots=[USE_CASES_ROOT / "favorites"],
        forbidden_prefixes=[f"{APP_PACKAGE}.crud", f"{APP_PACKAGE}.infrastructure"],
    )


def test_watch_use_cases_do_not_import_infrastructure() -> None:
    _assert_no_imports(
        layer="watch",
        roots=[USE_CASES_ROOT / "watch"],
        forbidden_prefixes=[f"{APP_PACKAGE}.crud", f"{APP_PACKAGE}.infrastructure"],
    )


def test_security_does_not_import_application_or_use_cases() -> None:
    _assert_no_imports(
        layer="security",
        roots=[APP_ROOT / "security"],
        forbidden_prefixes=[f"{APP_PACKAGE}.application", f"{APP_PACKAGE}.use_cases"],
    )


def test_transport_does_not_import_domain_directly() -> None:
    _assert_no_imports(
        layer="transport",
        roots=[APP_ROOT / "routers", APP_ROOT / "api"],
        forbidden_prefixes=[f"{APP_PACKAGE}.domain"],
    )
