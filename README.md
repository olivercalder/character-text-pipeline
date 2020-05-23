# character-text-pipeline
A text processing pipeline designed to extract, clean, and translate early modern texts from the TCP project.

## Usage

The character text pipeline functions as a pipeline which begins with raw xml files from the TCP project and performs a number of operations such as cleaning and translation.

In particular, these scripts are tuned for the files found in `P5_snapshot_201502`, available from the TCP project website. Several of these files are included in `plays_of_interest/`.

The pipeline functions by piping the output of one script into the input of another, using the standard POSIX pipe API.

Example usage:

```sh
pipeline$ python3 extract.py ../data/plays_of_interest/A08* | python3 clean.py | python3 translate.py -d ../dicts/additional_dict.txt | python3 separate.py -d ready_for_ml
```

The pipeline can be exited at any time and picked up by another script later by redirecting the input and output:

```sh
pipeline$ python3 extract.py ../data/plays_of_interest/* | python3 clean.py -o cleaned_parts.txt
pipeline$ python3 translate.py -i cleaned_parts.txt | python3 separate.py -m
```

The separate script can also be inserted at any (or all) points in the pipeline without interrupting it, in order to preserve intermediate outputs.

```sh
pipeline$ ./extract.py A08360.xml A04732.xml | ./separate.py -m -d xml_parts | ./clean.py | ./separate.py -m -d cleaned_parts | ./translate.py | ./separate.py -m -d translated_parts
```

## Core Components

### extract

Reads one or more xml files from the TCP project and extracts all of the spoken parts into separate text for each character.

This script provides an output of the form expected by `clean.py` and `separate.py`.

```
Usage information for extract.py

    extract.py - extracts raw character speech from xml TCP files

    Usage:
        python3 extract.py [OPTION]... [FILE]...

    Writes one character's xml text per line to stdout, where each line is in
    the style of a tsv row, with the first element being the TCP code, the
    second element being the character's name, and the remaining elements being
    the xml <l>...</l> tags containing the speech of that character. Thus,
    stdout is of the form:
        TCPcode\tcharacter\txmltext[\txmltext]...\n


    -h              Display this help message.

    -d directory    Specify the input directory in which xml files are stored.
                        This directory is prepended to all filenames supplied
                        as arguments
                        If -c, also prepend to all filenames given by the TCP
                        codes in the csv file.
                        If different xml files are in differen directories,
                        then please specify their directories as part of their
                        filenames, and do not use this option.

    -c filename     Specify a csv file containing a list of VEP TCP codes.
                        If -d is also used, then the input directory will be
                        prepended to each VEP code found in this csv file.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout. A tsv file is preferred.
```

### clean

Reads input from `extracy.py` or a corresponding input file and cleans it by resolving or removing all xml tags, and then cleaning it of all non-ASCII characters. What remains is a space-separated string of words spoken by each character.

This script provides output of the form expected by `translate.py` and `separate.py`.

```
Usage information for clean.py

    clean.py - clean character speech from xml output produced by extracy.py

    Usage:
        python3 clean.py [OPTION]... 

    Reads one character's xml text per line of stdin, where each line is in
    the style of a tsv row, with the first element being the TCP code, the
    second element being the character's name, and the remaining elements being
    the xml <l>...</l> tags and their corresponding to that character. Thus,
    stdin is of the form:
        TCPcode\tcharacter\txmltext[\txmltext]...\n

    Writes one character's cleaned text per line of stdout, where each line is
    space-separated words, with the first word being the TCP code, the second
    word being the character's name, and the remaining words being the ascii
    cleaned words, though still in their Old English forms, when applicable.
    Thus, stdout is of the form:
        TCPcode character word [word]...\n


    -h              Display this help message.

    -i filename     Specify an input tsv-like file from which to read character
                        xml text data. If this is specified, then does not read
                        from stdin.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.
```

### translate

Reads input from `clean.py` or a corresponding input file and translates it by running all words through one or more dictionaries which replace archaic words and spellings with their modern equivalents. This is meant to allow the output to be converted to phonemes using the Carnegie Mellon phoneme dictionary or a similar process.

This script provides output of the form expected by `separate.py`.

```
Usage information for translate.py

    translate.py - translate character speech from Old English to modern English

    Usage:
        python3 translate.py [OPTION]... 

    Reads one character's cleaned text per line of stdin, where each line is a
    string of words separated by spaces. The first word is the TCP code, the
    second word being the character's name, and the remaining words being
    the cleaned words spoken by that character. Thus, stdin is of the form:
        TCPcode character word [word]...\n

    Writes one character's translated text per line of stdout, where each line is
    space-separated words, with the first word being the TCP code, the second
    word being the character's name, and the remaining words being the character's
    words in their modern English forms, when translation is available.
    Thus, stdout is of the form:
        TCPcode character word [word]...\n


    -h              Display this help message.

    -i filename     Specify an input file from which to read the cleaned text
                        text data for each character, where each line of the
                        file is of the format described above. If this option
                        is specified, then does not read from stdin.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.

    -d dictfile     Specify the dictionary file to be used to translate words in
                        character text. By default, the script is designed to
                        use standardizer_dictionary.txt, as used in the VEP
                        Pipeline project, found here:
                            https://github.com/uwgraphics/VEP-pipeline
                        If multiple dictionaries are to be used, simply call
                        this program multiple times with different files
                        specified using -d. The output of this program can be
                        piped directly into another instance of the program
                        using the standard POSIX pipe API.
                        Ex:
                            $ python3 extract.py A08360.xml | python3 clean.py | \
                              python3 translate.py -d dict1.txt | \
                              python3 translate.py -d dict2.txt

    -s separator    Specify the separator used by the dictionary file.

    -p              Preserve Old English word forms, such as "altereth".
```

### separate

Separates a single string containing many newline-separated characters and speech into separate files.

This script provides output of the form expected by `merge.py`, and is its inverse.

```
Usage information for separate.py

    separate.py - translate character speech from Old English to modern English

    Usage:
        python3 separate.py [OPTION]... 

    Reads one character's text per line of stdin, the format of the line
    corresponds to the output of one of the other scripts in the pipeline.
    Thus, the line is a tsv row or a line of space-separated strings, where
    the first string is the TCP code, the second string is the character's
    name, and all remaining strings are either xml or single words.
    Thus, each line of stdin is of the form:
        TCPcode character word [word]...\n
    OR
        TCPcode\tcharacter\txmltext[\txmltext]...\n

    Separates each line of stdin into a separate character and writes that
    character's text to a file for that character.
    Passes stdin to stdout without modification, thus allowing this script to
    be inserted into the pipeline to save some stage of the output without
    interrupting the pipeline.


    -h              Display this help message.

    -i filename     Specify an input file from which to read the text data for
                        each character, where each line of the file is of the
                        format described above. If this option
                        is specified, then does not read from stdin.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.

    -d directory    Specify the output directory in which to write separated
                        character texts.

    -m              Match output directory names to the TCP code for each
                        character. Thus, sort characters into directories
                        according to the TCP code of the xml file from which
                        they originate. If -d is used, these directories will
                        all be within the directory given by -d.
```

### merge

Merges many separate files into a single newline-separated string with a character and their speech for each line.

This script is also compatible with any similarly structured character text files, such as those provided by [The Folger Shakespeare](www.folgerdigitaltexts.org/api)

This script provides output of the form expected by `clean.py`, `translate.py`, or `separate.py`.

```
Usage information for merge.py

    merge.py - merge character speech from many files which were produced by
            extract.py into one output string of the form expected by all
            of the other scripts (besides extract) in the pipeline.
            Requires that the filenames be of the form:
                code_character.fileextension
            While files produced by extract.py are preferred, also works with
            other files which satisfy this naming convention. Additionally,
            The -l and -r flags can be used to make other filenames conform
            to this convention, such as
                python3 merge.py -s 1 text_Ham_Hamlet.txt
            This allows the merge script (and thus the other scripts in the
            pipeline) to be used in conjunction with the Sonic Signatures
            project, found here:
                https://github.com/olivercalder/sonic-signatures

    Usage:
        python3 merge.py [OPTION]... [FILE]...

    Writes one character's text per line to stdout, where each line is in
    the style of a tsv row, with the first element being the TCP code, the
    second element being the character's name, and the remaining elements being
    the xml <l>...</l> tags and their corresponding to that character. Thus,
    stdout is of the form:
        TCPcode\tcharacter\txmltext[\txmltext]...\n


    -h              Display this help message.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.

    -s char         Specify a separator to use between text elements for a
                        character's speech. This overrides the default space
                        or tab character, where if a tab exists in any of the
                        files, a tab is used as a separator for all, else a
                        space is used.

    -l #            Specify a number of elements (each separated by an
                        underscore character) to strip from the left of
                        the filename when adding it to the output string.
                        For example,
                            python3 merge.py -s 1 text_Ham_Hamlet.txt
                        produces
                            Ham Hamlet word [word]...\n

    -r #            Specify a number of elements (each separated by an
                        underscore character) to strip from the right of
                        the filename when adding it to the output string.
                        For example,
                            python3 merge.py -r 1 Ham_Hamlet_orig.txt

                        The -l and -r flags can be used together as well.
                        For example,
                            python3 merge.py -l 2 -r 1 orig_text_Ham_Hamlet_cleaned-ready.txt
                        produces
                            Ham Hamlet word [word]...\n
```
