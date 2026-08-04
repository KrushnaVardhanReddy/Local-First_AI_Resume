import pydantic
from rendercv.schema.models.design.classic_theme import ClassicTheme

class TwoColumnDarkThemeOptions(ClassicTheme):
    """
    This class defines the configuration options for the two-column-dark theme.
    """
    theme: pydantic.Field(
        default="two-column-dark",
        description="The theme of the CV."
    )
