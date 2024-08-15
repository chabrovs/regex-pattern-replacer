from dataclasses import dataclass, field, fields
from abc import ABC, abstractmethod
from functools import wraps
import argparse
import re
import os
from typing import Any, Callable, Generator


### [BLOCK]: GLOBAL VARIABLES (code bellow) ###

APPLICATION_METADATA = {
    "version": '0.2',
    "GitHub": 'https://github.com/chabrovs/regex-pattern-replacer',
}

### [BLOCK]: META CLASSES AND DESCRIPTORS (code bellow) ###


class DefaultValueDescriptor:
    def __init__(self, name, default):
        self.name = name
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self.default
        return instance.__dict__.get(self.name, self.default)


class DataclassDefaultsMeta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        for field in fields(cls):
            default = field.default
            if default is field.default_factory:
                default = field.default_factory()
            setattr(cls, field.name, DefaultValueDescriptor(field.name, default))


### [BLOCK]: DATA CLASSES (code bellow) ###

# NOTE: This dataclass is not in use in version 0.1 and newer.
@dataclass(repr=True, init=False)
class Stdout(DataclassDefaultsMeta):
    help_text: str = """Script v.0.1 Replace certain code patterns in your projects files like .html .css .js etc. using RegEx\n\nUsage: python3 script.py [OPTIONS] full_path Replacement Pattern\n\nOptions: \n-h --help \tPrint help message. \n\nExample:\t >>>python3 script.py /home/user/myproject <h*>Hello World !</h*> <h1>Hello Script !</h1>\n\t Result: From this pattern in code <h*>Hello World !</h*> to this pattern<h1>Hello Script !</h1>\n"""
    helper_text: str = """For help try: \n>>>python3 script.py --help\n"""
    no_such_option_error: str = """There is no such option """


@dataclass(slots=True, repr=True, init=False)
class ReplacerArguments:
    full_path: str
    pattern: str
    replacement: str
    file_extensions: list[str] | None = field(default_factory=list)
    verbose: bool = False

    def __str__(self) -> str:
        return f"full_path={self.full_path}, pattern={self.pattern}, replacement={self.replacement}, file_extensions={self.file_extensions}"

    @classmethod
    def get_slots(cls) -> tuple[str]:
        return cls.__slots__

    @classmethod
    def initialize_file_extensions(cls):
        cls.file_extensions = ['.html']
        print(
            f"""[INFO]: File extensions were not specified. Looking for files with default extensions: {cls.file_extensions}
        You can use -e --extensions flag to specify extensions. 
        Command example: $script.py /path pattern replacement -e js xml 
        Note: do NOT use dots and commas.    
        \n""")

    @classmethod
    def build(cls, cli_arguments: list[tuple[str, Any]]) -> None:
        try:
            cli_arguments_dist = dict(cli_arguments)
        except ValueError as e:
            print(f"Error: {e}")

        cls.full_path = cli_arguments_dist.get('full_path')
        cls.pattern = cli_arguments_dist.get('pattern')
        cls.replacement = cli_arguments_dist.get('replacement')
        cls.verbose = True if cli_arguments_dist.get('verbose') else False
        print(f"[DEBUG]: <ln 87> verbose={cls.verbose}")

        if cli_arguments_dist.get('extensions'):
            cls.file_extensions = cli_arguments_dist.get('extensions')
        else:
            cls.initialize_file_extensions()

### [BLOCK]: DECORATORS ###

def default_verbose(callback: Callable, callbackArgument='use_func_result') -> Callable:
    """
    :Param callback: A function that should contain implementation of verbose logic inside.
    :Param callbackArgument: Choose what arguments to pass to the Callback function.
        Options: 
        - "use_func_args" to pass the wrapped function arguments as arguments for the Callback function.
        - "use_func_result" to pass the wrapped function results as arguments for the Callback function.
    """

    def outer(func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            if ReplacerArguments.verbose == True:
                try:
                    match callbackArgument:
                        case 'use_func_args':
                            callback(*args, **kwargs)
                        case 'use_func_result':
                            callback(result)
                        case _:
                            raise Exception(f"[VERBOSE ERROR]: Argument option ({callbackArgument}) for the Callback function ({callback.__name__}) is not supported.\n Available options: 'use_func_args', 'use_func_result'")
                except TypeError:
                    raise Exception(
                        f"[VERBOSE]: function ({func.__name__}) does not support verbose.")
            return result
        return inner
    return outer


### [BLOCK]: VERBOSE CALLBACKS ###

def verbose_get_matched_files(matched_files: list[str] | Generator) -> None:
    if isinstance(matched_files, Generator):
        raise NotImplementedError(
            "Verbose is not supported for the 'Generator' datatype")

    print(f'[VERBOSE]: Patterns will be replaced in these files:')
    for num, file_absolute_path in enumerate(matched_files):
        print(f'\t #{num} {file_absolute_path}')


def verbose_read_file(cls, absolute_path: str) -> None:
    print(f'[VERBOSE]: Reading file {absolute_path}')


### [BLOCK]: ABSTRACT BASE CLASSES and INTERFACES (bellow) ###

class FileManager(ABC):
    """
    Work with files and directories.
    """

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def find_files(self, start_directory: str, files_extensions: list[str], top_down=True):
        """Find files with certain files extensions """
        ...

    @default_verbose(verbose_read_file, callbackArgument='use_func_args')
    def read_file(self, absolute_filepath: str) -> str:
        with open(str(absolute_filepath), 'r') as file:
            content = file.read()

        return content

    def write_file(self, absolute_filepath: str, modified_content: str) -> None:
        with open(str(absolute_filepath), 'w') as file:
            file.write(modified_content)


class DocumentScanner(ABC):
    """
    Abstract base class that works with individual files and their contents.
    """

    def __init__(self) -> None:
        super().__init__()
        self.current_file_manager = FileFinderIterator()
        # NOTE: Add an option to chose current_file_manager dynamically. \
        # In version 0.1 you can specify FileFined based on an iterator or decorator manually by changing the `current_file_manager` variable.

    def get_file_content(self, absolute_path: str) -> str:
        """
        Return the file content.
        """

        return self.current_file_manager.read_file(absolute_path)

    @abstractmethod
    def substitute(self, absolute_path: str, pattern: str, replacement: str, file_extensions: list) -> Any:
        ...


### [BLOCK]: CLASS IMPLEMENTATION ###

class FileFinderGenerator(FileManager):
    def find_files(self, start_directory: str, files_extensions: list[str], top_down=True):
        """Find files with certain files extensions """
        for root, directories, files in os.walk(start_directory, topdown=top_down):
            for file in files:
                file_splitted = file.split('.')
                if file_splitted[-1] in files_extensions:
                    yield os.path.join(root, file)


class FileFinderIterator(FileManager):
    def find_files(self, start_directory: str, files_extensions: list[str], top_down=True) -> list[str]:
        """Find files with certain files extensions """
        matched_files = []
        for root, directories, files in os.walk(start_directory, topdown=top_down):
            for file in files:
                file_splitted = file.split('.')
                if file_splitted[-1] in files_extensions:
                    matched_files.append(os.path.join(root, file))

        return matched_files


class RegExScanner(DocumentScanner):
    """
    Scan file context and modify it.
    """

    def __init__(self) -> None:
        super().__init__()

    @default_verbose(verbose_get_matched_files)
    def get_matched_files(self, absolute_filepath: str) -> list | Generator:
        return self.current_file_manager.find_files(
            start_directory=absolute_filepath,
            files_extensions=ReplacerArguments.file_extensions
        )

    def substitute(self, absolute_filepath: str, pattern: str, replacement: str) -> None:
        """
        Pattern is the pattern of code that will be replaced. Needs to be written in RegEx.
        Replacement is the new piece of code that will be used to replace the pattern. Also needs to be written if RegEx.
        Scan the document and substitute.
        """

        matched_files = self.get_matched_files(absolute_filepath)

        for matched_file in matched_files:
            # print(f"DEBUG: <ln: 190>: {matched_file} ")
            content = self.get_file_content(matched_file)
            modified_content = re.sub(pattern, replacement, content)
            self.current_file_manager.write_file(
                matched_file, modified_content)


### [BLOCK]: APIs (code bellow) ###

class Replacer:
    """
    Replacer Interface is the main application interface.
    Used to interact with the backend.
    Note: This interface is implemented using composition approach rather that inheritance.
    """

    def __init__(self) -> None:
        """
        Composite low layer interfaces.
        """
        self.regExScanner = RegExScanner()

    def print_current_version(self) -> None:
        """
        Print the current version of this application
        """

        print(f"Version: {APPLICATION_METADATA.get('version')}")

    def substitute(self, replacer_arguments: ReplacerArguments) -> None:
        """
        Find all files with a specified extension in the directory and subdirectories.
        :Param replacer_argument: A dataclass 'ReplacerArguments` that contains all required arguments \
            for a pattern substitution, such as: 
                - absolute path to the directory you want to operate with,
                - pattern you want to be replaced <pattern>,
                - pattern you want to replace with <replacement>.
        """

        self.regExScanner.substitute(
            absolute_filepath=replacer_arguments.full_path,
            pattern=replacer_arguments.pattern,
            replacement=replacer_arguments.replacement
        )

    def foo(self) -> None:
        """
        [DEV] <ln: 290>: For development only.
        """

        print(ReplacerArguments())
        print("[Replacer Interface] foo is executed!")

    def foo_with_args(self, args: ReplacerArguments) -> None:
        """
        [DEV] <ln: 298>: For development only.
        """

        print(f'[DEBUG] <ln: 301>: Provided args: {args}')


class Cli(Replacer):
    """
    Command line interface.
    """

    def __init__(self) -> None:
        self.replacer = Replacer()
        self.parser = argparse.ArgumentParser("Replacer")
        self.group_helper_flags = self.parser.add_mutually_exclusive_group()
        self.parser.usage = 'script.py [OPTION] absolute_path_to_the_directory replacement pattern'
        self.setup_arguments()

    def setup_arguments(self) -> None:
        self.parser.add_argument(
            '-v', '--verbose', action='store_true', help="Enable verbose output")
        self.group_helper_flags.add_argument(
            '-V', '--version', action='store_true', help="Print current version")
        self.parser.add_argument(
            'full_path', type=str, help="Set absolute path to the directory", default=None, nargs='?')
        self.parser.add_argument(
            'pattern', type=str, help='Pattern you wish to be replaced', default=None, nargs='?')
        self.parser.add_argument(
            'replacement', type=str, help='Pattern you wish to use', default=None, nargs='?')
        self.parser.add_argument(
            '-e', '--extensions', nargs='+', help="Provide list of file extensions list -e .js")

    def run(self) -> None:
        args: argparse.Namespace = self.parser.parse_args()
        print(args._get_kwargs())

        if args.version:
            self.replacer.print_current_version()
        else:
            for name, arg in args._get_kwargs():
                if arg == "":
                    raise ValueError("Provide valid arguments!")

            ReplacerArguments.build(args._get_kwargs())
            current_replacer_arguments: ReplacerArguments = ReplacerArguments()
            self.replacer.substitute(current_replacer_arguments)


### [BLOCK]: ENTRY POINT (code bellow) ###

def main():
    myapp = Cli()
    myapp.run()


if __name__ == '__main__':
    main()
