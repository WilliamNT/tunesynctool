# Character folds applied before tokenizing, so the tokenizer only ever sees
# one form of each thing that real metadata spells several ways.
#
# Dashes: en and em dash collapse to the ASCII hyphen, which the tokenizer
# labels DASH. Without this, "Wonderwall – Remastered" tags the separator as
# UNKNOWN and the parser cannot tell it is a dash.
#
# Apostrophes: the smart and modifier-letter variants collapse to the ASCII
# apostrophe, which the tokenizer already treats as alphanumeric. Without this,
# ' is alphanumeric but ' and ʼ are UNKNOWN, so "Rock 'n' Roll" splits oddly.

SUBSTITUTIONS = {
    "–": "-",
    "—": "-",
    "’": "'",
    "‘": "'",
    "ʼ": "'",
}