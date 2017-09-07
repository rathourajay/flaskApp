"""
Base LLO Exception
"""
class LLOException(Exception):
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        super(LLOException, self).__init__()
        self._error_string = self.message
        if len(args) > 0:
            args = ["%s" % arg for arg in args]
            self._error_string = (self._error_string +
                                  "\nDetails: %s" % '\n'.join(args))

    def __str__(self):
        return self._error_string


class InvalidConfiguration(LLOException):
    message = "Invalid Configuration"


class Unauthorized(LLOException):
    message = 'Unauthorized'


class Forbidden(LLOException):
    message = 'Invalid credentials'


class EndpointNotFound(LLOException):
    message = "Endpoint not found"


class RequestFailed(LLOException):
    message = "Request failed"


class InvalidResponseKey(LLOException):
    message = "Invalid key of response body"


class NoAgent(LLOException):
    message = "No agent found"


class DBError(LLOException):
    message = "DB Error"


class InvalidNeutronEndpoint(LLOException):
    message = "Invalid neutron endpoint"


class HostnameNotFound(LLOException):
    message = "Host name not found for compute port"
