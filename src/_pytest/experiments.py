class PytestExerimentalApiWarning(FutureWarning):
    "warning category used to denote experiments in pytest"

    @classmethod
    def simple(cls, apiname):
        return cls(
            "{apiname} is an experimental api that may change over time".format(
                apiname=apiname
            )
        )


PYTESTER_COPY_EXAMPLE = PytestExerimentalApiWarning.simple("testdir.copy_example")
