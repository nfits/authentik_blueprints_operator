from kubesdk.crd import (
    CustomK8sResourceDefinition,
    CustomK8sResource,
    crd_field,
    CRDFieldSpec,
)
from kube_models import Loadable
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class BlueprintStatusEnum(str, Enum):
    SUCCESSFUL = "successful"
    WARNING = "warning"
    ERROR = "error"
    ORPHANED = "orphaned"
    UNKNOWN = "unknown"


class BlueprintVersion(int, Enum):
    V1 = 1


class BlueprintEntryState(str, Enum):
    ABSENT = "absent"
    CREATED = "created"
    MUST_CREATED = "must_created"
    PRESENT = "present"


@dataclass(kw_only=True, frozen=True, slots=True)
class BlueprintEntry(Loadable):
    model: str = crd_field(spec=CRDFieldSpec())

    id: Optional[str] = crd_field(spec=CRDFieldSpec())
    state: Optional[BlueprintEntryState] = crd_field(
        spec=CRDFieldSpec(
            enum=[s.value for s in BlueprintEntryState],
        )
    )
    conditions: Optional[List[Any]] = crd_field(spec=CRDFieldSpec())
    permissions: Optional[List[Any]] = crd_field(
        spec=CRDFieldSpec(x_kubernetes_preserve_unknown_fields=True)
    )
    attrs: Optional[Any] = crd_field(
        spec=CRDFieldSpec(x_kubernetes_preserve_unknown_fields=True)
    )
    identifiers: Optional[Any] = crd_field(
        spec=CRDFieldSpec(x_kubernetes_preserve_unknown_fields=True)
    )


@dataclass(slots=True, kw_only=True, frozen=True)
class ConfigMapContextSource(Loadable):
    name: str = crd_field(spec=CRDFieldSpec())


@dataclass(slots=True, kw_only=True, frozen=True)
class SecretContextSource(Loadable):
    name: str = crd_field(spec=CRDFieldSpec())


@dataclass(slots=True, kw_only=True, frozen=True)
class ContextFromSource(Loadable):
    configMapRef: Optional[ConfigMapContextSource] = crd_field(
        spec=CRDFieldSpec(), default=None
    )
    prefix: str = crd_field(spec=CRDFieldSpec(default=""))
    secretRef: Optional[SecretContextSource] = crd_field(
        spec=CRDFieldSpec(), default=None
    )


@dataclass(kw_only=True, frozen=True, slots=True)
class BlueprintSpec(Loadable):
    version: int = crd_field(
        spec=CRDFieldSpec(
            default=BlueprintVersion.V1.value,
            enum=[s.value for s in BlueprintVersion],
            description="Blueprint version",
        )
    )

    context: Optional[Any] = crd_field(
        spec=CRDFieldSpec(default={}, x_kubernetes_preserve_unknown_fields=True)
    )
    contextFrom: List[ContextFromSource] = crd_field(spec=CRDFieldSpec(default=[]))

    entries: List[BlueprintEntry] = crd_field(spec=CRDFieldSpec(default=[]))

    enabled: bool = crd_field(spec=CRDFieldSpec(default=True))


@dataclass(kw_only=True, frozen=True, slots=True)
class BlueprintStatus(Loadable):
    status: BlueprintStatusEnum = crd_field(
        spec=CRDFieldSpec(
            default=BlueprintStatusEnum.UNKNOWN.value,
            enum=[s.value for s in BlueprintStatusEnum],
        )
    )

    last_applied: Optional[str] = crd_field(
        spec=CRDFieldSpec(type="string", format="date-time")
    )


@dataclass(kw_only=True, frozen=True, slots=True)
class BlueprintV1Alpha1(CustomK8sResource):
    is_namespaced_ = True
    group_ = "cscg.live"
    plural_ = "blueprints"

    apiVersion = f"{group_}/v1alpha1"
    kind = "Blueprint"

    spec: BlueprintSpec

    status: BlueprintStatus


@dataclass
class BlueprintCRD(CustomK8sResourceDefinition):
    versions = [BlueprintV1Alpha1]
    crd_short_names_ = ["bp"]
    crd_singular_ = "blueprint"
