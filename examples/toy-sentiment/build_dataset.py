#!/usr/bin/env python3
"""Build the toy-sentiment example dataset (stdlib only).

Generates data/train.jsonl and data/test.jsonl from a small, hand-written,
generic sentiment corpus (film/tech/food/travel/retail review style, no real
people or personal content). Split is stratified by label with a fixed
random seed so the result is fully deterministic and reproducible.

LEARNABILITY DESIGN (this is the point of this revision): every sentence is
built around one or more words from a small, fixed, shared sentiment
vocabulary (SENTIMENT_VOCAB below). Each vocab word is reused across at
least 3 different sentences, spanning different topics and sentence
structures, so a bag-of-words model actually has repeated evidence to learn
from and a stratified 70/30 split leaves each word well represented in
train regardless of which sentences land in test. This is intentional
vocabulary sharing across splits, not leakage -- see DATASET_NOTES.md.

Sentences are NOT built as opposite-label templates that differ by a single
swapped word (that was the bug in the previous revision: a discriminative
adjective could be out-of-vocabulary for train). Positive and negative
sentences are written independently with varied structure and phrasing.

Usage:
    python3 build_dataset.py
"""
import json
import random
import re
from pathlib import Path

SEED = 42
TRAIN_FRACTION = 0.70  # per-class fraction assigned to train

# Fixed, compact, shared sentiment vocabulary. Every sentence below is built
# around at least one of these words; each word is reused >=3 times across
# distinct sentences/topics (see build_dataset.py assertions and
# verify_split.py's learnability check).
POSITIVE_VOCAB = [
    "great", "love", "excellent", "wonderful", "amazing",
    "best", "enjoyed", "happy", "fantastic", "recommend",
]
NEGATIVE_VOCAB = [
    "terrible", "hate", "awful", "worst", "boring",
    "disappointing", "poor", "broken", "waste", "avoid",
]

# Each sentence below is built around TWO words from the class vocabulary
# (a "shift" combinatorial design over the 10-word vocab so every word
# occurs in exactly 6 of the 30 sentences per class). Using two vocab words
# per sentence instead of one roughly doubles the aggregate log-likelihood
# signal available to the bag-of-words model relative to incidental
# stopword/topic-noun noise, which is what made the single-word-per-sentence
# version of this corpus classify at only ~0.67 test accuracy despite
# passing the leakage/learnability checks -- learnability (word is
# in-vocabulary) is necessary but not sufficient; the word also needs
# enough repeated evidence to outweigh sentence-to-sentence noise in a
# tiny corpus.
POSITIVE = [
    "I love how great this coffee shop treats its regulars every morning.",
    "I love this store's excellent selection of hiking gear.",
    "The excellent service made for a wonderful evening out.",
    "The wonderful staff and amazing food made this trip memorable.",
    "This is the best and most amazing view I have seen from a hotel balcony.",
    "We enjoyed the best meal of our entire vacation at this small diner.",
    "The whole family enjoyed the show and left feeling genuinely happy.",
    "I am happy to say the repair shop did a fantastic job on my bike.",
    "This museum tour was fantastic and I would recommend it to anyone.",
    "I recommend this bookstore, the staff give great suggestions every time.",
    "The gym trainer was great and gave us excellent tips on form.",
    "I love how this park hosts wonderful outdoor concerts every summer.",
    "The chef's tasting menu was excellent and the desserts were amazing.",
    "Our anniversary weekend was wonderful, easily the best trip we have taken.",
    "The amazing fireworks display was something we truly enjoyed with the kids.",
    "This is the best pizza in town and it always makes me happy.",
    "We enjoyed the fantastic acoustics of the new concert hall.",
    "I am happy with the tailoring and would recommend this shop to friends.",
    "The new headphones sound fantastic and the case is great too.",
    "I recommend this cafe because I love their seasonal espresso blends.",
    "The customer support agent was great and made a wonderful first impression.",
    "I love the amazing photos this camera takes in low light.",
    "The vineyard tour offered excellent wine and the best scenery in the valley.",
    "It was a wonderful surprise, and we enjoyed every course of the tasting.",
    "The kids were happy about the amazing new playground equipment.",
    "This bakery makes the best croissants, a truly fantastic way to start the day.",
    "We enjoyed the play so much that I would recommend it to everyone I know.",
    "She was happy with the great fit of her new running shoes.",
    "The lead singer's performance was fantastic, and fans said they love this band's energy.",
    "I would recommend this hotel for its excellent rooftop restaurant.",
]

NEGATIVE = [
    "I hate how this diner treats regulars, the wait was terrible tonight.",
    "I hate to admit it, but the awful smell in the lobby never went away.",
    "The awful traffic made this the worst commute of the entire month.",
    "This was the worst lecture I have sat through, utterly boring from start to end.",
    "The sequel felt boring and the ending was deeply disappointing.",
    "Support's response was disappointing, and the fix itself was poor at best.",
    "The packaging was poor and the item inside arrived broken.",
    "The vacuum arrived broken and it was a total waste of money.",
    "Renewing that membership was a waste, and I would avoid it going forward.",
    "I would avoid this parking garage, the lighting is terrible at night.",
    "The hold music was terrible and the wait time was simply awful.",
    "I hate long layovers, and this was the worst one I have had.",
    "The documentary's narration was awful and the pacing was boring throughout.",
    "This turned out to be the worst haircut, a disappointing result after the price I paid.",
    "The training session was boring and the materials were poor quality.",
    "The update was disappointing and left several features broken.",
    "The insulation in this apartment is poor, making heating bills a waste.",
    "The zipper was broken after the first use, so I would avoid this brand.",
    "Sitting through that meeting was a waste, the presentation was terrible.",
    "I would avoid that airline, I hate how they handle delays.",
    "The soundcheck was terrible, honestly the worst I have heard at that venue.",
    "I hate sitting through boring safety briefings on every single flight.",
    "The remake had awful pacing and a disappointing final act.",
    "The customer line moved at the worst pace due to poor staffing.",
    "The tour guide was boring and half the exhibits were broken anyway.",
    "The reunion tour was disappointing, honestly a waste of the ticket price.",
    "The stitching quality is poor, so I would avoid ordering this size again.",
    "The elevator has been broken for weeks, making the terrible commute even worse.",
    "I hate when a subscription renews automatically, it feels like a waste every time.",
    "I would avoid that mechanic, the awful noise came back within days.",
]


def stratified_split(items, label, rng):
    shuffled = list(items)
    rng.shuffle(shuffled)
    n_train = round(len(shuffled) * TRAIN_FRACTION)
    train = [{"text": t, "label": label} for t in shuffled[:n_train]]
    test = [{"text": t, "label": label} for t in shuffled[n_train:]]
    return train, test


_TOKEN_RE = re.compile(r"[a-z']+")


def _word_counts(sentences, vocab):
    counts = {w: 0 for w in vocab}
    for s in sentences:
        toks = set(_TOKEN_RE.findall(s.lower()))
        for w in vocab:
            if w in toks:
                counts[w] += 1
    return counts


def main():
    assert len(POSITIVE) == len(set(POSITIVE)), "duplicate positive sentence in source list"
    assert len(NEGATIVE) == len(set(NEGATIVE)), "duplicate negative sentence in source list"
    assert set(POSITIVE).isdisjoint(set(NEGATIVE)), "a sentence appears in both classes"

    # Design-time guarantee: every vocab word must occur in >=5 sentences of
    # its class (design target is 6, via the two-word-per-sentence
    # combinatorial layout above), so that (a) a 70/30 stratified split
    # leaves it in train with overwhelming probability, and (b) the word has
    # enough repeated evidence to give the bag-of-words model a strong
    # signal over incidental stopword/topic-noun noise in this tiny corpus
    # (verified again post-split by verify_split.py's learnability check).
    pos_counts = _word_counts(POSITIVE, POSITIVE_VOCAB)
    neg_counts = _word_counts(NEGATIVE, NEGATIVE_VOCAB)
    for w, c in pos_counts.items():
        assert c >= 5, f"positive vocab word {w!r} used only {c} times, need >=5"
    for w, c in neg_counts.items():
        assert c >= 5, f"negative vocab word {w!r} used only {c} times, need >=5"

    rng = random.Random(SEED)
    pos_train, pos_test = stratified_split(POSITIVE, "positive", rng)
    neg_train, neg_test = stratified_split(NEGATIVE, "negative", rng)

    train = pos_train + neg_train
    test = pos_test + neg_test

    # Deterministic within-split order: shuffle once more with the same seed
    # so classes are interleaved rather than block-ordered, then sort is not
    # applied (order itself carries no information; stdlib json.dumps is used
    # as-is for readability).
    rng.shuffle(train)
    rng.shuffle(test)

    out_dir = Path(__file__).parent / "data"
    out_dir.mkdir(exist_ok=True)

    with open(out_dir / "train.jsonl", "w") as f:
        for row in train:
            f.write(json.dumps(row) + "\n")

    with open(out_dir / "test.jsonl", "w") as f:
        for row in test:
            f.write(json.dumps(row) + "\n")

    print(f"total={len(POSITIVE) + len(NEGATIVE)} "
          f"train={len(train)} (pos={len(pos_train)}, neg={len(neg_train)}) "
          f"test={len(test)} (pos={len(pos_test)}, neg={len(neg_test)}) "
          f"seed={SEED}")


if __name__ == "__main__":
    main()
