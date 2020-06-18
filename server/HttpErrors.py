http_codes = {
    400: "Bad Request", 401: "Unauthorized", 402: "Payment Required", 403: "Forbidden", 404: "Not Found",
    405: "Method Not Allowed", 406: "Not Acceptable", 408: "Request Timeout",
    409: "Conflict", 410: "Gone", 411: "Length Required", 412: "Precondition Failed", 413: "Payload Too Large",
    414: "URI Too Long", 415: "Unsupported Media Type", 416: "Range Not Satisfiable", 417: "Expectation Failed",
    418: "I'm a teapot", 422: "Unprocessable Entity", 425: "Too Early", 426: "Upgrade Required",
    428: "Precondition Required", 429: "Too Many Requests", 431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons", 500: "Internal Server Error", 501: "Not Implemented",
    505: "HTTP Version Not Supported"
}


class HttpException(Exception):
    def __init__(self, code):
        self.code = str(code) + " " + http_codes[code]

    def __str__(self):
        return self.code
