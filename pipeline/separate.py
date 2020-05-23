#!/usr/bin/python3

import sys
import getopt
import os


def verify_string(in_string):
    '''Verifies that every line of the string is either valid or empty. For a
    line to be valid, it must have at least two elements (the TCP code and the
    character name). Returns True if the string is valid, else False.'''
    for line in in_string.split('\n'):
        if line.strip() == '':
            continue
        splitter = ' '
        if '\t' in line:
            splitter = '\t'
        line_split = line.split(splitter)
        if len(line_split) < 2:
            return False
    return True


def separate(in_string, directory='', match=False):
    '''Takes an input string which has a line for each character, where the
    lines are separated by newline \\n characters. The format of the line
    corresponds to the output of one of the other scripts in the pipeline.
    Thus, the line is a tsv row or a line of space-separated strings, where
    the first string is the TCP code, the second string is the character's
    name, and all remaining strings are either xml or single words.
    Thus, each line is of the form:
        TCPcode character word [word]...\\n
    OR
        TCPcode\\tcharacter\\txmltext[\\txmltext]...\\n
    
    Separates each of these lines into a separate character file, where the
    filename is given by <TCPcode>_<character>.txt and the contents of the file
    are the contents of the line with the TCP code and character removed.
    '''
    assert(verify_string)
    if directory:
        directory = directory.rstrip('/') + '/'
    for line in in_string.split('\n'):
        if line.strip() == '':
            continue
        splitter = ' '
        if '\t' in line:
            splitter = '\t'
        line_split = line.split(splitter)
        TCPcode, speaker = line_split[:2]
        speech = splitter.join(line_split[2:])
        out_dir = directory
        if match:
            out_dir = out_dir + TCPcode + '/'
        if out_dir:
            try:
                os.makedirs(out_dir, 0o755)
            except FileExistsError:
                pass
        with open(out_dir + TCPcode + '_' + speaker + '.txt', 'w') as outfile:
            outfile.write(speech)


def parse_separate(arg_list):
    '''Parses command-line arguments and runs the core separate() function
    accordingly. Writes each character's text to a separate file, and writes
    the original input to stdout so that separate.py can be inserted into the
    pipeline without interrupting it.''' 
    optlist, args = getopt.getopt(arg_list, 'hmi:o:d:')
    infile = sys.stdin
    outfile = sys.stdout
    directory = ''
    match = False
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - translate character speech from Old English to modern English

    Usage:
        python3 {0} [OPTION]... 

    Reads one character's text per line of stdin, the format of the line
    corresponds to the output of one of the other scripts in the pipeline.
    Thus, the line is a tsv row or a line of space-separated strings, where
    the first string is the TCP code, the second string is the character's
    name, and all remaining strings are either xml or single words.
    Thus, each line of stdin is of the form:
        TCPcode character word [word]...\\n
    OR
        TCPcode\\tcharacter\\txmltext[\\txmltext]...\\n

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
'''.format(sys.argv[0]))
            exit(0)
        if o == '-i':
            infile = open(a, 'r')
        if o == '-o':
            outfile = open(a, 'w')
        if o == '-d':
            directory = a.rstrip('/') + '/'
        if o == '-m':
            match = True
    in_string = infile.read()
    separate(in_string, directory, match)
    outfile.write(in_string)
    if infile != sys.stdin:
        infile.close()
    if outfile != sys.stdout:
        outfile.close()


def main():
    parse_separate(sys.argv[1:])


if __name__ == '__main__':
    main()
