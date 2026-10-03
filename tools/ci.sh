#!/usr/bin/env bash
# UCOS continuous integration — the only entry point (ADR-036).
# Runs every check in the same order on a laptop and in GitHub Actions. Deterministic, offline after
# dependency install, no AI calls, no secrets, no human steps.
#
#   tools/ci.sh            check everything (fails on stale generated files)
#   tools/ci.sh --fix      regenerate generated files first, then check everything
#   tools/ci.sh --quick    skip the slow guards (OpenAPI deep validation, self-test, site build)
#
# Environment:
#   UCOS_PYTHON   interpreter to build the virtualenv from (default: python3)
#   UCOS_VENV     virtualenv directory (default: .venv)
#   BUF_BASE_REF  git ref for proto breaking-change detection (CI sets it; skipped when unset)
#   CI=true       makes optional tools (buf, node) mandatory
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
FIX=0; QUICK=0
for arg in "$@"; do
  case "$arg" in
    --fix) FIX=1 ;;
    --quick) QUICK=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done
IN_CI="${CI:-false}"
# Isolate from the caller's Python environment (a PYTHONPATH in a shell profile must not leak into CI).
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE
export PYTHONNOUSERSITE=1 PYTHONHASHSEED=0 LC_ALL=C.UTF-8 TZ=UTC
VENV="${UCOS_VENV:-.venv}"
FAILED=()
START=$(date +%s)

group() { if [[ "$IN_CI" == "true" ]]; then echo "::group::$1"; else printf '\n== %s\n' "$1"; fi; }
endgroup() { if [[ "$IN_CI" == "true" ]]; then echo "::endgroup::"; fi; }
run() {  # run <name> <command...>; records failure but keeps going so one run reports everything
  local name="$1"; shift
  group "$name"
  local t0=$(date +%s)
  if "$@"; then
    endgroup; printf '   ok    %-38s %3ss\n' "$name" "$(( $(date +%s) - t0 ))"
  else
    endgroup; printf '   FAIL  %-38s %3ss\n' "$name" "$(( $(date +%s) - t0 ))"
    FAILED+=("$name")
    if [[ "$IN_CI" == "true" ]]; then echo "::error title=$name::check failed (run tools/ci.sh locally for details)"; fi
  fi
}
need() {  # need <tool>: mandatory in CI, optional locally
  if command -v "$1" >/dev/null 2>&1; then return 0; fi
  if [[ "$IN_CI" == "true" ]]; then echo "required tool missing in CI: $1" >&2; exit 3; fi
  echo "   skip  $1 not installed (mandatory in CI)"; return 1
}

# ------------------------------------------------------------------ toolchain
group "Python toolchain (hash-locked)"
PYBASE="${UCOS_PYTHON:-python3}"
want="$(cat .python-version 2>/dev/null || true)"
have="$("$PYBASE" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
if [[ -n "$want" && "$want" != "$have" ]]; then
  echo "warning: .python-version is $want but $PYBASE is $have; the lock may not resolve" >&2
fi
if [[ ! -x "$VENV/bin/python" ]]; then "$PYBASE" -m venv "$VENV"; fi
PY="$VENV/bin/python"
stamp="$VENV/.lock-sha256"
lock_sha="$("$PY" -c 'import hashlib,sys; print(hashlib.sha256(open("tools/requirements.txt","rb").read()).hexdigest())')"
if [[ "$(cat "$stamp" 2>/dev/null || true)" != "$lock_sha" ]]; then
  "$PY" -m pip install --quiet --disable-pip-version-check --retries 5 --timeout 60 \
    --require-hashes --no-deps -r tools/requirements.txt
  echo "$lock_sha" > "$stamp"
fi
"$PY" -m pip check
endgroup

# ------------------------------------------------------------------ regenerate (optional)
if [[ "$FIX" == "1" ]]; then
  run "regenerate manifests"        "$PY" tools/gen_manifests.py
  run "regenerate registries"       "$PY" tools/gen_registries.py
  run "regenerate contracts"        "$PY" tools/gen_contracts.py
fi

# ------------------------------------------------------------------ checks
run "generated manifests in sync"   "$PY" tools/gen_manifests.py --check
run "generated registries in sync"  "$PY" tools/gen_registries.py --check
run "generated contracts in sync"   "$PY" tools/gen_contracts.py --check
run "spec consistency (ucos_check)" "$PY" tools/ucos_check.py
run "composition rules agree (closure.dl oracle)" "$PY" tools/datalog.py oracle
if [[ "$QUICK" == "1" ]]; then
  run "contracts, scenarios, SLOs"  "$PY" tools/validate_contracts.py --quick
else
  run "contracts, scenarios, SLOs"  "$PY" tools/validate_contracts.py
  run "guards fail on defects"      "$PY" tools/selftest.py
fi

if need buf; then
  run "proto lint (buf)" buf lint spec/api/proto
  if [[ -n "${BUF_BASE_REF:-}" ]] && git cat-file -e "${BUF_BASE_REF}:spec/api/proto/buf.yaml" 2>/dev/null; then
    run "proto breaking changes (buf)" buf breaking spec/api/proto --against ".git#ref=${BUF_BASE_REF},subdir=spec/api/proto"
  fi
fi

if [[ "$QUICK" == "0" ]] && need node; then
  build_site() {
    (cd tools/site && npm ci --silent --no-audit --no-fund && node build.mjs "$ROOT/generated/site")
  }
  run "site builds" build_site
  check_k6() { for f in tools/spikes/k6/*.js; do node --check "$f" || return 1; done; }
  run "spike load scripts parse" check_k6
fi

# ------------------------------------------------------------------ summary
echo
if (( ${#FAILED[@]} )); then
  echo "CI FAILED (${#FAILED[@]}): ${FAILED[*]}   [$(( $(date +%s) - START ))s]"
  [[ "$FIX" == "0" ]] && echo "hint: generated files stale? run tools/ci.sh --fix"
  exit 1
fi
echo "CI PASSED   [$(( $(date +%s) - START ))s]"
