class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

class UserError(Exception):
    """Raised for user-facing errors such as missing directories or incorrect arguments."""
    pass

class LLMError(Exception):
    """Raised when an LLM provider encounters a network or API failure."""
    pass

class RenderError(Exception):
    """Raised when PDF rendering fails (e.g., RenderCV error or missing source files)."""
    pass

class PromptError(Exception):
    """Raised when a prompt template file cannot be found."""
    pass

class ValidationError(Exception):
    """Raised when data fails validation (e.g., an LLM response is too short)."""
    pass
