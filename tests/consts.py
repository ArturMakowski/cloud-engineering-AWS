"""Constant values used for tests."""

import uuid
from pathlib import Path

THIS_DIR = Path(__file__).parent
PROJECT_DIR = (THIS_DIR / "../").resolve()
TEST_BUCKET_NAME = f"test-cloud-course-bucket-artur-{str(uuid.uuid4())[:5]}"
