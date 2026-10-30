"""Central registry importing all SQLModel table classes.

Ensures SQLAlchemy metadata is fully populated and bidirectional
Relationship back_populates mappers resolve cleanly across slices.
"""

# Import tables in dependency order
import server.modules.catalog.models  # noqa: F401
import server.modules.closure.models  # noqa: F401
import server.modules.identity.models  # noqa: F401
import server.modules.inventory.models  # noqa: F401
import server.modules.remitos.models  # noqa: F401
