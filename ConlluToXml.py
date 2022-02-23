import argparse
import glob
import os
import re

from tqdm import tqdm


def convert_upos(text):
    upos_dict = {
        "NOUN": "S",
        "PROPN": "S,propn",
        "VERB": "V",
        "ADJ": "A",
        "PRON": "SPRO",
        "DET": "APRO",
        "PRED": "PRAEDIC",
        "PREDPRO": "PRAEDICPRO",
        "ADP": "PR",
        "SCONJ": "CONJ",
        "CCONJ": "CONJ"
    }
    for key in upos_dict:
        if key == text:  # При совпадении upos и ключа в словаре, заменить на значение ключа
            text = upos_dict[key]
    return text


def convert_grammar(text):  # Замена
    grammar = text.split("|")
    grammar_swap_dict = {
        "Abbr=Yes": "abbr",
        #
        "Analyt=Yes": "analyt",
        #
        "Animacy=Anim": "anim",
        "Animacy=Inan": "inan",
        #
        "Anom=Yes": "anom",
        #
        "Aspect=Imp": "",
        "Aspect=Perf": "",
        #
        "Case=Nom": "nom",
        "Case=Nom1": "nom",
        "Case=Acc": "acc",
        "Case=Acc2": "acc2",
        "Case=Gen": "accgen",
        "Case=Par": "gen2",
        "Case=Dat": "dat",
        "Case=Dat2": "dat",
        "Case=Ins": "ins",
        "Case=Loc": "loc",
        "Case=Loc2": "loc2",
        "Case=Voc": "voc",
        #
        "Clitic=Yes": "cl",
        "Clitic=No": "ton",
        #
        "Degree=Pos": "comp",
        "Degree=Cmp": "comp",
        "Degree=Cmp2": "comp2",
        "Degree=Sup": "supr",
        #
        "Gender=Masc": "m",
        "Gender=Fem": "f",
        "Gender=Neut": "n",
        "Gender=Com": "mf",
        #
        "Mood=Cnd": "cond",
        "Mood=Imp": "imper",
        "Mood=Imp2": "imper2",
        "Mood=Ind": "indic",
        #
        "Number=Sing": "sg",
        "Number=Dual": "du",
        "Number=Plur": "pl",
        "Number=Adnum": "adnum",
        #
        "NumForm=Digit": "digit",
        "NumForm=Cyril": "digit",
        "NumForm=Roman": "digit",
        "NumForm=Word": "",
        "NumType=Card": "cardnum",
        "NumType=Ord": "ordnum",
        "NumType=Sets": "colnum",
        #
        "Person=1": "1p",
        "Person=2": "2p",
        "Person=3": "3p",
        #
        "Polarity=Neg": "neg",
        #
        "Poss=Yes": ",poss",
        #
        "PronType=Prs": "prspro",
        "PronType=Dem": "dempro",
        "PronType=Int": "intpro",
        "PronType=Rel": "relpro",
        "PronType=Neg": "negpro",
        "PronType=Ind": "indpro",
        "PronType=Tot": "qpro",
        #
        "Reflex=Yes": "refl",
        "Reflex=No": "nrefl",
        #
        "Tense=Pres": "nonpast",
        "Tense=Past": "praet",
        "Tense=Fut": "fut",
        "Tense=Fut1": "fut1",
        "Tense=Fut2": "fut2",
        "Tense=Aor": "aor",
        "Tense=Imp": "iperf",
        "Tense=Perf": "perf",
        "Tense=Pqp": "pqperf",
        #
        "Typo=Yes": "distort",
        #
        "Variant=Short": "brev",
        "Variant=Long": "plen",
        #
        "VerbForm=Conv": "ger",
        "VerbForm=Fin": "finit",
        "VerbForm=Inf": "ger",
        "VerbForm=Part": "partcp",
        "VerbForm=PartRes": "perf",
        "VerbForm=Sup": "supin",
        #
        "Voice=Act": "act",
        "Voice=Pass": "pass",
        "Voice=Mid": "med",
        "Voice=Necess": "debit"
    }
    new_gram = []
    for gram in grammar:
        for key in grammar_swap_dict:
            if key == gram and grammar_swap_dict[key] != "":
                new_gram.append(grammar_swap_dict[key])
                break
    if len(new_gram) > 0:
        return "," + ",".join(new_gram)
    return ""


def special_cases(lex, upos, feat):  # Замена уникальных кейсов, если нет делать обычную замену
    if lex in ["один", "одиный", "единъ", "единый"]:
        return "ANUM"
    if upos == "PRAEDIC" and re.match(r'Case=', feat):
        return "PRAEDICPRO"
    if upos == "ADJ" and re.match(r'Decl=ANUM', feat):
        return "ANUM"
    return convert_upos(upos)  # Конвертируем части речи в другой тагсет


def text_into_xml(text_str):
    text = text_str.strip("\n").split("\t")  # Получить текст в виде списка
    word = text[1]
    lex = text[2]
    gr = special_cases(text[2], text[3], text[5])
    feature = convert_grammar(text[5])  # convert grammatical features
    wf = text[9].split("|")[0]
    xml_style = f'<w><ana lex="{lex}" gr="{gr}{feature}" {wf}/>{word}</w>{space_after_check(text[9])}'
    return xml_style


def get_paragraphs(text):
    paragraph = text.split('\n\n')  # Получить параграфы
    if paragraph[-1].strip() == '':
        paragraph = paragraph[:-1]
    else:
        paragraph[-1] = paragraph[-1].strip()
    return paragraph


def space_after_check(wf_text):
    space_text = wf_text.split("|")
    for i in space_text:
        if i == "SpaceAfter=No":
            return ""
    return " "


def create_tags(tag_list, first):  # opening and closing tags
    end = ""
    start = ""
    tags = ""
    if first:  # Если первый параграф
        if "# newdoc id" in tag_list[0]:
            tags = tag_list[0]
        tags += "\n<p><se>"
    else:
        if "# newpar" in tag_list and "# sent_id" in tag_list:
            end = "</se></p>"
            start = "<p><se>"
        elif "# sent_id" in tag_list:
            end = "</se>"
            start = "<se>"
        if "# newdoc id" in tag_list[0]:
            tags = f"{end}\n\n{tag_list[0]}\n{start}"
        else:
            tags = f"{end}\n\n{start}"
    return tags


def edit_punct_xml(xml):  # Убираем строчки с пунктуацией из частей речи и добавляем на конец прошлого
    new_xml = []
    for line in range(len(xml)):
        if 'gr="PUNCT"' in xml[line]:
            punct = re.findall(r'/>(.*?)</', xml[line])
            punct = punct[-1]
            if line != 0:  # Если пунктуация не первая строчка
                new_xml[-1] += punct
        else:
            new_xml.append(xml[line])
    return new_xml


def remove_empty_lex(xml):  # Убираем пустой lex
    new_xml = []
    for line in xml:
        new_xml.append(re.sub(r'lex="_" ', '', line))
    return new_xml


def create_xml(path, folder=False):
    folder_name = "/"
    head = os.path.split(path)[0]
    tail = os.path.split(path)[1]
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
        paragraphs = get_paragraphs(text)
        if folder:
            folder_name = '/xml/'
        with open(f'{head}{folder_name}{tail.split(".")[0]}.xml', 'w',
                  encoding='utf-8', newline='\n') as outf:
            print('<?xml version="1.0" encoding="UTF-8"?>\n<html><body>', file=outf)
            for i in range(len(paragraphs)):
                xml = []  # Тело
                tags = []  # Шапка
                for sent in paragraphs[i].split("\n"):
                    if sent.split("\t")[0].isdigit():
                        xml.append(text_into_xml(sent))
                    else:
                        tags.append(sent.strip("\n"))
                if len(tags) > 0:
                    if i != 0:  # Если не первый параграф
                        print(create_tags(tags, False), file=outf)
                    else:
                        print(create_tags(tags, True), file=outf)
                xml = edit_punct_xml(xml)
                xml = remove_empty_lex(xml)
                print(f"\n".join(xml), file=outf)
            print('</se></p>\n</body></html>', file=outf)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='conllu to xml converter.')
    parser.add_argument("path", help="Path to file or directory", type=str)
    args = parser.parse_args()
    if re.search(r'.conllu', args.path):  # Если аргумент заканчивается на .connlu - значит это файл
        print(f"file - {args.path}")
        create_xml(args.path)
        print(f"created xml file for - {args.path}")
    else:
        files = list(glob.glob(f"{args.path}/*.conllu"))
        if len(files) > 0:
            print(f"folder - {args.path}")  # Если нет, то папка
            if not os.path.exists(f"{args.path}/xml"):  # Если папки xml не существует создать ее
                os.makedirs(f"{args.path}/xml")
            pbar = tqdm(range(len(files)), desc="starting")
            for confile in pbar:  # для каждого файла с расширением .conllu в папке
                pbar.set_description(os.path.split(files[confile])[1])
                create_xml(files[confile], folder=True)
                tqdm.write(f"created xml file for - {os.path.split(files[confile])[1]}")
                if confile == (len(files) - 1):
                    pbar.set_description("finished")
        else:
            print("Empty folder")
