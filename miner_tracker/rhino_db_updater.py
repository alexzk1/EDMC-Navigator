from .database import DatabaseManager


class RhinoMiningDbUpdater:
    """
    Listens to the RhinoMiningEventDetector and tries to update DB if commodity/material was not manually entered.
    Once DB is complete, marks this point as exclusion zone.
    """

    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
