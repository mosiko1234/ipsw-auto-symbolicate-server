#!/bin/sh
set -e
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/ipsw || true 