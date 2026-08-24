# Markers that mean a distinct recording of the same work. A version mismatch
# is demoted by the scorer but not rejected, which is the "better than nothing"
# case: if only a remix is in the catalog, the remix is what you get.
RECORDING_VERSION_KEYWORDS = {
    "remix", "live", "acoustic", "karaoke", "cover", "tribute",
    "instrumental", "demo", "session", "bootleg", "unplugged",
    "nightcore", "version", "club", "dub", "vip", "extended",
    "slowed", "reverb", "sped", "rerecorded", "recorded",
}

# Markers that are cosmetic: the same recording in different paint. Stripped
# but never penalised. edition / anniversary / singles are reissue and packaging
# descriptors, not a different recording.
COSMETIC_KEYWORDS = {
    "remaster", "remastered", "remasters", "edit", "mix", "radio",
    "single", "singles", "official", "video", "audio", "lyrics", "hd", "4k",
    "mono", "stereo", "remasterizado", "remasterizada",
    "edition", "anniversary", "edited", "soundtrack",
}

# Bare words that introduce a featured artist. "feat." tokenizes as "feat" +
# ".", so only the word matters here. Rare enough as plain words that they
# count as a feature wherever they appear. "pres." is the "presents" shorthand.
FEATURE_KEYWORDS = {
    "featuring", "feat", "ft", "prod", "produced", "pres", "presents",
}

# Words that introduce a feature only as the opening word of a region. "with"
# is ordinary English ("Dancing with the Stars"); loose in the core it is the
# title"s preposition, not a feature, so it only counts at the start of a region.
FEATURE_KEYWORDS_GATED = {
    "with",
}

# "w" alone is a single letter and shows up in titles, so it is never a feature
# by itself. "w/" is, but only because the slash stays as its own SLASH token
# right after the "w". The classifier matches the two-token pair (w, SLASH).
FEATURE_SLASH = "w"

# Track-placement descriptors: which slot on a release this is, not which
# recording. Stripped like cosmetic markers but labelled apart. They apply only
# in a bracket or after a trailing dash; as the whole title they fall back to
# TITLE under the never-empty-core rule. "pt" / "pts" are the part-number
# abbreviations; the full word "part" is left out on purpose ("Part of Me").
TIER_KEYWORDS = {
    "bonus", "intro", "outro", "interlude", "prelude", "reprise",
    "skit", "segue", "deluxe", "prologue", "epilogue", "pt", "pts",
}