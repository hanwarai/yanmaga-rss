#!/usr/bin/env sh
# pyproject.toml の [dependency-groups] ci にピンした uv 本体のバージョンを解決し、
# GitHub Actions の $GITHUB_OUTPUT 形式 ("version=X.Y.Z") で標準出力に出す。
#
# ci.yaml と gh-pages.yaml の両方がこれを使う。ピン読み取りの契約を一箇所に集約し、
# ワークフロー間でロジックがドリフトするのを防ぐ目的。
#
# grep -P は GNU 限定で macOS では動かないため、ローカルでも試せるよう POSIX sed で書いている。
set -eu

pyproject="${1:-pyproject.toml}"

version=$(sed -n 's/.*"uv==\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)".*/\1/p' "$pyproject" | head -n 1)

if [ -z "$version" ]; then
  echo "could not resolve uv version pin from $pyproject" >&2
  exit 1
fi

echo "version=$version"
