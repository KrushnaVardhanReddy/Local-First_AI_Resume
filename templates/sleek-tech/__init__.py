import pydantic
from rendercv.schema.models.design.classic_theme import ClassicTheme

class SleekTechThemeOptions(ClassicTheme):
    """
    This class defines the configuration options for the sleek-tech theme.
    """
    theme: pydantic.Field(
        default="sleek-tech",
        description="The theme of the CV."
    )
