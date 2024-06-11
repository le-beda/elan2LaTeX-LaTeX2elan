import re
from collections import defaultdict

BACKSLASH = '\\'
SKIP_LINE = '\n\n'

specials = ['\\' '{', '}', '#', '^', '␣', '%']

def in_fig(text):
    return '{' + text + '}'

def open_file(filename):
    text = open(filename, encoding='utf-8').read()
    return text

def fakeverb(text):
    for special in specials:
        text = text.replace(special, BACKSLASH + special)
    return text


def elan_data(file):
    # elan = elan.replace('&', '')
    # elan = elan.replace('<', '&lt;')
    # elan = elan.replace('>', '&gt;')
    elan = open_file(file).splitlines()
    transc = defaultdict(str)
    transl = defaultdict(str)
    gloss = defaultdict(str)
    comment = defaultdict(str)

    for line in elan:
        tokens = line.split('\t')
        if len(tokens) == 9:
            indices = (0, 2, 4, 8)
        else:
            indices = (0, 2, 3, 4)

        layer = tokens[indices[0]]
        time_start = tokens[indices[1]]
        time_finish = tokens[indices[2]]
        text = tokens[indices[3]]

        if layer == 'transcription':
            transc[(time_start, time_finish)] = text
        elif layer == 'translation':
            transl[(time_start, time_finish)] = text
        elif layer == 'gloss':
            gloss[(time_start, time_finish)] = text
        elif layer == 'comment':
            comment[(time_start, time_finish)] = text
    return transc, transl, gloss, comment


def to_latex(file):
    if file == '':
        file = '1.txt'
    transc, transl, gloss, comment = elan_data(file)
    pivot_dictionary = mapping(transc, transl, gloss, comment)

    informant = input('Enter informant code ')
    expeditioner = input('Enter expeditioner code ')
    expeditiondate = input('Enter epedition date ')
    whoelse = input('Who else was there? ')
    theme = input('Approx theme? ')

    tex_file = '.'.join(file.split('.')[:-1]) + '.tex'

    with open(tex_file, "w") as f:
        with open("header.tex", "r") as header:
            f.write(header.read()) 

        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH+'informant')}{in_fig(informant)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH+'expeditioner')}{in_fig(expeditioner)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH+'expeditiondate')}{in_fig(expeditiondate)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH+'whoelse')}{in_fig(whoelse)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH+'theme')}{in_fig(theme)}" + SKIP_LINE)

        with open("metadata.tex", "r") as metadata:
            f.write(metadata.read()) 

        for key, value in pivot_dictionary.items():

            transcription = value[0]
            translation = value[1]
            gloss = value[2]
            comment = value[3]

            transcription_tokens = transcription.split(' ')
            glosses_tokens = gloss.split(' ')
            len_transc = len(transcription_tokens)
            len_gloss = len(glosses_tokens)
            if len_transc > len_gloss:
                glosses_tokens.extend([''] * (len_transc - len_gloss))
            elif len_gloss > len_transc:
                transcription_tokens.extend([''] * (len_gloss - len_transc))

            word_cnt = len(transcription_tokens)
            f.write( '\\renewcommand{\\columncnt}' + in_fig(str(word_cnt)) + '\n' )

            with open("subsection_header.tex", "r") as subsection_header:
                f.write(subsection_header.read()) 

            f.write(' & '.join(map(lambda  x: fakeverb(x), transcription_tokens)) + ' ' + BACKSLASH*2 + '\n' )
            f.write(' & '.join(map(lambda  x: fakeverb(x), glosses_tokens)) + ' ' + BACKSLASH*2 + '\n')
            # f.write(BACKSLASH + 'enquote' + in_fig(translation) + ' ' + BACKSLASH*2 + '\n' )
            f.write(fakeverb('"' + translation + '"') + ' ' + BACKSLASH*2 + '\n' )
            f.write(fakeverb(f'{key[0]} — {key[1]}') + ' ' + BACKSLASH*2 + '\n' )
            f.write(fakeverb(comment) + ( ' ' + BACKSLASH*2 + '\n') * (comment != ''))

            f.write("\\end{tblr}" + SKIP_LINE)

        f.write('\\end{document}') 


def mapping(transc, transl, gloss, comment):
    pivot_dic = {}
    for key, value in transc.items():
        trnsl = transl[key]
        gls = gloss[key]
        cmnt = comment[key]
        pivot_dic[key] = [value, trnsl, gls, cmnt]
    return pivot_dic


def glossing(text):
    # text = text.replace(' ', '\t')
    glossed_text = re.split(r'([a-z+])', text)
    return glossed_text


def main():
    file = input('Input the name of .txt file, imported from ELAN (default = 1.txt on Enter) ')
    to_latex(file)


if __name__ == '__main__':
    main()