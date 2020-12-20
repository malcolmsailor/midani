# Midani

Make piano-roll animations from midi files

## Description

TODO

Requires Python >= 3.8

## Dependencies

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

The same, but animate at 2fps rather than the default 30fps, so you can get a flavor of the results without waiting quite so long:

`python midani.py --midi [MIDIFILE] --test`

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

### Sample files

The subdirectory `sample_settings` contains a few sample settings files to quickly demonstrate a few of the different options available.

The subdirectory `sample_music` contains a few midi files to play with for demo purposes. I created these algorithmically with another project of mine. I have provided mp3s generated therefrom with `fluidsynth` and a free General MIDI soundfont. The audio fidelity may leave something to be desired.

## Major TODOs

- documentation
- tests
- finish sample_settings
- mop-up bugs etc.
