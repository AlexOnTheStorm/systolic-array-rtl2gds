#!/usr/bin/env bash
# Run the LibreLane Classic flow on flow/config.yaml inside the LibreLane Docker image.
#
#   ./run_flow.sh <run_tag> [KEY=VALUE ...]      # extra args become `-c KEY=VALUE` overrides
#   ./run_flow.sh r0_10ns CLOCK_PERIOD=10        # baseline (untuned)
#   ./run_flow.sh r1_14ns                        # tuned (CLOCK_PERIOD from config.yaml)
#
# Narrow bind mounts on purpose: this folder read-write, the gemm RTL folder read-only,
# the PDK in ~/.ciel. (`librelane --dockerized` mounts all of $HOME and crashed Docker
# Desktop on this Mac -- see env.md section 5.2.) Paths inside the container are identical
# to host paths, so `dir::` paths in config.yaml resolve the same way.
# Output: runs/<run_tag>/ (gitignored), <run_tag>.log, and one line appended to
# ../reports/walltime.txt.
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)                                  # practice/asic_rtl2gds
RTL=$(cd "$ROOT/../gemm_kernelgen/rtl" && pwd)                # read-only source
IMG=ghcr.io/librelane/librelane:3.0.17
TAG=${1:?usage: run_flow.sh <run_tag> [KEY=VALUE ...]}; shift
OVR=(); for kv in "$@"; do OVR+=(-c "$kv"); done

if [ -e "$HERE/runs/$TAG" ]; then
  echo "runs/$TAG already exists; pick another tag or delete it" >&2; exit 1
fi
mkdir -p "$ROOT/reports"
START=$(date +%s)
docker run --rm -i \
  -v "$ROOT:$ROOT" -v "$RTL:$RTL:ro" -v "$HOME/.ciel:$HOME/.ciel" -e PDK_ROOT="$HOME/.ciel" \
  -w "$HERE" "$IMG" \
  librelane --pdk sky130A --run-tag "$TAG" ${OVR[@]+"${OVR[@]}"} config.yaml > "$HERE/$TAG.log" 2>&1
RC=$?
WALL=$(( $(date +%s) - START ))
LINE="$(date '+%Y-%m-%d %H:%M') tag=$TAG overrides=[$*] rc=$RC wall_s=$WALL"
echo "$LINE" | tee -a "$ROOT/reports/walltime.txt"
exit $RC
