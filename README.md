## What is regex-pattern-replacer
It is a Python script that is meant to help developers refactor one RegEx expression in multiple files as ones.

## How does it work ?
1. RegEx Pattern Replaces takes a directory, the pattern you want to replace, the pattern you want to use as a replacement, and required file extensions as arguments.
2. The script goes to the specific directory.
3. Recursively, it finds all files with the required extensions
4. Scans those files for the pattern you have specified.
5. If the pattern was found, the script substitutes the pattern into another pattern you had specified.
6. Save the modified content back to the original file.

## Use cases:
Let's say, you would like to change the name of all csrf tokens in the project:
In this case: `$python3 regex-pattern-replacer /path/to/your/project/templates '(<[^>]*?)\{\s*%\s*csrf_token\s*%\s*\}(.*?>)' '\1{% csrf_protected %}\2' -e html js`

## Usage
`$python3 regex-pattern-replacer [OPTION] absolute_path_to_the_directory replacement pattern`
### Options:
  Option | Description
------------ | -------------
-h --help | print help message
-f --force | Write changes even if a pattern was not found, even the substitution was not made.
-v --verbose | verbose output
-V --version | print current version
-e --extensions [EXTENSIONS...] | Specify file extensions to look for in the directory. E.g. html js 
# Example:
`$python3 regex-pattern-replacer -v /path/to/your/project/templates 'RegExPattern_to_be_replaced' 'RegExPattern' -e html js xml`

