#!/usr/bin/env python3
"""Local, byte-approved marketing timelines. No upload, generation or publishing."""
import argparse
import contextlib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from PIL import ImageFont
from ags_common import LOUDNORM, group_word_lists, transcribe_words, video_info
from ags_editorial_sub import STYLES, write_ass, subtitles_filter
from ags_reframe import reframe_filter


def _run(args, cwd=None):
    try:
        result = subprocess.run([str(a) for a in args], capture_output=True, text=True, cwd=cwd)
    except OSError as exc:
        raise RuntimeError(f"Missing local dependency: {exc}") from exc
    if result.returncode:
        raise RuntimeError(f"Local media command failed: {result.stderr[-3000:]}")
    return result.stdout


def _json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read JSON {path}: {exc}") from exc


def _save(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
        tmp = Path(stream.name)
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _file(base, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected a nonempty local asset path')
    path = (base / value).resolve()
    if not path.is_file():
        raise ValueError(f"Missing local file: {path}")
    return path


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonblank")
    return value


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{field} must be finite numeric seconds, not bool")
    return float(value)


def _probe(path):
    try:
        data = json.loads(_run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))
        streams = data.get('streams', [])
        raw_duration = data.get('format', {}).get('duration', 0)
        duration = float(raw_duration) if raw_duration not in (None, '', 'N/A') else 0.0
        return {'duration': duration, 'audio': any(s['codec_type'] == 'audio' for s in streams),
                'video': any(s['codec_type'] == 'video' for s in streams)}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid media {path}: {exc}") from exc


def _transcript(path, source, duration, content):
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise ValueError(f'Invalid transcript JSON: {path}') from exc
    if not isinstance(data, dict) or not isinstance(data.get('source'), str):
        raise ValueError(f"Transcript requires source identity: {path}")
    if (path.parent / data['source']).resolve() != source:
        raise ValueError(f"Transcript source identity does not match {source}")
    declared = _number(data.get('duration'), 'transcript duration')
    if declared <= 0 or abs(declared - duration) > 0.25:
        raise ValueError(f"Transcript duration does not match actual media: {path}")
    words = data.get('words')
    if not isinstance(words, list):
        raise ValueError(f"Transcript words must be a list: {path}")
    previous = 0.0
    result = []
    for word in words:
        if not isinstance(word, dict):
            raise ValueError('Each transcript word must be an object')
        start, end = _number(word.get('start'), 'word start'), _number(word.get('end'), 'word end')
        if not 0 <= start < end <= duration or start < previous:
            raise ValueError(f"Unordered/out-of-range word interval: {word}")
        if any(character in str(word.get('word', '')) for character in ('\r', '\n', '\x00')):
            raise ValueError('Transcript word contains unsafe subtitle control characters')
        result.append({'start': start, 'end': end, 'word': _text(word.get('word'), 'word')})
        previous = end
    return result


def inspect_source(source, transcript_path, model='base'):
    source = _file(Path.cwd(), str(source))
    target = Path(transcript_path).absolute()
    if target.exists() or target.resolve() == source:
        raise ValueError('Transcript destination must be a new file, never the source')
    media = _probe(source)
    if not (media['video'] or media['audio']) or media['duration'] <= 0:
        raise ValueError('Source must be finite-duration local video or audio')
    try:
        silent = not media['audio']
        if media['audio']:
            detection = subprocess.run(['ffmpeg', '-v', 'info', '-nostdin', '-i', str(source), '-vn', '-af',
                                        'silencedetect=n=-50dB:d=0.1', '-f', 'null', '-'], capture_output=True, text=True)
            if detection.returncode:
                raise RuntimeError(f'Cannot inspect source audio: {detection.stderr[-1000:]}')
            starts = re.findall(r'silence_start:\s*([0-9.]+)', detection.stderr)
            ends = re.findall(r'silence_end:\s*([0-9.]+)', detection.stderr)
            silent = bool(len(starts) == 1 and float(starts[0]) <= 0.01 and
                          (not ends or float(ends[-1]) >= media['duration'] - 0.1))
        if not silent:
            from faster_whisper.utils import download_model
            local_model = str(Path(model).resolve()) if Path(model).is_dir() else download_model(model, local_files_only=True)
            words = transcribe_words(source, local_model)
        else:
            words = []
    except Exception as exc:
        raise RuntimeError(f"Local transcription failed; install/cache the Whisper model before offline inspection: {exc}") from exc
    data = {'source': str(source), 'duration': media['duration'],
            'words': [{'start': a, 'end': b, 'word': text} for a, b, text in words],
            'speech_status': 'NO_SPEECH_SILENT_MEDIA' if silent else 'TRANSCRIBED'}
    target.parent.mkdir(parents=True, exist_ok=True)
    _save(target, data)
    return {**media, 'source': str(source), 'transcript': str(target), 'speech_status': data['speech_status']}


def _load(plan_path):
    path = Path(plan_path).resolve()
    try:
        plan_bytes = path.read_bytes()
    except OSError as exc:
        raise ValueError(f'Cannot read plan: {exc}') from exc
    try:
        plan = json.loads(plan_bytes)
    except ValueError as exc:
        raise ValueError(f'Invalid plan JSON: {exc}') from exc
    if not isinstance(plan, dict) or type(plan.get('version')) is not int or plan['version'] != 1:
        raise ValueError('Plan version must be 1')
    for key in ('objective', 'audience'):
        _text(plan.get(key), key)
    if plan.get('format') not in {'education', 'objection', 'demo', 'sourced_case_study', 'offer'}:
        raise ValueError('Unknown marketing format')
    if type(plan.get('strict_3c')) is not bool or any(not isinstance(plan.get(k), str) for k in ('hook', 'cta')):
        raise ValueError('strict_3c must be boolean; hook and cta must be strings')
    persona = plan.get('persona')
    if not isinstance(persona, dict) or persona.get('style') not in STYLES:
        raise ValueError('Persona requires a supported caption style')
    for key in ('color', 'highlight'):
        if not isinstance(persona.get(key), str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', persona[key]):
            raise ValueError(f'Persona {key} must be #RRGGBB')
    font = _file(path.parent, persona.get('font'))
    initial = {font: _sha(font)}
    try:
        family = ImageFont.truetype(str(font), 12).getname()[0]
        if any(character in family for character in (',', '\r', '\n', '\x00')):
            raise ValueError('Persona font family contains unsafe ASS delimiters')
    except OSError as exc:
        raise ValueError(f'Invalid persona font: {font}') from exc
    assets = {font}
    sources = plan.get('sources')
    if not isinstance(sources, dict) or not sources:
        raise ValueError('Plan requires sources')
    media = {}
    for key, item in sources.items():
        _text(key, 'source ID')
        if not isinstance(item, dict):
            raise ValueError('Source must be an object')
        _text(item.get('source_note'), 'source provenance')
        source = _file(path.parent, item.get('path'))
        initial[source] = _sha(source)
        assets.add(source)
        info = _probe(source)
        info.update(path=source, words=None)
        if item.get('transcript'):
            transcript = _file(path.parent, item['transcript'])
            transcript_bytes = transcript.read_bytes()
            initial[transcript] = hashlib.sha256(transcript_bytes).hexdigest()
            assets.add(transcript)
            info['words'] = _transcript(transcript, source, info['duration'], transcript_bytes)
        media[key] = info
    segments = plan.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('Plan requires ordered segments')
    duration, words, edits = 0.0, [], []
    for segment in segments:
        if not isinstance(segment, dict) or segment.get('source_id') not in media:
            raise ValueError('Segment references unknown source')
        info = media[segment['source_id']]
        start, end = _number(segment.get('start'), 'segment start'), _number(segment.get('end'), 'segment end')
        if not info['video'] or not 0 <= start < end <= info['duration']:
            raise ValueError('Segment must fit actual source video duration')
        if any(abs(boundary * 30 - round(boundary * 30)) > 1e-7 for boundary in (start, end)):
            raise ValueError('Segment boundaries must lie on 30fps frame boundaries; propose adjusted plan before approval')
        if segment.get('beat') not in {'context', 'diagnosis', 'mechanism', 'takeaway'}:
            raise ValueError('Unknown semantic segment beat')
        if info['words'] is None:
            raise ValueError('Every segment source requires a transcript, empty for no speech')
        if not info['audio'] and info['words']:
            raise ValueError('Silent video cannot have invented speech captions')
        for word in info['words']:
            for boundary in (start, end):
                if word['start'] < boundary < word['end']:
                    raise ValueError(f"Cut {boundary} splits word {word['word']!r} ({word['start']}-{word['end']}); adjust plan")
            if start <= word['start'] and word['end'] <= end:
                words.append({**word, 'start': duration + word['start'] - start, 'end': duration + word['end'] - start})
        edits.append((duration, duration + end - start))
        duration += end - start
    voice = None
    if 'voiceover' in plan:
        voice = plan['voiceover']
        if not isinstance(voice, dict):
            raise ValueError('voiceover must be an object')
        _text(voice.get('source_note'), 'voiceover provenance')
        recording = _file(path.parent, voice.get('path'))
        transcript = _file(path.parent, voice.get('transcript'))
        transcript_bytes = transcript.read_bytes()
        initial[recording] = _sha(recording)
        initial[transcript] = hashlib.sha256(transcript_bytes).hexdigest()
        info = _probe(recording)
        if not info['audio'] or info['duration'] < duration:
            raise ValueError('Voiceover audio must cover the output timeline')
        assets.update((recording, transcript))
        all_words = _transcript(transcript, recording, info['duration'], transcript_bytes)
        if any(w['start'] < duration < w['end'] for w in all_words):
            raise ValueError('Output end splits a voiceover word; adjust timeline')
        words = [w for w in all_words if w['end'] <= duration]
        voice = recording
    overlays = plan.get('overlays')
    if not isinstance(overlays, list):
        raise ValueError('overlays must be a list')
    role = {'a_roll': duration, 'proof': 0.0, 'mood': 0.0}
    previous = 0.0
    for overlay in sorted(overlays, key=lambda o: _number(o.get('start'), 'overlay start') if isinstance(o, dict) else -1):
        if not isinstance(overlay, dict) or overlay.get('source_id') not in media:
            raise ValueError('Overlay references unknown source')
        start, end = _number(overlay.get('start'), 'overlay start'), _number(overlay.get('end'), 'overlay end')
        offset = _number(overlay.get('source_start'), 'overlay source_start')
        info = media[overlay['source_id']]
        if not 0 <= start < end <= duration or start < previous or offset < 0:
            raise ValueError('Overlay intervals must fit output and not overlap')
        if any(abs(boundary * 30 - round(boundary * 30)) > 1e-7 for boundary in (start, end, offset)):
            raise ValueError('Overlay boundaries/source_start must lie on 30fps frame boundaries; revise plan before approval')
        if overlay.get('role') not in {'proof', 'mood'}:
            raise ValueError('Overlay role must be proof or mood')
        # Still image demuxers expose a video stream but no positive duration.
        if not info['video'] or (info['duration'] > 0 and offset + end - start > info['duration']) or (info['duration'] <= 0 and offset != 0):
            raise ValueError('Overlay source interval exceeds actual video/image')
        if overlay['role'] == 'proof':
            _text(overlay.get('source_note'), 'proof overlay provenance')
            _text(sources[overlay['source_id']].get('source_note'), 'proof source provenance')
        role[overlay['role']] += end - start
        role['a_roll'] -= end - start
        previous = end
    try:
        canonical = json.dumps(plan, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'Plan must be finite JSON: {exc}') from exc
    bound = [(str(asset), _sha(asset)) for asset in sorted(assets)]
    if path.read_bytes() != plan_bytes or any(initial[Path(asset)] != checksum for asset, checksum in bound):
        raise ValueError('Input bytes changed during validation; retry against stable local files')
    digest = hashlib.sha256((canonical + '\n' + json.dumps(bound, ensure_ascii=False)).encode('utf-8')).hexdigest()
    from ags_vi_script import score_hook
    hook_words = [word for word in words if word['start'] < min(3.0, duration)]
    hook_audit = score_hook(' '.join(word['word'] for word in hook_words), plan['hook'])
    hook_audit['spoken_interval'] = [0.0, min(3.0, duration)]
    override = plan.get('hook_override_reason')
    if override is not None:
        _text(override, 'hook_override_reason')
    hook_audit['override_reason'] = override
    hook_audit['disposition'] = 'PASS' if hook_audit['ok'] else ('HUMAN_OVERRIDE' if override else 'ADVISORY_WARNING')
    if plan['strict_3c'] and not hook_audit['ok']:
        raise ValueError(f'Strict hook audit blocked plan: {hook_audit["errors"]}')
    result = {'plan_hash': digest, 'duration': duration, 'words': words, 'role_durations': role,
              'hook_audit': hook_audit, 'asset_hashes': dict(bound)}
    return path, plan, media, font, voice, assets, edits, result


def validate_plan(plan_path):
    return _load(plan_path)[-1]


def _sidecar(path, stage):
    return path.with_name(f'{path.stem}.{stage}.approval.json')


def _draft_record(path):
    return path.with_name(f'{path.stem}.draft.render.json')


def _approval(path, stage, digest):
    approval = _json(_sidecar(path, stage))
    if approval.get('plan_hash') != digest or approval.get('stage') != stage or not str(approval.get('reason', '')).strip():
        raise ValueError(f'Stale/missing {stage} approval; approve current bytes explicitly')
    if stage == 'draft':
        video = Path(approval.get('video', ''))
        if not video.is_file() or _sha(video) != approval.get('video_sha256'):
            raise ValueError('Draft artifact changed; review and approve the current successful draft')
    return approval


def approve_plan(plan_path, stage, reason):
    if stage not in {'plan', 'draft'}:
        raise ValueError('Approval stage must be plan or draft')
    _text(reason, 'Explicit caller-confirmed approval reason')
    path = Path(plan_path).resolve()
    loaded = _load(path)
    result = loaded[-1]
    destination = _sidecar(path, stage)
    if destination.is_symlink() or destination.resolve() in loaded[5] | {path}:
        raise ValueError('Approval destination collides with a source or symlink')
    approval = {'stage': stage, 'plan_hash': result['plan_hash'], 'reason': reason,
                'consent': 'caller-confirmed local record; not authenticated reviewer identity'}
    if stage == 'draft':
        _approval(path, 'plan', result['plan_hash'])
        record = _json(_draft_record(path))
        report_bytes = Path(record.get('report', '')).read_bytes()
        report = json.loads(report_bytes)
        video = Path(record.get('video', ''))
        if report.get('status') != 'ok' or report.get('stage') != 'draft' or report.get('plan_hash') != result['plan_hash']:
            raise ValueError('A current successful draft report is required')
        if not video.is_file() or _sha(video) != report.get('video_sha256'):
            raise ValueError('Successful draft bytes changed; render and review again')
        manifest = record.get('artifact_hashes')
        if not isinstance(manifest, dict) or not manifest:
            raise ValueError('Successful draft receipt has no artifact manifest')
        if hashlib.sha256(report_bytes).hexdigest() != manifest.get('report.json'):
            raise ValueError('Successful draft report changed during approval')
        for name, checksum in manifest.items():
            artifact = video.parent / name
            if artifact.is_symlink() or not artifact.is_file() or _sha(artifact) != checksum:
                raise ValueError(f'Draft delivery artifact changed: {name}')
        approval.update(video=str(video.resolve()), video_sha256=_sha(video), report=record['report'])
        approval['artifact_hashes'] = manifest
    _save(destination, approval)
    return approval


def _safe_output(output_dir, assets, stage):
    raw = Path(output_dir).absolute()
    # Compare caller-controlled components below the existing source parent; do not reject OS /tmp aliases.
    for component in [raw, *raw.parents]:
        if component.is_symlink() and component not in {Path('/tmp'), Path('/var')}:
            raise ValueError(f'Symlink output alias is unsafe: {component}')
    output = raw.resolve()
    if any(asset == output or output in asset.parents for asset in assets):
        raise ValueError('Output directory contains/collides with a source, transcript or font')
    target = output / stage
    if target.exists() or target.is_symlink():
        raise ValueError(f'Stage destination already exists: {target}; select a new output directory')
    return output, target


def _encode_piece(info, start, seconds, audio_info, audio_start, destination, work):
    still = info['duration'] <= 0
    args = ['ffmpeg', '-v', 'error', '-nostdin']
    args += ['-loop', '1'] if still else ['-ss', start]
    args += ['-i', info['path']]
    if audio_info and audio_info['audio']:
        args += ['-ss', audio_start, '-i', audio_info['path']]
    else:
        args += ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
    if still:
        vf = 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1'
    else:
        vf = reframe_filter(info['path'], start, seconds, work)
        from ags_common import filter_path
        vf = vf.replace(filter_path(work / 'reframe_cmds.txt'), 'reframe_cmds.txt')
    args += ['-t', seconds, '-map', '0:v:0', '-map', '1:a:0', '-vf', vf,
             '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
             '-bf', '0',
             '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', destination]
    _run(args, cwd=work)


def _write_delivery(directory, plan_path, plan, assets, groups, intervals):
    def stamp(seconds):
        milliseconds = round(seconds * 1000)
        return f'{milliseconds // 3600000:02d}:{milliseconds // 60000 % 60:02d}:{milliseconds // 1000 % 60:02d},{milliseconds % 1000:03d}'
    text = ''.join(f"{index}\n{stamp(group[0][0])} --> {stamp(group[-1][1])}\n{' '.join(w[2] for w in group)}\n\n"
                   for index, group in enumerate(groups, 1))
    (directory / 'subtitles.srt').write_text(text, encoding='utf-8')
    _save(directory / 'plan.json', plan)
    _save(directory / 'provenance.json', {'original_plan': str(plan_path), 'sources': plan['sources'],
          'overlays': plan['overlays'], 'voiceover': plan.get('voiceover'), 'encoded_intervals': intervals,
          'assets': [{'path': str(asset), 'sha256': _sha(asset)} for asset in sorted(assets)]})


def _publish_exclusive(source, target):
    """Atomic directory publication without replacing an existing destination."""
    import ctypes
    if os.name == 'nt':
        os.rename(source, target)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        result = libc.renamex_np(os.fsencode(source), os.fsencode(target), 4)  # RENAME_EXCL
    elif sys.platform.startswith('linux') and hasattr(libc, 'renameat2'):
        result = libc.renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1)  # RENAME_NOREPLACE
    else:
        raise RuntimeError('Atomic no-replace directory publication is unavailable on this OS')
    if result:
        error = ctypes.get_errno()
        raise ValueError(f'Stage publication refused: {os.strerror(error)}')


def _export_reviewed(path, output_dir, target, assets, digest):
    import shutil
    approved = _approval(path, 'draft', digest)
    draft = Path(approved['video']).parent
    report_bytes = (draft / 'report.json').read_bytes()
    if hashlib.sha256(report_bytes).hexdigest() != approved['artifact_hashes'].get('report.json'):
        raise ValueError('Reviewed draft report changed')
    report = json.loads(report_bytes)
    if report.get('plan_hash') != digest or report.get('video_sha256') != approved['video_sha256']:
        raise ValueError('Reviewed draft report no longer matches approved bytes')
    with tempfile.TemporaryDirectory(prefix='.ags-final-', dir=target.parent) as temporary:
        publish = Path(temporary) / 'stage'
        publish.mkdir()
        for name in ('video.mp4', 'subtitles.ass', 'subtitles.srt', 'contact-sheet.jpg', 'provenance.json', 'plan.json'):
            source = draft / name
            if not source.is_file() or source.is_symlink():
                raise ValueError(f'Reviewed draft is missing a regular delivery artifact: {name}')
            shutil.copyfile(source, publish / ('final.mp4' if name == 'video.mp4' else name))
        for name in approved['artifact_hashes']:
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe artifact path in draft approval')
            if relative.parts and relative.parts[0] == 'fonts':
                source = draft / relative
                if len(relative.parts) != 2 or (draft / 'fonts').is_symlink() or source.is_symlink() or not source.is_file():
                    raise ValueError(f'Unsafe approved font artifact: {name}')
                (publish / 'fonts').mkdir(exist_ok=True)
                shutil.copyfile(source, publish / relative)
        for name, checksum in approved['artifact_hashes'].items():
            copied = publish / ('final.mp4' if name == 'video.mp4' else name)
            if name == 'report.json':
                continue
            if not copied.is_file() or _sha(copied) != checksum:
                raise ValueError(f'Reviewed delivery artifact changed: {name}')
        if _sha(publish / 'final.mp4') != approved['video_sha256']:
            raise ValueError('Draft changed while exporting; final not published')
        _save(publish / 'report.json', {**report, 'stage': 'final', 'export': 'EXACT_REVIEWED_DRAFT_BYTES'})
        if validate_plan(path)['plan_hash'] != digest:
            raise ValueError('Plan/source changed during export')
        _approval(path, 'plan', digest)
        _approval(path, 'draft', digest)
        _safe_output(output_dir, assets | {path}, 'final')
        _publish_exclusive(publish, target)
    return {'status': 'ok', 'stage': 'final', 'video': str(target / 'final.mp4'),
            'subtitles': str(target / 'subtitles.ass'), 'srt': str(target / 'subtitles.srt'),
            'contact_sheet': str(target / 'contact-sheet.jpg'), 'report': str(target / 'report.json'),
            'provenance': str(target / 'provenance.json'), 'plan_snapshot': str(target / 'plan.json')}


def render_plan(plan_path, output_dir, stage='draft'):
    if stage not in {'draft', 'final'}:
        raise ValueError('Render stage must be draft or final')
    path, plan, media, font, voice, assets, edits, validated = _load(plan_path)
    if stage == 'draft' and (_draft_record(path).is_symlink() or _draft_record(path).resolve() in assets | {path}):
        raise ValueError('Draft record destination collides with a source or symlink')
    digest = validated['plan_hash']
    _approval(path, 'plan', digest)
    if stage == 'final':
        _approval(path, 'draft', digest)
    output, target = _safe_output(output_dir, assets | {path}, stage)
    output.mkdir(parents=True, exist_ok=True)
    if stage == 'final':
        return _export_reviewed(path, output_dir, target, assets, digest)
    with tempfile.TemporaryDirectory(prefix='.ags-editor-', dir=output) as temporary:
        work = Path(temporary)
        import shutil
        frozen = work / 'inputs'
        frozen.mkdir()
        copies = {}
        for index, asset in enumerate(sorted(assets)):
            snapshot = frozen / f'{index:04d}{asset.suffix}'
            shutil.copyfile(asset, snapshot)
            if _sha(snapshot) != validated['asset_hashes'][str(asset)]:
                raise ValueError('Input bytes changed before snapshot; nothing rendered')
            copies[asset] = snapshot
        media = {key: {**info, 'path': copies[info['path']]} for key, info in media.items()}
        font = copies[font]
        voice = copies[voice] if voice else None
        publish = work / 'stage'
        publish.mkdir()
        pieces = []
        role_frames = {'a_roll': 0, 'proof': 0, 'mood': 0}
        encoded_intervals = []
        for index, (segment, (out_start, out_end)) in enumerate(zip(plan['segments'], edits)):
            boundaries = sorted({out_start, out_end} | {max(out_start, min(out_end, o[k])) for o in plan['overlays'] for k in ('start', 'end')})
            for a, b in zip(boundaries, boundaries[1:]):
                if b <= a:
                    continue
                overlay = next((o for o in plan['overlays'] if o['start'] <= a < o['end']), None)
                base = media[segment['source_id']]
                visual = media[overlay['source_id']] if overlay else base
                start = overlay['source_start'] + a - overlay['start'] if overlay else segment['start'] + a - out_start
                piece = work / f'piece-{len(pieces):05d}.mkv'
                piece_work = work / f'filter-{len(pieces):05d}'
                piece_work.mkdir()
                first_frame, last_frame = round(a * 30), round(b * 30)
                if last_frame <= first_frame:
                    raise ValueError('Timeline interval is shorter than one output frame; adjust plan')
                frame_count = last_frame - first_frame
                _encode_piece(visual, start, frame_count / 30, base, segment['start'] + a - out_start, piece, piece_work)
                role = overlay['role'] if overlay else 'a_roll'
                role_frames[role] += frame_count
                encoded_intervals.append({'start_frame': first_frame, 'end_frame': last_frame,
                                          'role': role, 'source_id': overlay['source_id'] if overlay else segment['source_id'],
                                          'source_start': start})
                pieces.append(piece)
        # Generated basenames avoid concat-demuxer quoting of user-supplied paths.
        listing = work / 'concat.txt'
        listing.write_text(''.join(f"file '{piece.name}'\n" for piece in pieces), encoding='utf-8')
        joined = work / 'joined.mkv'
        _run(['ffmpeg', '-v', 'error', '-nostdin', '-f', 'concat', '-safe', '1', '-i', listing, '-c', 'copy', joined])
        cfg = STYLES[plan['persona']['style']]
        groups = []
        caption_intervals = [(0.0, validated['duration'])] if voice else edits
        for a, b in caption_intervals:
            tuples = [(w['start'], w['end'], w['word']) for w in validated['words'] if a <= w['start'] and w['end'] <= b]
            groups.extend(group_word_lists(tuples, cfg['max_chars'], cfg['max_seconds'], clean=False, semantic_chunk=True))
        ass = publish / 'subtitles.ass'
        fontdir = publish / 'fonts'
        fontdir.mkdir()
        import shutil
        copied_font = fontdir / font.name
        shutil.copyfile(font, copied_font)
        write_ass(groups, ass, 1080, 1920, style=plan['persona']['style'], highlight=plan['persona']['highlight'],
                  text_color=plan['persona']['color'], font_file=copied_font,
                  hook=(' '.join(plan['hook'].split()), min(3.0, validated['duration'] / 2 if plan['cta'] else validated['duration'])) if plan['hook'] else None)
        if plan['cta']:
            cta_ass = work / 'cta.ass'
            write_ass([], cta_ass, 1080, 1920, style=plan['persona']['style'],
                      highlight=plan['persona']['highlight'], text_color=plan['persona']['color'],
                      font_file=copied_font, hook=(' '.join(plan['cta'].split()), validated['duration']))
            from ags_editorial_sub import format_ass_time
            events = [line for line in cta_ass.read_text(encoding='utf-8').splitlines() if line.startswith('Dialogue:')]
            with ass.open('a', encoding='utf-8') as stream:
                for event in events:
                    fields = event.split(',', 3)
                    fields[1] = format_ass_time(max(validated['duration'] / 2 if plan['hook'] else 0, validated['duration'] - 3))
                    stream.write(','.join(fields) + '\n')
        _write_delivery(publish, path, plan, assets, groups, encoded_intervals)
        video = publish / 'video.mp4'
        args = ['ffmpeg', '-v', 'error', '-nostdin', '-i', joined]
        if voice:
            args += ['-i', voice]
        args += ['-map', '0:v:0', '-map', '1:a:0' if voice else '0:a:0', '-t', round(validated['duration'] * 30) / 30,
                 '-vf', "subtitles=stage/subtitles.ass:fontsdir=stage/fonts", '-af', LOUDNORM, '-c:v', 'libx264', '-preset', 'fast',
                 '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000', '-movflags', '+faststart', video]
        if not voice and not any(media[s['source_id']]['audio'] for s in plan['segments']):
            args[-1:-1] = ['-an']
        _run(args, cwd=work)
        harness = Path(__file__).resolve().parent.parent / 'harness'
        if str(harness) not in sys.path:
            sys.path.insert(0, str(harness))
        from ags_anti_slop_guard import AntiSlopGuard
        guard = AntiSlopGuard(video)
        sheet = publish / 'contact-sheet.jpg'
        with contextlib.redirect_stdout(io.StringIO()):
            guard_status = guard.run_full_guard(sheet)
        if guard_status == 1:
            raise RuntimeError('Quality guard blocked publication: ' + '; '.join(guard.issues + guard.warnings))
        actual_duration = video_info(video)['duration']
        if abs(actual_duration - validated['duration']) > 0.1:
            raise RuntimeError('Encoded duration deviates from approved timeline')
        encoded_frames = int(_run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                                  '-show_entries', 'stream=nb_read_frames', '-of', 'default=nw=1:nk=1', video]).strip())
        if encoded_frames != sum(role_frames.values()):
            raise RuntimeError('Encoded frame count does not match exclusive role timeline')
        role_seconds = {key: count / 30 for key, count in role_frames.items()}
        report = {**validated, 'status': 'ok', 'stage': stage, 'duration': actual_duration,
                  'role_durations': role_seconds, 'role_frames': role_frames, 'fps': 30,
                  'role_fractions': {k: v / encoded_frames for k, v in role_frames.items()},
                  'technical': 'PASS' if guard_status == 0 else 'WARNING', 'guard_warnings': guard.warnings,
                  'guard_measures': guard.measures, 'human_review': 'NOT_CHECKED', 'face_tracking': 'NOT_VERIFIED',
                  'hosts': {k: 'NOT_CHECKED' for k in ('claude_code', 'codex', 'gemini_cli', 'cursor', 'antigravity')},
                  'speech_status': 'CAPTIONED' if validated['words'] else 'NO_SPEECH_REPORTED_EMPTY_TRANSCRIPT',
                  'strict_3c': plan['strict_3c'], 'video_sha256': _sha(video)}
        _save(publish / 'report.json', report)
        if validate_plan(path)['plan_hash'] != digest:
            raise ValueError('Source/plan bytes changed during rendering; nothing published')
        _approval(path, 'plan', digest)
        if stage == 'final':
            _approval(path, 'draft', digest)
        _safe_output(output_dir, assets | {path}, stage)
        manifest = {str(item.relative_to(publish)): _sha(item) for item in publish.rglob('*') if item.is_file()}
        receipt = {'status': 'ok', 'stage': stage, 'video': str(target / 'video.mp4'),
                   'report': str(target / 'report.json'), 'artifact_hashes': manifest}
        previous_receipt = _draft_record(path).read_bytes() if _draft_record(path).exists() else None
        _save(_draft_record(path), receipt)
        try:
            _publish_exclusive(publish, target)
        except Exception:
            if previous_receipt is None:
                _draft_record(path).unlink(missing_ok=True)
            else:
                _save(_draft_record(path), json.loads(previous_receipt))
            raise
    result = {'status': 'ok', 'stage': stage, 'video': str(target / 'video.mp4'),
              'subtitles': str(target / 'subtitles.ass'), 'contact_sheet': str(target / 'contact-sheet.jpg'),
              'report': str(target / 'report.json'), 'srt': str(target / 'subtitles.srt'),
              'provenance': str(target / 'provenance.json'), 'plan_snapshot': str(target / 'plan.json')}
    return result


def render_batch(plan_paths, output_dir, stage='draft'):
    jobs = []
    for index, plan in enumerate(plan_paths):
        job = {'plan': str(plan)}
        try:
            job.update(status='ok', result=render_plan(plan, Path(output_dir) / f'{index:04d}', stage))
        except Exception as exc:
            job.update(status='error', error=f'{type(exc).__name__}: {exc}')
        jobs.append(job)
    return {'jobs': jobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect')
    inspect.add_argument('source')
    inspect.add_argument('transcript_path')
    inspect.add_argument('--model', default='base')
    validate = commands.add_parser('validate')
    validate.add_argument('plan_path')
    approve = commands.add_parser('approve')
    approve.add_argument('plan_path')
    approve.add_argument('--stage', choices=['plan', 'draft'], required=True)
    approve.add_argument('--reason', required=True)
    render = commands.add_parser('render')
    render.add_argument('plan_paths', nargs='+')
    render.add_argument('--output-dir', required=True)
    render.add_argument('--stage', choices=['draft', 'final'], default='draft')
    render.add_argument('--batch', action='store_true')
    args = parser.parse_args()
    try:
        with contextlib.redirect_stdout(sys.stderr):
            if args.command == 'inspect':
                result = inspect_source(args.source, args.transcript_path, args.model)
            elif args.command == 'validate':
                result = validate_plan(args.plan_path)
            elif args.command == 'approve':
                result = approve_plan(args.plan_path, args.stage, args.reason)
            elif args.batch:
                result = render_batch(args.plan_paths, args.output_dir, args.stage)
            elif len(args.plan_paths) == 1:
                result = render_plan(args.plan_paths[0], args.output_dir, args.stage)
            else:
                raise ValueError('Multiple plans require explicit render --batch')
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
