import logging
from pathlib import Path

import akflib.rendering.core as render
from akflib.rendering.objs import AKFBundle

from akf_windows.api.artifacts import WindowsArtifactServiceAPI
from akf_windows.api.chromium import ChromiumServiceAPI

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

bundle = AKFBundle()


with ChromiumServiceAPI.auto_connect("192.168.50.4") as service:
    # with ChromiumServiceAPI.auto_connect("localhost") as service:
    history = service.get_history("msedge")

    # just keep the first 10 entries
    # facet.urlHistoryEntry = facet.urlHistoryEntry[:10]

    # print(history)
    bundle.add_object(history)

with WindowsArtifactServiceAPI.auto_connect("192.168.50.4") as service_2:
    # with WindowsArtifactServiceAPI.auto_connect("localhost") as service_2:
    prefetch_objs = service_2.collect_prefetch_dir()

    # just keep the first 10 entries
    # prefetch_objs = prefetch_objs[:10]

    bundle.add_objects(prefetch_objs)

renderer_paths = [
    "akflib.renderers.prefetch.PrefetchRenderer",
    "akflib.renderers.urlhistory.URLHistoryRenderer",
]

renderers = render.get_renderer_classes(renderer_paths)
pandoc_path = render.get_pandoc_path()
if not pandoc_path:
    logger.error("Pandoc is not installed or not found in the system PATH.")
    exit(1)

# result = render.render_bundle(bundle, renderers, Path("."))
# for x in result.values():
#     print(x)

render.bundle_to_pdf(
    bundle,
    renderers,
    Path("./playground"),
    pandoc_path,
    False,
)
