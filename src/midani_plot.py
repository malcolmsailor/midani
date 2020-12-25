"""Plots frames according to settings.
"""

import math

import src.midani_annotations as midani_annotations
import src.midani_colors as midani_colors
import src.midani_misc_classes as midani_misc_classes
import src.midani_r as midani_r
import src.midani_score as midani_score
import src.midani_time as midani_time


def _rect_or_its_shadow_in_frame(now, note, settings):
    return (
        note.start + settings.min_shadow_x_time - now <= settings.note_end
        and now - note.end - settings.max_shadow_x_time <= settings.note_start
    )


def _line_or_its_shadow_in_frame(now, note, note_i, settings, voice_i):

    if (
        note.start + settings.min_shadow_x_time - now <= settings.note_end
        and now - note.end - settings.max_shadow_x_time <= settings.note_start
    ):
        return True
    try:
        prev = voice_i[note_i - 1]
    except IndexError:
        pass
    else:
        if (
            prev.start + settings.min_shadow_x_time - now <= settings.line_end
            and now - prev.start - settings.max_shadow_x_time
            <= settings.line_start
        ):
            return True
    try:
        next_ = voice_i[note_i + 1]
    except IndexError:
        pass
    else:
        if (
            next_.start + settings.min_shadow_x_time - now <= settings.line_end
            and now - next_.start - settings.max_shadow_x_time
            <= settings.line_start
        ):
            return True
    return False


def get_voice_and_line_tuples(now, settings, table):
    rect_tuples = []
    line_tuples = []
    if settings.bounce_type == "scalar":
        bounce_term = max(1, settings.bounce_radius,)
    else:
        bounce_term = 0
    for voice_i, voice in zip(settings.voice_order, table):
        color = settings[voice_i]["color"]
        rect_tuples.append([])
        line_tuples.append([])
        for note_i, note in enumerate(voice):
            rect_in_frame = _rect_or_its_shadow_in_frame(now, note, settings)
            line_in_frame = (
                _line_or_its_shadow_in_frame(now, note, note_i, settings, voice)
                if settings[voice_i]["connection_lines"]
                else False
            )
            if not rect_in_frame and not line_in_frame:
                continue

            t_until_attack = note.start - now
            if settings.scale_notes_from_attack:
                t_until_for_scale = t_until_attack
            else:
                t_until_for_scale = note.t_mid - now
            scale_x_factor, scale_y_factor = table.scale_factors(
                t_until_for_scale, voice_i
            )
            highlight_factor = table.highlight_factor(t_until_attack)
            if settings[voice_i]["connection_lines"]:
                line_scale_factor = table.line_scale_factor(t_until_for_scale)
            flutter = 0
            if settings.max_flutter_size > 0:
                flutter += table.pitch_flutters[voice_i][note.pitch](now)
            # (Following condition is not true if settings.bounce_len is
            # zero, so no need to check that separately)
            if (
                settings.bounce_radius > 0
                and 0 < -t_until_attack < settings.bounce_len
            ):
                bounce = (
                    settings.bounce_radius
                    * (
                        (t_until_attack + settings.bounce_len)
                        / settings.bounce_len
                    )  # proportion of bounce_len since attack
                    * math.sin((-t_until_attack) * settings.bounce_sin_factor)
                ) + bounce_term
                if settings.bounce_type == "scalar":
                    scale_x_factor *= bounce
                    scale_y_factor *= bounce
                else:
                    flutter += bounce
            if rect_in_frame:
                rect_tuples[-1].append(
                    midani_misc_classes.RectTuple(
                        note,
                        scale_x_factor,
                        scale_y_factor,
                        flutter,
                        color,
                        highlight_factor,
                    )
                )
            if line_in_frame:
                line_tuples[-1].append(
                    midani_misc_classes.LineTuple(
                        note,
                        line_scale_factor,
                        flutter,
                        color,
                        highlight_factor,
                    )
                )

    return rect_tuples, line_tuples


def _get_shadow_gradient(
    shadow_i, shadow_color, main_color, hl_factor, settings
):
    shadow_n_strength = shadow_i / (
        settings.num_shadows + settings.shadow_gradient_offset
    )
    shadow_n_color = midani_colors.blend_colors(
        shadow_color, main_color, shadow_n_strength,
    )
    if (hl_blend := hl_factor * settings.shadow_hl_strength) :
        shadow_n_color = midani_colors.blend_colors(
            shadow_n_color, settings.highlight_color, hl_blend,
        )
    return shadow_n_color


def draw_note_shadows(
    shadow_i, shadow_position, rect_tuples, window, settings, table, r_boss
):
    shadow_n = settings.num_shadows - shadow_i
    for voice_i, voice in zip(settings.voice_order, rect_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i]["rectangles"]
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        shadow_color = midani_colors.blend_colors(
            window.bg_color,
            settings[voice_i]["shadow_color"],
            settings[voice_i]["shadow_strength"],
        )
        shadow_n_color = shadow_color

        for rect in voice:
            half_width = (
                rect.note.dur
                * rect.scale_x_factor
                * settings.shadow_scale ** shadow_n
                / 2
            )
            half_height = (
                channel.note_height
                * rect.scale_y_factor
                * settings.shadow_scale ** shadow_n
                / 2
            )
            shadow_x = shadow_position.shadow_x
            shadow_y = shadow_position.shadow_y
            if settings.shadow_gradients:
                shadow_n_color = _get_shadow_gradient(
                    shadow_i,
                    shadow_color,
                    rect.color,
                    rect.highlight_factor,
                    settings,
                )
            bottom = channel.y_position(rect.pitch) - half_height + shadow_y
            top = channel.y_position(rect.pitch) + half_height + shadow_y
            if bottom >= top:
                continue
            r_boss.plot_rect(
                max(window.start, rect.note.mid + shadow_x - half_width,),
                min(window.end, rect.note.mid + shadow_x + half_width,),
                bottom,
                top,
                shadow_n_color,
            )


def draw_shadows(line_tuples, rect_tuples, window, settings, table, r_boss):
    if settings.shadows <= 0:
        return
    for shadow_i, shadow_position in enumerate(
        reversed(settings.shadow_positions)
    ):
        draw_line_shadows(
            shadow_i,
            shadow_position,
            line_tuples,
            window,
            settings,
            table,
            r_boss,
        )
        draw_note_shadows(
            shadow_i,
            shadow_position,
            rect_tuples,
            window,
            settings,
            table,
            r_boss,
        )


def _connection_line_conditions_apply(now, src, dst, settings):
    if dst.note.start - now > settings.line_end:
        return False
    if now - src.note.end > settings.line_start:
        return False
    if (
        settings.no_connection_lines_between_simultaneous_notes
        and src.note.start == dst.note.start
    ):
        return False
    if dst.note.mid - src.note.mid > settings.max_connection_line_duration:
        return False
    if abs(dst.pitch - src.pitch) > settings.max_connection_line_interval:
        return False
    return True


def draw_line_shadows(
    shadow_i, shadow_position, line_tuples, window, settings, table, r_boss
):
    for voice_i, voice in zip(settings.voice_order, line_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i]["connection_lines"]
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        shadow_color = midani_colors.blend_colors(
            window.bg_color,
            settings[voice_i]["shadow_color"],
            settings[voice_i]["shadow_strength"],
        )
        for src, dst in zip(voice, voice[1:]):
            if not _connection_line_conditions_apply(
                window.now, src, dst, settings
            ):
                continue
            if settings.shadow_gradients:
                src_color = midani_colors.blend_colors(
                    src.color,
                    settings.con_line_offset_color,
                    settings.con_line_offset_prop,
                )
                shadow_n_color = _get_shadow_gradient(
                    shadow_i,
                    shadow_color,
                    src_color,
                    0,  # no highlighting of connection lines
                    settings,
                )
            else:
                shadow_n_color = shadow_color
            r_boss.plot_line(
                x1=src.note.mid + shadow_position.cline_shadow_x,
                x2=dst.note.mid + shadow_position.cline_shadow_x,
                y1=channel.y_position(src.pitch)
                + shadow_position.cline_shadow_y,
                y2=channel.y_position(dst.pitch)
                + shadow_position.cline_shadow_y,
                width=settings.con_line_width * src.scale_factor,
                color=shadow_n_color,
            )


def draw_connection_lines(line_tuples, window, settings, table, r_boss):
    for voice_i, voice in zip(settings.voice_order, line_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i]["connection_lines"]
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        for src, dst in zip(voice, voice[1:]):
            if not _connection_line_conditions_apply(
                window.now, src, dst, settings
            ):
                continue
            color = midani_colors.blend_colors(
                src.color,
                settings.con_line_offset_color,
                settings.con_line_offset_prop,
            )
            r_boss.plot_line(
                x1=src.note.mid,
                x2=dst.note.mid,
                y1=channel.y_position(src.pitch),
                y2=channel.y_position(dst.pitch),
                color=color,
                width=settings.con_line_width * src.scale_factor,
            )


def draw_notes(rect_tuples, window, settings, table, r_boss):
    for voice_i, voice in zip(settings.voice_order, rect_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i]["rectangles"]
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        for rect in voice:
            hl_strength_factor = (
                rect.highlight_factor * settings.highlight_strength
            )
            if hl_strength_factor > 0:
                color = midani_colors.blend_colors(
                    rect.color, settings.highlight_color, hl_strength_factor
                )
            else:
                color = rect.color
            half_width = 0.5 * rect.note.dur * rect.scale_x_factor
            half_height = 0.5 * rect.scale_y_factor
            r_boss.plot_rect(
                x1=max(window.start, rect.note.mid - half_width),
                x2=min(window.end, rect.note.mid + half_width),
                y1=channel.y_position(rect.pitch - half_height),
                y2=channel.y_position(rect.pitch + half_height),
                color=color,
            )


def draw_lyrics(window, lyricist, settings, r_boss):
    lyric = lyricist(window.now)
    if lyric is None:
        return
    x = (window.end - window.start) * settings.lyrics_x + window.start
    y = settings.lyrics_y
    r_boss.text(
        text=lyric,
        x=x,
        y=y,
        color=settings.lyrics_color,
        size=settings.lyrics_size,
    )


def draw_annotations(window, settings, r_boss):
    y = 0.1
    for annot in settings.add_annotations:
        if annot in midani_annotations.ANNOT:
            for line in midani_annotations.ANNOT[annot](window).split("\n"):
                r_boss.text(
                    text=line, x=window.now, y=y, color=settings.annot_color,
                )
                y += 0.025


def plot(settings):
    score = midani_score.read_score(settings)
    tempo_changes = midani_time.TempoChanges(score)
    settings.update_from_score(score, tempo_changes)
    score = midani_score.crop_score(score, settings, tempo_changes)
    table = midani_misc_classes.PitchTable(score, settings, tempo_changes)
    r_boss = midani_r.RBoss(settings)
    window = midani_misc_classes.Window(settings)
    lyricist = midani_annotations.Lyricist(settings)
    now = window.get_first_now()
    while window.in_range(now):
        window.update(now)
        # In original script, I get the current tempo here, because "bounce"
        # was set in beats. But now, "bounce" is in seconds, so we have no
        # need for tempi.
        r_boss.init_png(window)
        if settings.now_line:
            r_boss.now_line(now, window)
        rect_tuples, line_tuples = get_voice_and_line_tuples(
            now, settings, table
        )
        draw_shadows(line_tuples, rect_tuples, window, settings, table, r_boss)
        draw_connection_lines(line_tuples, window, settings, table, r_boss)
        draw_notes(rect_tuples, window, settings, table, r_boss)
        draw_lyrics(window, lyricist, settings, r_boss)
        draw_annotations(window, settings, r_boss)
        now += settings.frame_increment
    r_boss.run_r()
    return r_boss.png_fnumber
