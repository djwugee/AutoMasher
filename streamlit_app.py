import streamlit as st
import os
import base64
import traceback
import numpy as np
from fyp.app import mashup_from_id, load_dataset
from fyp import mashup_song, MashupConfig, MashupMode, get_url, InvalidMashup, Audio
from fyp.audio.analysis import ChordMetric

# Set to None to disable caching
CACHE_DIR: str | None = "./resources/cache"

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

def main():
    st.set_page_config(page_title="AutoMasher", layout="wide")

    def handle_refresh(input_yt_link, starting_point, dataset_path):
        try:
            link = get_url(input_yt_link)
        except Exception as e:
            st.error(f"Error: Invalid YouTube link ({e})")
            return None, None

        title = link.video_title
        # Set load_on_the_fly to True to avoid loading the entire dataset into memory
        dataset = load_dataset(MashupConfig(1, dataset_path=dataset_path, load_on_the_fly=True))

        try:
            audio = dataset.get_audio(link)
            slice_end = min(audio.duration, starting_point + 10)
            audio = audio.slice_seconds(starting_point, slice_end)
        except Exception as e:
            st.error(f"Error: {e}")
            st.code(traceback.format_exc())
            return None, None

        return title, audio

    def handle_mashup(
        input_yt_link,
        starting_point,
        mashup_id,
        min_transpose_slider,
        max_transpose_slider,
        min_delta_bpm_slider,
        max_delta_bpm_slider,
        mashup_mode_str,
        max_distance_input,
        keep_first_k_input,
        filter_first,
        filter_uneven_bars,
        filter_uneven_bars_min_threshold_input,
        filter_uneven_bars_max_threshold_input,
        filter_short_song_bar_threshold_input,
        search_radius_input,
        left_pan,
        save_original,
        append_song_to_dataset,
        chord_metric_str,
        dataset_path,
        subsets,
    ):
        mashup_mode_ = MashupMode.NATURAL if not mashup_mode_str.strip() else {
            v: k for k, v in get_mashup_mode_desc_map().items()
        }[mashup_mode_str]

        chord_metric_ = ChordMetric.DEFAULT if not chord_metric_str.strip() else {
            v: k for k, v in get_chord_metric_desc_map().items()
        }[chord_metric_str]

        config = MashupConfig(
            starting_point=starting_point,
            min_transpose=min_transpose_slider,
            max_transpose=max_transpose_slider,
            min_delta_bpm=min_delta_bpm_slider,
            max_delta_bpm=max_delta_bpm_slider,
            max_distance=max_distance_input,
            mashup_mode=mashup_mode_,
            filter_first=filter_first,
            search_radius=search_radius_input,
            keep_first_k_results=keep_first_k_input,
            filter_uneven_bars=filter_uneven_bars,
            filter_uneven_bars_min_threshold=filter_uneven_bars_min_threshold_input,
            filter_uneven_bars_max_threshold=filter_uneven_bars_max_threshold_input,
            filter_short_song_bar_threshold=filter_short_song_bar_threshold_input,
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

        if mashup_id and mashup_id != "Enter Mashup ID":
            try:
                mashup_audio = mashup_from_id(mashup_id, config)
                return "Mashup complete!", mashup_audio
            except InvalidMashup as e:
                st.error(f"Error: {e}")
                st.code(traceback.format_exc())
                return f"Error: {e}", None

        try:
            link = get_url(input_yt_link)
        except Exception as e:
            return f"Error: Invalid YouTube link ({e})", None

        try:
            mashup_audio, _, system_message = mashup_song(link, config)
            return system_message, mashup_audio
        except Exception as e:
            st.error(f"Error: {e}")
            st.code(traceback.format_exc())
            return f"Error: {e}", None


    # Header and Logo
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("resources/assets/auto_mashup.png"):
            st.image("resources/assets/auto_mashup.png", width=150)

    st.markdown("<h1 style='text-align: center;'>Auto Masher</h1>", unsafe_allow_html=True)

    st.markdown(
        "This demo is provided for research purposes only. All audio materials used in this pipeline constitutes as research, and thus, pursuant to Section 107 of the 1976 Copyright Act, constitutes as fair use. Please do not use it for commercial purposes."
    )

    st.header("Create Mashup")

    col_left, col_right = st.columns(2)

    with col_left:
        input_yt_link = st.text_input(
            label="Input YouTube Link",
            value="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste a YouTube link here to get started"
        )
        starting_point = st.number_input(
            label="Starting point (seconds)",
            value=43.0,
            min_value=0.0,
            help="Pick a complete verse, ideally at the start of the chorus, to get the best results"
        )
        dataset_path = st.text_input(
            label="Dataset Path",
            value="./resources/dataset",
            help="The path to the dataset."
        )

    with col_right:
        title_placeholder = st.empty()
        title_placeholder.text_input(
            label="Video Title",
            value="",
            placeholder="Rick Astley - Never Gonna Give You Up",
            disabled=True,
            help="The title of the video will be displayed here"
        )
        audio_placeholder = st.empty()
        refresh_button = st.button("Refresh input audio", type="primary")

        if refresh_button:
            with st.spinner("Refreshing..."):
                title, audio = handle_refresh(input_yt_link, starting_point, dataset_path)
                if title:
                    title_placeholder.text_input(
                        label="Video Title",
                        value=title,
                        disabled=True,
                        key="video_title_filled"
                    )
                if audio:
                    audio_placeholder.audio(audio.numpy(), sample_rate=int(audio.sample_rate))

    with st.expander("Advanced Settings"):
        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            min_transpose_slider = st.slider(
                label="Min Transpose",
                min_value=-6,
                max_value=6,
                value=-3,
                step=1,
                help="The minimum number of semitones to transpose the song. The search result will include songs transposed between min_transpose and max_transpose",
            )
            max_transpose_slider = st.slider(
                label="Max Transpose",
                min_value=-6,
                max_value=6,
                value=3,
                step=1,
                help="The maximum number of semitones to transpose the song. The search result will include songs transposed between min_transpose and max_transpose",
            )
            min_delta_bpm_slider = st.slider(
                label="Min Delta BPM",
                min_value=0.5,
                max_value=2.0,
                value=0.8,
                help="The minimum relative BPM difference between the two songs. Say song A has 100 BPM, then song B can have a BPM between 100 * min_delta_bpm and 100 * max_delta_bpm"
            )
            max_delta_bpm_slider = st.slider(
                label="Max Delta BPM",
                min_value=0.5,
                max_value=2.0,
                value=1.25,
                help="The maximum relative BPM difference between the two songs. Say song A has 100 BPM, then song B can have a BPM between 100 * min_delta_bpm and 100 * max_delta_bpm"
            )
            mashup_mode_options = list(get_mashup_mode_desc_map().values())
            mashup_mode = st.radio(
                label="Mashup Mode",
                options=mashup_mode_options,
                index=mashup_mode_options.index("Let the system decide"),
                help="The mode to use when mashing up the songs. Vocals A will keep the vocals of song A and the music of song B. Vocals B will keep the vocals of song B and the music of song A. DRUMS_A will keep the drums of song A and the music of song B. DRUMS_B will keep the drums of song B and the music of song A. VOCALS_NATURAL will pick between VOCALS_A and VOCALS_B based on the activity of the vocals using some heuristics. DRUMS_NATURAL will pick between DRUMS_A and DRUMS_B based on the activity of the drums using heuristics below. NATURAL will pick between VOCALS_NATURAL and DRUMS_NATURAL based on the activity of the vocals and drums using some heuristics"
            )
            mashup_id = st.text_input(
                label="Mashup ID",
                placeholder="Enter Mashup ID",
                help="If you have a mashup ID, you can enter it here to recreate the mashup. In this case the song link and starting point will be ignored"
            )
            save_original = st.checkbox(
                label="Save Original",
                value=False,
                help="Save the original song in the output as well"
            )
            append_song_to_dataset = st.checkbox(
                label="Append Song to Dataset",
                value=True,
                help="Append the song to the dataset for future use"
            )
            left_pan = st.number_input(
                label="Left Pan",
                value=0.15,
                min_value=-0.5,
                max_value=0.5,
                help="The left pan of the vocals in the output mashup. Other parts will be panned accordingly"
            )
            subsets = st.text_input(
                label="Subsets",
                value="",
                help="The data subsets to use. Leave empty to use all songs. Use a comma to separate the subsets. For example: 'fyp,laion:12m'."
            )

        with col_adv2:
            max_distance_input = st.number_input(
                label="Max Song Distance",
                value=5.0,
                min_value=0.0,
                help="The maximum compatibility distance allowed between the two songs. Anything above this value will be filtered out."
            )
            keep_first_k_input = st.number_input(
                label="Keep first k results",
                value=5,
                min_value=-1,
                help="Keep only the top k results from the pipeline instead of returning all results. This will make some parts slightly more efficient but mostly it's for debugging purposes. Set to -1 to keep all results"
            )
            filter_first = st.checkbox(
                label="Filter First",
                value=True,
                help="Filter only the best match from each song. Say if song A matches with song B at both bar 8 with a score of 85 and bar 16 with a score of 90. If filter_first is True, the pipeline will only consider the match at bar 16. If filter_first is False, both results will be returned"
            )
            filter_uneven_bars = st.checkbox(
                label="Filter Uneven Bars",
                value=False,
                help="Filter out songs in the dataset that might have a faulty beat detection result which is characterized by uneven bar lengths. This will decrease the number of candidate songs but could potentially improve the quality of the mashup."
            )
            filter_uneven_bars_min_threshold_input = st.number_input(
                label="Min Threshold",
                value=0.9,
                help="Minimum tempo change threshold to the unevenness of bars"
            )
            filter_uneven_bars_max_threshold_input = st.number_input(
                label="Max Threshold",
                value=1.1,
                help="Maximum tempo change threshold to the unevenness of bars"
            )
            filter_short_song_bar_threshold_input = st.number_input(
                label="Short Song Bar Threshold",
                value=12,
                help="Filter out songs in the dataset that might have a faulty beat detection result which is characterized by too few number of bars. This will filter out songs that has less than filter_short_song_bar_threshold bars"
            )
            search_radius_input = st.number_input(
                label="Search Radius",
                value=3,
                help="The range to perform beat extrapolation. Keep at 3 unless you know what you're doing"
            )
            chord_metric_options = list(get_chord_metric_desc_map().values())
            chord_metric = st.selectbox(
                label="Chord Metric",
                options=chord_metric_options,
                index=chord_metric_options.index("Default"),
            )

    mashup_button = st.button("Mashup!", type="primary", use_container_width=True)

    if mashup_button:
        with st.spinner("Mashing up... This may take a while."):
            msg, mashup_audio = handle_mashup(
                input_yt_link,
                starting_point,
                mashup_id,
                min_transpose_slider,
                max_transpose_slider,
                min_delta_bpm_slider,
                max_delta_bpm_slider,
                mashup_mode,
                max_distance_input,
                keep_first_k_input,
                filter_first,
                filter_uneven_bars,
                filter_uneven_bars_min_threshold_input,
                filter_uneven_bars_max_threshold_input,
                filter_short_song_bar_threshold_input,
                search_radius_input,
                left_pan,
                save_original,
                append_song_to_dataset,
                chord_metric,
                dataset_path,
                subsets,
            )
            st.text_area("Output Message", value=msg, height=200)
            if mashup_audio:
                st.audio(mashup_audio.numpy(), sample_rate=int(mashup_audio.sample_rate))

if __name__ == "__main__":
    main()
