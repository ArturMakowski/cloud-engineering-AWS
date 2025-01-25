#!/bin/bash

set -e

#####################
# --- Constants --- #
#####################

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
MINIMUM_TEST_COVERAGE_PERCENT=0


##########################
# --- Task Functions --- #
##########################

# start the FastAPI app, enabling hot reload on save (assuming aws_python packages is installed)
function run {
    AWS_PROFILE=aws-course-sso \
    S3_BUCKET_NAME="test-bucket" \
    uv run uvicorn src.aws_python.main:create_app --reload  --factory
}

# start the FastAPI app, pointed at a mocked aws endpoint
function run-mock {
    set +e

    # Start moto.server in the background on localhost:5000
    uv run python -m moto.server -p 5001 &
    MOTO_PID=$!


    # point the AWS CLI and boto3 to the mocked AWS server using mocked credentials
    export AWS_ENDPOINT_URL="http://localhost:5001"
    export AWS_SECRET_ACCESS_KEY="mock" # pragma: allowlist secret
    export AWS_ACCESS_KEY_ID="mock"
    export AWS_DEFAULT_REGION="us-east-1"
    export S3_BUCKET_NAME="test-bucket"

    # create a bucket called "some-bucket" using the mocked aws server
    aws s3 mb "s3://$S3_BUCKET_NAME"

    #######################################
    # --- Mock OpenAI with mockserver --- #
    #######################################

    OPENAI_MOCK_PORT=5002 python tests/mocks/openai_fastapi_mock_app.py &
    OPENAI_MOCK_PID=$!

    # point the OpenAI SDK to the mocked OpenAI server using mocked credentials
	export OPENAI_BASE_URL="http://localhost:${OPENAI_MOCK_PORT}"
	export OPENAI_API_KEY="mocked_key" # pragma: allowlist secret

    ###########################################################
    # --- Schedule the mocks to shut down on FastAPI Exit --- #
    ###########################################################

    # schedule: when uvicorn stops, kill the moto.server and mocked open-ai server process
    trap 'kill $MOTO_PID; kill $OPENAI_MOCK_PID' EXIT

    # Set AWS endpoint URL and start FastAPI app with uvicorn in the foreground
    uv run uvicorn src.aws_python.main:create_app --reload --factory

    # Wait for the moto.server process to finish (this is optional if you want to keep it running)
    wait $MOTO_PID
    wait $OPENAI_MOCK_PID
}

# start the FastAPI app, enabling hot reload on save (assuming aws_python packages is not installed)
function run-py {
    AWS_PROFILE=aws-course-sso \
    S3_BUCKET_NAME="test-bucket" \
    PYTHONPATH="${THIS_DIR}/src" \
    uv run uvicorn src.aws_python.main:create_app --reload  --factory
}

# install core and development Python dependencies into the currently activated venv
function install {
    uv sync --group dev --group test --group qa
}

# run linting, formatting, and other static code quality tools
function lint {
    uv run pre-commit run --color=always --all-files
}

# same as `lint` but with any special considerations for CI
function lint:ci {
    # We skip no-commit-to-branch since that blocks commits to `main`.
    # All merged PRs are commits to `main` so this must be disabled.
    SKIP=no-commit-to-branch uv run pre-commit run --color=always --all-files
}

# execute tests that are not marked as `slow`
function test:quick {
    run-tests -m "not slow" ${@:-"$THIS_DIR/tests/"}
}

# execute tests against the installed package; assumes the wheel is already installed
function test:ci {
    INSTALLED_PKG_DIR="$(uv run python -c 'import aws_python; print(aws_python.__path__[0])')"
    # in CI, we must calculate the coverage for the installed package, not the src/ folder
    COVERAGE_DIR="$INSTALLED_PKG_DIR" run-tests
}

# (example) ./run.sh test tests/test_states_info.py::test__slow_add
function run-tests {
    PYTEST_EXIT_STATUS=0

    # clean the test-reports dir
    rm -rf "$THIS_DIR/test-reports" || mkdir "$THIS_DIR/test-reports"

    # execute the tests, calculate coverage, and generate coverage reports in the test-reports dir
    uv run pytest ${@:-"$THIS_DIR/tests/"} \
        --cov "${COVERAGE_DIR:-$THIS_DIR/src}" \
        --cov-report html \
        --cov-report term \
        --cov-report xml \
        --junit-xml "$THIS_DIR/test-reports/report.xml" \
        --cov-fail-under "$MINIMUM_TEST_COVERAGE_PERCENT" || ((PYTEST_EXIT_STATUS+=$?))
    mv coverage.xml "$THIS_DIR/test-reports/" || true
    mv htmlcov "$THIS_DIR/test-reports/" || true
    mv .coverage "$THIS_DIR/test-reports/" || true
    return $PYTEST_EXIT_STATUS
}

function test:wheel-locally {
    rm -rf test-env || true
    uv venv test-env
    clean || true
    uv build
    uv pip install ./dist/*.whl pytest pytest-cov --python test-env
    test:ci
    rm -rf test-env || true
}

# serve the html test coverage report on localhost:8000
function serve-coverage-report {
    uv run python -m http.server --directory "$THIS_DIR/test-reports/htmlcov/" 8000
}

# build a wheel and sdist from the Python source code
function build {
    uv build --sdist --wheel "$THIS_DIR/"
}

function release:test {
    lint
    clean
    build
    publish:test
}

function release:prod {
    release:test
    publish:prod
}

function publish:test {
    try-load-dotenv || true
    twine upload dist/* \
        --repository testpypi \
        --username=__token__ \
        --password="$TEST_PYPI_TOKEN"
}

function publish:prod {
    try-load-dotenv || true
    twine upload dist/* \
        --repository pypi \
        --username=__token__ \
        --password="$PROD_PYPI_TOKEN"
}

# remove all files generated by tests, builds, or operating this codebase
function clean {
    rm -rf dist build coverage.xml test-reports
    find . \
      -type d \
      \( \
        -name "*cache*" \
        -o -name "*.dist-info" \
        -o -name "*.egg-info" \
        -o -name "*htmlcov" \
      \) \
      -not -path "*env/*" \
      -exec rm -r {} + || true

    find . \
      -type f \
      -name "*.pyc" \
      -not -path "*env/*" \
      -exec rm {} +
}

# export the contents of .env as environment variables
function try-load-dotenv {
    if [ ! -f "$THIS_DIR/.env" ]; then
        echo "no .env file found"
        return 1
    fi

    while read -r line; do
        export "$line"
    done < <(grep -v '^#' "$THIS_DIR/.env" | grep -v '^$')
}

# print all functions in this file
function help {
    echo "$0 <task> <args>"
    echo "Tasks:"
    compgen -A function | cat -n
}

TIMEFORMAT="Task completed in %3lR"
time ${@:-help}
