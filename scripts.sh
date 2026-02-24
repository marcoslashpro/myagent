#!/usr/bin/bash


run_example() {
    echo -e "Installing dependencies...\n"
    uv sync --group examples && uv pip install -e .
    echo -e "Dependencies installed successfully.\n"
    uv run "examples/$1"
}

run_test() {
    echo -e "Syncing dependencies...\n"
    uv sync --group dev && uv pip install -e .
    echo -e "Dependencies installed successfully.\n"
    uv run pytest "$@"
}


case "$1" in
    run-example)
        run_example "$2"
        ;;
    run-tests)
        run_test "${@:2}"
        ;;
    *)
        echo "Unknown command \"$1\""
        ;;
esac