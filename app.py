import pickle
import random

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt

import pandas as pd
from datetime import datetime


conn = st.connection("gsheets", type=GSheetsConnection)

with open('./data/audios_to_human_test.pkl', 'rb') as f:
    audios = pickle.load(f)

real_audios_index = list(range(len(audios['Real'])))
random.shuffle(real_audios_index)

gen_audios_index = list(range(len(audios['Generado'])))
random.shuffle(gen_audios_index)


def get_index():
    p_value = random.uniform(0, 1)
    type_data = 'Real' if p_value < 0.5 else 'Generado'
    if type_data == "Real":
        index = real_audios_index.pop(0)
    else:
        index = gen_audios_index.pop(0)

    return type_data, index

def load_audio(array):
    st.audio(array, sample_rate=16_000)

def active():
    # Variables de ambiente
    st.session_state.active = True
    st.session_state.wating = False
    st.session_state.slider = False

    st.session_state.cant_real = 0
    st.session_state.cant_gen = 0
    st.session_state.tp_real = 0
    st.session_state.tp_gen = 0

    data = conn.read(worksheet='Asignacion', usecols=list(range(2)), ttl=10)
    idx_sheet = data['Ocupacion'].idxmin()
    to_load_sheet = data.loc[idx_sheet, 'Hoja']
    st.session_state.sheet_name = to_load_sheet

    data.loc[idx_sheet, 'Ocupacion'] = 1
    conn.update(worksheet='Asignacion', data=data)
    data = conn.read(worksheet=to_load_sheet, usecols=list(range(4))).dropna().to_dict('list')
    st.session_state.df_results = data


def keep_wating():
    st.session_state.wating = True

def stop_wating():
    st.session_state.wating = False
    st.session_state.slider = False

    

def freeze_slider():
    st.session_state.slider = True

if 'active' not in st.session_state:
    st.session_state.active = False


# Function to load and play the audio file 



with st.sidebar:
    st.write("En la barra de la izquierda tiene la muestra de datos reales con los que puede entrenar su oído.")
    for i in [2, 100, 400, 600, 503, 100, 50]:
        array = audios["Real"][i]["audio"]
        st.audio(array, sample_rate=16_000)

if not st.session_state.active:
    st.write("# Marcación de audios")
    st.write("Para el siguiente ejercicio debe calificar que tan real le parece el audio. Asignandole una nota de 1 a 5.")
    st.button('Comenzar', on_click=active)
    

if st.session_state.active:

    st.write(f'## Widget interactivo')
    st.write(f"""
        Cada 20 audios marcados pordrá ver los resultados de sus marcaciones.
        Actualmente lleva ({(st.session_state.cant_gen + st.session_state.cant_real) % 20} / 20)
        """)
    if not st.session_state.wating:
        type_data, index = get_index()
        st.session_state.type_data = type_data
        st.session_state.index = index

    type_data = st.session_state.type_data
    index = st.session_state.index

    audio_obj = audios[type_data][index]
    # st.write(type_data, index)
    load_audio(audio_obj['audio'])

    is_gen_ptg = st.slider('Lo acepta como un dato real. (1 = Generado | 5 = Real)', 1, 5, step=1, on_change=keep_wating(), disabled=st.session_state.slider)

    st.button('Confirmar', on_click=freeze_slider, disabled=st.session_state.slider)

    if st.session_state.slider:
        res = "Generado" if is_gen_ptg < 3 else "Real"
        check = "Mal❌"
        if type_data == 'Generado':
            st.session_state.cant_gen += 1
            if type_data == res:
                st.session_state.tp_gen += 1
                check = "Bien✅ "
        else:
            st.session_state.cant_real += 1
            if type_data == res:
                st.session_state.tp_real += 1
                check = "Bien✅ "

        dict_results = st.session_state.df_results
        dict_results['Fecha'].append(datetime.now())
        dict_results['Tipo '].append(type_data)
        dict_results['Audio'].append(audios[type_data][index]['root'])
        dict_results['Calificación'].append(is_gen_ptg)

        if (st.session_state.cant_gen + st.session_state.cant_real) % 5 == 0: 
            sheet_name = st.session_state.sheet_name
            
            data = pd.DataFrame(dict_results)
            conn.update(worksheet=sheet_name, data=data)

        st.write(f"Se marcó como {res} y realmente es {type_data}. La respuesta está {check}")
        st.button("Siguiente Audio", on_click=stop_wating)


    if (st.session_state.cant_gen + st.session_state.cant_real) % 5 == 0\
        and (st.session_state.cant_gen + st.session_state.cant_real) > 0:
        st.write('# Resultados')

        fig, axes = plt.subplots(1, 2, figsize=(10, 8))

        # Define the data
        cant = st.session_state.cant_gen
        tp = st.session_state.tp_gen
        value_1 = tp/cant if cant != 0 else 0.5
        data = [value_1, 1 - value_1]
        labels = [f'Bien = {tp}', f'Mal = {cant - tp}']
        axes[0].pie(data, labels=labels, autopct="%1.1f%%")
        axes[0].set_title("Generados")

        cant = st.session_state.cant_real
        tp = st.session_state.tp_real
        value_1 = tp/cant if cant != 0 else 0.5
        data = [value_1, 1 - value_1]
        labels = [f'Bien = {tp}', f'Mal = {cant - tp}']
        axes[1].pie(data, labels=labels, autopct="%1.1f%%")
        axes[1].set_title("Reales")

        st.pyplot(fig)