# AutoMasher Streamlit Application

A full-featured GUI for creating music mashups using the AutoMasher backend, built with Streamlit.

## Features

- 🎵 **YouTube Integration**: Paste any YouTube link to create mashups
- 🎚️ **Audio Preview**: Preview your selected audio before creating the mashup
- ⚙️ **Advanced Settings**: Full control over all mashup parameters:
  - Transpose settings (min/max semitones)
  - BPM deviation controls
  - Mashup mode selection (Vocal A/B, Drums A/B, Natural modes)
  - Song distance filtering
  - Bar filtering options
  - Chord metric selection
  - And much more!
- 💾 **Download**: Download your created mashups directly
- 🔄 **Mashup ID Support**: Recreate mashups using mashup IDs

## Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install streamlit
pip install -r requirements.txt
```

## Running the Application

Start the Streamlit server:

```bash
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

Then open your browser and navigate to `http://localhost:8501`

## Usage Guide

### Basic Workflow

1. **Input Settings**
   - Paste a YouTube link in the input field
   - Set the starting point (in seconds) - pick a complete verse or chorus start
   - Click "Refresh Preview" to verify the audio loads correctly

2. **Advanced Settings** (Optional)
   - Expand the advanced settings section
   - Adjust transpose range, BPM limits, mashup mode, etc.
   - Most default values work well for typical use cases

3. **Create Mashup**
   - Click the "🎵 Create Mashup!" button
   - Wait for the processing to complete
   - Listen to your mashup and download it!

### Advanced Settings Explained

- **Transpose**: Controls the pitch shifting range for matching songs
- **Delta BPM**: Sets the acceptable tempo difference between songs
- **Mashup Mode**: 
  - Vocal A/B: Keep vocals from song A or B
  - Drums A/B: Keep drums from song A or B
  - Natural modes: Automatically select based on audio analysis
- **Song Distance**: Lower values = stricter matching, higher = more candidates
- **Filter Options**: Fine-tune which songs are considered for mashup

## Tips for Best Results

1. **Choose Good Starting Points**: Pick complete verses or choruses, ideally at the start
2. **Adjust Song Distance**: Start with 5, increase if no matches found
3. **Use NATURAL Mode**: Works best for most songs
4. **Enable Filtering**: Filter uneven bars can improve quality
5. **Preview First**: Always refresh preview to ensure the audio loads correctly

## Troubleshooting

### No Suitable Songs Found
- Increase the Max Song Distance value
- Widen the BPM range (min/max delta BPM)
- Try a different starting point in the song

### Audio Preview Not Loading
- Check your internet connection
- Verify the YouTube link is valid
- Ensure the dataset path is correct

### Out of Memory Errors
- Enable "load_on_the_fly" mode (already enabled by default)
- Reduce the dataset size or use subsets
- Close other applications

## Comparison with Gradio Version

This Streamlit version provides:
- ✅ Same functionality as the Gradio demo
- ✅ Modern, responsive UI
- ✅ Better mobile support
- ✅ Session state management
- ✅ Progress indicators during processing
- ✅ Detailed result expanders
- ✅ Direct download buttons

## File Structure

```
/workspace/
├── streamlit_app.py      # Main Streamlit application
├── fyp/                  # AutoMasher backend
│   └── app/
│       └── core.py       # Core mashup logic
├── resources/            # Dataset and assets
│   ├── dataset/          # Audio dataset
│   └── assets/           # UI assets (logo, etc.)
└── README_STREAMLIT.md   # This file
```

## API Reference

The application uses these core functions from the AutoMasher backend:

- `mashup_song()`: Create mashup from YouTube link
- `mashup_from_id()`: Recreate mashup from ID
- `load_dataset()`: Load the audio dataset
- `get_url()`: Normalize YouTube URLs

## License

This application is provided for research purposes only. All audio materials used constitute fair use under Section 107 of the 1976 Copyright Act. Commercial use is prohibited.

## Support

For issues or questions, please refer to the main AutoMasher repository documentation.
