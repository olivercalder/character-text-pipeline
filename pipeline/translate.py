#!/usr/bin/python3

import sys
import getopt

std_dict_path = '../dicts/standardizer_dictionary.txt'


def get_translation_dictionary(dict_filename=std_dict_path, separator=':', modernize=True):
    '''Loads a translation dictionary from the given dictionary file, which
    should have lines of the form:
        old_english:modern_english:priority
    where priority is 0 if the translation should always occur (ie. 'fore),
    1 if the replacement preserves Old English word forms (ie. abideth), and
    2 if the replacement translates into odern English (ie. amogst).
    Returns the dictionary.'''
    translation_dict = {}
    with open(dict_filename, 'r') as dict_file:
        for line in dict_file:
            line = line.strip()
            if line and line[0] != '#':
                line_elements = line.split(separator)
                assert(len(line_elements) >= 2)
                key = line_elements[0].replace(',', ' ')
                val = line_elements[1].replace(',', ' ')
                if len(line_elements) == 2:
                    translation_dict[key] = val
                else:
                    prio = line_elements[2]
                    if prio == '0':
                        translation_dict[key] = val
                    elif modernize and prio == '2':
                        translation_dict[key] = val
                    elif prio == '1':
                        translation_dict[key] = val
    return translation_dict


def translate(in_string, dict_filename=std_dict_path, separator=':', modernize=True):
    '''Translates Old English and common abbreviations or words with missing
    letters into modern English using a dictionary file. The input text should
    be a string with rows separated by newline \\n characters, and each row
    should contain words separated by spaces, where the first word is the TCP
    code, the second word is the character's name, and the remaining words are
    the character's speech. Returns an output string of the same form, with
    words which are in the dictionary substituted with their translations.'''
    translation_dict = get_translation_dictionary(dict_filename, separator, modernize)
    out_list = []
    for row in in_string.strip().split('\n'):
        words = row.split()
        assert(len(words) >= 2)
        TCPcode = words[0]
        character = words[1]
        row_list = [TCPcode, character]
        for word in words[2:]:
            if word in translation_dict:
                row_list.append(translation_dict[word])
            else:
                row_list.append(word)
        out_list.append(' '.join(row_list))
    return '\n'.join(out_list) + '\n'


def parse_translate(arg_list):
    '''Parses command-line arguments and runs the core translate() function
    accordingly. Writes the output to stdout unless an output file is specified
    using the -o flag.'''
    optlist, args = getopt.getopt(arg_list, 'hpi:o:d:')
    infile = sys.stdin
    outfile = sys.stdout
    dict_filename = std_dict_path
    separator = ':'
    modernize = True
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - translate character speech from Old English to modern English

    Usage:
        python3 {0} [OPTION]... 

    Reads one character's cleaned text per line of stdin, where each line is a
    string of words separated by spaces. The first word is the TCP code, the
    second word being the character's name, and the remaining words being
    the cleaned words spoken by that character. Thus, stdin is of the form:
        TCPcode character word [word]...\\n

    Writes one character's translated text per line of stdout, where each line is
    space-separated words, with the first word being the TCP code, the second
    word being the character's name, and the remaining words being the character's
    words in their modern English forms, when translation is available.
    Thus, stdout is of the form:
        TCPcode character word [word]...\\n


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
                            $ python3 extract.py A08360.xml | python3 clean.py | \\
                              python3 translate.py -d dict1.txt | \\
                              python3 translate.py -d dict2.txt

    -s separator    Specify the separator used by the dictionary file.

    -p              Preserve Old English word forms, such as "altereth".
'''.format(sys.argv[0]))
            exit(0)
        if o == '-i':
            infile = open(a, 'r')
        if o == '-o':
            outfile = open(a, 'w')
        if o == '-d':
            dict_filename = a
        if o == '-p':
            modernize = False
    in_string = infile.read()
    out_string = translate(in_string, dict_filename, separator, modernize)
    outfile.write(out_string)
    if infile != sys.stdin:
        infile.close()
    if outfile != sys.stdout:
        outfile.close()


def main():
    parse_translate(sys.argv[1:])


if __name__ == '__main__':
    main()
