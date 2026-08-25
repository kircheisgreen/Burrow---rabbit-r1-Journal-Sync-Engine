import unittest
from unittest.mock import MagicMock, mock_open, patch

from rabbit_sync import sync_engine
from rabbit_sync.transformers import transform_to_mindmap_text
from rabbit_sync.visualizer import generate_mindmap_svg


class MindMapVisualizerTests(unittest.TestCase):
    def test_uses_journal_content_for_mind_map_topics(self):
        central_topic = "Journal - 2026-08-23"
        content = """
        Speaker 1: AI governance is the main challenge.
        Speaker 2: Privacy and accessibility are critical design issues.
        Speaker 3: Training data quality affects trust and adoption.
        """

        svg = generate_mindmap_svg(central_topic, content)

        self.assertIn("AI governance", svg)
        self.assertIn("Privacy", svg)
        self.assertIn("accessibility", svg)
        self.assertIn("Journal - 2026-08-23", svg)

    def test_run_headless_sync_uses_journal_title_for_mindmap_render(self):
        journal = {
            "id": "journal-1",
            "createdAt": "2026-08-18T12:00:00Z",
            "summary": "BMS Diversity Award Keynote Media B",
            "content": "Speaker 1: AI governance matters.\nSpeaker 2: Privacy and accessibility are critical."
        }

        with patch.object(sync_engine, 'authenticate_google', return_value=MagicMock()), \
             patch.object(sync_engine, 'fetch_rabbit_journals', return_value=[journal]), \
             patch.object(sync_engine, 'get_or_create_folder', side_effect=['lecturer_folder', 'journal_folder']), \
             patch.object(sync_engine, 'upload_processed_file'), \
             patch.object(sync_engine, 'build', return_value=MagicMock()), \
             patch.object(sync_engine, 'get_existing_file_metadata', return_value=(None, None)), \
             patch.object(sync_engine, 'load_history', return_value={}), \
             patch.object(sync_engine, 'save_history'), \
             patch('builtins.open', new_callable=mock_open()), \
             patch.object(sync_engine, 'generate_mindmap_svg', return_value='<svg></svg>') as mock_svg:
            sync_engine.run_headless_sync(
                token='token',
                client_secret='credentials.json',
                active_workflows=['Mind Mapping'],
                log_callback=lambda *args, **kwargs: None,
            )

        central_topic = mock_svg.call_args[0][0]
        self.assertIn('BMS Diversity Award Keynote Media B', central_topic)
        self.assertNotIn('General Lecturer', central_topic)

    def test_generate_mindmap_svg_reads_mindmap_doc_structure(self):
        mindmap_text = """# BMS Diversity Award Keynote Media B — VISUALIZATION STRUCTURAL DIAGRAM OUTLINE

                ┌──────────────────────────────────────┐
                │    CENTRAL SUBJECT:                  │
                │    BMS Diversity Award Keynote Media B │
                └──────────────────────────────────────┘
                                   │
                                   ├─── [Node 1]: AI governance matters
                                   ├─── [Node 2]: Privacy and accessibility are critical
"""

        svg = generate_mindmap_svg('BMS Diversity Award Keynote Media B', mindmap_text)

        self.assertIn('BMS Diversity Award Keynote Media B', svg)
        self.assertIn('AI governance matters', svg)
        self.assertIn('Privacy and accessibility are critical', svg)

    def test_transform_to_mindmap_text_uses_mind_map_guidance(self):
        journal_text = "Speaker 1: AI governance matters.\nSpeaker 2: Privacy and accessibility are critical.\nSpeaker 3: Training data quality affects trust and adoption."

        mm = transform_to_mindmap_text('BMS Diversity Award Keynote Media B', journal_text)

        self.assertIn('CENTRAL IDEA', mm)
        self.assertIn('Mind mapping note-taking is a visual method', mm)
        self.assertIn('Why Use Mind Maps:', mm)
        self.assertIn('Shows how different ideas connect to each other.', mm)
        self.assertIn('Main Branch:', mm)


if __name__ == "__main__":
    unittest.main()
