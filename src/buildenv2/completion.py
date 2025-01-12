from abc import ABC, abstractmethod


class CompletionCommand(ABC):
    """
    Class representing a command for shell autocompletion.
    """

    @abstractmethod
    def get_command(self) -> str:  # pragma: no cover
        """
        Get the command string for autocompletion, to be added to generated completion script.

        :return: Command string for autocompletion
        """
        raise NotImplementedError("Subclasses must implement this method")


class EvalCompletionCommand(CompletionCommand):
    """
    Class representing a command for shell autocompletion.
    The provided command is supposed to return a bash script snippet to be evaluated with the "eval" command.

    :param command: The command to be evaluated
    """

    def __init__(self, command: str):
        super().__init__()
        self._command = command

    def get_command(self) -> str:
        """
        Get the command string for autocompletion, to be added to generated completion script.

        :return: Command string for autocompletion
        """
        return f'eval "$({self._command})"'


class ArgCompleteCompletionCommand(EvalCompletionCommand):
    """
    Class representing a command for shell autocompletion.
    The provided command is supposed to be an entry-point using *argcomplete*

    :param command: Single command name using argcomplete lib
    """

    def __init__(self, command: str):
        super().__init__(f"register-python-argcomplete {command}")
