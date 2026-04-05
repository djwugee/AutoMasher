"""
AutoMasher - Streamlit GUI Application
A full-featured GUI for creating music mashups using the AutoMasher backend.
"""

import os
import base64
import traceback
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

import streamlit as st
import numpy as np

from fyp import (
    YouTubeURL, 
    MashupConfig, 
    mashup_song, 
    mashup_from_id, 
    InvalidMashup, 
    Audio,
    get_url,
    MashupMode
)
from fyp.audio.analysis.chord import ChordMetric
from fyp.app import load_dataset


# ============================================================================
# Configuration and Constants
# ============================================================================

DEFAULT_DATASET_PATH = "./resources/dataset"
DEFAULT_YOUTUBE_LINK = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
DEFAULT_STARTING_POINT = 43.0
LOGO_PATH = "resources/assets/auto_mashup.png"


# ============================================================================
# Helper Functions
# ============================================================================

def get_mashup_mode_map() -> Dict[str, MashupMode]:
    """Returns a mapping from display names to MashupMode enums."""
    return {
        "Vocal A": MashupMode.VOCAL_A,
        "Vocal B": MashupMode.VOCAL_B,
        "Drums A": MashupMode.DRUMS_A,
        "Drums B": MashupMode.DRUMS_B,
        "Vocal Auto": MashupMode.VOCALS_NATURAL,
        "Drums Auto": MashupMode.DRUMS_NATURAL,
        "Let the system decide": MashupMode.NATURAL,
    }


def get_chord_metric_map() -> Dict[str, ChordMetric]:
    """Returns a mapping from display names to ChordMetric enums."""
    return {
        "Default": ChordMetric.DEFAULT,
        "KL Divergence": ChordMetric.KL_DIVERGENCE,
        "Jensen-Shannon": ChordMetric.JENSEN_SHANNON,
        "Monte Carlo": ChordMetric.MONTE_CARLO,
    }


def get_mashup_mode_reverse_map() -> Dict[MashupMode, str]:
    """Returns a reverse mapping from MashupMode enums to display names."""
    return {v: k for k, v in get_mashup_mode_map().items()}


def get_chord_metric_reverse_map() -> Dict[ChordMetric, str]:
    """Returns a reverse mapping from ChordMetric enums to display names."""
    return {v: k for k, v in get_chord_metric_map().items()}


def audio_to_bytes(audio: Audio) -> bytes:
    """Convert Audio object to bytes for Streamlit audio player."""
    return audio.numpy().tobytes()


def get_base64_logo() -> str:
    """Get base64 encoded logo for display."""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""


def init_session_state():
    """Initialize session state variables."""
    if "mashup_complete" not in st.session_state:
        st.session_state.mashup_complete = False
    if "output_audio" not in st.session_state:
        st.session_state.output_audio = None
    if "output_message" not in st.session_state:
        st.session_state.output_message = ""
    if "input_audio" not in st.session_state:
        st.session_state.input_audio = None
    if "video_title" not in st.session_state:
        st.session_state.video_title = ""
    if "processing" not in st.session_state:
        st.session_state.processing = False


# ============================================================================
# Core Mashup Logic
# ============================================================================

def create_mashup_config(
    starting_point: float,
    min_transpose: int,
    max_transpose: int,
    min_delta_bpm: float,
    max_delta_bpm: float,
    mashup_mode: MashupMode,
    max_distance: float,
    keep_first_k: int,
    filter_first: bool,
    filter_uneven_bars: bool,
    filter_uneven_bars_min: float,
    filter_uneven_bars_max: float,
    filter_short_song_bar_threshold: int,
    search_radius: int,
    left_pan: float,
    save_original: bool,
    append_song_to_dataset: bool,
    chord_metric: ChordMetric,
    dataset_path: str,
    subsets: str,
) -> MashupConfig:
    """Create a MashupConfig from user inputs."""
    return MashupConfig(
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
        filter_uneven_bars_min_threshold=filter_uneven_bars_min,
        filter_uneven_bars_max_threshold=filter_uneven_bars_max,
        filter_short_song_bar_threshold=filter_short_song_bar_threshold,
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


def process_mashup_from_youtube(
    youtube_link: str,
    config: MashupConfig
) -> Tuple[Optional[Audio], str]:
    """Process mashup from YouTube link."""
    try:
        link = get_url(youtube_link)
    except Exception as e:
        return None, f"Error: Invalid YouTube link ({e})"

    try:
        mashup, _, system_message = mashup_song(link, config)
        return mashup, system_message
    except InvalidMashup as e:
        return None, f"Error: {e}"
    except Exception as e:
        print(traceback.format_exc())
        return None, f"Error: {e}"


def process_mashup_from_id(
    mashup_id: str,
    config: MashupConfig
) -> Tuple[Optional[Audio], str]:
    """Process mashup from mashup ID."""
    try:
        mashup = mashup_from_id(mashup_id, config)
        return mashup, "Mashup complete!"
    except InvalidMashup as e:
        return None, f"Error: {e}"
    except Exception as e:
        print(traceback.format_exc())
        return None, f"Error: {e}"


def get_audio_preview(
    youtube_link: str,
    starting_point: float,
    dataset_path: str
) -> Tuple[Optional[Audio], str]:
    """Get audio preview from YouTube link."""
    try:
        link = get_url(youtube_link)
    except Exception as e:
        return None, f"Error: Invalid YouTube link ({e})"

    title = link.video_title
    
    try:
        dataset = load_dataset(MashupConfig(
            starting_point=1, 
            dataset_path=dataset_path, 
            load_on_the_fly=True
        ))
        audio = dataset.get_audio(link)
        slice_end = min(audio.duration, starting_point + 10)
        audio = audio.slice_seconds(starting_point, slice_end)
        return audio, title
    except Exception as e:
        print(traceback.format_exc())
        return None, f"Error: {e}"


# ============================================================================
# UI Components
# ============================================================================

def render_header():
    """Render the application header."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_data = get_base64_logo()
        if logo_data:
            st.image(logo_data, width=150)
        st.title("Auto Masher")
    
    st.markdown("""
    > **Note:** This demo is provided for research purposes only. 
    > All audio materials used in this pipeline constitutes as research, 
    > and thus, pursuant to Section 107 of the 1976 Copyright Act, 
    > constitutes as fair use. Please do not use it for commercial purposes.
    """)


def render_input_section() -> Dict[str, Any]:
    """Render the input section and return user inputs."""
    st.header("🎵 Input Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        youtube_link = st.text_input(
            "YouTube Link",
            value=DEFAULT_YOUTUBE_LINK,
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste a YouTube link here to get started"
        )
        
        starting_point = st.number_input(
            "Starting Point (seconds)",
            value=DEFAULT_STARTING_POINT,
            min_value=0.0,
            step=0.1,
            help="Pick a complete verse, ideally at the start of the chorus, to get the best results"
        )
        
        dataset_path = st.text_input(
            "Dataset Path",
            value=DEFAULT_DATASET_PATH,
            help="The path to the dataset"
        )
    
    with col2:
        # Preview section
        st.subheader("Audio Preview")
        
        if st.button("🔄 Refresh Preview", key="refresh_preview"):
            with st.spinner("Loading audio preview..."):
                audio, title = get_audio_preview(youtube_link, starting_point, dataset_path)
                if audio:
                    st.session_state.input_audio = audio
                    st.session_state.video_title = title
                else:
                    st.error(title)
                    st.session_state.input_audio = None
                    st.session_state.video_title = ""
        
        if st.session_state.video_title:
            st.text_input("Video Title", value=st.session_state.video_title, disabled=True)
        
        if st.session_state.input_audio:
            st.audio(
                st.session_state.input_audio.numpy(),
                sample_rate=int(st.session_state.input_audio.sample_rate),
                format="audio/wav"
            )
    
    return {
        "youtube_link": youtube_link,
        "starting_point": starting_point,
        "dataset_path": dataset_path,
    }


def render_advanced_settings() -> Dict[str, Any]:
    """Render the advanced settings section and return user inputs."""
    st.header("⚙️ Advanced Settings")
    
    with st.expander("Show Advanced Settings", expanded=False):
        # Row 1: Transpose settings
        col1, col2 = st.columns(2)
        with col1:
            min_transpose = st.slider(
                "Min Transpose (semitones)",
                min_value=-6,
                max_value=6,
                value=-3,
                step=1,
                help="The minimum number of semitones to transpose the song"
            )
        with col2:
            max_transpose = st.slider(
                "Max Transpose (semitones)",
                min_value=-6,
                max_value=6,
                value=3,
                step=1,
                help="The maximum number of semitones to transpose the song"
            )
        
        # Row 2: BPM settings
        col1, col2 = st.columns(2)
        with col1:
            min_delta_bpm = st.slider(
                "Min Delta BPM",
                min_value=0.5,
                max_value=2.0,
                value=0.8,
                step=0.05,
                help="The minimum relative BPM difference between the two songs"
            )
        with col2:
            max_delta_bpm = st.slider(
                "Max Delta BPM",
                min_value=0.5,
                max_value=2.0,
                value=1.25,
                step=0.05,
                help="The maximum relative BPM difference between the two songs"
            )
        
        # Row 3: Mashup mode and ID
        col1, col2 = st.columns(2)
        with col1:
            mashup_mode_display = st.radio(
                "Mashup Mode",
                options=list(get_mashup_mode_map().keys()),
                index=list(get_mashup_mode_map().keys()).index("Let the system decide"),
                help="The mode to use when mashing up the songs"
            )
        with col2:
            mashup_id = st.text_input(
                "Mashup ID (Optional)",
                placeholder="Enter Mashup ID to recreate a mashup",
                help="If you have a mashup ID, enter it here to recreate the mashup"
            )
        
        # Row 4: Checkboxes
        col1, col2, col3 = st.columns(3)
        with col1:
            save_original = st.checkbox(
                "Save Original",
                value=False,
                help="Save the original song in the output"
            )
        with col2:
            append_to_dataset = st.checkbox(
                "Append to Dataset",
                value=True,
                help="Append the song to the dataset for future use"
            )
        with col3:
            filter_first = st.checkbox(
                "Filter First",
                value=True,
                help="Filter only the best match from each song"
            )
        
        # Row 5: More settings
        col1, col2 = st.columns(2)
        with col1:
            left_pan = st.number_input(
                "Left Pan",
                value=0.15,
                min_value=-0.5,
                max_value=0.5,
                step=0.01,
                help="The left pan of the vocals in the output mashup"
            )
            
            subsets = st.text_input(
                "Subsets",
                value="",
                placeholder="fyp,laion:12m",
                help="Data subsets to use (comma-separated). Leave empty for all."
            )
        
        with col2:
            max_distance = st.number_input(
                "Max Song Distance",
                value=5.0,
                min_value=0.0,
                step=0.1,
                help="Maximum compatibility distance between songs"
            )
            
            keep_first_k = st.number_input(
                "Keep First K Results",
                value=5,
                min_value=-1,
                step=1,
                help="Keep only top K results (-1 for all)"
            )
        
        # Row 6: Filter settings
        col1, col2 = st.columns(2)
        with col1:
            filter_uneven_bars = st.checkbox(
                "Filter Uneven Bars",
                value=False,
                help="Filter out songs with uneven bar lengths"
            )
            
            search_radius = st.number_input(
                "Search Radius",
                value=3,
                min_value=0,
                step=1,
                help="Range to perform beat extrapolation"
            )
        
        with col2:
            filter_short_threshold = st.number_input(
                "Short Song Bar Threshold",
                value=12,
                min_value=0,
                step=1,
                help="Minimum number of bars for a song"
            )
        
        # Row 7: Uneven bars thresholds
        col1, col2 = st.columns(2)
        with col1:
            filter_uneven_min = st.number_input(
                "Uneven Bars Min Threshold",
                value=0.9,
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                help="Minimum tempo change threshold"
            )
        with col2:
            filter_uneven_max = st.number_input(
                "Uneven Bars Max Threshold",
                value=1.1,
                min_value=1.0,
                max_value=2.0,
                step=0.01,
                help="Maximum tempo change threshold"
            )
        
        # Row 8: Chord metric
        chord_metric_display = st.selectbox(
            "Chord Metric",
            options=list(get_chord_metric_map().keys()),
            index=0,
            help="The chord metric to use for the mashup"
        )
        
        return {
            "min_transpose": min_transpose,
            "max_transpose": max_transpose,
            "min_delta_bpm": min_delta_bpm,
            "max_delta_bpm": max_delta_bpm,
            "mashup_mode_display": mashup_mode_display,
            "mashup_id": mashup_id,
            "save_original": save_original,
            "append_to_dataset": append_to_dataset,
            "filter_first": filter_first,
            "left_pan": left_pan,
            "subsets": subsets,
            "max_distance": max_distance,
            "keep_first_k": keep_first_k,
            "filter_uneven_bars": filter_uneven_bars,
            "search_radius": search_radius,
            "filter_short_threshold": filter_short_threshold,
            "filter_uneven_min": filter_uneven_min,
            "filter_uneven_max": filter_uneven_max,
            "chord_metric_display": chord_metric_display,
        }


def render_output_section():
    """Render the output section."""
    st.header("🎧 Output")
    
    if st.session_state.output_message:
        st.success("✅ Mashup Complete!") if "completed" in st.session_state.output_message.lower() or "created" in st.session_state.output_message.lower() else st.info(st.session_state.output_message)
        
        # Display detailed message in expandable section
        with st.expander("View Detailed Results"):
            st.text(st.session_state.output_message)
    
    if st.session_state.output_audio:
        st.audio(
            st.session_state.output_audio.numpy(),
            sample_rate=int(st.session_state.output_audio.sample_rate),
            format="audio/wav"
        )
        
        # Download button
        audio_bytes = st.session_state.output_audio.numpy().tobytes()
        st.download_button(
            label="📥 Download Mashup",
            data=audio_bytes,
            file_name="mashup.wav",
            mime="audio/wav"
        )


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="AutoMasher",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Render header
    render_header()
    
    # Sidebar with quick info
    with st.sidebar:
        st.header("ℹ️ Quick Guide")
        st.markdown("""
        ### How to Use:
        1. Paste a YouTube link
        2. Set the starting point (in seconds)
        3. Click 'Refresh Preview' to verify
        4. Adjust advanced settings if needed
        5. Click '🎵 Create Mashup!'
        
        ### Tips:
        - Pick a complete verse or chorus start
        - Starting point should be >= 0
        - Lower song distance = better matches
        - NATURAL mode works best for most songs
        """)
        
        st.divider()
        
        st.header("🔗 Useful Links")
        st.markdown("[GitHub Repository](https://github.com/HKUST-FYPHO2)")
    
    # Render input section
    input_data = render_input_section()
    
    # Render advanced settings
    advanced_data = render_advanced_settings()
    
    # Mashup button and processing
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        mashup_button = st.button(
            "🎵 Create Mashup!",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.processing
        )
    
    if mashup_button:
        st.session_state.processing = True
        st.session_state.mashup_complete = False
        st.session_state.output_audio = None
        st.session_state.output_message = ""
        
        # Create progress container
        progress_container = st.empty()
        status_container = st.empty()
        
        with status_container.status("Processing mashup...", expanded=True) as status:
            try:
                # Create config
                mashup_mode = get_mashup_mode_map()[advanced_data["mashup_mode_display"]]
                chord_metric = get_chord_metric_map()[advanced_data["chord_metric_display"]]
                
                config = create_mashup_config(
                    starting_point=input_data["starting_point"],
                    min_transpose=advanced_data["min_transpose"],
                    max_transpose=advanced_data["max_transpose"],
                    min_delta_bpm=advanced_data["min_delta_bpm"],
                    max_delta_bpm=advanced_data["max_delta_bpm"],
                    mashup_mode=mashup_mode,
                    max_distance=advanced_data["max_distance"],
                    keep_first_k=advanced_data["keep_first_k"],
                    filter_first=advanced_data["filter_first"],
                    filter_uneven_bars=advanced_data["filter_uneven_bars"],
                    filter_uneven_bars_min=advanced_data["filter_uneven_min"],
                    filter_uneven_bars_max=advanced_data["filter_uneven_max"],
                    filter_short_song_bar_threshold=advanced_data["filter_short_threshold"],
                    search_radius=advanced_data["search_radius"],
                    left_pan=advanced_data["left_pan"],
                    save_original=advanced_data["save_original"],
                    append_song_to_dataset=advanced_data["append_to_dataset"],
                    chord_metric=chord_metric,
                    dataset_path=input_data["dataset_path"],
                    subsets=advanced_data["subsets"],
                )
                
                # Process mashup
                if advanced_data["mashup_id"] and advanced_data["mashup_id"].strip():
                    status.write("🔄 Processing mashup from ID...")
                    audio, message = process_mashup_from_id(
                        advanced_data["mashup_id"],
                        config
                    )
                else:
                    status.write("🔄 Searching for compatible songs...")
                    audio, message = process_mashup_from_youtube(
                        input_data["youtube_link"],
                        config
                    )
                
                if audio:
                    st.session_state.output_audio = audio
                    st.session_state.output_message = message
                    st.session_state.mashup_complete = True
                    status.update(label="✅ Mashup Complete!", state="complete")
                else:
                    status.update(label="❌ Error", state="error")
                    st.error(message)
                    
            except Exception as e:
                status.update(label="❌ Error", state="error")
                st.error(f"An unexpected error occurred: {e}")
                print(traceback.format_exc())
            finally:
                st.session_state.processing = False
    
    # Render output section
    render_output_section()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: gray;">
        <small>AutoMasher © 2024 | Built with Streamlit</small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
