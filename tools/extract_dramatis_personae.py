#!/usr/bin/python3

import sys
import getopt
import os
import xml.etree.ElementTree as ET
sys.path.append(sys.path[0] + '/..')  # Assuming script is in tools directory, add project directory to path
import pipeline.clean as clean


def extract_dramatis_personae(filename):
    '''Returns a tsv string where each row is separated by a newline \\n. The
    first element of each row is the TCP code followed by a hyphen and the
    number of the <div type="dramatis_personae"> tag in which the character
    speech was found, and the following element of the row is the character's
    name and description from the dramatis personae div element, cleaned by
    replacing newline characters and tabs with spaces and removing xml elements
    similarly to clean.py'''
    try:
        root = ET.parse(filename).getroot()
    except ET.ParseError:
        print('ERROR: File {} could not be parsed.'.format(filename), file=sys.stederr)
        return ''
    root_tag = root.tag
    url = root_tag[:root_tag.find('}') + 1]
    tsv_list = []
    count = 0
    for div in root.iter(url + 'div'):
        if 'type' in div.attrib and div.attrib['type'] == 'dramatis_personae':
            count += 1
            elements = []
            for item in div.iter(url + 'item'):  # First get all items, if there are any
                if len([l for l in item.iter(url + 'list')]) == 0:  # Skip this item if it contains another list
                    elements.append(item)
            for p in div.iter(url + 'items'):  # Get all <p> elements, including ones containing tables
                elements.append(p)
            contents = []
            for elem in elements:
                table = elem.find(url + 'table')
                if table is None:
                    table = elem.find('table')
                tables = [t for t in elem.iter(url + 'table')]
                if table is None and len(tables) > 0:
                    print('WARNING: {}-{}\n    Table in item but table is not found as a child of the element'.format(filename, count), file=sys.stderr)
                    print(ET.tostring(elem), file=sys.stderr)
                    print(file=sys.stderr)
                if table is not None:  # There is a table, so take the first cell from each row
                    found_row = False
                    for row in table.findall(url + 'row'):
                        found_row = True
                        for cell in row.findall(url + 'cell'):
                            contents.append(ET.tostring(cell, encoding='unicode'))
                    if not found_row:
                        print('WARNING: {}-{}\n    Failed to find row in table:'.format(filename, count), file=sys.stderr)
                        print(ET.tostring(table), file=sys.stderr)
                        print(file=sys.stderr)
                else:
                    contents.append(ET.tostring(elem, encoding='unicode'))

            xml_dict = clean.get_xml_dictionary()
            for content in contents:

                content = content.replace('\n', ' ')
                content = content.replace('\t', ' ')
                content = content.strip()
                if content:

                    try:
                        element = ET.fromstring(content)
                    except ET.ParseError:
                        print('ERROR: {}-{}\n    Failed to parse text:'.format(filename, count), file=sys.stderr)
                        print(content, file=sys.stderr)
                        print(file=sys.stderr)
                        exit(1)
                    for tag_del in clean.get_xml_delete() + ['label']:
                        clean.remove_tags(element, clean.get_ns_tag(tag_del))
                    content = ET.tostring(element, encoding='unicode')

                    content = clean.fill_gaps(content)

                    for key in xml_dict:
                        if key in content:
                            content = content.replace(key, xml_dict[key])

                    content = clean.ignore_tags(content, clean.get_xml_ignore() + ['p', 'cell'])

                    content = clean.remove_abbreviations(content)

                    while '  ' in content:
                        content = content.replace('  ', ' ')
                    content = content.strip()

                    if '<' in content or '>' in content:
                        print('WARNING: {}-{}\n    Text not fully cleaned of xml.'.format(filename, count), file=sys.stderr)
                        print(content, file=sys.stderr)
                        print(file=sys.stderr)
                        quit()

                    if content:
                        filename_id = filename.split('/')[-1]
                        row = [filename_id.replace('.xml', '') + '-' + str(count), content]
                        tsv_list.append('\t'.join(row))
    return '\n'.join(tsv_list) + '\n'


def parse_csv(filename, column=0):
    filenames = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            filenames.append(row[column] + '.xml')
    return filenames


def parse_extract_dramatis_personae(arg_list):
    '''Parses command-line arguments and runs core extract_dramatis_personae()
    function accordingly. Writes the output to stdout unless an output file is
    specified using the -o flag.'''
    optlist, args = getopt.getopt(arg_list, 'hd:c:o:')
    in_directory = ''
    outfile = sys.stdout
    for o, a in optlist:
        if o == '-h':
            print('''
Usage information for {0}

    {0} - extracts character names from dramatis personae divs

    Usage:
        python3 {0} [OPTION]... [FILE]...

    Writes one character's name (and description if it exists) per line to
    stdout, where each line is in the style of a tsv row, with the first element
    being the TCP code followed by a hyphen and the number of the dramatis
    personae div in which the character was found in the given xml file, and the
    second element being the character's name and description.
    Thus, stdout is of the form:
        TCPcode-1\\tcharacter\\txmltext[\\txmltext]...\\n


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
            in_directory = a.rstrip('/') + '/'
        if o == '-c':
            args += parse_csv(a)
        if o == '-o':
            outfile = open(a, 'w')
    dramatis_personae_string_list = []
    for filename in args:
        filename = in_directory + filename
        dramatis_personae_string = extract_dramatis_personae(filename)
        if dramatis_personae_string.strip():
            dramatis_personae_string_list.append(extract_dramatis_personae(filename).strip())
        else:
            print('WARNING: No dramatis personae elements found in the entirety of file {}'.format(filename), file=sys.stderr)
    tsv_string = '\n'.join(dramatis_personae_string_list) + '\n'
    outfile.write(tsv_string)
    if outfile != sys.stdout:
        outfile.close()


def main():
    if len(sys.argv) == 1:
        print('Please include filename of xml file from which to extract text,', file=sys.stderr)
        print('or include -c csvfile containing metadata with TCP codes.', file=sys.stderr)
        exit(1)
    parse_extract_dramatis_personae(sys.argv[1:])


if __name__ == '__main__':
    main()
