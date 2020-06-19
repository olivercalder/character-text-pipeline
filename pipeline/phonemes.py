#!/usr/bin/python3

import sys
import getopt
import nltk
# nltk.download('cmudict')
# OR
# $ python3 -m nltk.downloader [-d /usr/share/nltk_data] cmudict


def load_phoneme_dict(dict_filename, separator=' '):
    '''Loads a dictionary from a csv-style file where elements are separated
    by the character given by the separator parameter (space character by
    default). The format of each line should be as follows, with the spaces
    between words replaced by the given separator:
        word W ER1 D
    The phonemes should be consistent with those used by the cmudict, and can
    optionally exclude the number after vowel sounds if the -e flag is not
    used. Returns the dictionary.'''
    phoneme_dict = {}
    with open(dict_filename, 'r') as dict_file:
        for line in dict_file:
            line = line.strip()
            if line and line[0] != '#':
                line_elements = line.split(separator)
                assert(len(line_elements) >= 2)
                key = line_elements[0].lower()
                val = [line_elements[1:]]
                phoneme_dict[key] = val
    return phoneme_dict


def load_unknowns_dict(unknowns_file):
    '''Loads an existing unknowns dictionary from the tsv file given by the
    unknowns file parameter. Returns the dictionary.'''
    unknowns_dict = {}
    with open(unknowns_file, 'r') as dict_file:
        for line in dict_file:
            line = line.strip()
            if line and line[0] != '#':
                line_elements = line.split('\t')
                assert(len(line_elements) >= 2)
                word = line_elements[0].lower()
                count = int(line_elements[1])
                unknowns_dict[word] = count
    return unknowns_dict


def dict_to_tsv(dictionary):
    '''Converts an unknown words dictionary into tsv format for writing to
    stderr or an unknowns file. Returns a string which is of tsv format, with
    each line being a word and the count of its occurrences, separated by a tab
    character.'''
    out_list = []
    for key in sorted(dictionary, key=lambda x: dictionary[x], reverse=True):
        out_list.append('\t'.join([key, str(dictionary[key])]))
    return '\n'.join(out_list) + '\n'


def get_phonemes_and_unknowns(in_string, preserve_emphasis=False, phoneme_dict=nltk.corpus.cmudict.dict(), unknowns_dict={}):
    '''Converts character text into phonemes by using the Carnegie Mellon
    University phoneme dictionary from nltk.corpus.cmudict.dict(), or another
    dictionary provided by the phoneme_dict argument which maps words to
    phonemes as follows:
        'a': [['AH0'], ['EY1']]
    where the value for any given key is a list of pronunciations for the given
    word, and each pronunciation is given by a list of phonemes. The words from
    each line of input (excluding the character's name and play code) are
    converted to phonemes using this dictionary, and returned in a string of the
    same form as the input string (given by in_string). If words are not in the
    phoneme dictionary, they will be added to the unknowns dictionary along with
    the number of times they occur. Existing dictionaries may be passed in, and
    the counts for existing entries will be incremented. The output string of
    phonemes and the unknowns_dict are returned as a tuple.'''
    out_list = []
    for row in in_string.strip().split('\n'):
        words = row.split()
        assert(len(words) >= 2)
        TCPcode = words[0]
        character = words[1]
        row_list = [TCPcode, character]
        for word in words[2:]:
            word = word.lower()
            if word in phoneme_dict:
                pronunciation = phoneme_dict[word][0]  # Use first pronunciation
                for phon in pronunciation:
                    if phon[-1].isdigit() and not preserve_emphasis:
                        row_list.append(phon[:-1])
                    else:
                        row_list.append(phon)
            else:
                if word not in unknowns_dict:
                    unknowns_dict[word] = 0
                unknowns_dict[word] += 1
        out_list.append(' '.join(row_list))
    return ('\n'.join(out_list) + '\n', unknowns_dict)


def parse_phonemes(arg_list):
    '''Parses command-line arguments and runs the core get_phonemes_and_unknowns()
    function accordingly. Writes the output to stdout unless an output file is
    specified using the -o flag. Writes unknowns to stderr in tsv format unless
    an unknowns file is specified using the -u flag.'''
    optlist, args = getopt.getopt(arg_list, 'hei:o:u:l:d:s:')
    preserve_emphasis = False
    infile = sys.stdin
    outfile = sys.stdout
    unknowns_file = sys.stderr
    unknowns_dict = {}
    dict_filename = ''
    separator = ','
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - translate character speech from words into phonemes

    Usage:
        python3 {0} [OPTION]... 

    Reads one character's cleaned and modernized text per line of stdin, where
    each line is a string of words separated by spaces. The first word is the
    TCP code, the second word being the character's name, and the remaining
    words being the cleaned and modernized words spoken by that character.
    Thus, stdin is of the form:
        TCPcode character word [word]...\\n

    Writes one character's phoneme string per line of stdout, where each line is
    space-separated words, with the first word being the TCP code, the second
    word being the character's name, and the remaining words being the character's
    phonemes in the order in which they occur in their speech.
    Thus, stdout is of the form:
        TCPcode character phoneme [phoneme]...\\n


    -h              Display this help message.

    -e              Preserve emphasis markings on vowel phonemes

    -i filename     Specify an input file from which to read the cleaned and
                        modernized text for each character, where each line of
                        the file is of the format described above. If this option
                        is specified, then does not read from stdin.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.

    -u filename     Specify an output file to which to write the unknown word
                        counts in tsv format, rather than writing to stderr.

    -l filename     Specify an unknowns tsv file from which to load an existing
                        unknowns dictionary, which will be incremented as
                        needed.

    -d dictfile     Specify the phoneme dictionary file to be used to translate
                        words into phonemes.
                        If multiple dictionaries are to be used, simply call
                        this program multiple times with different files
                        specified using -d. The output of this program can be
                        piped directly into another instance of the program
                        using the standard POSIX pipe API.
                        Ex:
                            $ python3 extract.py A08360.xml | python3 clean.py | \\
                              python3 translate.py | python3 {0} | \\
                              python3 {0} -d custom_dict.csv

    -s separator    Specify the separator used by the dictionary file.
                        To use a space character, use the flag as -s " "
                        To use a tab character, use the flag as -s "\\t"
'''.format(sys.argv[0]))
            exit(0)
        if o == '-e':
            preserve_emphasis = True
        if o == '-i':
            infile = open(a, 'r')
        if o == '-o':
            outfile = open(a, 'w')
        if o == '-u':
            unknowns_file = open(a, 'w')
        if o == '-l':
            unknowns_dict = load_unknowns_dict(a)
        if o == '-d':
            dict_filename = a
        if o == '-s':
            separator = a
            if separator == '\\t' or separator == '\\\\t':
                separator == '\t'
    if dict_filename != '':
        phoneme_dict = load_phoneme_dict(a, separator)
    else:
        phoneme_dict = nltk.corpus.cmudict.dict()
    in_string = infile.read()
    out_string, unknowns_dict = get_phonemes_and_unknowns(in_string, preserve_emphasis, phoneme_dict, unknowns_dict)
    outfile.write(out_string)
    unknowns_file.write(dict_to_tsv(unknowns_dict))
    if infile != sys.stdin:
        infile.close()
    if outfile != sys.stdout:
        outfile.close()
    if unknowns_file != sys.stderr:
        unknowns_file.close()


def main():
    parse_phonemes(sys.argv[1:])


if __name__ == '__main__':
    main()
