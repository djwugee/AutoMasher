"""Streamlit UI for AutoMasher.

This app mirrors the Gradio demo workflow from demo.py while using Streamlit widgets.
"""

from __future__ import annotations

import io
import traceback

import soundfile as sf
import streamlit as st

from fyp import Audio, InvalidMashup, MashupConfig, MashupMode, get_url, mashup_song
from fyp.app import load_dataset, mashup_from_id
from fyp.audio.analysis import ChordMetric


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


def audio_to_wav_bytes(audio: Audio) -> bytes:
    """Convert Audio object to WAV bytes for Streamlit playback/download."""
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio.numpy(), int(audio.sample_rate), format="WAV")
    wav_buffer.seek(0)
    return wav_buffer.read()


def mashup(
    input_yt_link: str,
    starting_point: float,
    mashup_id: str,
    min_transpose_slider: int,
    max_transpose_slider: int,
    min_delta_bpm_slider: float,
    max_delta_bpm_slider: float,
    mashup_mode: str,
    max_distance_input: float,
    keep_first_k_input: int,
    filter_first: bool,
    filter_uneven_bars: bool,
    filter_uneven_bars_min_threshold_input: float,
    filter_uneven_bars_max_threshold_input: float,
    filter_short_song_bar_threshold_input: int,
    search_radius_input: int,
    left_pan: float,
    save_original: bool,
    append_song_to_dataset: bool,
    chord_metric: str,
    dataset_path: str,
    subsets: str,
):
    mashup_mode_ = (
        MashupMode.NATURAL
        if not mashup_mode.strip()
        else {v: k for k, v in get_mashup_mode_desc_map().items()}[mashup_mode]
    )

    chord_metric_ = (
        ChordMetric.DEFAULT
        if not chord_metric.strip()
        else {v: k for k, v in get_chord_metric_desc_map().items()}[chord_metric]
    )

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
            return "Mashup complete!", audio_to_wav_bytes(mashup_audio)
        except InvalidMashup as exc:
            print(traceback.format_exc())
            return f"Error: {exc}", None
        except Exception as exc:  # keep parity with generic error handling
            print(traceback.format_exc())
            return f"Error: {exc}", None

    try:
        link = get_url(input_yt_link)
    except Exception as exc:
        return f"Error: Invalid YouTube link ({exc})", None

    try:
        mashup_audio, _, system_message = mashup_song(link, config)
        return system_message, audio_to_wav_bytes(mashup_audio)
    except InvalidMashup as exc:
        print(traceback.format_exc())
        return f"Error: {exc}", None
    except Exception as exc:
        print(traceback.format_exc())
        return f"Error: {exc}", None


def get_audio_from_link(input_yt_link: str, starting_point: float, dataset_path: str):
    try:
        link = get_url(input_yt_link)
    except Exception as exc:
        return f"Error: Invalid YouTube link ({exc})", None, None

    title = link.video_title
    dataset = load_dataset(MashupConfig(1, dataset_path=dataset_path, load_on_the_fly=True))

    try:
        audio = dataset.get_audio(link)
        slice_end = min(audio.duration, starting_point + 10)
        audio = audio.slice_seconds(starting_point, slice_end)
    except Exception as exc:
        print(traceback.format_exc())
        return f"Error: {exc}", None, None

    return title, audio_to_wav_bytes(audio), "audio/wav"


def main():
    st.set_page_config(page_title="AutoMasher (Streamlit)", layout="wide")
    st.title("Auto Masher")
    st.caption(
        "This demo is provided for research purposes only. Do not use it for commercial purposes."
    )

    col1, col2 = st.columns(2)
    with col1:
        input_yt_link = st.text_input(
            "Input YouTube Link",
            value="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste a YouTube link here to get started.",
        )
        starting_point = st.number_input(
            "Starting point (seconds)",
            min_value=0.0,
            value=43.0,
            step=1.0,
            help="Pick a complete verse, ideally around chorus start, for best results.",
        )
        dataset_path = st.text_input(
            "Dataset Path",
            value="./resources/dataset",
            help="The path to the dataset.",
        )

    with col2:
        st.text_input(
            "Video Title",
            value=st.session_state.get("input_title", "Rick Astley - Never Gonna Give You Up"),
            disabled=True,
        )

        if st.button("Refresh input audio", type="primary"):
            with st.spinner("Loading input clip..."):
                title_or_error, input_audio_bytes, mime = get_audio_from_link(
                    input_yt_link, starting_point, dataset_path
                )
            if input_audio_bytes is None:
                st.session_state["input_audio_error"] = title_or_error
            else:
                st.session_state["input_title"] = title_or_error
                st.session_state["input_audio_bytes"] = input_audio_bytes
                st.session_state["input_audio_mime"] = mime
                st.session_state.pop("input_audio_error", None)

        if "input_audio_error" in st.session_state:
            st.error(st.session_state["input_audio_error"])
        if "input_audio_bytes" in st.session_state:
            st.audio(
                st.session_state["input_audio_bytes"],
                format=st.session_state.get("input_audio_mime", "audio/wav"),
            )

    with st.expander("Advanced Settings"):
        adv_l, adv_r = st.columns(2)
        with adv_l:
            min_transpose_slider = st.slider("Min Transpose", -6, 6, -3, 1)
            max_transpose_slider = st.slider("Max Transpose", -6, 6, 3, 1)
            min_delta_bpm_slider = st.slider("Min Delta BPM", 0.5, 2.0, 0.8, 0.01)
            max_delta_bpm_slider = st.slider("Max Delta BPM", 0.5, 2.0, 1.25, 0.01)
            mashup_mode = st.radio(
                "Mashup Mode",
                options=list(get_mashup_mode_desc_map().values()),
                index=list(get_mashup_mode_desc_map().values()).index("Let the system decide"),
            )
            mashup_id = st.text_input("Mashup ID", value="")
            save_original = st.checkbox("Save Original", value=False)
            append_song_to_dataset = st.checkbox("Append Song to Dataset", value=True)
            left_pan = st.number_input(
                "Left Pan", min_value=-0.5, max_value=0.5, value=0.15, step=0.01
            )
            subsets = st.text_input("Subsets", value="")
        with adv_r:
            max_distance_input = st.number_input(
                "Max Song Distance", min_value=0.0, value=5.0, step=0.1
            )
            keep_first_k_input = st.number_input(
                "Keep first k results", min_value=-1, value=5, step=1
            )
            filter_first = st.checkbox("Filter First", value=True)
            filter_uneven_bars = st.checkbox("Filter Uneven Bars", value=False)
            filter_uneven_bars_min_threshold_input = st.number_input(
                "Min Threshold", value=0.9, step=0.01
            )
            filter_uneven_bars_max_threshold_input = st.number_input(
                "Max Threshold", value=1.1, step=0.01
            )
            filter_short_song_bar_threshold_input = st.number_input(
                "Short Song Bar Threshold", min_value=0, value=12, step=1
            )
            search_radius_input = st.number_input(
                "Search Radius", min_value=0, value=3, step=1
            )
            chord_metric = st.selectbox(
                "Chord Metric",
                options=list(get_chord_metric_desc_map().values()),
                index=list(get_chord_metric_desc_map().values()).index("Default"),
            )

    if st.button("Create mashup", type="primary"):
        with st.spinner("Creating mashup... this can take a while"):
            output_message, output_audio_bytes = mashup(
                input_yt_link,
                float(starting_point),
                mashup_id,
                int(min_transpose_slider),
                int(max_transpose_slider),
                float(min_delta_bpm_slider),
                float(max_delta_bpm_slider),
                mashup_mode,
                float(max_distance_input),
                int(keep_first_k_input),
                bool(filter_first),
                bool(filter_uneven_bars),
                float(filter_uneven_bars_min_threshold_input),
                float(filter_uneven_bars_max_threshold_input),
                int(filter_short_song_bar_threshold_input),
                int(search_radius_input),
                float(left_pan),
                bool(save_original),
                bool(append_song_to_dataset),
                chord_metric,
                dataset_path,
                subsets,
            )

        if output_audio_bytes is None:
            st.error(output_message)
        else:
            st.success(output_message)
            st.audio(output_audio_bytes, format="audio/wav")
            st.download_button(
                "Download mashup (WAV)",
                data=output_audio_bytes,
                file_name="automasher_mashup.wav",
                mime="audio/wav",
            )


if __name__ == "__main__":
    main()
