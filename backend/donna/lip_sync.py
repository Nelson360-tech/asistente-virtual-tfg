import json

from openfacefx import generate_from_alignment
from openfacefx.export_cues import dominant_cues
from openfacefx.ipa import IPA_MAPPING
from openfacefx.timing import parse_piper_alignments, resolve_ends, to_segments


class LipSync:
    """Converts Piper phoneme timings into visemes with timestamps."""

    def __init__(self, fps=30):
        self.fps = fps

    def visemes(self, alignments, sample_rate):
        if not alignments:
            return []

        timings = json.dumps({
            "alignments": [
                {"phoneme": item.phoneme, "num_samples": int(item.num_samples)}
                for item in alignments
            ]
        })
        events = resolve_ends(parse_piper_alignments(timings, sample_rate))
        track = generate_from_alignment(
            to_segments(events), fps=self.fps, mapping=IPA_MAPPING
        )
        return [
            {"start": round(float(start), 3), "end": round(float(end), 3), "viseme": name}
            for start, end, name in dominant_cues(track, rest_name="sil")
        ]