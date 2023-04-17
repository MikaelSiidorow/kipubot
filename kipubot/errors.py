"""Custom exceptions for Kipubot."""


class NoEntriesError(Exception):
    """Raised when there are no entries in a raffle."""

    pass


class NoRaffleError(Exception):
    """Raised when there is no raffle in a chat."""

    pass


class AlreadyRegisteredError(Exception):
    """Raised when a user tries to register twice."""

    pass
