# CRUD REST API with FastAPI and AWS

A production-ready REST API built with FastAPI and AWS services. This project demonstrates cloud-native Python development with automated testing, CI pipelines.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Development](#development)
  - [Dependency Management](#dependency-management)
  - [Code Quality Tools](#code-quality-tools)
  - [Scripts](#scripts)
- [Testing](#testing)
- [Local Development](#local-development)
- [Deployment](#deployment)
  - [AWS Lambda Deployment](#aws-lambda-deployment)
- [CI/CD](#cicd)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This API provides CRUD operations for file management, leveraging AWS services:

- Lambda for serverless compute
- API Gateway for API management
- S3 for object storage
- FastAPI for the web framework

## Features

- **RESTful API Endpoints**: Complete CRUD operations for file management
- **AWS Integration**: Serverless architecture using Lambda, API Gateway, and S3
- **OpenAPI Documentation**: Auto-generated API documentation with FastAPI
- **Container Support**: Docker configurations for both development and Lambda deployment
- **Comprehensive Testing**: Unit tests with pytest and load testing with Locust
- **Type Safety**: Static type checking with MyPy
- **Code Quality**: Automated linting and formatting with pre-commit hooks

## Prerequisites

Core requirements:

- uv (Python 3.11+)
- Make/CMake
- Docker
- AWS CLI (configured with appropriate credentials)
- Git

## Getting Started

- **Clone for development**:

```bash
git clone https://github.com/ArturMakowski/cloud-engineering-AWS.git
cd cloud-engineering-AWS
make install
```

## Development

### Dependency Management

The project uses modern Python tooling:

- `pyproject.toml` for project metadata and dependencies
- Dependency groups for different purposes:
  - `test`: Testing tools
  - `qa`: Code quality tools
  - `dev`: Development utilities
  - `aws-lambda`: Lambda-specific dependencies

### Code Quality Tools

Automated checks run on every commit via pre-commit hooks:

```bash
make lint
```

### Scripts

Key utility scripts:

- `scripts/generate-openapi.py`: Generates OpenAPI schema
- `run.sh`: Contains deployment and utility functions:

  ```bash
  make help  # List all available commands
  ```

## Testing

Run the test suite:

```bash
# Run all unit tests
make test

# Load testing with Locust
make run-locust
```

Tests include:

- Unit tests with pytest
- Integration tests with moto (AWS mocking)
- Load testing with Locust
- Coverage reporting

## Local Development

```bash
make run-mock
```

## Deployment

### AWS Lambda Deployment

```bash
make deploy-lambda
```

The deployment process:

1. Builds dependencies with `uv` in a Lambda-compatible container
2. Creates a Lambda layer for dependencies
3. Packages application code
4. Updates Lambda function and layer

## CI/CD

The project uses GitHub Actions for:

- Running tests on wheel builds
- Code quality checks
- Generating and validating OpenAPI documentation
