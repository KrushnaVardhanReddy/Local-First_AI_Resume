import pydantic
from rendercv.schema.models.design.classic_theme import ClassicTheme

class CreativeThemeOptions(ClassicTheme):
    """
    This class defines the configuration options for the creative theme.
    """
    theme: pydantic.Field(
        default="creative",
        description="The theme of the CV."
    )
