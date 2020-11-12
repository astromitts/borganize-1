class DateStrConverter:
    regex = '[0-9]{8}'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%08d' % value
