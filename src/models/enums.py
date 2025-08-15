from enum import Enum


class ProjectStatus(str, Enum):
    NEW = "NEW"
    DISCOVERY = "DISCOVERY"
    PLANNING = "PLANNING"
    DESIGN = "DESIGN"
    BUILD = "BUILD"
    TEST = "TEST"
    REVIEW = "REVIEW"
    DEPLOY = "DEPLOY"
    MONITOR = "MONITOR"
    DONE = "DONE"
    TEST_FAIL = "TEST_FAIL"
    ROLLBACK = "ROLLBACK"


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    DONE = "done"
