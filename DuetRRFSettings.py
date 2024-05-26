import json
import os

from UM.Logger import Logger

from cura.CuraApplication import CuraApplication

DUETRRF_SETTINGS = "duetrrf/instances"

# PanelDue firmware v3.5.0:
# ref https://forum.duet3d.com/post/270550 and https://forum.duet3d.com/post/270553

# Display X = 480
# >>> rowTextHeight = 21 ; 7 * rowTextHeight + (2 * rowTextHeight) / 3
# 161.0
# >>> margin = 2 ; fullPopupWidth = 480 - (2 * margin) ; fileInfoPopupWidth = fullPopupWidth - (4 * margin) ; fileInfoPopupWidth / 3 + 5;
# 161.0

# Display X = 800
# >>> rowTextHeight = 32 ; 7 * rowTextHeight + (2 * rowTextHeight) / 3
# 245.33333333333334
# >>> margin = 4 ; fullPopupWidth = 800 - (2 * margin) ; fileInfoPopupWidth = fullPopupWidth - (4 * margin) ; fileInfoPopupWidth / 3 + 5;
# 263.6666666666667

DEFAULT_THUMBNAIL_SIZES = [
    (48, 48), # DuetWebControl Job File List table icon
    # (160, 160), # PanelDue 4.3" (not supporting thumbnails currently, DISPLAY_X=480)
    (240, 240), # PanelDue 5" and 7" (both have DISPLAY_X=800)
    (320, 320), # DuetWebContol Job File List expanded hover image (largest available thumbnail gets chosen)
]
DEFAULT_THUMBNAIL_SIZES_STR = ",".join([f"{w}x{h}" for w, h in DEFAULT_THUMBNAIL_SIZES])

def _load_prefs():
    application = CuraApplication.getInstance()
    global_container_stack = application.getGlobalContainerStack()
    if not global_container_stack:
        return {}, None
    printer_id = global_container_stack.getId()
    p = application.getPreferences()
    s = json.loads(p.getValue(DUETRRF_SETTINGS))
    return s, printer_id

def init_settings():
    application = CuraApplication.getInstance()
    p = application.getPreferences()
    p.addPreference(DUETRRF_SETTINGS, json.dumps({}))

def get_config() -> dict:
    s, printer_id = _load_prefs()
    if printer_id in s:
        config = s[printer_id]

        # migrate to the latest default values
        return save_config(
            url=config.get("url", ""),
            duet_password=config.get("duet_password", ""),
            http_user=config.get("http_user", ""),
            http_password=config.get("http_password", ""),
            embed_thumbnails=config.get("embed_thumbnails", True),
            thumbnail_sizes=config.get("thumbnail_sizes", DEFAULT_THUMBNAIL_SIZES_STR),
        )

    return {}

def save_config(url: str, duet_password: str, http_user: str, http_password: str, embed_thumbnails: bool, thumbnail_sizes: str):
    s, printer_id = _load_prefs()
    s[printer_id] = {
            "url": url,
            "duet_password": duet_password,
            "http_user": http_user,
            "http_password": http_password,
            "embed_thumbnails": embed_thumbnails,
            "thumbnail_sizes": thumbnail_sizes,
        }
    application = CuraApplication.getInstance()
    p = application.getPreferences()
    p.setValue(DUETRRF_SETTINGS, json.dumps(s))
    return s[printer_id]

def delete_config(printer_id=None):
    s, active_printer_id = _load_prefs()
    if not printer_id:
        printer_id = active_printer_id
    if printer_id in s:
        del s[printer_id]
        application = CuraApplication.getInstance()
        p = application.getPreferences()
        p.setValue(DUETRRF_SETTINGS, json.dumps(s))
        return True
    return False

def get_plugin_version():
    plugin_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin.json")
    try:
        with open(plugin_file_path) as plugin_file:
            plugin_info = json.load(plugin_file)
        return plugin_info["version"]
    except:
        return None
