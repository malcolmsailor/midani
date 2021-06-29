# Features from the original script that I have left unimplemented in the re-factored version

- Multiple "rectangles" per note
- Color ranges
- Colors are randomized (and with possibility of "freezing" them)
- settings:
    - shadow_highlight_weaken_factor: float = 1
    - close_shadows: bool = True
- bg_colors per-channel (I don't think this was ever implemented, in any case)

# Things that could be added longterm

- allow different shapes for notes
- matplotlib rather than R
- allow rotation of notes, channel skew, etc.
So many, but a few are
- line width on a per-voice basis
- settings.shadow_scale applies to connection lines as well?
- connection_lines for simultaneous notes go to previous/following non-simultaneous notes?

# Scheme ideas

Something like this:
shadow_positions=[(-5, -5), (-10, -10), (-15, -15), (-20, -20)],
with shadow_gradients

Primary colors every 4 beats or so for bg_colors

# Known issues

- extremely long midi notes can behave strangely
