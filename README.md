# Midani

Make piano-roll animations from midi files.

Frames are plotted with R and then combined into a video with opencv-python. Finally, audio is added with FFmpeg. Why, you might ask, is R used to plot frames, rather than a Python plotting library like Matplotlib? For no better reason than that at the time I started the script (in summer 2018), R was the only plotting software I was familiar with.

## Dependencies

Requires Python >= 3.8

- Python libraries:
    - opencv-python
    - mido
- Other:
    - R to plot frames
    - FFmpeg to add audio

## Installation

To install R and FFmpeg on MacOS with Homebrew:

```
brew install r
brew install ffmpeg
```

To install Python dependencies, from script directory:

```
pip install -r requirements.txt
```

## Example Usage:

Create an animation with the default settings:

`python midani.py --midi [MIDIFILE]`

The same, but add audio as well:

`python midani.py --midi [MIDIFILE] --audio [AUDIOFILE]`

The same, but animate at 2fps rather than the default 30fps, so you can get a flavor of the results without waiting quite so long:

`python midani.py --midi [MIDIFILE] --audio [AUDIOFILE] --test`

Create an animation using one of the sample settings and one of the sample midi/audio files:

`python midani.py --settings sample_settings/settings1.py`

## Usage

```
usage: midani.py [-h] [-m MIDI] [-a AUDIO] [-s SETTINGS] [-t]

Animate a midi file. The path to a midi file must either be included as a
command line argument with -m/--midi, or it must be specified with the
"midifname" keyword argument in a settings file provided with -s/--settings.

optional arguments:
  -h, --help            show this help message and exit
  -m MIDI, --midi MIDI  path to midi file to animate
  -a AUDIO, --audio AUDIO
                        path to audio file to add to video
  -s SETTINGS, --settings SETTINGS
                        path to settings file containing a Python dictionary
  -t, --test            set frame rate to a maximum of 2 fps
```

## Sample files

The subdirectory `sample_settings` contains a few sample settings files to quickly demonstrate a few of the different options available.

The subdirectory `sample_music` contains a few midi files to play with for demo purposes. I created these algorithmically with another project of mine. I have provided mp3s generated therefrom with `fluidsynth` and a free General MIDI soundfont. The audio fidelity may leave something to be desired.

## Configuration

For full documentation of the various settings available, see `docs/settings.md`.

To configure with custom settings, save a file containing only a python dictionary, and pass it as an argument with `-s`/`--settings`. This file will be parsed with `ast.literal_eval` so, to quote the Python docs, it "may only consist of the following Python literal structures: strings, bytes, numbers, tuples, lists, dicts, sets, booleans, and None."

For example, if you wanted a "primary color" note color palette, with white background color, you could save the following dictionary in a file called `example.py` and then invoke the script with `--settings example.py`:

```python
{
    "color_palette": (
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
    ),
    "bg_colors": (
        (255, 255, 255),
    ),
}
```

For more examples, see the files in `sample_settings/`.

## Major TODOs

- documentation
- tests
- finish sample_settings
- mop-up bugs etc.
