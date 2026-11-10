"""A simple in-memory cache for video nonce tokens."""

import asyncio
from asyncio import Lock
from dataclasses import dataclass, field
from datetime import UTC, datetime

from pisec_server.core.exceptions import RecordAlreadyExistsError
from pisec_server.core.models.nonceable import Nonceable


@dataclass(frozen=True)
class NonceEntry:
    """Contains expiry datetime for a token that is linked to a nonce."""

    expires_at: datetime


@dataclass(frozen=True)
class InMemoryVideoNonceStore:
    """A simple in-memory cache for video nonce tokens.

    Should be replaced with a better solution like redis in the future.
    """

    _nonces: dict[str, NonceEntry] = field(default_factory=dict[str, NonceEntry])
    _lock: Lock = field(default_factory=lambda: asyncio.Lock())

    async def nonce_exists(self, nonce: str) -> bool:
        """Checks if a given nonce exists in the cache.

        Additionally purges any expired nonces from the cache.
        """
        await self.purge_expired()

        async with self._lock:
            return nonce in self._nonces

    async def consume_nonce(self, nonceable: Nonceable) -> None:
        """Marks a given nonce as used so callers can track them.

        Additionally purges any expired nonces from the cache.

        Raises:
            RecordAlreadyExistsError: If the nonce was already marked as used.
        """
        await self.purge_expired()

        async with self._lock:
            if nonceable.nonce in self._nonces:
                raise RecordAlreadyExistsError("Nonce already exists!")

            self._nonces[nonceable.nonce] = NonceEntry(nonceable.expires_at)

    async def purge_expired(self) -> None:
        """Removes expired nonces from the cache."""
        async with self._lock:
            current_time = datetime.now(UTC)
            expired_nonces = [nonce for nonce, entry in self._nonces.items() if entry.expires_at < current_time]

            for nonce in expired_nonces:
                del self._nonces[nonce]


# A global singleton nonce store
nonce_store = InMemoryVideoNonceStore()
