#!/usr/bin/env python3
"""Language gate v3: precise Norwegian-ability requirement detection (fixes 'in Norwegian' bug)."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"

# Phrases that REQUIRE Norwegian ability. Norwegian word 'norsk' or English 'norwegian'.
HARD_CUE = [
    # fluent / proficiency statements
    r"fluen\w*\s+(?:in\s+)?(?:norsk|norwegian)",
    r"fluen\w*\s+(?:i\s+)?(?:norsk|norwegian)",
    r"fluency\s+in\s+(?:norsk|norwegian)",
    r"(?:norsk|norwegian)\s+proficien\w*", r"proficien\w*\s+in\s+(?:norsk|norwegian)",
    r"(?:good|strong|excellent|solid|very\s+good|high)\s+(?:command|knowledge|proficiency|skills|understanding)"
    r"[^.]{0,40}(?:norsk|norwegian)",
    r"(?:norsk|norwegian)\s+language\s+skills", r"norwegian\s+on\s+a\s+fluent",
    r"(?:norsk|norwegian)\s+and\s+english", r"english\s+and\s+(?:norsk|norwegian)",
    r"(?:norsk|norwegian)\s+og\s+engelsk", r"engelsk\s+og\s+norsk",
    r"(?:norsk|norwegian)\s+eller\s+engelsk", r"engelsk\s+eller\s+norsk",
    r"(?:norsk|norwegian)\s+som\s+arbeidsspråk", r"(?:norsk|norwegian)\s+er\s+arbeidsspråk",
    r"arbeidsspråk[^.]{0,40}(?:norsk|norwegian)", r"(?:norsk|norwegian)[^.]{0,40}arbeidsspråk",
    r"working\s+language\s+will\s+be\s+(?:norsk|norwegian)",
    r"everyday\s+working\s+language[^.]{0,30}(?:norsk|norwegian)",
    r"(?:norsk|norwegian)[^.]{0,45}(?:språk|beherskes|må\s+kunne|må\s+beherske|er\s+et\s+krav|"
    r"er\s+krav|påkrevd|grunnleggende\s+norsk|språklig|grammatikk|nivå)",
    r"(?:krav|påkrevd|må\s+kunne|må\s+beherske|behersk\w*)[^.]{0,45}(?:norsk|norwegian)",
    r"(?:norsk|norwegian)[^.]{0,35}(?:språkkunnskap|ferdighet\w*|forstår\w*|kunnskap)",
    r"behersk\w*[^.]{0,30}norsk", r"snakker[^.]{0,25}norsk", r"skriver[^.]{0,25}norsk",
    r"god\s+norsk", r"gode\s+norsk", r"gods\s+norsk", r"norsk\w*\s+nivå",
    # Scandinavian / Nordic language requirement
    r"(?:skandinavisk|scandinavian|nordisk)\s+(?:språk|language)",
    r"ett\s+skandinavisk", r"et\s+skandinavisk", r"(?:a\s+)?scandinavian\s+language",
    r"fluen\w*[^.]{0,30}(?:scandinavian|nordic|skandinavisk|nordisk)",
    r"(?:scandinavian|nordic)[^.]{0,30}(?:language|språk)[^.]{0,40}(?:er\s+påkrevd|required|krav|must)",
    r"fluen\w*\s+(?:i\s+)?(?:english|engelsk)[^.]{0,40}(?:scandinavian|nordic|skandinavisk|nordisk)",
    r"(?:english|engelsk)[^.]{0,25}and[^.]{0,10}a\s+scandinavian",
    r"(?:english|engelsk)[^.]{0,25}and[^.]{0,15}(?:a\s+)?(?:relevant\s+)?(?:nordic|nordisk)\s+(?:language|språk)",
    r"(?:english|engelsk)[^.]{0,40}(?:and|&)\s+(?:a\s+)?(?:relevant\s+)?(?:nordic|nordisk)\s+language",
    r"(?:english|engelsk)[^.]{0,25}and[^.]{0,10}a\s+nordic",
    r"(?:norwegian|norsk)[^.]{0,25}or\s+another\s+scandinavian",
    r"norwegian[^.]{0,30}(?:er\s+et\s+krav|krav|påkrevd|er\s+påkrevd)",
]
SOFT_MARK = re.compile(r"(er\s+en\s+fordel|er\s+et\s+pluss|pluss\s+til|\bfordel\b|an\s+advantage|"
                        r"is\s+an?\s+advantage|is\s+a\s+plus|nice\s+to\s+have|optional|preferred|"
                        r"er\s+ønskelig|will\s+be\s+considered\s+an\s+advantage|"
                        r"but\s+not\s+a\s+requirement|er\s+en\s+bonus|will\s+be\s+an?\s+advantage|"
                        r"seen\s+as\s+a\s+(?:bonus|plus)|counts\s+as\s+an?\s+advantage)", re.I)
OTHER_LANG = re.compile(r"\b(english|engelsk|french|fransk|german|tysk|italian|italiensk|swedish|svensk|"
                         r"danish|dansk|spanish|spansk|arabic|arabisk|portuguese|portugisisk|polish|polsk|"
                         r"dutch|nederlandsk|mandarin|chinese|kinesisk|hindi|russian|rusk)\b", re.I)
LANG_TOKEN = re.compile(r"\b(norsk|norwegian|english|engelsk|french|fransk|german|tysk|italian|italiensk|"
                         r"swedish|svensk|danish|dansk|spanish|spansk|arabic|arabisk|portuguese|"
                         r"portugisisk|polish|polsk|scandinavian|skandinavisk|nordic|nordisk)\b", re.I)

def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n", text)
    return [" ".join(p.split()) for p in parts if p.strip()]

def evaluate(body):
    hard, soft = [], []
    for sent in sentences(body):
        if not re.search(r"\b(norsk|norwegian|scandinav\w*|skandinavisk|nordisk|nordic)\b", sent, re.I):
            continue
        if not any(re.search(p, sent, re.I) for p in HARD_CUE):
            continue
        # soft marker that directly qualifies the Norwegian/Scandinavian mention
        soft_m = None
        for mm in SOFT_MARK.finditer(sent):
            soft_m = mm
            break
        if soft_m:
            # A soft marker cancels the requirement only if it refers to the Norwegian
            # mention itself. If another language sits between the Norwegian mention and
            # the soft marker (e.g. "Fluent in Norwegian and English (Spanish is a plus)"),
            # the marker qualifies that other language -> the Norwegian demand is HARD.
            nor_pos = [m.start() for m in re.finditer(r"\b(norsk|norwegian)\b", sent, re.I)]
            other_between = False
            for np_ in nor_pos:
                lo, hi = min(np_, soft_m.start()), max(np_, soft_m.start())
                between = sent[lo:hi]
                toks = [t for t in LANG_TOKEN.findall(between)
                        if t.lower() not in ("norsk", "norwegian")]
                if toks:
                    other_between = True
            if not other_between:
                soft.append(sent)
                continue
        hard.append(sent)
    return hard, soft

if __name__ == "__main__":
    tests = [
        "Fluent in Norwegian and English",
        "Fluent in Norwegian and English, with excellent verbal and written communication skills",
        "Fluency in Norwegian and English",
        "Excellent communication skills in Norwegian and English",
        "Strong communication skills in both Norwegian and English",
        "Fluent in written and spoken English and a Scandinavian language",
        "Fluent in English communication skills (Norwegian is an advantage)",
        "Fluent English communication skills, both written and spoken; Norwegian language skills are an advantage",
        "Good command of written and spoken English",
        "Fluency in English is required; proficiency in a Scandinavian language is an advantage",
        "Working knowledge of Norwegian laws, regulations, and standards relevant to construction",
        "Knowledge of the Norwegian Public Administration Act (Forvaltningsloven) is an advantage, but not a requirement",
        "Fluency in English; proficiency in French, Arabic, or Norwegian is an advantage",
        "Norwegian is an advantage",
        "Meget gode kunnskaper i norsk og engelsk, både muntlig og skriftlig",
        "Du snakker norsk flytende og er generelt god i engelsk",
        "Fluent in English, which is the working language",
        "Excellent communication and negotiation skills in English and a relevant Nordic language",
        "Native or fluent English, Norwegian, or Swedish speaker",
        "Fluent in English, both written and spoken, at a high professional level",
        "Norsk og engelsk, både skriftlig og muntlig",
    ]
    for t in tests:
        h, s = evaluate(t)
        print(f"{'HARD' if h else ('soft' if s else 'none'):5} | {t[:95]}")
