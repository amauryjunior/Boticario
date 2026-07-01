"""Self-test / health check helpers — RF01 (system initialization)."""
from dataclasses import dataclass, field


@dataclass
class ModuleStatus:
    name: str
    ok: bool
    critical: bool
    message: str = ""


@dataclass
class HealthReport:
    statuses: list = field(default_factory=list)

    def add(self, name, ok, critical, message=""):
        self.statuses.append(ModuleStatus(name, ok, critical, message))

    @property
    def has_critical_failure(self):
        return any(not s.ok and s.critical for s in self.statuses)

    @property
    def degraded(self):
        return any(not s.ok and not s.critical for s in self.statuses)

    def summary_lines(self):
        lines = []
        for s in self.statuses:
            state = "OK" if s.ok else ("CRITICAL FAIL" if s.critical else "DEGRADED")
            suffix = f" ({s.message})" if s.message else ""
            lines.append(f"[SELF_TEST] {s.name}: {state}{suffix}")
        return lines
