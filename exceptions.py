class ParseLineError(Exception):
    def __init__(self, line):
        self.line = line
        super(ParseLineError, self).__init__()

    def __str__(self):
        return f"Line unable to be parsed: {self.line}"


class ParseInputNumberError(Exception):
    def __init__(self, line):
        self.line = line
        super(ParseInputNumberError, self).__init__()

    def __str__(self):
        return f"Invalid number of inputs: {self.line}"


class ParseNoGateError(Exception):
    def __init__(self, name):
        self.name = name
        super(ParseNoGateError, self).__init__()

    def __str__(self):
        return f"Output created, but no corresponding logic gate: {self.name}"


class ParseInputNotFoundError(Exception):
    def __init__(self, line, name):
        self.line = line
        self.name = name
        super(ParseInputNotFoundError, self).__init__()

    def __str__(self):
        return f"Cannot find corresponding node {self.name} from {self.line}"
