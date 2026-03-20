# 🛡️ Secure Operator

> **Golden Stack #2** — Sandboxed Code Execution with NVIDIA NeMo-Claw + OpenClaw + OpenShell

This blueprint is purpose-built for AI agents that need to **execute complex tools, scripts, and code in complete isolation** — without compromising the host infrastructure. NVIDIA's Agent Toolkit provides the security perimeter.

---

## 🏗️ Architecture

```
  User Request
       │
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │                    NeMo-Claw Privacy Router               │
  │  ┌──────────────┐    PII detected?                        │
  │  │  INPUT RAIL  │ ──► Yes → Local model only (Nemotron)  │
  │  │ (jailbreak + │ ──► No  → Cloud model allowed (Azure)  │
  │  │  PII check)  │                                         │
  │  └──────────────┘                                         │
  └────────────────────────┬─────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  OpenClaw   │  ← Orchestration engine
                    │    Agent    │
                    └──────┬──────┘
                           │ tool call
                    ┌──────▼──────────────────┐
                    │   NVIDIA OpenShell       │
                    │   (sandboxed runtime)    │
                    │                          │
                    │  ┌─────────────────────┐ │
                    │  │  Python Interpreter  │ │  CPU/Memory limits
                    │  │  File Reader         │ │  Network: isolated
                    │  │  SAP Connector       │ │  gVisor-hardened
                    │  └─────────────────────┘ │
                    └─────────────────────────-┘
                           │ result
                    ┌──────▼──────┐
                    │  OUTPUT RAIL │  ← NeMo-Claw filters response
                    └─────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose v2.x
- NVIDIA Container Toolkit (for GPU inference)
- **NVIDIA NeMo-Claw**: `curl -fsSL https://nvidia.com/nemoclaw.sh | bash`

### 1. Install NeMo-Claw on host
```bash
make nemoclaw-install
nemoclaw onboard          # Follow the onboarding wizard
```

### 2. Configure
```bash
cp .env.example .env
cp config.yaml.example config.yaml
nano .env                 # Fill all <CHANGE_ME> placeholders
```

### 3. Start
```bash
make up
```

---

## ⚙️ Configuration

### Key Config Sections (`config.yaml`)

```yaml
inference:
  provider: vllm           # vllm | azure_ai_foundry | nvidia-nemotron

orchestration:
  framework: openclaw

sandbox:
  runtime: nvidia-openshell
  openshell:
    resource_limits:
      max_memory_mb: 2048
      max_cpu_cores: 2
    network_policy: isolated   # isolated | restricted | full

security:
  nemoclaw:
    privacy_mode: strict       # strict | balanced | permissive
    guardrails:
      pii_redaction: true
      jailbreak_detection: true

tools:
  enabled: python-interpreter,file-reader,web-search
```

### Key `.env` Variables

| Variable | Description |
|---|---|
| `INFERENCE_PROVIDER` | `vllm` / `azure_ai_foundry` / `nvidia-nemotron` |
| `NEMOCLAW_ENABLED` | Enable/disable NeMo-Claw guardrails |
| `NEMOCLAW_PRIVACY_MODE` | `strict` / `balanced` / `permissive` |
| `OPENSHELL_ENABLED` | Enable OpenShell sandbox for code execution |
| `OPENSHELL_NETWORK_POLICY` | `isolated` / `restricted` / `full` |
| `ENABLED_TOOLS` | Comma-separated list of active tools |

---

## 🛡️ NVIDIA Security Stack

| Component | Role |
|---|---|
| **NeMo-Claw** | Privacy + security policy layer on top of OpenClaw |
| **OpenClaw** | Agent orchestration OS (agentic runtime) |
| **NVIDIA OpenShell** | Isolated execution sandbox with syscall filtering |
| **Privacy Router** | Decides if data can go to cloud models (PII-aware) |

---

## 🧪 Testing

```bash
make test-unit       # Unit tests (no services)
make nemoclaw-status # Verify NeMo-Claw is running
```

---

## 📄 License
Proprietary — All rights reserved.
