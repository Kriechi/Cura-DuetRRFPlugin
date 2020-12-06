import json

from cura.CuraApplication import CuraApplication

DUETRRF_SETTINGS = "duetrrf/instances"

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

def get_config():
    s, printer_id = _load_prefs()
    if printer_id in s:
        return s[printer_id]
    return {}

def save_config(url, duet_password, http_user, http_password):
    s, printer_id = _load_prefs()
    s[printer_id] = {
            "url": url,
            "duet_password": duet_password,
            "http_user": http_user,
            "http_password": http_password,
        }
    application = CuraApplication.getInstance()
    p = application.getPreferences()
    p.setValue(DUETRRF_SETTINGS, json.dumps(s))
    return s

def delete_config():
    s, printer_id = _load_prefs()
    if printer_id in s:
        del s[printer_id]
        application = CuraApplication.getInstance()
        p = application.getPreferences()
        p.setValue(DUETRRF_SETTINGS, json.dumps(s))
        return True
    return False
