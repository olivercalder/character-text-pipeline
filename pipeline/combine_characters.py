#!/usr/bin/python3

import sys
import getopt


def get_character_dictionary(dict_filename, separator='\t'):
    '''Loads a character dictionary from the given dictionary file, which
    should have lines of the form:
        TCPcode-#,raw character name,substitution
    The separator can be a tab, comma, colon, or any other separator given.
    The dictionary maps the tuple (TCPcode-#, raw character name) to the value
    given by substitution. Returns the dictionary.'''
    character_dict = {}
    with open(dict_filename, 'r') as dict_file:
        for line in dict_file:
            line = line.strip()
            if line and line[0] != '#':
                line_elements = line.split(separator)
                assert(len(line_elements) == 3)
                TCPcode, key, val = line_elements
                character_dict[(TCPcode, key)] = val
    return character_dict


def combine_characters(in_string, dict_filename, separator='\t'):
    '''Translates raw or abbreviated character names into their complete names,
    concatenating the speech for all abbreviations which map to the same name
    into one character. Note that this does not preserve the original ordering
    of speech for any given character. Any characters which are in the
    dictionary will be converted, and any which are not in the dictionary will
    be left unchanged.'''
    character_dict = get_character_dict(dict_filename, separator)
    speech_dict = {}
    splitter = ' '
    if '\t' in in_string:
        splitter = '\t'
    for row in in_string.strip().split('\n'):
        words = row.split(splitter)
        TCPcode, character = words[:2]
        if (TCPcode, character) in character_dict:
            character = character_dict[(TCPcode, character)]
        if splitter == ' ':
            character = character.replace(' ', '-')
        if (TCPcode, character) not in speech_dict:
            speech_dict[(TCPcode, character)] = []
        speech_dict[(TCPcode, character)].append(words[2:])
    out_list = []
    for key in speech_dict:
        out_list.append(splitter.join(list(key) + speech_dict[key]))
    return '\n'.join(sorted(out_list)) + '\n'


def parse_combine_characters(arg_list):
    '''Parses command-line arguments and runs the core combine_characters()
    function accordingly. Writes the output to stdout unless an output file
    is specified using the -o flag.'''
    optlist, args = getopt.getopt(arg_list, 'hi:o:d:s:')
    infile = sys.stdin
    outfile = sys.stdout
    separator = '\t'
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - translate from raw abbreviated character names to full
                    character names, concatenating speech when raw characters
                    map to the same full character name.

    Usage:
        python3 {0} [-d] dictionary_filename [dictionary2_filename] [OPTION]...

    Reads one character's speech per line of stdin, where each line is a
    string of words separated by tabs or spaces. The first word is the TCP code
    and the number of the play from which it was extracted, the second word is
    the character's name, and the remaining words are the character's speech.
    Thus, stdin is of the form:
        TCPcode-# character word [word]...\\n
    OR
        TCPcode-#\\tcharacter\\tword[\\tword]...\\n

    All non-flag arguments to the script are treated as dictionary filenames.
    The -d flag may be used (for consistency) but it is not necessary. If
    multiple dictionary files are used, it is assumed that they use the same
    separator between "columns" of the tsv- or csv-like dictionary file. By
    default, a tab character \\t is used as the separator, though another
    separator can be substituted using the -s flag.

    Writes one combined character's speech per line of stdout, where each line
    is space- or tab-separated words according to the input speech. The first
    word is the TCP code and the number of the play from which it was extracted,
    the second word is the character's converted name, and the remaining words
    are the combined words of all the original characters which the dictionary
    mapped to that character. Characters which are not in the dictionary are
    left unchanged. Thus, stdout is of the same form as stdin.


    -h              Display this help message.

    -i filename     Specify an input file from which to read the combined text
                        data for each character, where each line of the file is
                        of the format described above. If this option is
                        specified, then does not read from stdin.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.

    -d dictfile     Specify the dictionary file to be used to translate and
                        combine characters.

    -s separator    Specify the separator used by the dictionary file. The
                        default is a tab character "\\t". To use a space,
                        use `-s " "`. If multiple dictionaries are used which
                        utilize different separators, pipe the output of this
                        script into another instance of this script with a
                        different separator flag and the corresponding
                        dictionaries.
'''.format(sys.argv[0]))
            exit(0)
        if o == '-i':
            infile = open(a, 'r')
        if o == '-o':
            outfile = open(a, 'w')
        if o == '-d':
            args.append(a)
        if o == '-s':
            separator = a
    string = infile.read()
    if len(args) == 0:
        print('ERROR: {}: Please specify one or more dictionary files as arguments.'.format(sys.argv[0]), file=sys.stderr)
        print('    For usage information, run: python3 {} -h'.format(sys.argv[0]), file=sys.stderr)
        exit(1)
    string = translate(string, dict_filename, separator, modernize)
    for dict_filename in args:
        string = combine_characters(string, dict_filename, separator)
    outfile.write(string)
    if infile != sys.stdin:
        infile.close()
    if outfile != sys.stdout:
        outfile.close()


def main():
    parse_combine_characters(sys.argv[1:])


if __name__ == '__main__':
    main()
