import os

import streamlit as st
import requests
import pandas as pd
import tensorflow as tf
import numpy as np
import pickle
from ai.markov_chain import MarkovChainLyricsGenerator, load_markov_model_from_disk
from ai.dummy import DummyLyricsGenerator, load_dummy_model_from_disk
from glob import glob
from datetime import datetime
from vulgar_words import censor_vulgar_text,is_vulgar_text, censor_vulgar_text
from data.preprocessing import tokens_2_str

from data.load_corpus import CorpusDataManager

cdm = CorpusDataManager()
############ 2. SETTING UP THE PAGE LAYOUT AND TITLE ############

# `st.set_page_config` is used to display the default layout width, the title of the app, and the emoticon in the browser tab.

st.set_page_config(
    layout="centered", page_title="AI Rap FR Lyrics Generator", page_icon=":robot_face:"
)

st.markdown("""
<style>
#root > div:nth-child(1) > div.withScreencast > div > div > div > section > div.block-container.css-91z34k.egzxvld4 > div:nth-child(1) > div > div.stTabs.css-0.exp6ofz0 > div > div:nth-child(1) > div{
  display: flex;
  justify-content: center;
  
}

#tabs-bui3-tabpanel-1 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v4 > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(2) > div {
    display: flex;
    justify-content: right;
}

</style>
""", unsafe_allow_html=True)

############ CREATE THE LOGO AND HEADING ############

# We create a set of columns to display the logo and the heading next to each other.


c1, c2 = st.columns([0.32, 2])

# The snowflake logo will be displayed in the first column, on the left.

with c1:
    st.image(
        "images/logo1.png",
        width=95,
    )

# The heading will be on the right.

with c2:
    st.title("AiRap - FR Lyrics Generator")
    st.caption(
        "Générateur de textes, produisant des phrases et des couplets de rap en français, en s'inspirant du style, de la structure et des thèmes abordés par les rappeurs français.")

# We need to set up session state via st.session_state so that app interactions don't reset the app.

if not "valid_inputs_received" in st.session_state:
    st.session_state["valid_inputs_received"] = False



############ TABBED NAVIGATION ############

# First, we're going to create a tabbed navigation for the app via st.tabs()
# tabInfo displays info about the app.
# tabMain displays the main app.

# tabs


DummyTab, MarkovTab, LSTMTab, GPT2Tab = st.tabs(["Dummy", "Markov", "LSTM", "GPT-2"])

def sample(preds, temperature=1.0):
    preds = np.asarray(preds).astype('float64')
    preds = np.where(preds == 0, 1e-8, preds) # remplacer toutes les valeurs égales à zéro par une petite valeur proche de zéro
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1) #todo : prendre le deuxième
    index_max_1 = np.argmax(probas)

    # Trier les prédictions pour obtenir les indices des deux plus grands éléments
    sorted_indices = np.argsort(preds)[::-1][:2]

    return sorted_indices[0], sorted_indices[1]


def generate_text(model, starting_words,window_size, words_indices, indices_words, max_length=50, diversity=1):
    assert max_length > len(starting_words),f"max_length {max_length} must > len(starting_words) {len(starting_words)}"
    length = max_length - len(starting_words)

    generated = starting_words#[:]
    sentence = starting_words[-window_size:]
    for i in range(length):
        x_pred = np.zeros((1, window_size, len(words_indices)))
        #print(sentence)
        for t, word in enumerate(sentence):
            x_pred[0, t, words_indices[word]] = 1.

        preds = model.predict(x_pred, verbose=0)[0]

        next_index, else_next_index = sample(preds, diversity)
        #print([indices_words[next_index],indices_words[else_next_index]])
        #next_word = indices_words[else_next_index if sentence[-1] == "\n" and indices_word[next_index] == "\n"  else next_index]
        next_word = indices_words[next_index]
        #print(generated)
        generated.append(next_word)
        sentence = sentence[-(window_size-1):] + [next_word]
    return tokens_2_str(generated,remove_extra_nlines=True)


# generate a text
def form(model_name):
    model_name = model_name.lower()
    result = {}

    # Now, we create a form via `st.form` to collect the user inputs.

    # All widget values will be sent to Streamlit in batch.
    # It makes the app faster!

    with st.form(key="my_form"+model_name):
        c1, c2 = st.columns([0.3, 0.7])
        c1_, c2_, c3_ = st.columns([0.3, 0.3, 0.3])

        # select the artist's name ([kery james, rohff, ...])
        artist_name = [c1_ if model_name in ['markov'] else c1_][0].selectbox('Select an artist',
                                                                             ["*ALL*", 'Kery James', 'Rohff',"Booba"], index=1) #todo trouver des rappeurs potables et blanc
        result["artist_name"] = artist_name

        # select k for k-grams
        if model_name == "markov" and st.session_state["valid_inputs_received"]:

            k = [c2_ if model_name in ['markov'] else c2_][0].selectbox('Select k for k-grams', list(range(1, 7)),index=4)

            result["k"] = int(k)

        # max length of the generated text
        max_length = [c3_ if model_name in ['markov'] else c3_][0].slider('Max length', 10, 500, 50, 10)
        result["max_length"] = int(max_length)

        new_line = "\n"
        pre_defined_phrases = [
            "Je suis"
        ]
        # Python list comprehension to create a string from the list of keyphrases.
        phrases_string = f"{new_line.join(map(str, pre_defined_phrases))}"

        # The block of code below displays a text area
        # So users can paste their phrases to classify

        start_text = st.text_area(
            # Instructions
            "Enter keyphrases to classify",
            # 'sample' variable that contains our keyphrases.
            phrases_string,
            # The height
            height=80,
            # The tooltip displayed when the user hovers over the text area.
            help=f"",
            key="area"+model_name,
        )

        # The block of code below:

        # 1. Converts the data st.text_area into a Python list.
        # 2. It also removes duplicates and empty lines.
        # 3. Raises an error if the user has entered more lines than in MAX_KEY_PHRASES.

        start_words = start_text.split()  # Converts the pasted text to a Python list

        result["start_text"] = start_text

        submit_button = st.form_submit_button(label="Submit")


    return submit_button,result

def generate_next_text_by_model_name(model_name,start_text, artist_name, max_length):
    global cdm
    artist_name_ = None if artist_name == "*ALL*" else artist_name
    if model_name == "dummy":

        if dummy_model := load_dummy_model_from_disk(cdm, artist_name=artist_name_):
            #st.success(f"🤖 {dummy_model}")
            generated_next_text = dummy_model.generate_text(start_text, max_len=max_length,  return_with_starting_sent=False)


    elif model_name == "markov":

        if markov_model := load_markov_model_from_disk(cdm,artist_name=artist_name_, min_freq = 0 if artist_name else 2):

            #st.success(f"🤖 {markov_model}")
            generated_next_text = markov_model.generate_text(start_text, max_len=max_length, return_with_starting_sent=False)

    elif model_name == "lstm":
        lstm_model_path = "ai/models/lstm/model_lstm_1_keryjames.hdf5"
        # import word dictionary (with pickle)
        with open("data/datasets/dataset-1273-keryjames-20230208/word_index_dict_union.pkl", "rb") as f:
            word_indices = pickle.load(f)
        indices_word = {v: k for k, v in word_indices.items()}
        if os.path.exists(lstm_model_path):
            lstm_model = tf.keras.models.load_model(lstm_model_path)

            #st.success(f"🤖 {lstm_model}")
            generated_next_text = generate_text(lstm_model,start_text.lower().split(),window_size=10, words_indices=word_indices, indices_words=indices_word, max_length=max_length,diversity=0.8)


    return generated_next_text
def generator_section(model_name):

    submit_button, result_form = form(model_name=model_name)

    start_text = result_form["start_text"]
    artist_name = result_form["artist_name"]
    max_length = result_form["max_length"]
    generated_text = None
    ############ CONDITIONAL STATEMENTS ############

    # Now, let us add conditional statements to check if users have entered valid inputs.
    # E.g. If the user has pressed the 'submit button without text, without labels, and with only one label etc.
    # The app will display a warning message.
    print("*"*100)
    print("submit_button",submit_button)
    print(result_form)
    print("st.session_state.valid_inputs_received",st.session_state.valid_inputs_received)
    if submit_button and not start_text:
        st.warning("🤖 You have not entered any text as input")
        st.session_state.valid_inputs_received = False
        print("You have not entered any text as input")
        st.stop()

    elif submit_button and not artist_name:
        st.warning("🤖 You have not selected an artist")
        st.session_state.valid_inputs_received = False
        print("You have not selected an artist")
        st.stop()

    elif submit_button and not max_length:
        st.warning("🤖 You have not selected a max length")
        st.session_state.valid_inputs_received = False
        print("You have not selected a max length")
        st.stop()


    elif submit_button or st.session_state.valid_inputs_received:
        print("@"*100)
        if submit_button:


            # The block of code below if for our session state.
            # This is used to store the user's inputs so that they can be used later in the app.
            st.session_state.valid_inputs_received = True

            generated_next_text = generate_next_text_by_model_name(model_name,start_text, artist_name, max_length)
            #print("##",generated_next_text)

            generated_text = f"{start_text} {generated_next_text}" if model_name not in ["lstm"] else generated_next_text

            st.markdown("### Résultat : ")
            st.caption(f"Le texte généré est affiché ci-dessous fait environ {len(generated_text.split())} mots.")

            st.text(censor_vulgar_text(generated_text))


            # The code below is for the download button
            # Cache the conversion to prevent computation on every rerun

            cs  = st.columns([1,1,1])

            with cs[-1]:

                st.caption("")
                file_name = f"{artist_name}_{model_name}_generated_text.txt"
                st.download_button(
                    label="Télécharger le résultat 💾",
                    data=generated_text,
                    file_name=file_name,
                    mime="text/csv",
                )

    return submit_button, result_form, generated_text


with DummyTab:

    st.markdown(
        """
        Il s'agit d'un modèle qui n'a pas été entraîné sur de grandes quantités de données et qui n'a pas appris les relations complexes entre les mots et les phrases.
        
    
        
        
        """
    )

    submit_button, result_form, generated_text = generator_section(model_name="dummy")

with MarkovTab:

    st.subheader("Markov")
    st.markdown(
        """
        Basé sur la chaîne de Markov.
        """
    )

    submit_button, result_form, generated_text = generator_section(model_name="markov")


with LSTMTab:
    st.subheader("LSTM")
    st.markdown(
        """
        Basé sur le modèle LSTM.
        """
    )

    submit_button, result_form, generated_text = generator_section(model_name="lstm")

with GPT2Tab:
    st.subheader("GPT2")
    st.markdown(
        """
        Basé sur le modèle GPT2. 
        """
    )

    submit_button, result_form, generated_text = generator_section(model_name="gpt2")



with st.expander("💯 - Evaluation des résultats"):
    st.markdown(
        """
        Il existe plusieurs façons d'évaluer nos modèles de génération de texte, chacun ayant ses propres avantages et inconvénients. 
        Voici les deux méthodes que j'ai utilisées pour évaluer les performances de mes modèles :
        
        - **Evaluation par human judgment** : Cette méthode consiste à demander à un panel d'experts ou de personnes non spécialisées de juger la qualité des textes générés. Les participants peuvent noter les textes sur une échelle de qualité ou les classer par ordre de qualité. Pour ce faire j'ai conçu un formulaire Google Forms qui permet aux participants de noter les textes générés par les modèles ([Lien vers le formulaire](https://docs.google.com/forms/d/e/1FAIpQLScNivr7uYF3UwK5JoiLYp_ZjpaO8xVz0lasNvlo-oNbZ4-7Dw/viewform?usp=sf_link)).
        - **BLEU score** : Le score BLEU est une mesure de la qualité d'un texte généré par rapport à un texte de référence. On mesure la similitude entre un texte généré et un corpus de référence en utilisant des n-grammes communs.  Les scores de BLEU varient de 0 à 1, où 1 représente une correspondance parfaite entre les textes générés et le corpus de référence. Un score élevé signifie que les textes générés sont similaires au corpus de référence, ce qui peut être considéré comme un indicateur de qualité.
        
        En combinant les deux méthodes d'évaluation, nous pouvons obtenir une idée plus précise te complète de la qualité de nos modèles de génération de texte.
        """
    )

with st.expander("ℹ - A propos"):
    st.markdown(
        """
        Ce projet a été réalisé par [Mlamali SAID SALIMO](https://www.linkedin.com/in/mlamalisaidsalimo/).
        """
    )
