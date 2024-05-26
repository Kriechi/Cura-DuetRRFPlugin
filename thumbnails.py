import base64
import traceback
from io import StringIO

try: # Cura 5
    from PyQt6 import QtCore
    from PyQt6.QtCore import QCoreApplication, QBuffer
    from PyQt6.QtGui import QImage
except: # Cura 4
    from PyQt5 import QtCore
    from PyQt5.QtCore import QCoreApplication, QBuffer
    from PyQt5.QtGui import QImage

from UM.Logger import Logger

from cura.Snapshot import Snapshot

from .qoi import QOIEncoder
from . import DuetRRFSettings


def encode_as_qoi(thumbnail):
    # https://qoiformat.org/qoi-specification.pdf
    pixels = [thumbnail.pixel(x, y) for y in range(thumbnail.height()) for x in range(thumbnail.width())]
    pixels = [(unsigned_p ^ (1 << 31)) - (1 << 31) for unsigned_p in pixels]
    encoder = QOIEncoder()
    r = encoder.encode(
        width=thumbnail.width(),
        height=thumbnail.height(),
        pixels=pixels,
        alpha=thumbnail.hasAlphaChannel(),
        linear_colorspace=False
    )
    if not r:
        raise ValueError("image size unsupported")
    Logger.log("d", f"Successfully encoded {thumbnail.width()}x{thumbnail.height()} thumbnail in QOI format.")

    size = encoder.get_encoded_size()
    return encoder.get_encoded()[:size]

def encode_as_png(thumbnail):
    buffer = QBuffer()
    buffer.open(QBuffer.ReadWrite)
    thumbnail.save(buffer, "PNG")
    buffer.close()
    return buffer.data()

def generate_thumbnail():
    config: dict = DuetRRFSettings.get_config()
    if not config.get("embed_thumbnails", True):
        Logger.log("d", "Skipping thumbnail embedding because its not enabled for this printer.")
        return
    raw_sizes: str = config.get("thumbnail_sizes", "").lower().strip()
    sizes = DuetRRFSettings.DEFAULT_THUMBNAIL_SIZES
    if raw_sizes == "none" or raw_sizes == "no" or raw_sizes == "false":
        Logger.log("d", f"Skipping thumbnail embedding because no valid sizes defined for this printer. Found value: {raw_sizes}")
        return
    elif raw_sizes == "":
        Logger.log("d", f"Using default thumbnail sizes.")
    else:
        try:
            sizes = [s.strip().split("x", 1) for s in raw_sizes.strip().split(",")]
            sizes = [(int(w), int(h)) for w, h in sizes]
        except:
            Logger.log("d", f"Using default thumbnail sizes. Failed to parse config value: {raw_sizes}")


    thumbnail_stream = StringIO()
    Logger.log("d", f"Rendering thumbnail image in sizes: {sizes}")

    for width, height in sizes:
        try:
            thumbnail = Snapshot.snapshot(width=width, height=height)
            if thumbnail is None:
                Logger.log("d", f"Skipping failed {width}x{height} thumbnail.")
                continue

            qoi_data = encode_as_qoi(thumbnail)
            b64_data = base64.b64encode(qoi_data).decode('ascii')
            b64_encoded_size = len(b64_data)

            thumbnail_stream.write(f"; thumbnail_QOI begin {width}x{height} {b64_encoded_size}\n")
            max_row_length = 78
            for i in range(0, b64_encoded_size, max_row_length):
                s = b64_data[i:i+max_row_length]
                thumbnail_stream.write(f"; {s}\n")
            thumbnail_stream.write(f"; thumbnail_QOI end\n")

            Logger.log("d", f"Successfully embedded {width}x{height} thumbnail as base64 into gcode comments.")
        except Exception as e:
            Logger.log("e", "failed to create snapshot: " + str(e))
            Logger.log("e", traceback.format_stack())
            # continue without this QOI snapshot
            continue

    return thumbnail_stream
