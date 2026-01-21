import kopf
import yaml
from dataclasses import asdict
from deepdiff import DeepDiff
from kubesdk import get_k8s_resource
from kube_models.api_v1.io.k8s.api.core.v1 import ConfigMap, Secret
from authentik.blueprints.v1.importer import Importer
from authentik.tenants.models import Tenant
from datetime import datetime
import base64
from asgiref.sync import sync_to_async

from .helper import transpile_to_yaml_tags, BlueprintDumper
from .models.blueprints import (
    BlueprintSpec,
    BlueprintStatusEnum,
    BlueprintEntryState,
    ContextFromSource,
)


async def get_context(blueprint_spec: BlueprintSpec, namespace: str):
    context = blueprint_spec.context

    for contextFrom in blueprint_spec.contextFrom:
        contextFrom = ContextFromSource(**contextFrom)
        if contextFrom.configMapRef is not None:
            configMap = await get_k8s_resource(
                ConfigMap,
                namespace=namespace,
                name=contextFrom.configMapRef["name"],
            )

            if configMap.data is not None:
                context |= configMap.data

            if configMap.binaryData is not None:
                context |= configMap.binaryData

        if contextFrom.secretRef is not None:
            secret = await get_k8s_resource(
                Secret,
                namespace=namespace,
                name=contextFrom.secretRef["name"],
            )

            if secret.data is not None:
                context |= {
                    k: base64.b64decode(v).decode() for k, v in secret.data.items()
                }

    return context


async def get_blueprint_yaml(
    blueprint_spec: BlueprintSpec, name: str, labels: kopf.Labels, namespace: str
) -> str:
    spec = asdict(blueprint_spec)

    transpiled_data = transpile_to_yaml_tags(spec)

    transpiled_data["enabled"] = spec.get("enabled")
    transpiled_data["context"] = await get_context(
        blueprint_spec=blueprint_spec, namespace=namespace
    )
    transpiled_data["metadata"] = {"name": name, "labels": dict(labels)}

    yaml_payload = yaml.dump(
        transpiled_data,
        sort_keys=False,
        Dumper=BlueprintDumper,
    )

    return yaml_payload


def set_status(patch: kopf.Patch, status: BlueprintStatusEnum):
    patch.status["status"] = status.value
    patch.status["last_applied"] = datetime.now().isoformat(sep="T") + "Z"


@sync_to_async
def apply_blueprint(
    yaml_blueprint: str, name: str, logger: kopf.Logger
) -> BlueprintStatusEnum:
    for tenant in Tenant.objects.filter(ready=True):
        with tenant:
            importer = Importer.from_string(yaml_blueprint)

            valid, logs = importer.validate()
            if not valid:
                logger.error(f"Blueprint {name} invalid:")
                for log in logs:
                    logger.error(f"\t{log.logger}: {log.event}: {log.attributes}")

                return BlueprintStatusEnum.ERROR

            importer.apply()

    return BlueprintStatusEnum.SUCCESSFUL


@kopf.timer("blueprints", interval=10)
@kopf.on.create("blueprints")
async def create_fn(
    spec: kopf.Spec,
    name: str,
    namespace: str,
    labels: kopf.Labels,
    logger: kopf.Logger,
    patch: kopf.Patch,
    **kwargs,
):
    try:
        blueprint_spec = BlueprintSpec(**spec)
        if not blueprint_spec.enabled:
            set_status(patch=patch, status=BlueprintStatusEnum.SUCCESSFUL)
            return

        yaml_payload = await get_blueprint_yaml(
            blueprint_spec=blueprint_spec, name=name, labels=labels, namespace=namespace
        )

        res = await apply_blueprint(
            yaml_blueprint=yaml_payload, name=name, logger=logger
        )
        set_status(patch=patch, status=res)
    except Exception as e:
        set_status(patch=patch, status=BlueprintStatusEnum.ERROR)

        raise e


@kopf.on.delete("blueprints")
async def delete_fn(
    spec: kopf.Spec,
    name: str,
    namespace: str,
    labels: kopf.Labels,
    logger: kopf.Logger,
    patch: kopf.Patch,
    **kwargs,
):
    try:
        blueprint_spec = BlueprintSpec(**spec)
        if not blueprint_spec.enabled:
            set_status(patch=patch, status=BlueprintStatusEnum.SUCCESSFUL)
            return

        for entry in blueprint_spec.entries:
            state = entry.get("state")
            if (
                state is None
                or state == BlueprintEntryState.CREATED.value
                or state == BlueprintEntryState.MUST_CREATED.value
            ):
                entry["state"] = BlueprintEntryState.ABSENT.value

        yaml_payload = await get_blueprint_yaml(
            blueprint_spec=blueprint_spec, name=name, labels=labels, namespace=namespace
        )

        res = await apply_blueprint(
            yaml_blueprint=yaml_payload, name=name, logger=logger
        )
        set_status(patch=patch, status=res)
    except Exception as e:
        set_status(patch=patch, status=BlueprintStatusEnum.ERROR)
        raise e


@kopf.on.update("blueprints")
async def update_entries_fn(
    spec: kopf.Spec,
    name: str,
    namespace: str,
    labels: kopf.Labels,
    logger: kopf.Logger,
    patch: kopf.Patch,
    diff: kopf.Diff,
    **kwargs,
):
    try:
        blueprint_spec = BlueprintSpec(**spec)
        if not blueprint_spec.enabled:
            set_status(patch=patch, status=BlueprintStatusEnum.SUCCESSFUL)
            return

        for d in diff:
            if d.field != ("spec", "entries"):
                return

            match d.op:
                case kopf.DiffOperation.ADD:
                    # Process normaly
                    pass
                case kopf.DiffOperation.CHANGE:
                    # Check if entries is modified
                    new_identifies = [
                        (entry["model"], dict(entry.get("identifiers")))
                        for entry in d.new
                    ]

                    for old_entry in d.old:
                        identifier = dict(old_entry.get("identifiers"))

                        if (old_entry["model"], identifier) not in new_identifies:
                            state = old_entry.get("state")
                            if (
                                state is None
                                or state == BlueprintEntryState.CREATED.value
                                or state == BlueprintEntryState.MUST_CREATED.value
                            ):
                                old_entry["state"] = BlueprintEntryState.ABSENT.value

                                blueprint_spec.entries.append(old_entry)

                    # Check if values of entry is removed and warn
                    deep_diff = DeepDiff(d.old, d.new)
                    dictionary_item_removed = deep_diff.get("dictionary_item_removed")
                    if dictionary_item_removed is not None:
                        for d in dictionary_item_removed:
                            logger.warning(
                                f"Values removed at {d}, it will stay the same value!"
                            )

                case kopf.DiffOperation.REMOVE:
                    # Remove all with state
                    for old_entry in d.old:
                        state = old_entry.get("state")
                        if (
                            state is None
                            or state == BlueprintEntryState.CREATED.value
                            or state == BlueprintEntryState.MUST_CREATED.value
                        ):
                            old_entry["state"] = BlueprintEntryState.ABSENT.value

                            blueprint_spec.entries.append(old_entry)

        yaml_payload = await get_blueprint_yaml(
            blueprint_spec=blueprint_spec, name=name, labels=labels, namespace=namespace
        )

        res = await apply_blueprint(
            yaml_blueprint=yaml_payload, name=name, logger=logger
        )
        set_status(patch=patch, status=res)
    except Exception as e:
        set_status(patch=patch, status=BlueprintStatusEnum.ERROR)
        raise e
