import pydantic
from rendercv.schema.models.design.classic_theme import ClassicTheme

class ModernBlueThemeOptions(ClassicTheme):
    """
    This class defines the configuration options for the modern-blue theme.
    """
    theme: pydantic.Field(
        default="modern-blue",
        description="The theme of the CV."
    )
