#!/usr/bin/python3

import sys
import getopt
import xml.etree.ElementTree as ET


def get_child_lps(root):
    '''Recursively finds all child <l> or <p> elements, ensuring that <l> or <p>
    tags inside of other <l> or <p> tags are only counted once, as part of their
    parent's xml content.'''
    url = root.tag[:root.tag.find('}') + 1]
    lps = []
    for child in root:
        if child.tag == url + 'l' or child.tag == url + 'p':
            lps.append(child)
        else:
            lps += get_child_lps(child)
    return lps


def extract(filename):
    '''Returns a tsv string where each row is separated by a newline \\n. The
    first element of each row is the TCP code followed by a hyphen and the
    number of the <text> tag in which the character speech was found, the second
    element of the row is the character name, and the remaining elements are the
    raw xml <l>...</l> elements, with newline characters within the xml replaced
    by ' ' in order to allow the tsv formatting.'''
    try:
        root = ET.parse(filename).getroot()
    except ET.ParseError:
        print('ERROR: File {} could not be parsed.'.format(filename), file=sys.stderr)
        return ''
    root_tag = root.tag
    url = root_tag[:root_tag.find('}') + 1]
    tsv_list = []
    count = 0
    for text in root.iter(url + 'text'):  # Each "play of interest" has at least one <text> tag
        has_inner_text = False
        for sub_text in text.iter(url + 'text'):  # If the text element has an inner text element, ignore the former
            if sub_text != text:
                has_inner_text = True
        if has_inner_text:
            print('WARNING: {}\n    Skipping <text> tag because it contains an inner <text> tag.'.format(filename), file=sys.stderr)
            continue
        else:  # <text> tag has no inner <text> tags, so it is assumed that it specifies a single complete text
            count += 1
            parts = {}
            for sp in text.iter(url + 'sp'):
                speaker_iter = sp.iter(url + 'speaker')
                speaker = ''
                for s in speaker_iter:  # should only loop once
                    speaker = (speaker + ' '.join([text for text in s.itertext()])).replace('\n', ' ').strip()
                while '  ' in speaker:
                    speaker = speaker.replace('  ', ' ')
                if speaker == '':
                    print('WARNING: {}\n    No speaker for <sp> tag with elements:'.format(filename), file=sys.stderr)
                    print(ET.tostring(sp, encoding='unicode'), file=sys.stderr)
                    continue
                if speaker not in parts:
                    parts[speaker] = []
                child_lps = get_child_lps(sp)
                for lp in child_lps:
                    raw_text = ET.tostring(lp, encoding='unicode').strip()
                    text = raw_text[:raw_text.rfind('>') + 1]
                    if text != raw_text:
                        print('WARNING: {} {}\n    <l> or <p> element had trailing text, which was stripped:'.format(filename, speaker), file=sys.stderr)
                        print(raw_text, file=sys.stderr)
                        print('\n', file=sys.stderr)
                    text = text.replace('\n', ' ')
                    text = text.replace('\t', ' ')
                    text = text.strip()
                    if text:
                        parts[speaker].append(text)
            for speaker in sorted(parts):
                filename_id = filename.split('/')[-1]
                row = [filename_id.replace('.xml', '') + '-' + str(count), speaker] + parts[speaker]
                tsv_list.append('\t'.join(row))
    return '\n'.join(tsv_list) + '\n'


def parse_csv(filename, column=0):
    filenames = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            filenames.append(row[column] + '.xml')
    return filenames


def parse_extract(arg_list):
    '''Parses command-line arguments and runs the core extract() function
    accordingly. Writes the output to stdout unless an output file is specified
    using the -o flag.'''
    optlist, args = getopt.getopt(arg_list, 'hd:c:o:')
    in_directory = ''
    outfile = sys.stdout
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - extracts raw character speech from xml TCP files

    Usage:
        python3 {0} [OPTION]... [FILE]...

    Writes one character's xml text per line to stdout, where each line is in
    the style of a tsv row, with the first element being the TCP code, the
    second element being the character's name, and the remaining elements being
    the xml <l>...</l> tags containing the speech of that character. Thus,
    stdout is of the form:
        TCPcode\\tcharacter\\txmltext[\\txmltext]...\\n


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
'''.format(sys.argv[0]))
            exit(0)
        if o == '-d':
            # Specify the dirctory in which xml files are stored
            # This directory is prepended to all filenames supplied
            # in as arguments, and also to all filenames given by 
            # TCP codes in a csv file.
            # If different xml files in different directories, then
            # please specify directory as part of path to filename,
            # and do not use this option.
            in_directory = a.rstrip('/') + '/'
        if o == '-c':
            # Specify a csv file from which to read filenames.
            # If -d flag is also used, then input directory will be
            # prepended to each TCP code found in this csv file.
            args += parse_csv(a)
        if o == '-o':
            # Specify an output file instead of stdout.
            outfile = open(a, 'w', encoding='utf-8')
    file_string_list = []
    for filename in args:
        filename = in_directory + filename
        file_string = extract(filename)
        if file_string.strip():
            file_string_list.append(extract(filename).strip())
        else:
            print('WARNING: No <sp> tags found in the entirety of file {}'.format(filename), file=sys.stderr)
    tsv_string = '\n'.join(file_string_list) + '\n'
    outfile.write(tsv_string)
    if outfile != sys.stdout:
        outfile.close()


def main():
    if len(sys.argv) == 1:
        print('Please include filename of xml file from which to extract text,', file=sys.stderr)
        print('or include -c csvfile containing metadata with TCP codes.', file=sys.stderr)
        exit(1)
    parse_extract(sys.argv[1:])


if __name__ == '__main__':
    main()
