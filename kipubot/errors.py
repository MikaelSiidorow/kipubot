"""Custom exceptions for Kipubot."""


class NoEntriesError(Exception):
    """Raised when there are no entries in a raffle."""


class NoRaffleError(Exception):
    """Raised when there is no raffle in a chat."""


class AlreadyRegisteredError(Exception):
    """Raised when a user tries to register twice."""
