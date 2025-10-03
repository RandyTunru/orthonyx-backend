# bare exceptions for OpenAI API errors
class OpenAIError(Exception):
    pass

# specific exceptions for different error types
class OpenAIAuthError(OpenAIError):
    pass

class OpenAIRateLimitError(OpenAIError):
    pass

class OpenAITransientError(OpenAIError):
    pass

class OpenAITimeoutError(OpenAIError):
    pass

class OpenAIUnavailableError(OpenAIError):
    pass