# Features from the original script that I have left unimplemented in the re-factored version

- Multiple "rectangles" per note
- Color ranges
- Colors are randomized (and with possibility of "freezing" them)
- settings:
    - shadow_highlight_weaken_factor: float = 1
    - close_shadows: bool = True

# TODO

- colors should have transparency as well

# Scheme ideas

Something like this:
shadow_positions=[(-5, -5), (-10, -10), (-15, -15), (-20, -20)],
with shadow_gradients
