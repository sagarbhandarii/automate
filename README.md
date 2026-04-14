# Mobile Security Test Framework (MSTF)

A Python-based framework for orchestrating mobile app security and performance test suites across connected devices/emulators.

## Setup

### 1) Prerequisites
- Python 3.11+ recommended (CI uses Python 3.11).
- `pip`
- (Optional, depending on suites) Android SDK/ADB, Frida tooling, and device/emulator access.

### 2) Install dependencies
```bash
./scripts/bootstrap_env.sh
```

Or manually:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Configure runtime settings
- Default config file: `config.yaml`
- Additional suite/profile/device examples are under `configs/`.

### 4) Set Python module path
This repository uses a `src/` layout and does not currently include packaging metadata (`pyproject.toml`/`setup.py`).
Set `PYTHONPATH` before running tests or the CLI:

```bash
export PYTHONPATH=src
```

## Run Tests

### Run full test suite
```bash
PYTHONPATH=src pytest -q
```

### Run unit tests only
```bash
PYTHONPATH=src pytest -q tests/unit
```

### Run integration or end-to-end tests
```bash
PYTHONPATH=src pytest -q tests/integration
PYTHONPATH=src pytest -q tests/e2e
```

## Add New Test Cases

You can add tests at two levels:

### A) Add/extend pytest test files
1. Choose the appropriate directory:
   - `tests/unit/` for isolated logic tests
   - `tests/integration/` for component interaction tests
   - `tests/e2e/` for full-run orchestration tests
2. Create a new file named `test_<feature>.py`.
3. Add functions using pytest naming conventions (e.g., `def test_<behavior>(): ...`).
4. Run:
   ```bash
   PYTHONPATH=src pytest -q tests/unit/test_<feature>.py
   ```

### B) Add a new security suite/check in framework registry
1. Update `src/mstf/security_suite/registry.py`:
   - Add a `SecurityTestSuite(...)` entry in `get_registry()`.
   - Define one or more `SuiteCheck(check_id, title, log_hint)` values.
2. Enable the suite in `config.yaml` (or a profile config under `configs/`).
3. Add corresponding tests in `tests/unit/` to validate:
   - registration/selection behavior
   - expected check IDs and output structure
4. Run tests locally:
   ```bash
   PYTHONPATH=src pytest -q
   ```

## CI/CD Usage

This repository includes both GitHub Actions and Jenkins pipelines.

### GitHub Actions
Workflow file: `ci/github/workflow.yml`

Triggers:
- `pull_request`
- `push` to `main`
- manual `workflow_dispatch`

Default job behavior:
1. Checkout repository
2. Set up Python 3.11
3. Install dependencies (`pip install -r requirements.txt`)
4. Run tests (`pytest -q`)

### Jenkins
Pipelines:
- Root pipeline: `Jenkinsfile`
- Secondary pipeline example: `ci/jenkins/Jenkinsfile`

Typical stages:
- Checkout
- Dependency install
- Test execution with pytest
- JUnit report publication and artifact archiving (root `Jenkinsfile`)

## Run the CLI

After setting `PYTHONPATH=src`, run:

```bash
python -m mstf.main --config config.yaml --security
```

Useful options:
- `--suite <suite_id>` (repeatable)
- `--tag <tag>` (repeatable)
- `--performance`
- `--workers <n>`
