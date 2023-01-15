import re

import spacy

nlp = spacy.load("fr_core_news_sm")


# nlp.Defaults.stop_words.add("my_new_stopword")
# print(nlp.Defaults.stop_words)
def remove_section_brackets(text):
    return re.sub(r"(\[.*?\] \(.*?\))|(\[(.+)\])", "", text)  # avant ça split coulot refrain prendre en compte


def slice_lines(text, deb=None, fin=None):
    text = "\n".join(text.split("\n")[deb:fin])
    return text


def tokens_2_str(tokens: list) -> str:
    return " ".join(tokens).strip().replace("' ", "'").replace(" - ", "-").replace(" ,", ",")
# main function to preprocess text, with parameters to choose which preprocessing steps to apply
def preprocess_genius_text(text, lower_case=True, lemmatization=False, stop_words_removal=False,
                           stop_words_to_keep=None, punct_removal=False, token_output=False, crop_first_lines=True):
    if stop_words_to_keep is None:
        stop_words_to_keep = []
    # Exclude section brackets
    text = remove_section_brackets(text)
    if crop_first_lines and len(text.split("\n")) > 10:
        text = slice_lines(text, deb=1)
    text = text.strip()
    # lower case
    if lower_case:
        text = text.lower()
    # remove extra whitespace
    text = text.replace(u'\xa0', u' ')
    text = re.sub('[ ]+', ' ', text)
    text = re.sub('[\n]+', '\n', text)
    text = re.sub('\n ', '\n', text)
    tokens = list(nlp(text))

    # todo : manage contractions (j' => je, c' => ce, etc.)

    # stop words removal from tokenized text
    if stop_words_removal:
        tokens = [token for token in tokens if not token.is_stop or token.text in stop_words_to_keep]

    # punctuation removal
    if punct_removal:
        tokens = [token for token in tokens if not token.is_punct]

    # lemmatization from tokens
    if lemmatization:
        tokens = [token.lemma_ for token in tokens]
    else:
        tokens = [token.text for token in tokens]
    return tokens if token_output else tokens_2_str(tokens)


if __name__ == '__main__':
    # test on example text rap
    text = """[Intro] (Rohff)
    
    [Refrain] (Rohff) 
    J'suis né poussière et j'repartirai poussière \xa0
    Et le soleil se lèvera en même temps que la misère, frère
    T'es parti, t'étais là devant moi à me parler de Ya Rabi
    Tu venais d'te mettre à faire la ière-pri
    Que Dieu te préserve des châtiments
    Après la vie c'est autrement et la rue perd ses monuments
    Perd ses valeurs, perd ses principes
    Perd son respect de la discipline dans l'illicite
    Les peines s'alourdissent des assises aux cercueils
    Un article en page faits divers, une hajja en deuil
    Les femmes de la famille autour pour la soutenir
    Du chagrin de son fils qu'elle    a vu sortir
    Pour plus jamais revenir j'te
    """

    print(preprocess_genius_text(text, lower_case=True, lemmatization=True, stop_words_removal=True,
                                 punct_removal=True, token_output=True, crop_first_lines=False))
