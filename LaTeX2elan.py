import re

doc_header_info = """<?xml version="1.0" encoding="UTF-8"?>
<ANNOTATION_DOCUMENT AUTHOR="" DATE="2021-07-07T18:23:20+12:00" FORMAT="3.0" VERSION="3.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.mpi.nl/tools/elan/EAFv3.0.xsd">
    <HEADER MEDIA_FILE="" TIME_UNITS="milliseconds">
        <MEDIA_DESCRIPTOR MEDIA_URL="ABSOLUTE_FILEPATH.wav" MIME_TYPE="audio/x-wav" RELATIVE_MEDIA_URL="RELATIVE_FILEPATH.wav"/>
        <PROPERTY NAME="URN">urn:nl-mpi-tools-elan-eaf:6d60ea90-53bc-42ad-b1b5-613f79d1b43a</PROPERTY>
        <PROPERTY NAME="lastUsedAnnotationId">20</PROPERTY>
    </HEADER>\n"""

doc_ending = """    <LINGUISTIC_TYPE GRAPHIC_REFERENCES="false" LINGUISTIC_TYPE_ID="default-lt" TIME_ALIGNABLE="true"/>
    <LINGUISTIC_TYPE CONSTRAINTS="Included_In" GRAPHIC_REFERENCES="false" LINGUISTIC_TYPE_ID="wordtoword" TIME_ALIGNABLE="true"/>
    <LOCALE LANGUAGE_CODE="en"/>
    <CONSTRAINT DESCRIPTION="Time subdivision of parent annotation's time interval, no time gaps allowed within this interval" STEREOTYPE="Time_Subdivision"/>
    <CONSTRAINT DESCRIPTION="Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered" STEREOTYPE="Symbolic_Subdivision"/>
    <CONSTRAINT DESCRIPTION="1-1 association with a parent annotation" STEREOTYPE="Symbolic_Association"/>
    <CONSTRAINT DESCRIPTION="Time alignable annotations within the parent annotation's time interval, gaps are allowed" STEREOTYPE="Included_In"/>
</ANNOTATION_DOCUMENT>"""

NEW_LINE = ' \\\n'
AMPERSAND = ' & '

class Counter:
    """
    helper class that provides autoincrementing int variable
    """
    
    def __init__(self):
        self.__counter = 0
 
    def __call__(self, *args, **kwargs):
        self.__counter += 1
        return self.__counter

class Item:
    """
    small structure to store data about phrase with timecodes
    phrase is either transcription, or translation, or glossed phrase, or comment

    Args:
       TIME_SLOT_REF1 (str): timecode start (ms)
       TIME_SLOT_REF2 (str): timecode finish (ms)
       string (str): phrase
    """
    string = ''
    TIME_SLOT_REF1, TIME_SLOT_REF2 = '', ''
    def __init__(self, string, TIME_SLOT_REF1, TIME_SLOT_REF2):
        self.string = string
        self.TIME_SLOT_REF1 = TIME_SLOT_REF1
        self.TIME_SLOT_REF2 = TIME_SLOT_REF2

def convert_timecode(time_interval):
    """
    convert time from '00:12:11.454' to milliseconds

    Args:
       TIME_SLOT_REF1 (str): timecode start (ms)
       TIME_SLOT_REF2 (str): timecode finish (ms)
       string (str): phrase
    Returns:
       result (list(str, str)): converted timecodes
    """
    
    time_start, time_finish = time_interval[0], time_interval[1]
    result = []
    for s in [time_start, time_finish]:
        chunks = list(map(int, re.split(':|\.', s)))
        time_in_ms = chunks[-1] + ((chunks[0]*60+chunks[1])*60+chunks[2])*1000
        result.append(str(time_in_ms))
    return result

def find_block(data, line_id):
    """
    find first line of next information block in .tex file

    Args:
       data (str): file content
       line_id (int): current line number
    Returns:
       line_id (int): first line of next information block
    """
    
    search_label="cell{5}{1} = {c=\columncnt}{l}\n"
    while line_id < len(data) and data[line_id] != search_label:
        line_id += 1
        continue
    return line_id

def parse_block(data, line_id):
    """
    extract info about one audio description entry

    Args:
       data (str): file content
       line_id (int): current line number
    Returns:
       (time_start, time_finish, transc, gloss, transl, comment)
       entry's timestamps, transcription, glosses, translation, (optional) comment
    """
    line_id += 2
    transc = (data[line_id].rstrip(NEW_LINE)).split(AMPERSAND)
    line_id += 1
    gloss = (data[line_id].rstrip(NEW_LINE)).split(AMPERSAND)
    line_id += 1
    transl = data[line_id].lstrip('\enquote{').rstrip('}'+NEW_LINE)
    line_id += 1
    time_start, time_finish = convert_timecode(data[line_id].rstrip(NEW_LINE).split(' — '))
    line_id += 1
    
    comment = ''
    if data[line_id] != '\end{tblr}\n':
        comment = data[line_id].rstrip(NEW_LINE)
        
    transc = ' '.join(transc)
    gloss = ' '.join(gloss).lower()
    return time_start, time_finish, transc, gloss, transl, comment
            
def latex_data(file_path):
    """
    collect data from delimited file, imported from LaTeX

    Args:
       file_path (str): txt file
    Returns:
        (timeslots, transcs, transls, glosses, comments):
        arrays of entries' transcriptions, translations, glosses, comments
    """
    
    line_id = 0
    transls = []
    transcs = []
    glosses = []
    comments = []
    timeslots = []
    TIME_SLOT_REF_CNT = Counter()
    
    with open(file_path, 'r') as fp:
        data = fp.readlines()
        while line_id < len(data):
            line_id = find_block(data, line_id)
            if line_id == len(data):
                break
            time_start, time_finish, transc, gloss, transl, comment = parse_block(data, line_id)
            
            refs1 = [TIME_SLOT_REF_CNT() for _ in range(3)]
            if comment != '':
                refs1.append(TIME_SLOT_REF_CNT())
            refs2 = [TIME_SLOT_REF_CNT() for _ in range(3)]
            if comment != '':
                refs2.append(TIME_SLOT_REF_CNT())
            
            for ref in refs1:
                timeslots.append([ref, time_start])
            for ref in refs2:
                timeslots.append([ref, time_finish])
            
            ref_index = 0
            for string, array in zip([transc, transl, gloss], [transcs, transls, glosses]):
                time_ref1, time_ref2 = refs1[ref_index], refs2[ref_index]
                array.append(Item(string, time_ref1, time_ref2))
                ref_index += 1
            
            if comment != '':
                time_ref1, time_ref2 = refs1[ref_index], refs2[ref_index]
                comments.append(Item(comment, time_ref1, time_ref2))
            line_id += 1
                
    return timeslots, transcs, transls, glosses, comments

ANNOTATION_ID_CNT = Counter()
def write_tier(file, array):
    """
    write info about one channel to file

    Args:
       array (list): list of Items. represents information about either transcriptions, or translations,
       or glossed phrases, or comments with timecodes
       file (str): eaf file
    """
    
    annotation_pattern = """        <ANNOTATION>
            <ALIGNABLE_ANNOTATION ANNOTATION_ID="a{}" TIME_SLOT_REF1="ts{}" TIME_SLOT_REF2="ts{}">
                <ANNOTATION_VALUE>{}</ANNOTATION_VALUE>
            </ALIGNABLE_ANNOTATION>
        </ANNOTATION>\n"""
    
    for item in array:
        file.write(annotation_pattern.format(ANNOTATION_ID_CNT(), item.TIME_SLOT_REF1, item.TIME_SLOT_REF2, item.string))
        
    file.write('    </TIER>\n')
    
def to_elan(file_path, audio_path, timeslots, transcs, transls, glosses, comments):
    """
    convert data from parsed LaTex file to ELAN file with the same name

    Args:
       file_path (str): eaf file
       audio_path (str): wav file
       timeslots (list): list of timeslot values (in ms)
       transcs (list): list of transcriptions
       transls (list): list of translations
       glosses (list): list of glosses
       comments (list): list of comments
    """
    
    timeslot_pattern = """        <TIME_SLOT TIME_SLOT_ID="ts{}" TIME_VALUE="{}"/>\n"""
    tier_pattern = """    <TIER {}LINGUISTIC_TYPE_REF="{}" {}TIER_ID="{}">\n"""
    
    file = open(file_path, "w")
    file.write(doc_header_info)
    
    file.write('    <TIME_ORDER>\n')
    for timeslot in timeslots:
        file.write(timeslot_pattern.format(timeslot[0], timeslot[1]))
    file.write('    </TIME_ORDER>\n')
    
    file.write(tier_pattern.format('DEFAULT_LOCALE="en" ', 'default-lt', '', 'transcription'))
    write_tier(file, transcs)
    
    file.write(tier_pattern.format('DEFAULT_LOCALE="en" ', 'wordtoword', 'PARENT_REF="transcription" ', 'translation'))
    write_tier(file, transls)
    
    file.write(tier_pattern.format('DEFAULT_LOCALE="en" ', 'wordtoword', 'PARENT_REF="transcription" ', 'gloss'))
    write_tier(file, glosses)
    
    file.write(tier_pattern.format('', 'wordtoword', 'PARENT_REF="transcription" ', 'comment'))
    write_tier(file, comments)
    
    file.write(doc_ending)
    file.close()
    
def main():
    file = input('Input the name of .tex file, imported from LaTeX (default = 1.tex on Enter) \n')
    audio = input('Input the name of associated audio .wav file (default = 1.wav on Enter) \n')
    # TODO use .wav file in document header

    if file == '':
        file = '1.tex'
    output_file = file[:-3]+'eaf'
    if audio == '':
        audio = '1.wav'
    
    timeslots, transcs, transls, glosses, comments = latex_data(file)
    
    to_latex(file, audio, timeslots, transcs, transls, glosses, comments)


if __name__ == '__main__':
    main()
