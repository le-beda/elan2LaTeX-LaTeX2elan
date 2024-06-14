from collections import defaultdict

BACKSLASH = '\\'
SKIP_LINE = '\n\n'
SPECIALS = ['\\' '{', '}', '#', '^', '␣', '%']


def in_fig(text):
    """
    incase text in {}

    Args:
       text (str): initial text
    Returns:
        text (str): {text}
    """
    return '{' + text + '}'


def remove_specials(text):
    """
    add backslashes to the following special symbols: \\, \{, \}, \#, \^, \␣, \%

    Args:
       text (str): text with special symbols
    Returns:
        text (str): text with removed special symbols
    """
    for special in SPECIALS:
        text = text.replace(special, BACKSLASH + special)
    return text


def elan_data(file):
    """
    collect data from delimited file, imported from ELAN

    Args:
       file (str): txt file
    Returns:
        (transc, transl, gloss, comment):
        arrays of entries' transcriptions, translations, glosses, comments
    """
    with open(file, encoding='utf-8') as f:
        elan = f.read().splitlines()

    transc = defaultdict(str)
    transl = defaultdict(str)
    gloss = defaultdict(str)
    comment = defaultdict(str)

    for line in elan:
        tokens = line.split('\t')
        if len(tokens) == 9:
            indices = (0, 2, 4, 8)  # with ticked duration option on ELAN export
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


def mapping(transc, transl, gloss, comment):
    """
    map entries by timestamps

    Args:
        transc: array of entries' transcriptions
        transl: array of entries' translations
        gloss: array of entries' glosses
        comment: array of entries' comments
    Returns:
        pivot_dic: dict of timestamps: [transcription, translation, gloss, comment]
    """
    pivot_dic = {}

    for key, value in transc.items():
        trnsl = transl[key]
        gls = gloss[key]
        cmnt = comment[key]
        pivot_dic[key] = [value, trnsl, gls, cmnt]

    return pivot_dic


def to_latex(file):
    """
    convert delimited file, imported from ELAN, to LaTeX file with the same name

    Args:
       file (str): txt file
    """
    if file == '':
        file = '1.txt'
    transc, transl, gloss, comment = elan_data(file)
    pivot_dictionary = mapping(transc, transl, gloss, comment)

    informant = input('Enter informant code \n')
    expeditioner = input('Enter expeditioner code \n')
    expeditiondate = input('Enter epedition date \n')
    whoelse = input('Who else was there? \n')
    theme = input('Approx theme? \n')

    tex_file = '.'.join(file.split('.')[:-1]) + '.tex'

    with open(tex_file, "w") as f:
        f.write("\\documentclass[a4paper,12pt]{article}\n")

        languages = input(
'''Input languages present in your document, separated by commas.
In babel usepackage last language is considered the main one, activated by default.
(default = "english, russian" on Enter)\n'''
        )
        if languages == '':
            languages = "english, russian"

        f.write(f"\\usepackage[{languages}]" + "{babel}\n")

        with open("header.tex", "r") as header:
            f.write(header.read())

        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH + 'informant')}{in_fig(informant)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH + 'expeditioner')}{in_fig(expeditioner)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH + 'expeditiondate')}{in_fig(expeditiondate)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH + 'whoelse')}{in_fig(whoelse)}\n")
        f.write(f"{BACKSLASH}newcommand{in_fig(BACKSLASH + 'theme')}{in_fig(theme)}" + SKIP_LINE)

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
            f.write('\\renewcommand{\\columncnt}' + in_fig(str(word_cnt)) + '\n')

            with open("subsection_header.tex", "r") as subsection_header:
                f.write(subsection_header.read())

            f.write(' & '.join(map(lambda x: remove_specials(x), transcription_tokens)) + ' ' + BACKSLASH * 2 + '\n')
            f.write(' & '.join(map(lambda x: remove_specials(x), glosses_tokens)) + ' ' + BACKSLASH * 2 + '\n')
            f.write(BACKSLASH + 'enquote' + in_fig(translation) + ' ' + BACKSLASH*2 + '\n' )
            # f.write(remove_specials('"' + translation + '"') + ' ' + BACKSLASH * 2 + '\n')
            f.write(remove_specials(f'{key[0]} — {key[1]}') + ' ' + BACKSLASH * 2 + '\n')
            f.write(remove_specials(comment) + (' ' + BACKSLASH * 2 + '\n') * (comment != ''))

            f.write("\\end{tblr}" + SKIP_LINE)

        f.write('\\end{document}')


def main():
    file = input('Input the name of .txt file, imported from ELAN (default = 1.txt on Enter) \n')
    to_latex(file)


if __name__ == '__main__':
    main()
