import pickle
import random

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt

import pandas as pd
from datetime import datetime

conn = st.connection("gsheets", type=GSheetsConnection)



def get_list_audios(audios):
    p_value = random.uniform(0, 1)
    # type_data = 'Real' if p_value < 0.5 else 'Generado'
    # st.write(type_data)
    list_audios = random.choices(audios['Real'], k=10)
    list_audios += random.choices(audios['Generado'], k=10)
    
    random.shuffle(list_audios)

    return list_audios

def active():
    # Variables de ambiente
    st.session_state.active = True
    
    data = conn.read(worksheet='Asignacion', usecols=list(range(2)), ttl=10)
    idx_sheet = data['Ocupacion'].idxmin()
    to_load_sheet = data.loc[idx_sheet, 'Hoja']
    st.session_state.sheet_name = to_load_sheet

    data.loc[idx_sheet, 'Ocupacion'] += 1
    conn.update(worksheet='Asignacion', data=data)
    data = conn.read(worksheet=to_load_sheet, usecols=list(range(5))).dropna().to_dict('list')

    st.session_state.df_results = data

def save():
    st.session_state.saved = True

    sheet_name = st.session_state.sheet_name
    dict_results = st.session_state.df_results

    new_results = st.session_state.results
    list_audios = st.session_state.list_audios
    usuario = st.session_state.ususario

    date = datetime.now()
    audio_type = 'Real' if list_audios[0]["real"] else "Generado"
    for i, audio in enumerate(list_audios):
        dict_results['Fecha'].append(date)
        dict_results['Audio'].append(audio['root'])
        audio_type = 'Real' if audio["real"] else "Generado"
        dict_results['Tipo '].append(audio_type)
        dict_results['Calificación'].append(new_results[i])
        dict_results['Usuario'].append(usuario)

    data = pd.DataFrame(dict_results)
    conn.update(worksheet=sheet_name, data=data)


if 'active' not in st.session_state:
    with open('./data/real.pkl', 'rb') as f:
        audios_real = pickle.load(f)

    st.session_state.audios_real = random.choices(audios_real, k=20)
    
    st.session_state.active = False
    st.session_state.saved = False
    


with st.sidebar:
    st.write("En la barra de la izquierda tiene la muestra de datos reales con los que puede entrenar su oído.")
    audios_real = st.session_state.audios_real
    for a in audios_real:
        st.audio(a, sample_rate=16_000)

if not st.session_state.active:
    st.write("# Marcación de audios")
    st.write("""
        Para el siguiente ejercicio va recibir 20 audios para que determine si son reales o generados.
             
        ⬅️ En La barra de la izquierda va a encontrar audios reales de croacs de la Boana Faber que le permitiran entrenar su oido.
    """)
    with open('./data/audios_to_human_test.pkl', 'rb') as f:
        audios = pickle.load(f)

    st.session_state.list_audios  = get_list_audios(audios)
    st.session_state.ususario = ''

    st.button('Comenzar', on_click=active)




if st.session_state.active:
    list_audios = st.session_state.list_audios 

    type_1 = []

    ANSWERS = ['Real', 'Generado']
    for i, audio in enumerate(list_audios):
        
        with st.container(border=True):
            col1, col2 = st.columns(2)

            with col1:
                st.audio(audio['audio'], sample_rate=16_000)
            with col2:
                response = st.radio(
                    label="Este audio es:",
                    index=None,                
                    options=ANSWERS,
                    key=i,  # here
                    horizontal=True, 
                    disabled=st.session_state.saved
                )
                type_1.append(response)
                # if st.session_state.saved:
                #     res_is_real = type_1[i] == "Real"
                #     is_real = audio['real']
                #     if res_is_real ==  is_real:
                #         st.write("Respondió bien ✅")
                #     else:
                #         st.write("Respondió mal ❌")
    
    if not st.session_state.saved:
        st.session_state.results = type_1
        st.session_state.ususario = st.text_input(
            "Puede dejarnos su nombre si quiere saber el resultado de sus respuestas 👇 (Despues de escribir el nombre presione Enter)",
        )
        st.button(
            "Guardar respuestas",
            disabled=None in type_1,
            help="Para activar el boton debe terminar de marcar todas las respuestas.",
            on_click=save
        )
    
    if st.session_state.saved:
        st.write(
            f"Gracias por responder {st.session_state.ususario}.",
        )


