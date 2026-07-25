import pytest

from .helpers import make_cross_domain_artifact


@pytest.fixture
def cross_domain_artifact():
    return make_cross_domain_artifact()
