#!/bin/bash
set -e
cd indexer-rs && maturin develop && cd ..
cd diff-rs && maturin develop && cd ..
cd fsops-rs && maturin develop && cd ..
