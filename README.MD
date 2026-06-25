# CORE-ISOLATE: Sovereign Grid-Edge Controller

CORE-ISOLATE is an autonomous, physics-constrained control plane designed for real-time energy grid orchestration. It utilizes a hierarchical multi-agent architecture with deterministic safety kernels.

## Architecture
- **Cognitive Layer:** GPT-OSS 120B (Groq) for strategic grid optimization.
- **Governor Kernel:** Hard-coded physics-based safety constraints (Veto logic).
- **Adversarial Layer:** Continuous stress-testing node for system hardening.
- **Persistence:** Postgres-backed state management for industrial-grade fault tolerance.

## Getting Started
1. Install requirements: `pip install -r requirements.txt`
2. Set your environment: `export DATABASE_URL="postgresql://user:pass@localhost:5432/grid_db"`
3. Run: `python main.py`
