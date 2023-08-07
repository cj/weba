import icecream

icecream.install()

pytest_plugins = ["weba.test"]


def pytest_configure(config):  # type: ignore  # noqa: ARG001
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """


def pytest_sessionstart(session):  # type: ignore  # noqa: ARG001
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """


def pytest_sessionfinish(session, exitstatus):  # type: ignore  # noqa: ARG001
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """


def pytest_unconfigure(config):  # type: ignore  # noqa: ARG001
    """
    called before test process is exited.
    """
