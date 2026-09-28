"""Errors with stable exit codes so scripts and agents can react precisely."""


class FMError(Exception):
    exit_code = 2


class ValidationFailed(FMError):
    exit_code = 1


class StateError(FMError):
    """The requested transition is not allowed in the current state."""

    exit_code = 2


class AuthorityError(FMError):
    """The actor is not allowed to perform this action (e.g. an agent approving)."""

    exit_code = 3


class BlenderVersionError(FMError):
    exit_code = 4


class IntegrityError(FMError):
    """Ledger/state tampering or a locked decision changed without approval."""

    exit_code = 5
