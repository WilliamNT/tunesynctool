from tunesynctool.features.v2 import track_score
from tunesynctool.models import Track


def track(title=None, **kw):
    return Track(title=title, **kw)


def test_none_candidate_scores_zero():
    assert track_score(track('Save Your Tears', primary_artist='The Weeknd'), None) == 0.0


def test_isrc_match_short_circuits_to_one():
    a = track('Different Title', primary_artist='A', isrc='X')
    b = track('Other Title', primary_artist='B', isrc='X')
    assert track_score(a, b) == 1.0


def test_musicbrainz_match_short_circuits_to_one():
    a = track('Different Title', primary_artist='A', musicbrainz_id='m')
    b = track('Other Title', primary_artist='B', musicbrainz_id='m')
    assert track_score(a, b) == 1.0


def test_identical_tracks_score_one():
    a = track('Save Your Tears', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 1.0


def test_remix_against_original_is_demoted_not_rejected():
    a = track('Save Your Tears (Remix)', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.96
    assert track_score(b, a) == 0.96


def test_two_different_versions_demote_below_plain_vs_versioned():
    a = track('Save Your Tears (Remix)', primary_artist='The Weeknd')
    plain = track('Save Your Tears', primary_artist='The Weeknd')
    live = track('Save Your Tears (Live)', primary_artist='The Weeknd')
    assert track_score(a, live) < track_score(a, plain)


def test_same_version_text_is_not_penalized():
    a = track('Save Your Tears (Remix)', primary_artist='The Weeknd')
    b = track('Save Your Tears (Remix)', primary_artist='The Weeknd')
    assert track_score(a, b) == 1.0


def test_named_remixer_difference_is_demoted():
    a = track('Roses - Imanbek Remix', primary_artist='SAINt JHN')
    b = track('Roses - Skore Remix', primary_artist='SAINt JHN')
    score = track_score(a, b)
    assert score < 1.0
    assert score > 0.85


def test_original_version_against_plain_is_mildly_demoted():
    a = track('YMCA - Original Version 1978', primary_artist='Village People')
    b = track('YMCA', primary_artist='Village People')
    assert track_score(a, b) == 0.96


def test_live_and_remix_demote_equally():
    live = track('Save Your Tears (Live)', primary_artist='The Weeknd')
    remix = track('Save Your Tears (Remix)', primary_artist='The Weeknd')
    plain = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(live, plain) == track_score(remix, plain)


def test_acoustic_version_against_plain_stays_high():
    a = track('Save Your Tears (Acoustic Version)', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) > 0.9


def test_cosmetic_mismatch_is_not_penalized():
    a = track('Blues Deluxe (Remastered)', primary_artist='Joe Bonamassa')
    b = track('Blues Deluxe', primary_artist='Joe Bonamassa')
    assert track_score(a, b) == 1.0


def test_tier_mismatch_is_not_penalized():
    a = track('Save Your Tears - Bonus Track', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 1.0


def test_featured_version_against_solo_is_mildly_demoted():
    a = track('Save Your Tears (with Ariana Grande) - Bonus Track', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.95


def test_artist_mismatch_lowers_score():
    a = track('Save Your Tears', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='Drake')
    assert track_score(a, b) < 0.85


def test_artist_typo_still_scores_high():
    a = track('Save Your Tears', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weekend')
    assert track_score(a, b) > 0.9


def test_transposition_typo_is_tolerated():
    a = track('Recrod Your Tears', primary_artist='The Weeknd')
    b = track('Record Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) > 0.95


def test_duration_closeness_lifts_score():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    close = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=240)
    far = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=400)
    assert track_score(source, close) > track_score(source, far)


def test_duration_within_tolerance_is_full():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    within = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205)
    assert track_score(source, within) == 1.0


def test_duration_way_off_is_capped_by_gate():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    far = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=400)
    assert track_score(source, far) == 0.5


def test_missing_album_is_neutral():
    with_album = track('Save Your Tears', primary_artist='The Weeknd', album_name='After Hours')
    without = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(with_album, without) == 1.0


def test_album_case_difference_is_ignored():
    a = track('Save Your Tears', primary_artist='The Weeknd', album_name='After Hours')
    b = track('Save Your Tears', primary_artist='The Weeknd', album_name='after hours')
    assert track_score(a, b) == 1.0


def test_short_title_does_not_match_long_title_fully():
    a = track('Save', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) < 0.7


def test_title_floor_gate_caps_wrong_title():
    a = track('xyz', primary_artist='The Weeknd', duration_seconds=200, release_year=2021)
    b = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200, release_year=2021)
    assert track_score(a, b) == 0.5


def test_reordered_words_still_match():
    a = track('Save Your Tears', primary_artist='The Weeknd')
    b = track('Tears Your Save', primary_artist='The Weeknd')
    assert track_score(a, b) == 1.0


def test_contribution_agreement_when_artist_is_listed():
    a = track('Save Your Tears (feat. Ariana Grande)', primary_artist='The Weeknd', additional_artists=['Ariana Grande'])
    b = track('Save Your Tears (feat. Ariana Grande)', primary_artist='The Weeknd', additional_artists=['Ariana Grande'])
    assert track_score(a, b) == 1.0


def test_contribution_disagreement_different_feature_is_demoted():
    a = track('Save Your Tears (feat. Ariana Grande)', primary_artist='The Weeknd', additional_artists=['Ariana Grande'])
    b = track('Save Your Tears (feat. Drake)', primary_artist='The Weeknd', additional_artists=['Drake'])
    assert track_score(a, b) == 0.9


def test_contribution_solo_version_is_a_fallback():
    a = track('Save Your Tears (feat. Ariana Grande)', primary_artist='The Weeknd', additional_artists=['Ariana Grande'])
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.95


def test_remixer_in_artist_list_agrees():
    a = track('Roses - Imanbek Remix', primary_artist='SAINt JHN', additional_artists=['Imanbek'])
    b = track('Roses - Imanbek Remix', primary_artist='SAINt JHN', additional_artists=['Imanbek'])
    assert track_score(a, b) == 1.0


def test_isrc_present_on_one_side_does_not_short_circuit():
    a = track('Save Your Tears', primary_artist='The Weeknd', isrc='X')
    b = track('Blinding Lights', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.5


def test_musicbrainz_present_on_one_side_does_not_short_circuit():
    a = track('Save Your Tears', primary_artist='The Weeknd', musicbrainz_id='m')
    b = track('Blinding Lights', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.5


def test_isrc_mismatch_does_not_short_circuit():
    a = track('A', primary_artist='The Weeknd', isrc='X')
    b = track('B', primary_artist='The Weeknd', isrc='Y')
    assert track_score(a, b) == 0.5


def test_isrc_match_overrides_version_mismatch():
    a = track('Save Your Tears (Remix)', primary_artist='The Weeknd', isrc='X')
    b = track('Save Your Tears', primary_artist='The Weeknd', isrc='X')
    assert track_score(a, b) == 1.0


def test_both_empty_titles_are_neutral():
    a = track('', primary_artist='The Weeknd')
    b = track('', primary_artist='The Weeknd')
    assert track_score(a, b) == 1.0


def test_one_empty_title_is_capped_by_floor():
    a = track('', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.5


def test_subtitle_is_excluded_from_core():
    a = track('Save Your Tears (Energy 52)', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 1.0


def test_both_artists_absent_is_neutral():
    a = track('Save Your Tears')
    b = track('Save Your Tears')
    assert track_score(a, b) == 1.0


def test_one_artist_absent_is_demoted():
    a = track('Save Your Tears', primary_artist='The Weeknd')
    b = track('Save Your Tears')
    assert track_score(a, b) == 0.71


def test_source_artist_absent_is_neutral():
    source = track('Save Your Tears')
    candidate = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(source, candidate) == 1.0


def test_missing_artist_is_asymmetric():
    source = track('Save Your Tears')
    candidate = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(source, candidate) > track_score(candidate, source)


def test_remix_candidate_with_missing_source_artist_clears_floor():
    source = track('Save Your Tears')
    candidate = track('Save Your Tears (Remix)', primary_artist='The Weeknd')
    assert track_score(source, candidate) >= 0.75


def test_two_contributors_split_and_agree():
    a = track('Save Your Tears (feat. Ariana Grande & Flo Rida)', primary_artist='The Weeknd', additional_artists=['Ariana Grande', 'Flo Rida'])
    b = track('Save Your Tears (feat. Ariana Grande & Flo Rida)', primary_artist='The Weeknd', additional_artists=['Ariana Grande', 'Flo Rida'])
    assert track_score(a, b) == 1.0


def test_two_contributors_solo_fallback():
    a = track('Save Your Tears (feat. Ariana Grande & Flo Rida)', primary_artist='The Weeknd', additional_artists=['Ariana Grande', 'Flo Rida'])
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.95


def test_vs_split_contributor_agreement():
    a = track('Song (Benny Benassi vs MazZz)', primary_artist='X', additional_artists=['Benny Benassi', 'MazZz'])
    b = track('Song (Benny Benassi vs MazZz)', primary_artist='X', additional_artists=['Benny Benassi', 'MazZz'])
    assert track_score(a, b) == 1.0


def test_w_slash_opener_contribution():
    a = track('Save Your Tears (w/ Ariana Grande)', primary_artist='The Weeknd', additional_artists=['Ariana Grande'])
    b = track('Save Your Tears (w/ Ariana Grande)', primary_artist='The Weeknd', additional_artists=['Ariana Grande'])
    assert track_score(a, b) == 1.0


def test_remixer_keyword_contribution_agrees():
    a = track('Song (Benny Benassi Remix)', primary_artist='X', additional_artists=['Benny Benassi'])
    b = track('Song (Benny Benassi Remix)', primary_artist='X', additional_artists=['Benny Benassi'])
    assert track_score(a, b) == 1.0


def test_version_with_descriptor_is_mildly_demoted():
    a = track('Save Your Tears (Hot Remix)', primary_artist='The Weeknd')
    b = track('Save Your Tears (Cold Remix)', primary_artist='The Weeknd')
    assert track_score(a, b) == 0.94


def test_duration_at_tolerance_is_full():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    within = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=210)
    assert track_score(source, within) == 1.0


def test_duration_decays_monotonically():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    near = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205)
    mid = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=220)
    far = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=260)
    assert track_score(source, near) >= track_score(source, mid) >= track_score(source, far)


def test_duration_at_gate_boundary_is_not_gated():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    at_gate = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=260)
    assert track_score(source, at_gate) == 0.93


def test_duration_just_past_gate_is_capped():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    past_gate = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=261)
    assert track_score(source, past_gate) == 0.5


def test_duration_missing_one_side_is_neutral():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    without = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(source, without) == 1.0


def test_track_number_match_is_full():
    a = track('Save Your Tears', primary_artist='The Weeknd', track_number=3)
    b = track('Save Your Tears', primary_artist='The Weeknd', track_number=3)
    assert track_score(a, b) == 1.0


def test_track_number_mismatch_is_mildly_demoted():
    a = track('Save Your Tears', primary_artist='The Weeknd', track_number=3)
    b = track('Save Your Tears', primary_artist='The Weeknd', track_number=5)
    assert track_score(a, b) == 0.95


def test_year_within_band_is_full():
    a = track('Save Your Tears', primary_artist='The Weeknd', release_year=2020)
    b = track('Save Your Tears', primary_artist='The Weeknd', release_year=2021)
    assert track_score(a, b) == 1.0


def test_year_decay_is_mild():
    a = track('Save Your Tears', primary_artist='The Weeknd', release_year=2020)
    b = track('Save Your Tears', primary_artist='The Weeknd', release_year=2025)
    assert track_score(a, b) == 0.99


def test_year_far_apart_is_mildly_demoted():
    a = track('Save Your Tears', primary_artist='The Weeknd', release_year=1978)
    b = track('Save Your Tears', primary_artist='The Weeknd', release_year=2028)
    assert track_score(a, b) == 0.95


def test_album_mismatch_is_demoted():
    a = track('Save Your Tears', primary_artist='The Weeknd', album_name='After Hours')
    b = track('Save Your Tears', primary_artist='The Weeknd', album_name='Dawn FM')
    assert track_score(a, b) == 0.92


def test_album_typo_is_tolerated():
    a = track('Save Your Tears', primary_artist='The Weeknd', album_name='After Hours')
    b = track('Save Your Tears', primary_artist='The Weeknd', album_name='After Hour')
    assert track_score(a, b) == 0.99


def test_both_gates_cap_the_score():
    a = track('xyz', primary_artist='The Weeknd', duration_seconds=200)
    b = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=400)
    assert track_score(a, b) == 0.5


def test_all_fields_identical_scores_one():
    a = track('Save Your Tears', primary_artist='The Weeknd', album_name='After Hours', duration_seconds=200, track_number=5, release_year=2020, isrc='X', musicbrainz_id='m')
    b = track('Save Your Tears', primary_artist='The Weeknd', album_name='After Hours', duration_seconds=200, track_number=5, release_year=2020, isrc='X', musicbrainz_id='m')
    assert track_score(a, b) == 1.0


def test_scorer_is_symmetric_for_contributions():
    featured = track('Save Your Tears (feat. Ariana Grande)', primary_artist='The Weeknd', additional_artists=['Ariana Grande'])
    solo = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(featured, solo) == track_score(solo, featured)


def test_transposition_in_last_word_is_tolerated():
    a = track('Save Your Taers', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) > 0.95


def test_transposition_in_middle_word_is_tolerated():
    a = track('Save Yoru Tears', primary_artist='The Weeknd')
    b = track('Save Your Tears', primary_artist='The Weeknd')
    assert track_score(a, b) > 0.95