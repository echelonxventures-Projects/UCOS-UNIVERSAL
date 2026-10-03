#!/usr/bin/env bash
# Start deploy/local/compose.yaml and prove each service works. Used by the CI "devstack" job; runs locally
# with Docker. Tears everything down afterwards.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
C=(docker compose -f "$ROOT/deploy/local/compose.yaml" -p ucos-smoke)
trap '"${C[@]}" down -v >/dev/null 2>&1 || true' EXIT
"${C[@]}" up -d --wait --wait-timeout 300

echo "postgres: kernel schema applied with row-level security forced"
# Every tenant table has forced RLS (partitions are reached only through their parent).
want="kernel.audit_pending kernel.audit_records kernel.cmd_idempotency kernel.object_versions kernel.objects kernel.outbox kernel.triggers packs.sample_note"
got=$("${C[@]}" exec -T postgres psql -U postgres -d ucos -tAc \
  "SELECT string_agg(n.nspname || '.' || c.relname, ' ' ORDER BY n.nspname COLLATE "C", c.relname COLLATE "C") FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relforcerowsecurity AND NOT c.relispartition")
[[ "$got" == "$want" ]] || { echo "forced-RLS tables differ"; echo " want: $want"; echo " got:  $got"; exit 1; }

echo "redpanda: cluster healthy and a topic round-trips"
"${C[@]}" exec -T redpanda rpk topic create ucos.local.sample.note.v1 -p 3 >/dev/null
echo '{"type":"sample.note.created"}' | "${C[@]}" exec -T redpanda rpk topic produce ucos.local.sample.note.v1 >/dev/null
"${C[@]}" exec -T redpanda rpk topic consume ucos.local.sample.note.v1 -n 1 | grep -q 'sample.note.created'

echo "keycloak: dev realm imported and issues tokens"
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8180/realms/ucos-dev-sample/.well-known/openid-configuration || true)
  [[ "$code" == "200" ]] && break; sleep 3
done
[[ "$code" == "200" ]] || { echo "realm not served (HTTP $code)"; exit 1; }
token=$(curl -s -d grant_type=password -d client_id=ucos-gateway -d client_secret=dev-only-not-a-secret \
  -d username=asha -d password=asha-dev-password \
  http://localhost:8180/realms/ucos-dev-sample/protocol/openid-connect/token | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"][:10])')
[[ -n "$token" ]]

echo "temporal: frontend reachable"
for i in $(seq 1 60); do
  "${C[@]}" exec -T temporal temporal operator cluster health --address temporal:7233 2>/dev/null | grep -q SERVING && ok=1 && break
  sleep 3
done
[[ "${ok:-0}" == "1" ]] || { echo "temporal not serving"; exit 1; }
echo "devstack smoke: all services healthy"
