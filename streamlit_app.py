import os
import streamlit as st
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

def get_audio_bytes(audio: Audio):
    import io
    import soundfile as sf
    buffer = io.BytesIO()
    sf.write(buffer, audio.numpy().T, audio.sample_rate, format='WAV')
    return buffer.getvalue()

def main():
    st.title("Auto Masher")

    col_logo, col_text = st.columns([1, 5])
    with col_logo:
        if os.path.exists("resources/assets/auto_mashup.png"):
            st.image("resources/assets/auto_mashup.png", width=150)
    with col_text:
        st.markdown("""
        This demo is provided for research purposes only. All audio materials used in this pipeline constitutes as research, and thus, pursuant to Section 107 of the 1976 Copyright Act, constitutes as fair use. Please do not use it for commercial purposes.
        """)

    with st.expander("About Auto Masher"):
        st.markdown("""
        Auto Masher is a research project that aims to create pop song mashups with AI-assisted music information retrieval and analysis.
        In this project, we have compiled a dataset of pop songs and their corresponding chords and beats.
        The user will submit a song from YouTube, and the pipeline will automatically find the best song to mashup with the user's song.
        """)

    # Input section
    col1, col2 = st.columns(2)

    with col1:
        st.header("Input Settings")
        input_yt_link = st.text_input(
            "Input YouTube Link",
            value="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste a YouTube link here to get started"
        )
        starting_point = st.number_input(
            "Starting point (seconds)",
            value=43.0,
            min_value=0.0,
            help="Pick a complete verse, ideally at the start of the chorus, to get the best results"
        )
        dataset_path = st.text_input(
            "Dataset Path",
            value="./resources/dataset",
            help="The path to the dataset."
        )

        if st.button("Refresh input audio"):
            with st.spinner("Fetching audio..."):
                try:
                    link = get_url(input_yt_link)
                    title = link.video_title
                    st.session_state['video_title'] = title

                    dataset = load_dataset(MashupConfig(1, dataset_path=dataset_path, load_on_the_fly=True))
                    audio = dataset.get_audio(link)
                    slice_end = min(audio.duration, starting_point + 10)
                    preview_audio = audio.slice_seconds(starting_point, slice_end)
                    st.session_state['preview_audio'] = preview_audio
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state['video_title'] = ""
                    st.session_state['preview_audio'] = None

    with col2:
        st.header("Input Preview")
        if 'video_title' in st.session_state and st.session_state['video_title']:
            st.write(f"**Video Title:** {st.session_state['video_title']}")

        if 'preview_audio' in st.session_state and st.session_state['preview_audio'] is not None:
            audio_bytes = get_audio_bytes(st.session_state['preview_audio'])
            st.audio(audio_bytes, format='audio/wav')
        else:
            st.info("Click 'Refresh input audio' to see preview")

    # Advanced Settings
    with st.expander("Advanced Settings"):
        col_adv1, col_adv2 = st.columns(2)

        with col_adv1:
            min_transpose = st.slider("Min Transpose", -6, 6, -3)
            max_transpose = st.slider("Max Transpose", -6, 6, 3)
            min_delta_bpm = st.slider("Min Delta BPM", 0.5, 2.0, 0.8)
            max_delta_bpm = st.slider("Max Delta BPM", 0.5, 2.0, 1.25)

            mode_map = get_mashup_mode_desc_map()
            mashup_mode_str = st.radio(
                "Mashup Mode",
                options=list(mode_map.values()),
                index=list(mode_map.values()).index("Let the system decide")
            )

            mashup_id_input = st.text_input(
                "Mashup ID",
                placeholder="Enter Mashup ID",
                help="If you have a mashup ID, you can enter it here to recreate the mashup. In this case the song link and starting point will be ignored"
            )

            save_original = st.checkbox("Save Original", value=False)
            append_song_to_dataset = st.checkbox("Append Song to Dataset", value=True)
            left_pan = st.number_input("Left Pan", value=0.15, min_value=-0.5, max_value=0.5)
            subsets = st.text_input("Subsets", value="", help="Comma separated subsets, e.g. 'fyp,laion:12m'")

        with col_adv2:
            max_distance = st.number_input("Max Song Distance", value=5.0, min_value=0.0)
            keep_first_k = st.number_input("Keep first k results", value=5, min_value=-1)
            filter_first = st.checkbox("Filter First", value=True)
            filter_uneven_bars = st.checkbox("Filter Uneven Bars", value=False)

            filter_uneven_min = st.number_input("Min Threshold (Uneven Bars)", value=0.9)
            filter_uneven_max = st.number_input("Max Threshold (Uneven Bars)", value=1.1)

            filter_short_threshold = st.number_input("Short Song Bar Threshold", value=12)
            search_radius = st.number_input("Search Radius", value=3)

            metric_map = get_chord_metric_desc_map()
            chord_metric_str = st.selectbox(
                "Chord Metric",
                options=list(metric_map.values()),
                index=0
            )

    # Mashup action
    if st.button("Mashup!", type="primary", use_container_width=True):
        with st.spinner("Creating mashup... This may take a while."):
            try:
                # Resolve enums
                inv_mode_map = {v: k for k, v in get_mashup_mode_desc_map().items()}
                mashup_mode_ = inv_mode_map[mashup_mode_str]

                inv_metric_map = {v: k for k, v in get_chord_metric_desc_map().items()}
                chord_metric_ = inv_metric_map[chord_metric_str]

                config = MashupConfig(
                    starting_point=starting_point,
                    min_transpose=min_transpose,
                    max_transpose=max_transpose,
                    min_delta_bpm=min_delta_bpm,
                    max_delta_bpm=max_delta_bpm,
                    max_distance=max_distance,
                    mashup_mode=mashup_mode_,
                    filter_first=filter_first,
                    search_radius=search_radius,
                    keep_first_k_results=keep_first_k,
                    filter_uneven_bars=filter_uneven_bars,
                    filter_uneven_bars_min_threshold=filter_uneven_min,
                    filter_uneven_bars_max_threshold=filter_uneven_max,
                    filter_short_song_bar_threshold=filter_short_threshold,
                    left_pan=left_pan,
                    chord_metric=chord_metric_,
                    subsets=subsets,
                    _verbose=True,
                    save_original=save_original,
                    append_song_to_dataset=append_song_to_dataset,
                    load_on_the_fly=True,
                    assert_audio_exists=False,
                    dataset_path=dataset_path,
                )

                res_audio = None
                system_message = ""

                if mashup_id_input and mashup_id_input != "Enter Mashup ID":
                    res_audio = mashup_from_id(mashup_id_input, config)
                    system_message = "Mashup complete!"
                else:
                    link = get_url(input_yt_link)
                    res_audio, _, system_message = mashup_song(link, config)

                st.success(system_message)
                if res_audio:
                    audio_bytes = get_audio_bytes(res_audio)
                    st.audio(audio_bytes, format='audio/wav')
                    st.download_button(
                        label="Download Mashup",
                        data=audio_bytes,
                        file_name="mashup.wav",
                        mime="audio/wav"
                    )

            except Exception as e:
                st.error(f"Error: {e}")
                st.text(traceback.format_exc())

if __name__ == "__main__":
    main()
