#!/usr/bin/python3

import sys
import getopt
import os


def check_tab(filenames):
    '''Checks whether a tab character exists in any of the given filenames.
    Returns True if there is a tab character, else False.
    Coincidentally, also verifies that all files exist.'''
    use_tab = False
    for filename in filenames:
        with open(filename, 'r') as infile:
            if '\t' in infile.read():
                use_tab = True
        if use_tab:
            return True
    return False


def check_filenames(filenames, filename_separator='_', lstrip=0, rstrip=0):
    '''Checks that all files exist and that their filenames have the correct
    number of elements to be valid. That is, they must contain
    (lstrip + rstrip + 2) elements prior to the file extension.
    If any such filenames are found, adds them to a list, prints them to
    stderr, and returns false. Else returns True.'''
    rax = True
    not_found = []
    invalid = []
    for filename in filenames:
        if not os.path.isfile(filename):
            not_found.append(filename)
        elif len(filename.split(filename_separator)) != lstrip + rstrip + 2:
            invalid.append(filename)
    if len(not_found) > 0:
        print('ERROR: Files not found', file=sys.stderr)
        for filename in not_found:
            print('    ' + filename, file=sys.stderr)
        rax = False
    if len(invalid) > 0:
        print('ERROR: Invalid filenames given lstrip={}, rstrip={}'.format(lstrip, rstrip), file=sys.stderr)
        for filename in invalid:
            print('    ' + filename, file=sys.stderr)
        rax = False
    return rax


def merge(filenames, separator=None, filename_separator='_', lstrip=0, rstrip=0):
    '''Merges the given filenames into a single string of the form expected by
    all the other scripts (besides extract) in the pipeline. The separation
    between elements is either a space character or a tab character. If a tab
    character exists in any of the input files, the separator will use a tab as
    the separator, otherwise it will default to a space character.
    If the separator parameter is not None, the character given by that
    parameter will override any automatic decision. The contents of the input
    files will not be modified, ie. if the separator is a tab character and
    there are no tab characters, then the output string for that character will
    have three tab-separated elements: code\\tcharacter\\ttext
    The filename_separator parameter specifies which character to use to split
    the filename. By default, underscore _ is used.
    The lstrip and rstrip parameters specify how many components of the filename
    to ignore from the left and right, respectively, where each component is
    separated by an underscore character.
    Ex:
        merge('orig_text_Ham_Hamlet_clean.txt', lstrip=2, rstrip=1)
    produces
        Ham Hamlet word [word]...\\n'''
    assert(check_filenames(filenames, filename_separator, lstrip, rstrip))
    out_list = []
    if separator is None:
        separator = ' '
        if check_tab(filenames):
            separator = '\t'
    for filename in filenames:
        filename_str = '.'.join(filename.split('.')[:-1])  # Removes file extension, so assumes there is one, or that removing a trailing . is not harmful
        filename_list = filename_str.split(filename_separator)[lstrip:]
        if abs(rstrip) > 0:
            filename_list = filename_list[:-abs(rstrip)]
        TCPcode, speaker = filename_list
        with open(filename, 'r') as infile:
            text = infile.read()
            line_string = separator.join([TCPcode, speaker, text.strip()])
            out_list.append(line_string)
    return '\n'.join(out_list)


def parse_merge(arg_list):
    '''Parses command-line arguments and runs the core merge() function
    accordingly. Writes the output to stdout unless an output file is specified
    using the -o flag.'''
    optlist, args = getopt.getopt(arg_list, 'ho:s:t:l:r:')
    in_directory = ''
    outfile = sys.stdout
    lstrip = 0
    rstrip = 0
    separator = None
    filename_separator = '_'
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - merge character speech from many files which were produced by
            separate.py into one output string of the form expected by all
            of the other scripts (besides extract) in the pipeline.

    Usage:
        python3 {0} [OPTION]... [FILE]...

    Requires that the filenames be of the form:
        code_character.fileextension
    While files produced by extract.py are preferred, also works with other
    files which satisfy this naming convention. Additionally, the -l and -r
    flags can be used to make other filenames conform to this convention,
    such as
        python3 merge.py -s 1 text_Ham_Hamlet.txt
    This allows the merge script (and thus the other scripts in the pipeline)
    to be used in conjunction with the Sonic Signatures project, found here:
        https://github.com/olivercalder/sonic-signatures

    Writes one character's text per line to stdout, where each line is in
    the style of a tsv row, with the first element being the TCP code, the
    second element being the character's name, and the remaining elements being
    the xml <l>...</l> tags and their corresponding to that character. Thus,
    stdout is of the form:
        TCPcode\\tcharacter\\txmltext[\\txmltext]...\\n


    -h              Display this help message.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.

    -s char         Specify a separator to use between text elements for a
                        character's speech. This overrides the default space
                        or tab character, where if a tab exists in any of the
                        files, a tab is used as a separator for all, else a
                        space is used.

    -t char         Specify a filename separator to use when splitting
                        filenames into their play code and character name.
                        By defult, underscore _ is used.
                        For example,
                            python3 merge.py -t - Ham-Hamlet.txt
                        produces
                            Ham Hamlet word 

    -l #            Specify a number of elements (each separated by an
                        underscore character) to strip from the left of
                        the filename when adding it to the output string.
                        For example,
                            python3 merge.py -s 1 text_Ham_Hamlet.txt
                        produces
                            Ham Hamlet word [word]...\\n

    -r #            Specify a number of elements (each separated by an
                        underscore character) to strip from the right of
                        the filename when adding it to the output string.
                        For example,
                            python3 merge.py -r 1 Ham_Hamlet_orig.txt

                        All flags can be used together as well.
                        The -t flag takes effect before the -l or -r flags.
                        For example,
                            python3 merge.py -s : -t - -l 2 -r 1 orig-text-Ham-Hamlet-cleaned_ready.txt
                        produces
                            Ham:Hamlet:word[:word]...\\n
'''.format(sys.argv[0]), file=sys.stderr)
            exit(0)
        if o == '-o':
            outfile = open(a, 'w')
        if o == '-s':
            separator = a
        if o == '-t':
            filename_separator = a
        if o == '-l':
            lstrip = int(a)
        if o == '-r':
            rstrip = int(a)
    out_string = merge(args, separator, filename_separator, lstrip, rstrip)
    outfile.write(out_string)
    if outfile != sys.stdout:
        outfile.close()


def main():
    if len(sys.argv) == 1:
        sys.argv.append('-h')
    parse_merge(sys.argv[1:])


if __name__ == '__main__':
    main()
