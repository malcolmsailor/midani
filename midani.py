import math
import os
import random
import re
import subprocess

import cv2

import midi_funcs

import midani_annotations
import midani_colors
import midani_misc_classes
import midani_r
import midani_settings
import midani_time


def read_score(settings):
    return midi_funcs.read_midi_to_internal_data(
        settings.midifname, tet=settings.tet
    )


def crop_score(score, settings, tempo_changes):
    start_beat = tempo_changes.btime_from_ctime(settings.start_time)
    end_beat = tempo_changes.btime_from_ctime(settings.end_time)
    return score.get_passage(
        passage_start_time=start_beat,
        passage_end_time=end_beat,
        end_time_refers_to_attack=True,
    )


def sign(f):
    if f == 0:
        return f
    elif f < 0:
        return -1
    return 1


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
        next = voice_i[note_i + 1]
    except IndexError:
        pass
    else:
        if (
            next.start + settings.min_shadow_x_time - now <= settings.line_end
            and now - next.start - settings.max_shadow_x_time
            <= settings.line_start
        ):
            return True
    return False


def get_voice_and_line_tuples(now, window, settings, table):
    rect_tuples = []
    line_tuples = []
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
                line_scale_factor = table.line_scale_factor(
                    t_until_for_scale, voice_i
                )
            flutter = 0
            if settings.max_flutter_size > 0:
                flutter += table.pitch_flutters[voice_i][note.pitch](now)
            # (Following condition is not true if settings.bounce_len is
            # zero, so no need to check that separately)
            if 0 <= -t_until_attack < settings.bounce_len:
                # TODO review this math?
                bounce_factor = (t_until_attack / settings.bounce_len + 1) * (
                    math.sin((-t_until_attack) * settings.bounce_sin_factor)
                )
                bounce = settings.bounce_size * bounce_factor
                if settings.bounce_type == "scalar":
                    scale_x_factor *= 1 + bounce
                    scale_y_factor *= 1 + bounce
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


def draw_note_shadows(rect_tuples, window, settings, table, r_boss):
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
            window.bg_color(),
            settings[voice_i]["shadow_color"],
            settings[voice_i]["shadow_strength"],
        )
        for shadow_position in settings.shadow_positions:
            for shadow_i in range(settings.num_shadows):
                shadow_n = settings.num_shadows - shadow_i
                for rect in voice:
                    # I only ever used pxwidth and pywidth divided by 2 so I
                    # just divide them by 2 here
                    pxwidth = (
                        rect.note.dur
                        * rect.scale_x_factor
                        * settings.shadow_scale ** shadow_n
                        / 2
                    )
                    pywidth = (
                        channel.note_height
                        * rect.scale_y_factor
                        * settings.shadow_scale ** shadow_n
                        / 2
                    )
                    shadow_x = shadow_position.shadow_x * shadow_n
                    shadow_y = shadow_position.shadow_y * shadow_n
                    if settings.shadow_gradients:
                        shadow_n_strength = shadow_i / (
                            settings.num_shadows
                            + settings.shadow_gradient_offset
                        )
                        shadow_n_color = midani_colors.blend_colors(
                            shadow_color, rect.color, shadow_n_strength,
                        )
                        if (
                            hl_blend := rect.highlight_factor
                            * settings.shadow_hl_strength
                        ) :
                            shadow_n_color = midani_colors.blend_colors(
                                shadow_n_color,
                                settings.highlight_color,
                                hl_blend,
                            )
                    # TODO why is the value of half_height not calculated from
                    # basic_y_width and pywidth in the same way as half_width?
                    half_height = 0.5 * rect.scale_y_factor
                    bottom = (
                        channel.y_position(rect.pitch - half_height) + shadow_y
                    )
                    top = (
                        channel.y_position(rect.pitch + half_height) + shadow_y
                    )
                    if bottom >= top:
                        continue
                    half_width = 0.5 * rect.note.dur - pxwidth
                    r_boss.plot_rect(
                        max(
                            window.start,
                            rect.note.start + shadow_x + half_width,
                        ),
                        min(window.end, rect.note.end + shadow_x - half_width,),
                        bottom,
                        top,
                        shadow_n_color,
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
    if dst.note.start - src.note.end > settings.max_connection_line_distance:
        return False
    if abs(dst.pitch - src.pitch) > settings.max_connection_line_interval:
        return False
    return True


def draw_line_shadows(line_tuples, window, settings, table, r_boss):
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
            window.bg_color(),
            settings[voice_i]["shadow_color"],
            settings[voice_i]["shadow_strength"],
        )
        for shadow_position in settings.shadow_positions:
            for shadow_i in range(settings.num_shadows):
                for src, dst in zip(voice, voice[1:]):
                    if not _connection_line_conditions_apply(
                        window.now, src, dst, settings
                    ):
                        continue
                    r_boss.plot_line(
                        x1=src.note.mid + shadow_position.cline_shadow_x,
                        x2=dst.note.mid + shadow_position.cline_shadow_x,
                        y1=channel.y_position(src.pitch)
                        + shadow_position.cline_shadow_y,
                        y2=channel.y_position(dst.pitch)
                        + shadow_position.cline_shadow_y,
                        width=settings.con_line_width * src.scale_factor,
                        color=shadow_color,
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
            color = src.color
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


def draw_annotations(window, settings, r_boss):
    y = 0.1
    for annot in settings.add_annotations:
        if annot in midani_annotations.ANNOT:
            for line in midani_annotations.ANNOT[annot](window, settings).split(
                "\n"
            ):
                r_boss.annotate(
                    text=line, x=window.now, y=y, color=settings.annot_color,
                )
                y += 0.025


def plot(settings, table):
    r_boss = midani_r.RBoss(settings)
    window = midani_misc_classes.Window(settings)
    now = window.get_first_now()
    while window.in_range(now):
        window.update(now)
        # In original script, I get the current tempo here, because "bounce"
        # was set in beats. But now, "bounce" is in seconds, so we have no
        # need for tempi.
        # print(f"Time = {now}")
        r_boss.init_png(window)
        if settings.now_line:
            r_boss.now_line(now, window)
        rect_tuples, line_tuples = get_voice_and_line_tuples(
            now, window, settings, table
        )
        if settings.shadow_strength > 0:
            if not settings.shadows_over_clines:
                draw_note_shadows(rect_tuples, window, settings, table, r_boss)
            draw_line_shadows(line_tuples, window, settings, table, r_boss)
        draw_connection_lines(line_tuples, window, settings, table, r_boss)
        if settings.shadow_strength > 0 and settings.shadows_over_clines:
            draw_note_shadows(rect_tuples, window, settings, table, r_boss)
        draw_notes(rect_tuples, window, settings, table, r_boss)
        draw_annotations(window, settings, r_boss)
        now += settings.frame_increment

    r_boss.run_r()
    return r_boss.png_fnumber


def process_video(settings, n):
    # After http://tsaith.github.io/combine-images-into-a-video-with-python-3-and-opencv-3.html

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Be sure to use lower case
    out = cv2.VideoWriter(
        settings.video_fname,
        fourcc,
        1 / settings.frame_increment,
        (settings.out_width, settings.out_height),
    )

    if (
        len(settings.png_fname_base) + settings._png_fnum_digits + 4
        > os.get_terminal_size().columns
    ):
        print_png = os.path.basename(settings.png_fname_base)
    else:
        print_png = settings.png_fname_base

    print(f"Building {settings.video_fname}...")
    for i in range(1, n):
        str_i = str(i).zfill(settings._png_fnum_digits)
        img_path = f"{settings.png_fname_base}{str_i}.png"
        print(f"\r{print_png}{str_i}.png", end="")
        frame = cv2.imread(img_path)
        if frame is None:
            breakpoint(f"Couldn't read {img_path}")
        out.write(frame)
    print("\nDone.")

    out.release()
    cv2.destroyAllWindows()
    # TODO add audio?


def main(settings):
    if settings.process_video != "only":
        score = read_score(settings)
        tempo_changes = midani_time.TempoChanges(score)
        settings.update_from_score(score, tempo_changes)
        score = crop_score(score, settings, tempo_changes)
        pitch_table = midani_misc_classes.PitchTable(
            score, settings, tempo_changes
        )
        # TODO multiply channel_offsets by window_range?
        n_frames = plot(settings, pitch_table)
    else:
        png_pattern = re.compile(
            os.path.basename(settings.png_fname_base) + r"\d+\.png"
        )
        n_frames = len(
            [
                f
                for f in os.listdir(settings.output_dirname)
                if re.match(png_pattern, f)
            ]
        )
    if settings.process_video != "no":
        process_video(settings, n_frames)


if __name__ == "__main__":
    # TODO
    main()
