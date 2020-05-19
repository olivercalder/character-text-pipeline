#!/usr/bin/python3

import sys
import getopt
import codecs
import xml.etree.ElementTree as ET
import conversion_dict


def get_ns_tag(tag):
    return '{http://www.tei-c.org/ns/1.0}' + tag


def tag_opener(tag_str):
    return '<ns0:{}'.format(tag_str)


def start_tag(tag_str):
    return '<ns0:{} xmlns:ns0="http://www.tei-c.org/ns/1.0">'.format(tag_str)


def end_tag(tag_str):
    return '</ns0:{}>'.format(tag_str)


def get_xml_delete():
    '''Returns list of tags to delete, removing the tag and its text contents.'''
    delete_list = [
            'note',
            'pb',
            'stage'
            ]
    return delete_list


def get_xml_ignore():
    '''Returns list of tags to ignore, leaving their inner text in place.'''
    ignore_list = [
            'hi',
            'seg',
            'expan',
            'am',
            'ex',
            'list',
            'item',
            ]
    return ignore_list


def get_xml_dictionary():
    '''Returns dictionary to convert special xml characters to ASCII.'''
    xml_dict = {}
    xml_dict['<ns0:g ref="char:cmbAbbrStroke">̄</ns0:g>'] = 'm'
    xml_dict['<ns0:g ref="char:EOLhyphen"/>'] = ''
    xml_dict['<ns0:g ref="char:EOLhyphen" />'] = ''
    xml_dict['<ns0:g ref="char:abque"/>'] = ''
    xml_dict['<ns0:g ref="char:abque" />'] = ''
    xml_dict['<ns0:g ref="char:punc">▪</ns0:g>'] = ''
    xml_dict['<ns0:g ref="char:leaf">❧</ns0:g>'] = ''
    xml_dict['&amp;'] = 'and'
    xml_dict['&amp;c'] = 'etc'
    return xml_dict


def ignore_tags(text, tag_list):
    '''Removes the given tags from the text, leaving their inner text in place.'''
    for tag in tag_list:
        opener = tag_opener(tag)
        closer = end_tag(tag)
        while opener in text:
            start = text.find(opener)
            end = text.find('>', start)  # assume xml is well-formed and each tag is eventually closed
            text = text[:start] + text[end + 1:]
        while closer in text:  # no real need for a while loop here if using replace. Leaving it in case that changes
            text = text.replace(closer, '')
    return text


def fill_gaps(text):
    '''Finds <gap> tags and replaces them with ^ characters based on the extent value.'''
    while tag_opener('gap') in text:
        start = text.find(tag_opener('gap'))
        l = ET.fromstring(text)
        gap = l.find(get_ns_tag('gap'))
        if gap == None:
            gap = l.find('gap')
        if gap == None:
            print(text)
            print('\n\n')
            print('Can\'t find gap tag in <l>.')
            for child in l.iter():
                print(child.tag)
            exit()
        extent_str = gap.get('extent')
        extent = 0
        if extent_str is not None:
            extent_list = extent_str.split()
            if extent_list[1] == 'letter':  # if not letter, then just ignore the whole thing
                extent = int(extent_list[0])
        l.remove(gap)
        text = ET.tostring(l, encoding='unicode')
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        text = text[:start] + '^' * extent + text[start:]
    return text


def clean_xml(text):
    '''Cleans the given xml string by converting strings in the xml_dict to
    their corresponding values, then removing the tags in the xml ignore list
    (leaving their inner text in place), and then fully deleting all xml tags
    and their contents in the xml delete list. Returns the cleaned text, which
    should now be plaintext unicode with no xml formatting.'''

    xml_dict = get_xml_dictionary()
    for key in xml_dict:
        if key in text:
            text = text.replace(key, xml_dict[key])

    text = ignore_tags(text, get_xml_ignore())

    try:
        l = ET.fromstring(text)
    except ET.ParseError:
        print('\n\n', file=sys.stderr)
        print(text, file=sys.stderr)
        l = ET.fromstring(text)
    for tag_del in get_xml_delete():
        for node in l.findall(get_ns_tag(tag_del)):
            l.remove(node)
    text = ET.tostring(l, encoding='unicode')
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')

    text = fill_gaps(text)

    # Until this point, needed to preserve boundary tags in order to parse as xml
    # There may also be embedded <l> or <p> within the line
    text = ignore_tags(text, ['l', 'p'])

    if '<' in text or '>' in text:
        print('ERROR: Text not fully cleaned of xml.', file=sys.stderr)
        print(text, file=sys.stderr)
        exit(1)
    return text    


def clean_unicode(text):
    '''Cleans the given text by converting unicode characters to ASCII according
    to the dictionary in conversion_dict.py. Returns the cleaned text, which
    should be ASCII-conpatible characters. Inspired by the clean_word() function
    from characterCleaner.py, part of the VEP pipeline, which can be found here:
        https://github.com/uwgraphics/VEP-pipeline
    '''
    conv_dict = conversion_dict.getConversionDict()
    for char in text:
        try:
            codecs.encode(char, 'ascii', errors='strict')
        except UnicodeEncodeError:
            if char in conv_dict:
                text = text.replace(char, conv_dict[char])  # not great practice to modify an iterable as it is being iterated through
            else:
                text = text.replace(char, '@')
    text = text.replace('|', '')
    return text


def clean_punctuation(text):
    '''Cleans remaining punctuation which was not used for xml or unicode.'''
    for punc in ',.?!;:"()[]{}*':
        text = text.replace(punc, '')
    for punc in ['--']:
        text = text.replace(punc, ' ')
    return text


def clean(in_string):
    '''Cleans a tsv string by first resolving xml tags and special characters,
    and then replacing all non-ASCII characters with their ASCII equivalents
    using conversion_dict.py, which is a product of the VEP Pipeline project,
    found at  https://github.com/uwgraphics/VEP-pipeline
    Returns a string with rows separated by newline characters, where each row
    has words separated by spaces. The first word is the TCP code, the second
    word is the character, and all remaining words are the character's cleaned
    speech.'''
    out_list = []
    for row in in_string.strip().split('\n'):
        lines = row.split('\t')
        assert(len(lines) >= 2)
        TCPcode = lines[0]
        character = lines[1].replace(' ', '-')
        row_list = [TCPcode, character]
        for line in lines[2:]:
            text = clean_xml(line)
            text = clean_unicode(text)
            text = clean_punctuation(text)
            text = text.lower().strip()
            while '  ' in text:
                text = text.replace('  ', ' ')
            row_list.append(text)
        out_list.append(' '.join(row_list))
    return '\n'.join(out_list) + '\n'


def parse_clean(arg_list):
    '''Parses command-line arguments and runs the core clean() function
    accordingly. Writes the output to stdout unless an output file is specified
    using the -o flag.'''
    optlist, args = getopt.getopt(arg_list, 'hi:o:')
    infile = sys.stdin
    outfile = sys.stdout
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - clean character speech from xml output produced by extracy.py

    Usage:
        python3 {0} [OPTION]... 

    Reads one character's xml text per line of stdin, where each line is in
    the style of a tsv row, with the first element being the TCP code, the
    second element being the character's name, and the remaining elements being
    the xml <l>...</l> tags and their corresponding to that character. Thus,
    stdin is of the form:
        TCPcode\\tcharacter\\txmltext[\\txmltext]...\\n

    Writes one character's cleaned text per line of stdout, where each line is
    space-separated words, with the first word being the TCP code, the second
    word being the character's name, and the remaining words being the ascii
    cleaned words, though still in their Old English forms, when applicable.
    Thus, stdout is of the form:
        TCPcode character word [word]...\\n


    -h              Display this help message.

    -i filename     Specify an input tsv-like file from which to read character
                        xml text data. If this is specified, then does not read
                        from stdin.

    -o filename     Specify an output file to which to write output, rather
                        than writing to stdout.
'''.format(sys.argv[0]))
            exit(0)
        if o == '-i':
            infile = open(a, 'r', encoding='utf-8')
        if o == '-o':
            outfile = open(a, 'w')  # No need for utf-8 encoding after cleaning
    in_string = infile.read()
    out_string = clean(in_string)
    outfile.write(out_string)
    if infile != sys.stdin:
        infile.close()
    if outfile != sys.stdout:
        outfile.close()


def main():
    parse_clean(sys.argv[1:])


if __name__ == '__main__':
    main()
