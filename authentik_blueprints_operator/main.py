import kopf
import logging
from kubesdk import login
import asyncio
from .blueprints import *


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.WARNING


async def run():
    await login()

    await kopf.operator(
        clusterwide=False,
        namespace="authentik",
    )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
