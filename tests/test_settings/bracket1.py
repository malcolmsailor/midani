{
    "seed": 0,
    "note_width": 0.95,
    "max_connection_line_interval": 24,
    "bg_colors": [(255, 255, 255, 255)],
    "connection_line_end_offset": 0.1,
    "connection_line_start_offset": 0.1,
    "default_bracket_settings": {"x_offset": 0.02, "text_size": 2.0},
    "voice_settings": {
        0: {
            "bracket_settings": {
                "rlen": {
                    "color": (126, 145, 139),
                },
                "plen": {"color": (0, 0, 0)},
                "hlen": {"color": (72, 115, 134), "y_offset": 4},
            },
            "default_bracket_settings": {"above": True, "text_y_offset": 0.7},
            "color_loop_var_amount": 164,
        },
        1: {
            "bracket_settings": {
                "rlen": {"color": (126, 145, 139)},
                "plen": {"color": (0, 0, 0)},
                "hlen": {"color": (72, 115, 134), "y_offset": 4},
            },
            "default_bracket_settings": {"text_y_offset": 0.3},
            "color_loop_var_amount": 128,
            "color_loop": 7,
        },
    },
    "voice_order_reverse": True,
    "duplicate_voice_settings": {2: (3,)},
    "midi_fname": [
        "tests/test_mid/example1.mid",
    ],
    "video_fname": "tests/test_out/bracket1.mp4",
    "color_loop": 6,
    "brackets": [
        (0.0, 1.0, "plen", "pattern_len = 2"),
        (1.0, 2.0, "plen", "", 1.0),
        (0.0, 2.0, "hlen", "harmony_len = 4"),
        (2.0, 4.0, "hlen", "", 2.0),
    ],
    "channel_settings": {0: {"l_padding": 0.2, "h_padding": 0.2}},
}
