import streamlit as st
import os
import base64
import traceback
import numpy as np
from fyp.app import mashup_from_id, load_dataset
from fyp import mashup_song, MashupConfig, MashupMode, get_url, InvalidMashup, Audio
from fyp.audio.analysis import ChordMetric

# Page config
st.set_page_config(page_title="Auto Masher", page_icon="🎵", layout="wide")

def get_mashup_mode_desc_map():
    return {
        MashupMode.VOCAL_A: "Vocal A",
        MashupMode.VOCAL_B: "Vocal B",
        MashupMode.DRUMS_A: "Drums A",
        MashupMode.DRUMS_B: "Drums B",
        MashupMode.VOCALS_NATURAL: "Vocal Auto",
        MashupMode.DRUMS_NATURAL: "Drums Auto",
        MashupMode.NATURAL: "Let the system decide",
    }

def get_chord_metric_desc_map():
    return {
        ChordMetric.DEFAULT: "Default",
        ChordMetric.KL_DIVERGENCE: "KL Divergence",
        ChordMetric.JENSEN_SHANNON: "Jensen-Shannon",
        ChordMetric.MONTE_CARLO: "Monte Carlo",
    }

def get_base64_logo():
    logo_path = "resources/assets/auto_mashup.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

# Header
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    logo_base64 = get_base64_logo()
    if logo_base64:
        st.markdown(
            f'<div style="display: flex; justify-content: center;"><img src="data:image/png;base64,{logo_base64}" width="150"></div>',
            unsafe_allow_html=True,
        )
st.markdown("<h1 style='text-align: center;'>Auto Masher</h1>", unsafe_allow_html=True)

st.markdown(
    """
    This demo is provided for research purposes only. All audio materials used in this pipeline constitutes as research, and thus, pursuant to Section 107 of the 1976 Copyright Act, constitutes as fair use. Please do not use it for commercial purposes.
    """
)

# Sidebar for inputs and basic settings
st.header("Create Mashup")

with st.container():
    col_left, col_right = st.columns(2)
    
    with col_left:
        input_yt_link = st.text_input(
            "Input YouTube Link",
            value="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste a YouTube link here to get started"
        )
        starting_point = st.number_input(
            "Starting point (seconds)",
            value=43.0,
            min_value=0.0,
            step=0.1,
            help="Pick a complete verse, ideally at the start of the chorus, to get the best results"
        )
        dataset_path = st.text_input(
            "Dataset Path",
            value="./resources/dataset",
            help="The path to the dataset."
        )
        
        refresh_button = st.button("Refresh input audio", type="primary")

    with col_right:
        if refresh_button:
            with st.spinner("Loading audio..."):
                try:
                    link = get_url(input_yt_link)
                    st.write(f"**Video Title:** {link.video_title}")
                    
                    # Set load_on_the_fly to True to avoid loading the entire dataset into memory
                    dataset = load_dataset(MashupConfig(starting_point=1, dataset_path=dataset_path, load_on_the_fly=True))
                    audio = dataset.get_audio(link)
                    
                    slice_end = min(audio.duration, starting_point + 10)
                    audio_slice = audio.slice_seconds(starting_point, slice_end)
                    
                    st.audio(audio_slice.numpy(), sample_rate=int(audio_slice.sample_rate))
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.text(traceback.format_exc())
        else:
            st.info("Click 'Refresh input audio' to preview the selected portion of the song.")

# Advanced Settings
with st.expander("Advanced Settings"):
    col_adv1, col_adv2 = st.columns(2)
    
    with col_adv1:
        min_transpose = st.slider("Min Transpose", -6, 6, -3, help="The minimum number of semitones to transpose the song.")
        max_transpose = st.slider("Max Transpose", -6, 6, 3, help="The maximum number of semitones to transpose the song.")
        min_delta_bpm = st.slider("Min Delta BPM", 0.5, 2.0, 0.8, help="The minimum relative BPM difference between the two songs.")
        max_delta_bpm = st.slider("Max Delta BPM", 0.5, 2.0, 1.25, help="The maximum relative BPM difference between the two songs.")
        
        mode_desc_map = get_mashup_mode_desc_map()
        mashup_mode_desc = st.radio(
            "Mashup Mode",
            options=list(mode_desc_map.values()),
            index=list(mode_desc_map.values()).index("Let the system decide"),
            help="The mode to use when mashing up the songs."
        )
        
        mashup_id_input = st.text_input(
            "Mashup ID",
            placeholder="Enter Mashup ID",
            help="If you have a mashup ID, you can enter it here to recreate the mashup."
        )
        
        save_original = st.checkbox("Save Original", value=False, help="Save the original song in the output as well")
        append_song_to_dataset = st.checkbox("Append Song to Dataset", value=True, help="Append the song to the dataset for future use")
        left_pan = st.number_input("Left Pan", value=0.15, min_value=-0.5, max_value=0.5, step=0.01, help="The left pan of the vocals in the output mashup.")
        subsets = st.text_input("Subsets", value="", help="The data subsets to use. Leave empty to use all songs. Comma separated.")

    with col_adv2:
        max_distance = st.number_input("Max Song Distance", value=5.0, min_value=0.0, help="The maximum compatibility distance allowed.")
        keep_first_k = st.number_input("Keep first k results", value=5, min_value=-1, help="Keep only the top k results. -1 to keep all.")
        filter_first = st.checkbox("Filter First", value=True, help="Filter only the best match from each song.")
        filter_uneven_bars = st.checkbox("Filter Uneven Bars", value=False, help="Filter out songs that might have a faulty beat detection result.")
        min_threshold = st.number_input("Min Threshold (Uneven Bars)", value=0.9)
        max_threshold = st.number_input("Max Threshold (Uneven Bars)", value=1.1)
        short_song_threshold = st.number_input("Short Song Bar Threshold", value=12)
        search_radius = st.number_input("Search Radius", value=3)
        
        chord_metric_map = get_chord_metric_desc_map()
        chord_metric_desc = st.selectbox(
            "Chord Metric",
            options=list(chord_metric_map.values()),
            index=0
        )

# Mashup Button
if st.button("Mashup!", type="primary", use_container_width=True):
    with st.spinner("Generating mashup... This may take a while."):
        try:
            # Map descriptions back to enums
            inv_mode_map = {v: k for k, v in get_mashup_mode_desc_map().items()}
            mashup_mode = inv_mode_map[mashup_mode_desc]
            
            inv_chord_map = {v: k for k, v in get_chord_metric_desc_map().items()}
            chord_metric = inv_chord_map[chord_metric_desc]
            
            config = MashupConfig(
                starting_point=starting_point,
                min_transpose=min_transpose,
                max_transpose=max_transpose,
                min_delta_bpm=min_delta_bpm,
                max_delta_bpm=max_delta_bpm,
                max_distance=max_distance,
                mashup_mode=mashup_mode,
                filter_first=filter_first,
                search_radius=search_radius,
                keep_first_k_results=keep_first_k,
                filter_uneven_bars=filter_uneven_bars,
                filter_uneven_bars_min_threshold=min_threshold,
                filter_uneven_bars_max_threshold=max_threshold,
                filter_short_song_bar_threshold=short_song_threshold,
                left_pan=left_pan,
                chord_metric=chord_metric,
                subsets=subsets,
                _verbose=True,
                save_original=save_original,
                append_song_to_dataset=append_song_to_dataset,
                load_on_the_fly=True,
                assert_audio_exists=False,
                dataset_path=dataset_path,
            )
            
            if mashup_id_input and mashup_id_input != "Enter Mashup ID":
                mashup_audio = mashup_from_id(mashup_id_input, config)
                st.success("Mashup complete!")
                st.audio(mashup_audio.numpy(), sample_rate=int(mashup_audio.sample_rate))
            else:
                link = get_url(input_yt_link)
                mashup_audio, _, system_message = mashup_song(link, config)
                st.success("Mashup complete!")
                st.info(system_message)
                st.audio(mashup_audio.numpy(), sample_rate=int(mashup_audio.sample_rate))
                
        except Exception as e:
            st.error(f"Error: {e}")
            st.text(traceback.format_exc())
