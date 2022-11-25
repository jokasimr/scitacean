# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from __future__ import annotations
from typing import Optional
import uuid


class PID:
    """Stores the ID of database item.

    The ID is split into a prefix and the main identifier.
    The prefix identifies an instance of SciCat and the main identifier a dataset.

    The two components are merged using a "/", i.e.

    .. code-block:: python

        full_id = PID.prefix + '/' + PID.pid

    Equivalently, ``str`` can be used to construct the full id:

    .. code-block:: python

        full_id = str(PID)
    """

    __slots__ = ("_pid", "_prefix")

    def __init__(self, *, pid: str, prefix: Optional[str] = None):
        """

        Parameters
        ----------
        pid:
            Main part of the ID which uniquely identifies a dataset.
        prefix:
            Identifies the instance of SciCat.
        """
        self._pid = pid
        self._prefix = prefix

    @classmethod
    def parse(cls, x: str) -> PID:
        """Build a PID from a string.

        The string is split at the first "/" to determine
        prefix and main ID.
        This means that it only works if the prefix and main ID do
        not contain any slashes.

        Parameters
        ----------
        x:
            String holding an ID with or without prefix.

        Returns
        -------
        :
            A new PID object constructed from ``x``.
        """
        pieces = x.split("/", 1)
        if len(pieces) == 1:
            return PID(pid=pieces[0], prefix=None)
        return PID(prefix=pieces[0], pid=pieces[1])

    @classmethod
    def generate(cls, *, prefix: Optional[str] = None) -> PID:
        """Create a new unique PID.

        Uses UUID4 to generate the ID.

        Parameters
        ----------
        prefix:
            If given, the returned PID has this prefix.

        Returns
        -------
        :
            A new PID object.
        """
        return PID(prefix=prefix, pid=str(uuid.uuid4()))

    @property
    def pid(self) -> str:
        """Main part of the ID."""
        return self._pid

    @property
    def prefix(self) -> Optional[str]:
        """Prefix part of the ID if there is one."""
        return self._prefix

    @property
    def without_prefix(self) -> PID:
        """Return a new PID with the prefix set to None."""
        return PID(pid=self.pid, prefix=None)

    def __str__(self):
        if self.prefix is not None:
            return self.prefix + "/" + self.pid
        return self.pid

    def __repr__(self):
        return f"PID(prefix={self.prefix}, pid={self.pid})"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, PID):
            return False
        return self.prefix == other.prefix and self.pid == other.pid

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value) -> PID:
        if isinstance(value, str):
            return PID.parse(value)
        return value