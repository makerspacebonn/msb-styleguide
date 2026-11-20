"""Tests für die Versionslogik in build.py. Start: python3 -m unittest discover -s src"""
import unittest
from datetime import datetime, timezone

import build


def eintrag(version, zeit='2026-11-20T18:00:00Z', was='Etwas', **extra):
    return {'version': version, 'zeit': zeit, 'was': was, **extra}


def utc(text):
    return datetime.strptime(text, '%Y-%m-%dT%H:%M').replace(tzinfo=timezone.utc)


class NaechsteNummer(unittest.TestCase):
    def test_zaehlt_im_selben_monat_weiter(self):
        versionen = [eintrag('2026-11.6'), eintrag('2026-11.5'), eintrag('2026-02-15', '2026-02-15')]
        self.assertEqual(build.naechste_nummer(versionen, utc('2026-11-20T12:00')), '2026-11.7')

    def test_neuer_monat_beginnt_bei_eins(self):
        self.assertEqual(build.naechste_nummer([eintrag('2026-11.6')], utc('2026-12-01T09:00')), '2026-12.1')

    def test_monat_nach_berliner_zeit(self):
        # 30.11. 23:30 UTC ist in Berlin schon der 1. Dezember
        self.assertEqual(build.naechste_nummer([eintrag('2026-11.6')], utc('2026-11-30T23:30')), '2026-12.1')

    def test_zweistellige_nummern_zaehlen_numerisch(self):
        versionen = [eintrag('2026-11.9'), eintrag('2026-11.10')]
        self.assertEqual(build.naechste_nummer(versionen, utc('2026-11-20T12:00')), '2026-11.11')


class MitVersion(unittest.TestCase):
    def test_neue_version_vorn_mit_zeit_und_abdruck(self):
        alt = [eintrag('2026-11.6', fingerabdruck='aaa')]
        neu = build.mit_version(alt, 'Neu', utc('2026-11-20T19:10'), 'bbb', im_commit={'2026-11.6'})
        self.assertEqual(neu[0], {'version': '2026-11.7', 'zeit': '2026-11-20T19:10:00Z', 'was': 'Neu', 'fingerabdruck': 'bbb'})
        self.assertEqual(neu[1:], alt)

    def test_offene_version_wird_aktualisiert_statt_neu(self):
        alt = [eintrag('2026-11.7', was='Erst', fingerabdruck='aaa'), eintrag('2026-11.6')]
        neu = build.mit_version(alt, 'Erst und mehr', utc('2026-11-20T20:00'), 'ccc', im_commit={'2026-11.6'})
        self.assertEqual([v['version'] for v in neu], ['2026-11.7', '2026-11.6'])
        self.assertEqual((neu[0]['was'], neu[0]['fingerabdruck'], neu[0]['zeit']), ('Erst und mehr', 'ccc', '2026-11-20T20:00:00Z'))

    def test_offene_version_behaelt_text_ohne_neue_beschreibung(self):
        alt = [eintrag('2026-11.7', was='Erst', fingerabdruck='aaa')]
        self.assertEqual(build.mit_version(alt, '', utc('2026-11-20T20:00'), 'ccc', im_commit=set())[0]['was'], 'Erst')

    def test_nachgetragene_version_ohne_abdruck_bleibt_unangetastet(self):
        alt = [eintrag('2026-11.6')]
        neu = build.mit_version(alt, 'Neu', utc('2026-11-20T20:00'), 'ddd', im_commit=set())
        self.assertEqual([v['version'] for v in neu], ['2026-11.7', '2026-11.6'])

    def test_neue_version_braucht_beschreibung(self):
        with self.assertRaises(SystemExit):
            build.mit_version([eintrag('2026-11.6')], '', utc('2026-11-20T20:00'), 'eee', im_commit={'2026-11.6'})


class Stand(unittest.TestCase):
    def test_winterzeit(self):
        self.assertEqual(build.stand(eintrag('x', '2026-11-20T18:55:20Z')), '20.11.2026, 19:55 Uhr')

    def test_sommerzeit(self):
        self.assertEqual(build.stand(eintrag('x', '2026-07-01T10:00:00Z')), '01.07.2026, 12:00 Uhr')

    def test_nur_datum(self):
        self.assertEqual(build.stand(eintrag('x', '2026-02-15')), '15.02.2026')


class Fingerabdruck(unittest.TestCase):
    def test_aendert_sich_mit_dem_template(self):
        import pathlib
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / 'src').mkdir()
            (root / 'logos').mkdir()
            (root / 'src' / 'template.html').write_text('a')
            (root / 'src' / 'build.py').write_text('b')
            vorher = build.fingerabdruck(root)
            (root / 'src' / 'versionen.json').write_text('[]')
            self.assertEqual(build.fingerabdruck(root), vorher, 'versionen.json zählt nicht mit')
            (root / 'src' / 'template.html').write_text('a2')
            self.assertNotEqual(build.fingerabdruck(root), vorher)


if __name__ == '__main__':
    unittest.main()
