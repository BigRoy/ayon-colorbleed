from ayon_server.settings import BaseSettingsModel, SettingsField


class APNGCSettingsModel(BaseSettingsModel):
    executable: str = SettingsField("", title="APNGC Executable Path")
    profiles: list[str] = SettingsField(
        default_factory=list,
        title="APNGC Profiles")
    tinify_api_key: str = SettingsField("", title="Tinify API key")
    output_directory: str = SettingsField("",
                                          title="Conversion Output Directory")


class ColorbleedSettings(BaseSettingsModel):
    apngc: APNGCSettingsModel = SettingsField(
        default_factory=APNGCSettingsModel,
        title="APNGC"
    )


DEFAULT_VALUES = {
    "apngc": {
        "executable": "",
        "profiles": [],
        "tinify_api_key": "",
        "output_directory": ""
    }
}