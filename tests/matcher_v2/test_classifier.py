from tunesynctool.features.v2.matcher.core import normalize_str, tokenize, group_tokens, SemanticType

def groups_of(title):
    return group_tokens(tokenize(normalize_str(title)))

def types_of(title):
    return [g.semantic_type for g in groups_of(title)]

def group_with_text(title, text):
    for g in groups_of(title):
        if str(g) == text:
            return g
    raise AssertionError(f'no group with text {text!r} in {title!r}')

def test_plain_title_is_one_title_group():
    groups = groups_of('The Motto')
    assert types_of('The Motto') == [SemanticType.TITLE]
    assert str(groups[0]) == 'The Motto'

def test_title_followed_by_bracket():
    assert types_of('Save Your Tears (Remix)') == [
        SemanticType.TITLE,
        SemanticType.SEPARATOR,
        SemanticType.VERSION_MARKER,
        SemanticType.SEPARATOR,
    ]
    assert str(group_with_text('Save Your Tears (Remix)', 'Remix')) == 'Remix'

def test_two_brackets_produce_two_regions():
    groups = groups_of('Save Your Tears (Remix) (with Ariana Grande)')
    regions = [g for g in groups
               if g.semantic_type not in (SemanticType.TITLE, SemanticType.SEPARATOR)]
    assert len(regions) == 2
    assert str(regions[0]) == 'Remix'
    assert regions[0].semantic_type == SemanticType.VERSION_MARKER
    assert str(regions[1]) == 'with Ariana Grande'
    assert regions[1].semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_comma_inside_bracket_keeps_one_region():
    regions = [g for g in groups_of('One Of The Girls (with JENNIE, Lily Rose Depp)')
               if g.semantic_type not in (SemanticType.TITLE, SemanticType.SEPARATOR)]
    assert len(regions) == 1
    assert str(regions[0]) == 'with JENNIE, Lily Rose Depp'
    assert regions[0].semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_separator_inside_bracket_stays_with_region():
    regions = [g for g in groups_of('Sweet Dreams (Hot Remix / 2005 Remaster)')
               if g.semantic_type not in (SemanticType.TITLE, SemanticType.SEPARATOR)]
    assert len(regions) == 1
    assert str(regions[0]) == 'Hot Remix / 2005 Remaster'
    assert regions[0].semantic_type == SemanticType.VERSION_MARKER

def test_brackets_alone_fall_back_to_title():
    assert types_of('(Remix)') == [
        SemanticType.SEPARATOR,
        SemanticType.TITLE,
        SemanticType.SEPARATOR,
    ]
    assert group_with_text('(Remix)', 'Remix').semantic_type == SemanticType.TITLE

def test_square_and_curly_brackets_balance_like_parens():
    assert types_of('Track [2023 Remaster]') == [
        SemanticType.TITLE,
        SemanticType.SEPARATOR,
        SemanticType.COSMETIC_MARKER,
        SemanticType.SEPARATOR,
    ]
    assert types_of('Track {2023 Remaster}') == [
        SemanticType.TITLE,
        SemanticType.SEPARATOR,
        SemanticType.COSMETIC_MARKER,
        SemanticType.SEPARATOR,
    ]

def test_ampersand_at_depth_zero_is_separator():
    assert types_of('A & B') == [SemanticType.TITLE, SemanticType.SEPARATOR, SemanticType.TITLE]

def test_slash_at_depth_zero_is_separator():
    assert types_of('A / B') == [SemanticType.TITLE, SemanticType.SEPARATOR, SemanticType.TITLE]

def test_dash_at_depth_zero_is_separator():
    assert types_of('A - B') == [SemanticType.TITLE, SemanticType.SEPARATOR, SemanticType.TITLE]

def test_nested_brackets_stay_one_region():
    regions = [g for g in groups_of('X (a (b) c)') if g.semantic_type == SemanticType.SUBTITLE]
    assert len(regions) == 1
    assert str(regions[0]) == 'a (b) c'

def test_whitespace_only_fragment_between_brackets_is_dropped():
    assert all(g.semantic_type != SemanticType.TITLE or str(g).strip()
               for g in groups_of('X (a)  (b)'))

def test_en_dash_is_normalized_to_separator():
    assert types_of('A – B') == [SemanticType.TITLE, SemanticType.SEPARATOR, SemanticType.TITLE]

def test_empty_string_has_no_groups():
    assert groups_of('') == []

def test_unclosed_bracket_runs_to_end_then_falls_back_to_title():
    groups = groups_of('(Remix')
    assert [g.semantic_type for g in groups] == [SemanticType.SEPARATOR, SemanticType.TITLE]
    assert str(groups[1]) == 'Remix'

def test_subtitle_default_when_no_keyword():
    assert group_with_text('Mambo No. 5 (a Little Bit of...)',
                           'a Little Bit of...').semantic_type == SemanticType.SUBTITLE

def test_with_mid_phrase_stays_subtitle():
    assert group_with_text('The Way I Are (Dance with Somebody)',
                           'Dance with Somebody').semantic_type == SemanticType.SUBTITLE

def test_no_keyword_dash_tail_stays_title():
    g = group_with_text('Café Del Mar - Energy 52', 'Energy 52')
    assert g.semantic_type == SemanticType.TITLE

def test_love_hate_keeps_both_sides_as_title():
    assert types_of('Love - Hate') == [SemanticType.TITLE, SemanticType.SEPARATOR, SemanticType.TITLE]

def test_dash_keyword_tail_is_one_suffix_region():
    groups = groups_of('Later Bitches - Benny Benassi vs. MazZz & Constantin Remix')
    sep_values = [str(g) for g in groups if g.semantic_type == SemanticType.SEPARATOR]
    assert sep_values == ['-']
    suffix = [g for g in groups if g.semantic_type not in (SemanticType.TITLE, SemanticType.SEPARATOR)]
    assert len(suffix) == 1
    assert str(suffix[0]) == 'Benny Benassi vs. MazZz & Constantin Remix'

def test_dash_suffix_with_slash_inside_is_one_region():
    groups = groups_of('Money For Nothing - Single Edit / Remastered 2022')
    sep_values = [str(g) for g in groups if g.semantic_type == SemanticType.SEPARATOR]
    assert sep_values == ['-']
    suffix = [g for g in groups if g.semantic_type not in (SemanticType.TITLE, SemanticType.SEPARATOR)]
    assert len(suffix) == 1
    assert str(suffix[0]) == 'Single Edit / Remastered 2022'

def test_inword_dash_is_not_a_suffix():
    assert group_with_text('Shine On You Crazy Diamond, Pts. 1-5', '5').semantic_type == SemanticType.TITLE

def test_each_spaced_dash_is_its_own_suffix():
    groups = groups_of('Say It Loud - I\'m Black And I\'m Proud - Pt. 1')
    assert group_with_text('Say It Loud - I\'m Black And I\'m Proud - Pt. 1',
                           'I\'m Black And I\'m Proud').semantic_type == SemanticType.TITLE
    assert any(str(g) == 'Pt. 1' for g in groups)
    sep_values = [str(g) for g in groups if g.semantic_type == SemanticType.SEPARATOR]
    assert sep_values == ['-', '-']

def test_hyphenated_rerecorded_is_one_suffix_region():
    groups = groups_of('Ruff Ryders\' Anthem - Re-Recorded')
    assert not any(str(g) in ('Re', 'Recorded') and g.semantic_type == SemanticType.TITLE
                   for g in groups)
    assert any(str(g) == 'Re-Recorded' for g in groups)

def test_punctuation_only_fragment_after_bracket_is_dropped():
    groups = groups_of('Who Am I (What\'s My Name)?')
    assert not any(str(g) == '?' for g in groups)
    assert group_with_text('Who Am I (What\'s My Name)?', 'Who Am I').semantic_type == SemanticType.TITLE

def test_depth_zero_feature_is_split_from_title():
    groups = groups_of('Hot Mess feat. Elly Jackson - Duck Sauce Remix')
    assert group_with_text('Hot Mess feat. Elly Jackson - Duck Sauce Remix',
                           'Hot Mess').semantic_type == SemanticType.TITLE
    assert any(str(g) == 'feat. Elly Jackson' for g in groups)
    assert any(str(g) == 'Duck Sauce Remix' for g in groups)

def test_w_slash_starts_feature_region():
    groups = groups_of('Title w/ Artist')
    assert any(str(g) == 'Title' and g.semantic_type == SemanticType.TITLE for g in groups)
    assert any(str(g) == 'w/ Artist' for g in groups)

def test_bare_with_is_not_a_feature_opener():
    g = group_with_text('Dancing with the Stars', 'Dancing with the Stars')
    assert g.semantic_type == SemanticType.TITLE

def test_bracket_version_keyword_is_version_marker():
    g = group_with_text('Save Your Tears (Remix)', 'Remix')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_bracket_feature_opener_is_contribution():
    g = group_with_text('Save Your Tears (with Ariana Grande)', 'with Ariana Grande')
    assert g.semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_bracket_named_remixer_is_contribution():
    g = group_with_text('Later Bitches (Benny Benassi Remix)', 'Benny Benassi Remix')
    assert g.semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_depth_zero_feature_region_is_contribution():
    g = group_with_text('Hot Mess feat. Elly Jackson', 'feat. Elly Jackson')
    assert g.semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_w_slash_region_is_contribution():
    g = group_with_text('Title w/ Artist', 'w/ Artist')
    assert g.semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_dash_suffix_tier_is_tier_marker():
    g = group_with_text('Save Your Tears - Bonus Track', 'Bonus Track')
    assert g.semantic_type == SemanticType.TIER_MARKER

def test_dash_suffix_remix_is_version_marker():
    g = group_with_text('Roses - Imanbek Remix', 'Imanbek Remix')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_from_opener_is_subtitle():
    g = group_with_text('Stayin\' Alive - From "Saturday Night Fever" Soundtrack',
                        'From "Saturday Night Fever" Soundtrack')
    assert g.semantic_type == SemanticType.SUBTITLE

def test_from_opener_in_bracket_is_subtitle():
    assert group_with_text('No Room For A Saint (From F1 Movie)',
                           'From F1 Movie').semantic_type == SemanticType.SUBTITLE

def test_packaging_marker_name_is_not_contribution():
    g = group_with_text('Track (Foo Bar Remaster)', 'Foo Bar Remaster')
    assert g.semantic_type == SemanticType.COSMETIC_MARKER

def test_recording_type_name_is_version_not_contribution():
    g = group_with_text('Track (Foo Bar Live)', 'Foo Bar Live')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_remixer_keyword_name_is_contribution():
    g = group_with_text('Track (Foo Bar Remix)', 'Foo Bar Remix')
    assert g.semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_artist_list_overrides_recording_default():
    groups = group_tokens(
        tokenize(normalize_str('Track (Foo Bar Live)')),
        artists=['Foo Bar'],
    )
    g = [x for x in groups if str(x) == 'Foo Bar Live'][0]
    assert g.semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_suffix_spans_bracket_to_keyword():
    groups = groups_of('Dance - Mitsunari BR & Skore (BR) Remix')
    suffix = [g for g in groups
              if g.semantic_type not in (SemanticType.TITLE, SemanticType.SEPARATOR)]
    assert len(suffix) == 1
    assert str(suffix[0]) == 'Mitsunari BR & Skore (BR) Remix'
    assert suffix[0].semantic_type == SemanticType.CONTRIBUTION_MARKER
    assert not any(str(g) == 'Remix' for g in groups)

def test_keyword_inside_bracket_does_not_span_suffix():
    g = group_with_text('Love - Hate (Original Mix)', 'Hate')
    assert g.semantic_type == SemanticType.TITLE
    assert group_with_text('Love - Hate (Original Mix)',
                           'Original Mix').semantic_type == SemanticType.COSMETIC_MARKER

def test_single_cap_remixer_is_version_not_contribution():
    g = group_with_text('Sweet Dreams (Hot Remix)', 'Hot Remix')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_keyword_first_then_caps_is_version():
    g = group_with_text('Sinnerman - Live In New York/1965', 'Live In New York/1965')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_original_version_with_year_is_version():
    g = group_with_text('YMCA - Original Version 1978', 'Original Version 1978')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_artist_list_fallback_marks_contribution():
    groups = group_tokens(
        tokenize(normalize_str('Title (Afrojack Remix)')),
        artists=['Afrojack'],
    )
    g = [x for x in groups if str(x) == 'Afrojack Remix'][0]
    assert g.semantic_type == SemanticType.CONTRIBUTION_MARKER

def test_without_artist_list_single_cap_is_version():
    g = group_with_text('Title (Afrojack Remix)', 'Afrojack Remix')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_artist_list_needs_full_name_contiguous():
    groups = group_tokens(
        tokenize(normalize_str('Title (Calvin Remix)')),
        artists=['Calvin Harris'],
    )
    g = [x for x in groups if str(x) == 'Calvin Remix'][0]
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_version_keyword_beats_cosmetic_keyword():
    g = group_with_text('Macarena - Radio Version', 'Radio Version')
    assert g.semantic_type == SemanticType.VERSION_MARKER

def test_pure_cosmetic_region_is_cosmetic():
    g = group_with_text('Track (Official Video)', 'Official Video')
    assert g.semantic_type == SemanticType.COSMETIC_MARKER

def test_pure_tier_region_is_tier():
    g = group_with_text('Track (Interlude)', 'Interlude')
    assert g.semantic_type == SemanticType.TIER_MARKER