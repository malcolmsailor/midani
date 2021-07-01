"""Plots frames according to settings.
"""

import math
import operator

from . import midani_annotations
from . import midani_colors
from . import midani_misc_classes

from . import midani_r
from . import midani_score
from . import midani_time


def _rect_or_its_shadow_in_frame(now, note, settings, voice_i):
    return (
        note.start + settings[voice_i].min_shadow_x_time - now
        <= settings[voice_i].frame_note_end
        and now - note.end - settings[voice_i].max_shadow_x_time
        <= settings[voice_i].frame_note_start
    )


def _line_or_its_shadow_in_frame(now, note, note_i, settings, voice, voice_i):

    if (
        note.start + settings[voice_i].min_shadow_x_time - now
        <= settings[voice_i].frame_note_end
        and now - note.end - settings[voice_i].max_shadow_x_time
        <= settings[voice_i].frame_note_start
    ):
        return True
    try:
        prev = voice[note_i - 1]
    except IndexError:
        pass
    else:
        if (
            prev.start + settings[voice_i].min_shadow_x_time - now
            <= settings[voice_i].frame_line_end
            and now - prev.start - settings[voice_i].max_shadow_x_time
            <= settings[voice_i].frame_line_start
        ):
            return True
    try:
        next_ = voice[note_i + 1]
    except IndexError:
        pass
    else:
        if (
            next_.start + settings[voice_i].min_shadow_x_time - now
            <= settings[voice_i].frame_line_end
            and now - next_.start - settings[voice_i].max_shadow_x_time
            <= settings[voice_i].frame_line_start
        ):
            return True
    return False


def get_voice_and_line_tuples(now, settings, table):
    rect_tuples = []
    line_tuples = []
    for voice_i, voice in zip(settings.voice_order, table):
        if settings[voice_i].bounce_type == "scalar":
            bounce_term = max(
                1,
                settings[voice_i].bounce_radius,
            )
        else:
            bounce_term = 0
        voice_color = settings[voice_i].color
        color_loop = settings[voice_i].color_loop
        rect_tuples.append([])
        line_tuples.append([])
        for note_i, note in enumerate(voice):
            rect_in_frame = _rect_or_its_shadow_in_frame(
                now, note, settings, voice_i
            )
            line_in_frame = (
                _line_or_its_shadow_in_frame(
                    now, note, note_i, settings, voice, voice_i
                )
                if settings[voice_i].connection_lines
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
            highlight_factor = table.highlight_factor(t_until_attack, voice_i)
            if settings[voice_i].connection_lines:
                line_scale_factor = table.line_scale_factor(
                    t_until_for_scale, voice_i
                )
            flutter = 0
            if settings[voice_i].max_flutter_size > 0:
                flutter += table.pitch_flutters[voice_i][note.pitch](now)
            # (Following condition is not true if settings[voice_i].bounce_len is
            # zero, so no need to check that separately)
            if (
                settings[voice_i].bounce_radius > 0
                and 0 < -t_until_attack < settings[voice_i].bounce_len
            ):
                bounce = (
                    settings[voice_i].bounce_radius
                    * (
                        (t_until_attack + settings[voice_i].bounce_len)
                        / settings[voice_i].bounce_len
                    )  # proportion of bounce_len since attack
                    * math.sin(
                        (-t_until_attack) * settings[voice_i].bounce_sin_factor
                    )
                ) + bounce_term
                if settings[voice_i].bounce_type == "scalar":
                    scale_x_factor *= bounce
                    scale_y_factor *= bounce
                else:
                    flutter += bounce
            if color_loop is not None:
                color = color_loop[note_i % len(color_loop)]
            else:
                color = voice_color
            # LONGTERM why store these tuples in a list instead of plotting
            #   them directly from this function?
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
                        voice_color,
                        highlight_factor,
                    )
                )

    return rect_tuples, line_tuples


def _get_shadow_gradient(
    shadow_i, shadow_color, main_color, hl_factor, settings, voice_i
):
    shadow_n_strength = shadow_i / (
        settings[voice_i].num_shadows + settings[voice_i].shadow_gradient_offset
    )
    shadow_n_color = midani_colors.blend_colors(
        shadow_color,
        main_color,
        shadow_n_strength,
    )
    if (hl_blend := hl_factor * settings[voice_i].shadow_hl_strength) :
        shadow_n_color = midani_colors.blend_colors(
            shadow_n_color,
            settings[voice_i].highlight_color,
            hl_blend,
        )
    return shadow_n_color


def draw_note_shadows(
    shadow_i, shadow_position, rect_tuples, window, settings, table, plot_boss
):
    shadow_n = settings.num_shadows - shadow_i
    for voice_i, voice in zip(settings.voice_order, rect_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i].rectangles
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        shadow_color = midani_colors.blend_colors(
            window.bg_color,
            settings[voice_i].shadow_color,
            settings[voice_i].shadow_strength,
        )
        shadow_n_color = shadow_color

        for rect in voice:
            half_width = (
                rect.note.dur
                * rect.scale_x_factor
                * settings[voice_i].shadow_scale_x ** shadow_n
                / 2
            )
            # half_height = (
            #     channel.note_height
            #     * rect.scale_y_factor
            #     * settings[voice_i].shadow_scale ** shadow_n
            #     / 2
            # )
            height = channel.pixel_height(
                rect.scale_y_factor
                * settings[voice_i].shadow_scale_y ** shadow_n
            )
            lower_half = height // 2
            upper_half = height - lower_half
            shadow_y = shadow_position.shadow_y
            # bottom = channel.y_position(rect.pitch) - half_height + shadow_y
            # top = channel.y_position(rect.pitch) + half_height + shadow_y
            bottom = channel.y_position(rect.pitch) - lower_half + shadow_y
            top = channel.y_position(rect.pitch) + upper_half + shadow_y
            if bottom >= top:
                continue
            shadow_x = shadow_position.shadow_x
            if settings[voice_i].shadow_gradients:
                shadow_n_color = _get_shadow_gradient(
                    shadow_i,
                    shadow_color,
                    rect.color,
                    rect.highlight_factor,
                    settings,
                    voice_i,
                )
            plot_boss.plot_rect(
                max(
                    window.start,
                    rect.note.mid + shadow_x - half_width,
                ),
                min(
                    window.end,
                    rect.note.mid + shadow_x + half_width,
                ),
                bottom,
                top,
                shadow_n_color,
                zorder=5,
            )


def draw_shadows(line_tuples, rect_tuples, window, settings, table, plot_boss):
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
            plot_boss,
        )
        draw_note_shadows(
            shadow_i,
            shadow_position,
            rect_tuples,
            window,
            settings,
            table,
            plot_boss,
        )


def _connection_line_conditions_apply(now, src, dst, settings, voice_i):
    if dst.note.start - now > settings[voice_i].frame_line_end:
        return False
    if now - src.note.end > settings[voice_i].frame_line_start:
        return False
    if (
        settings[voice_i].no_connection_lines_between_simultaneous_notes
        and src.note.start == dst.note.start
    ):
        return False
    x1 = (
        src.note.mid
        if settings[voice_i].connection_line_end_offset is None
        else max(
            src.note.end - settings[voice_i].connection_line_end_offset,
            src.note.mid,
        )
    )
    x2 = (
        dst.note.mid
        if settings[voice_i].connection_line_start_offset is None
        else min(
            dst.note.start + settings[voice_i].connection_line_start_offset,
            dst.note.mid,
        )
    )
    if x2 - x1 > settings[voice_i].max_connection_line_duration:
        return False
    if (
        abs(dst.pitch - src.pitch)
        > settings[voice_i].max_connection_line_interval
    ):
        return False
    return True


def draw_line_shadows(
    shadow_i, shadow_position, line_tuples, window, settings, table, plot_boss
):
    for voice_i, voice in zip(settings.voice_order, line_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i].connection_lines
        ):
            continue
        line_start_offset = settings[voice_i].connection_line_start_offset
        line_end_offset = settings[voice_i].connection_line_end_offset
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        shadow_color = midani_colors.blend_colors(
            window.bg_color,
            settings[voice_i].shadow_color,
            settings[voice_i].shadow_strength,
        )
        for src, dst in zip(voice, voice[1:]):
            if not _connection_line_conditions_apply(
                window.now, src, dst, settings, voice_i
            ):
                continue
            if settings[voice_i].shadow_gradients:
                src_color = midani_colors.blend_colors(
                    src.color,
                    settings[voice_i].con_line_offset_color,
                    settings[voice_i].con_line_offset_prop,
                )
                shadow_n_color = _get_shadow_gradient(
                    shadow_i,
                    shadow_color,
                    src_color,
                    0,  # no highlighting of connection lines
                    settings,
                    voice_i,
                )
            else:
                shadow_n_color = shadow_color
            x1 = (
                src.note.mid
                if line_end_offset is None
                else max(src.note.end - line_end_offset, src.note.mid)
            )
            x2 = (
                dst.note.mid
                if line_start_offset is None
                else min(dst.note.start + line_start_offset, dst.note.mid)
            )
            plot_boss.plot_line(
                x1=x1 + shadow_position.cline_shadow_x,
                x2=x2 + shadow_position.cline_shadow_x,
                y1=channel.y_position(src.pitch)
                + shadow_position.cline_shadow_y,
                y2=channel.y_position(dst.pitch)
                + shadow_position.cline_shadow_y,
                width=settings[voice_i].con_line_width * src.scale_factor,
                color=shadow_n_color,
                zorder=1,
            )


def draw_connection_lines(line_tuples, window, settings, table, plot_boss):
    for voice_i, voice in zip(settings.voice_order, line_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i].connection_lines
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        line_start_offset = settings[voice_i].connection_line_start_offset
        line_end_offset = settings[voice_i].connection_line_end_offset
        for src, dst in zip(voice, voice[1:]):
            if not _connection_line_conditions_apply(
                window.now, src, dst, settings, voice_i
            ):
                continue
            color = midani_colors.blend_colors(
                src.color,
                settings[voice_i].con_line_offset_color,
                settings[voice_i].con_line_offset_prop,
            )
            x1 = (
                src.note.mid
                if line_end_offset is None
                else max(src.note.end - line_end_offset, src.note.mid)
            )
            x2 = (
                dst.note.mid
                if line_start_offset is None
                else min(dst.note.start + line_start_offset, dst.note.mid)
            )
            plot_boss.plot_line(
                x1=x1,
                x2=x2,
                y1=channel.y_position(src.pitch),
                y2=channel.y_position(dst.pitch),
                color=color,
                width=settings[voice_i].con_line_width * src.scale_factor,
                zorder=10,
            )


def draw_notes(rect_tuples, window, settings, table, plot_boss):
    for voice_i, voice in zip(settings.voice_order, rect_tuples):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or not settings[voice_i].rectangles
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        for rect in voice:
            hl_strength_factor = (
                rect.highlight_factor * settings[voice_i].highlight_strength
            )
            if hl_strength_factor > 0:
                color = midani_colors.blend_colors(
                    rect.color,
                    settings[voice_i].highlight_color,
                    hl_strength_factor,
                )
            else:
                color = rect.color
            half_width = 0.5 * rect.note.dur * rect.scale_x_factor
            # The next lines are part of an abortive attempt to express
            # x coordinates in pixels, which I foolishly started before
            # committing other changes...
            # width = window.x_width(rect.note.dur * rect.scale_x_factor)
            # left_width = width // 2
            # right_width = width - left_width
            # x_mid = window.x_position(rect.note.mid)
            height = channel.pixel_height(rect.scale_y_factor)
            lower_half = height // 2
            upper_half = height - lower_half
            plot_boss.plot_rect(
                x1=max(window.start, rect.note.mid - half_width),
                x2=min(window.end, rect.note.mid + half_width),
                # The next lines are part of an abortive attempt to express
                # x coordinates in pixels, which I foolishly started before
                # committing other changes...
                # x1=max(window.pixel_start, x_mid - left_width),
                # x2=min(window.pixel_end, x_mid + right_width),
                y1=channel.y_position(rect.pitch) - lower_half,
                y2=channel.y_position(rect.pitch) + upper_half,
                color=color,
                zorder=15,
            )


def draw_lyrics(window, lyricist, settings, plot_boss):
    lyric = lyricist(window.now)
    if lyric is None:
        return
    x = (window.end - window.start) * settings.lyrics_x + window.start
    y = settings.lyrics_y
    plot_boss.text(
        text=lyric,
        x=x,
        y=window.y_position(y),
        color=settings.lyrics_color,
        size=settings.lyrics_size,
        zorder=20,
    )


def draw_annotations(window, settings, plot_boss):
    y = 0.1
    for annot in settings.add_annotations:
        if annot in midani_annotations.ANNOT:
            for line in midani_annotations.ANNOT[annot](window).split("\n"):
                plot_boss.text(
                    text=line,
                    x=window.now,
                    y=window.y_position(y),
                    color=settings.annot_color,
                    size=settings.annot_size,
                    zorder=20,
                )
                y += 0.025


class NoBracket(Exception):
    """Raised in yield_bracket_coords() when there is no bracket."""


def yield_bracket_coords(bracket, voice, voice_i, bracket_settings, window):
    def _check_index(attr):
        val = getattr(bracket, attr)
        if isinstance(val, int):
            try:
                return getattr(voice[val], attr)
            except IndexError:
                print(
                    f"Warning: index {val} does not exist in voice "
                    f"{voice_i}, skipping bracket"
                )
                raise NoBracket  # pylint: disable=raise-missing-from
        return None

    def _check_coords(x1, x2):
        if x2 < window.start:
            raise NoBracket
        if x1 > window.end:
            raise NoBracket

    start_offset = bracket_settings.x_offset
    end_offset = -bracket_settings.x_offset
    start = _check_index("start")
    end = _check_index("end")
    if start is not None and end is not None:
        x1 = start + start_offset
        x2 = end + end_offset
        try:
            _check_coords(x1, x2)
        except NoBracket:
            pass
        else:
            yield x1, x2
    else:  # start and end should be floats... I should perhaps type-check that earlier
        x1 = bracket.start + start_offset
        x2 = bracket.end + end_offset
        try:
            _check_coords(x1, x2)
        except NoBracket:
            pass
        else:
            yield x1, x2
        if bracket.loop is not None:
            loop_end = (
                window.end_time
                if bracket.loop_end is None
                else bracket.loop_end
            )
            start = bracket.start
            while True:
                start += bracket.loop
                x2 += bracket.loop
                x1 = start + start_offset
                try:
                    _check_coords(x1, x2)
                except NoBracket:
                    pass
                else:
                    yield x1, x2
                if start >= loop_end:
                    break


def draw_brackets(table, window, settings, plot_boss):
    for voice_i, voice in zip(settings.voice_order, table):
        if (
            voice_i not in settings.voices_to_render
            or not voice
            or (
                None
                in (
                    settings[voice_i].brackets,
                    settings[voice_i].bracket_settings,
                )
            )
        ):
            continue
        channel_i = settings.chan_assmts[voice_i]
        channel = table.channels[channel_i]
        for bracket in settings[voice_i].brackets + settings.brackets:
            bracket_settings = settings[voice_i].bracket_settings[bracket.type]
            for x1, x2 in yield_bracket_coords(
                bracket, voice, voice_i, bracket_settings, window
            ):
                if bracket_settings.above:
                    op = operator.add
                    extreme = max
                    limit_pitch = voice.h_pitch
                else:
                    op = operator.sub
                    extreme = min
                    limit_pitch = voice.l_pitch
                if (
                    # If I ever implement validation earlier, then it
                    # shouldn't be necessary to check that these are
                    # *both* ints
                    isinstance(bracket.start, int)
                    and isinstance(bracket.end, int)
                    and bracket_settings.tight
                ):
                    y1 = op(
                        extreme(
                            note.pitch
                            for note in voice[bracket.start : bracket.end + 1]
                        ),
                        bracket_settings.y_offset,
                    )
                else:
                    y1 = op(limit_pitch, bracket_settings.y_offset)
                y2 = op(y1, bracket_settings.height)
                plot_boss.bracket(
                    x1=x1,
                    x2=x2,
                    y1=channel.y_position(y1),
                    y2=channel.y_position(y2),
                    color=bracket_settings.color,
                    width=bracket_settings.line_width,
                    zorder=20,
                )
                if not bracket.text:
                    continue
                if bracket_settings.above:
                    # the meaning of "position" is borrowed from R's 'adj'
                    # arg: 0 for left/bottom, 1 for right/top, and 0.5 for
                    # centered.
                    position = (0.5, 0)
                    y2 += bracket_settings.text_y_offset
                else:
                    position = (0.5, 1)
                    y2 -= bracket_settings.text_y_offset
                plot_boss.text(
                    bracket.text,
                    (x2 - x1) / 2 + x1,
                    channel.y_position(y2),
                    bracket_settings.color,
                    size=bracket_settings.text_size,
                    position=position,
                    zorder=20,
                )


def plot(settings, mpl, frame_list=None):
    score = midani_score.read_score(settings)
    tempo_changes = midani_time.TempoChanges(score)
    settings.update_from_score(score, tempo_changes)
    score = midani_score.crop_score(score, settings, tempo_changes)
    table = midani_misc_classes.PitchTable(score, settings, tempo_changes)
    if mpl:
        # we move the import statement here because we don't want to require
        # matplotlib unless it is actually being used.
        from . import plt_boss

        plot_boss = plt_boss.MPLBoss(settings)
    else:
        plot_boss = midani_r.RBoss(settings)
    window = midani_misc_classes.Window(settings)
    lyricist = midani_annotations.Lyricist(settings)
    if frame_list is not None:
        frame_iter = iter(frame_list)
        now = next(frame_iter)
    else:
        now = window.get_first_now()
    while window.in_range(now):
        window.update(now)
        # Originally, I got the current tempo here, because "bounce"
        # was set in beats. But now, "bounce" is in seconds, so we have no
        # need for tempi.
        with plot_boss.make_png(window):
            if settings.now_line:
                plot_boss.now_line(now, window)
            rect_tuples, line_tuples = get_voice_and_line_tuples(
                now, settings, table
            )
            draw_shadows(
                line_tuples, rect_tuples, window, settings, table, plot_boss
            )
            draw_connection_lines(
                line_tuples, window, settings, table, plot_boss
            )
            draw_notes(rect_tuples, window, settings, table, plot_boss)
            draw_lyrics(window, lyricist, settings, plot_boss)
            draw_annotations(window, settings, plot_boss)
            draw_brackets(table, window, settings, plot_boss)
            if frame_list is not None:
                try:
                    now = next(frame_iter)
                except StopIteration:
                    break
            else:
                now += settings.frame_increment
    plot_boss.run()
    return plot_boss.plot_count
