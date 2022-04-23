import base64
import traceback
from io import StringIO

from PyQt6 import QtCore
from PyQt6.QtCore import QCoreApplication, QBuffer
from PyQt6.QtGui import QImage

from UM.Application import Application
from UM.Logger import Logger
from UM.Math.Matrix import Matrix

from cura.Snapshot import Snapshot
from cura.PreviewPass import PreviewPass

from .qoi import QOIEncoder


def render_scene():
    scene = Application.getInstance().getController().getScene()
    active_camera = scene.getActiveCamera()
    render_width, render_height = active_camera.getWindowSize()
    render_width = int(render_width)
    render_height = int(render_height)
    Logger.log("d", f"Found active camera with {render_width=} {render_height=}")

    QCoreApplication.processEvents()

    preview_pass = PreviewPass(render_width, render_height)
    fovy = 30
    satisfied = False
    zooms = 0
    while not satisfied and zooms < 5:
        preview_pass.render()
        pixel_output = preview_pass.getOutput().convertToFormat(QImage.Format.Format_ARGB32)
        # pixel_output.save(os.path.expanduser(f"~/Downloads/foo-a-zoom-{zooms}.png"), "PNG")

        min_x, max_x, min_y, max_y = Snapshot.getImageBoundaries(pixel_output)
        size = max((max_x - min_x) / render_width, (max_y - min_y) / render_height)
        if size > 0.5 or satisfied:
            satisfied = True
        else:
            # make it big and allow for some empty space around
            zooms += 1
            fovy *= 0.75
            projection_matrix = Matrix()
            projection_matrix.setPerspective(fovy, render_width / render_height, 1, 500)
            active_camera.setProjectionMatrix(projection_matrix)

        Logger.log("d", f"Rendered thumbnail: {zooms=}, {size=}, {min_x=}, {max_x=}, {min_y=}, {max_y=}, {fovy=}")

    # crop to content
    pixel_output = pixel_output.copy(min_x, min_y, max_x - min_x, max_y - min_y)
    Logger.log("d", f"Cropped thumbnail to {min_x}, {min_y}, {max_x - min_x}, {max_y - min_y}.")
    # pixel_output.save(os.path.expanduser("~/Downloads/foo-b-cropped.png"), "PNG")

    Logger.log("d", "Successfully rendered scene.")
    return pixel_output


def render_thumbnail(pixel_output, width, height):
    # scale to desired width and height
    pixel_output = pixel_output.scaled(
        width, height,
        aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        transformMode=QtCore.Qt.TransformationMode.SmoothTransformation
    )
    Logger.log("d", f"Scaled thumbnail to {width=}, {height=}.")
    # pixel_output.save(os.path.expanduser("~/Downloads/foo-c-scaled.png"), "PNG")

    # center image within desired width and height if one dimension is too small
    if pixel_output.width() < width:
        d = int((width - pixel_output.width()) / 2.)
        pixel_output = pixel_output.copy(-d, 0, width, pixel_output.height())
        Logger.log("d", f"Centered thumbnail horizontally {d=}.")
    if pixel_output.height() < height:
        d = int((height - pixel_output.height()) / 2.)
        pixel_output = pixel_output.copy(0, -d, pixel_output.width(), height)
        Logger.log("d", f"Centered thumbnail vertically {d=}.")
    # pixel_output.save(os.path.expanduser("~/Downloads/foo-d-aspect-fixed.png"), "PNG")

    Logger.log("d", f"Successfully rendered {width}x{height} thumbnail.")
    return pixel_output

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
    thumbnail_stream = StringIO()
    Logger.log("d", "Rendering thumbnail image...")
    try:
        scene = render_scene()

        # PanelDue: 480×272 (4.3" displays) or 800×480 pixels (5" and 7" displays)
        # ref https://forum.duet3d.com/post/270550 and https://forum.duet3d.com/post/270553
        thumbnail_sizes = [
            (48, 48),
            (128, 128),
            (160, 160),
            (256, 256),
        ]
        for width, height in thumbnail_sizes:
            thumbnail = render_thumbnail(scene, width, height)
            qoi_data = encode_as_qoi(thumbnail)
            b64_data = base64.b64encode(qoi_data).decode('ascii')
            b64_encoded_size = len(b64_data)

            thumbnail_stream.write(f"; thumbnail_QOI begin {width}x{height} {b64_encoded_size}\n")
            max_row_length = 78
            for i in range(0, b64_encoded_size, max_row_length):
                s = b64_data[i:i+max_row_length]
                thumbnail_stream.write(f"; {s}\n")
            thumbnail_stream.write(f"; thumbnail_QOI end\n")

        Logger.log("d", "Successfully encoded thumbnails as base64 into gcode comments.")

        return thumbnail_stream
    except Exception as e:
        Logger.log("e", "failed to create snapshot: " + str(e))
        Logger.log("e", traceback.format_stack())
        # continue without the QOI snapshot
        return StringIO()
