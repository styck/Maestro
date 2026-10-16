"""Music-video mode (auto / performer / cinematic) drives performer gating."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from services.director.music_cues import format_music_cues
from services.director.music_performance import (
    _NO_PERFORMERS_VOCAL_DIRECTION,
    music_performance_direction,
)
from services.director.planners.music_video import (
    MusicVideoPlanner,
    _detect_performers,
)


class MusicVideoModeDetectionTests(unittest.TestCase):
    def test_negation_wins_over_performer_keywords(self):
        # "no singer, no hero" must NOT be read as performer-centric.
        self.assertFalse(_detect_performers("no singer, no hero, just an empty throne room", {}))
        self.assertFalse(_detect_performers("nobody in frame, only scenery", {}))
        self.assertFalse(_detect_performers("a landscape without people", {}))
        self.assertFalse(_detect_performers("a bar with no crowd", {}))
        self.assertFalse(_detect_performers("empty street at night", {}))

    def test_performer_keywords_detected(self):
        self.assertTrue(_detect_performers("a punk band performs on a club stage", {}))
        self.assertTrue(_detect_performers("a singer in the spotlight", {}))
        self.assertTrue(_detect_performers("a solo dancer under neon lights", {}))
        self.assertTrue(_detect_performers("a classical performance in a hall", {}))
        self.assertTrue(_detect_performers("two women in a duet", {}))
        self.assertTrue(_detect_performers("a DJ booth", {}))

    def test_performer_map_detected(self):
        self.assertTrue(_detect_performers("", {"verse": "the man", "chorus": "the woman"}))

    def test_empty_description_defaults_to_performer(self):
        self.assertTrue(_detect_performers("", {}))


class MusicVideoModeCueTests(unittest.TestCase):
    _CLIP = {
        'start': 20, 'end': 28, 'section_label': 'chorus',
        'percussion_activity': 'active',
        'music_cues': [{'type': 'percussion_entry', 'time': 22.4, 'confidence': 'estimated'}],
    }

    def test_timing_only_cues_have_no_instruments(self):
        text = format_music_cues(self._CLIP, performers=False)
        self.assertIn('rhythmic emphasis enters', text)
        self.assertNotIn('drummer', text.casefold())
        self.assertNotIn('guitar', text.casefold())
        self.assertNotIn('bass', text.casefold())
        self.assertNotIn('ensemble', text.casefold())

    def test_performer_cues_keep_instruments(self):
        text = format_music_cues(self._CLIP, performers=True)
        self.assertIn('drummer', text.casefold())

    def test_no_performer_vocal_direction(self):
        direction = music_performance_direction([], 'active', performers=False)
        self.assertEqual(direction, _NO_PERFORMERS_VOCAL_DIRECTION)
        self.assertIn('No one sings or lip-syncs', direction)
        self.assertNotIn('musicians', direction.casefold())

    def test_no_performer_direction_honors_visible_subjects(self):
        # An explicit on-screen subject must not get the blanket no-singer text.
        direction = music_performance_direction(
            [{'visual_description': 'a woman in a red dress', 'performance_role': 'non_vocal'}],
            'active',
            performers=False,
        )
        self.assertNotEqual(direction, _NO_PERFORMERS_VOCAL_DIRECTION)
        self.assertIn('non-singing presence', direction)

    def test_performer_direction_default_keeps_behavior(self):
        # Default performers=True: empty subjects still yield an empty direction.
        self.assertEqual(music_performance_direction([], 'active'), '')


class MusicVideoModePlannerTests(unittest.TestCase):
    def _run(self, scene_description, music_video_mode):
        captures = []

        def generate(**kwargs):
            captures.append(kwargs)
            return json.dumps([{
                'subjects_on_screen': [],
                'video_prompt': 'A moonlit desert landscape with wind-blown sand.',
                'camera_plan': {'framing': 'wide shot'},
                'window_prompts': [],
            }])

        planner = MusicVideoPlanner(llm_generate=generate, llm_generate_streaming=generate)
        with patch(
            'services.director.planners.music_video.classify_vocal_intervals',
            return_value=[],
        ):
            plan = planner.plan(
                clips=[{'start': 0, 'end': 8, 'label': 'verse'}],
                scene_description=scene_description,
                video_model='ltx2_25_22B_distilled',
                shot_image_policy='direct_references',
                music_video_mode=music_video_mode,
            )
        return planner, plan, captures[-1]['system_prompt']

    def test_cinematic_mode_overrides_performer_keywords(self):
        # Keywords say "band" but explicit cinematic mode must win.
        planner, plan, system_prompt = self._run(
            'A punk band performs on a club stage', 'cinematic',
        )
        self.assertFalse(planner._performers)
        self.assertIn('NO LEAD PERFORMERS', system_prompt)
        self.assertNotIn('MUSIC PERFORMANCE ROLES', system_prompt)
        self.assertIn('No one sings or lip-syncs', plan.shots[0].video_prompt)

    def test_performer_mode_overrides_negation(self):
        # "no singer" would auto-detect no performers, but explicit performer wins.
        planner, _plan, system_prompt = self._run(
            'no singer, no hero, just scenery', 'performer',
        )
        self.assertTrue(planner._performers)
        self.assertIn('MUSIC PERFORMANCE ROLES', system_prompt)
        self.assertNotIn('NO LEAD PERFORMERS', system_prompt)

    def test_auto_mode_detects_negation(self):
        planner, _plan, system_prompt = self._run(
            'no singer, no hero, just scenery', 'auto',
        )
        self.assertFalse(planner._performers)
        self.assertNotIn('MUSIC PERFORMANCE ROLES', system_prompt)

    def test_fingerprint_changes_with_mode(self):
        # Identical inputs but different modes must produce different planning
        # fingerprints, so a cached plan is never replayed across a mode toggle.
        def generate(**kwargs):
            return json.dumps([{
                'subjects_on_screen': [],
                'video_prompt': 'A moonlit desert landscape.',
                'camera_plan': {'framing': 'wide shot'},
                'window_prompts': [],
            }])

        fingerprints = []
        for mode in ('cinematic', 'performer'):
            planner = MusicVideoPlanner(llm_generate=generate, llm_generate_streaming=generate)
            with patch(
                'services.director.planners.music_video.classify_vocal_intervals',
                return_value=[],
            ):
                planner.plan(
                    clips=[{'start': 0, 'end': 8, 'label': 'verse'}],
                    scene_description='A punk band performs on a club stage',
                    video_model='ltx2_25_22B_distilled',
                    shot_image_policy='direct_references',
                    music_video_mode=mode,
                )
            fingerprints.append(planner._planning_checkpoint_fingerprint)

        self.assertEqual(len(fingerprints), 2)
        self.assertNotEqual(fingerprints[0], fingerprints[1])


if __name__ == '__main__':
    unittest.main()
