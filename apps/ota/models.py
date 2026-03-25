# Infrastructure re-export for Django ORM auto-discovery.
# Django's app registry scans this file to find models.
# The actual model definition lives in the infrastructure layer.
from apps.ota.infrastructure.orm_models import AppUpdate  # noqa: F401

__all__ = ["AppUpdate"]
