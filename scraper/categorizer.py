"""Bepaal vaste evenementcategorieën zonder externe diensten."""

import re
import unicodedata


CATEGORY_SLUGS = frozenset({
    "community", "sport", "kids_family", "culture", "workshop",
    "lecture", "market", "exhibition", "other",
})


def _text(value):
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


COMMUNITY = re.compile(
    r"\b(?:buurt\w*|wijk\w*|bewoner\w*|taalcaf(?:é|e)|talencaf(?:é|e)|"
    r"leesclub|inloop|ontmoetingscaf(?:é|e)|warme maaltijd|open coffee|"
    r"straatfeest|zomerwijkfeest|zomerfeest|openingsfestijn|"
    r"burendag|veteranendag|oktoberfest|pubquiz|popquiz|vrijmibo|"
    r"karaoke|disco|pride night|kermis|bbq)\b"
)
KNOWN_COMMUNITY_ACTIVITY = re.compile(
    r"\b(?:yap\s*&\s*yarn|gouda bij kaarslicht)\b"
)
SPORT = re.compile(
    r"\b(?:sport|buurtsport|yoga|wandelen|wandelgroep|wandeltocht|hardlopen|"
    r"fitness|bewegen|voetbal|zwemmen|vitaal|singelloop|asfaltloop|"
    r"goudasfaltloop|goudaasfaltloop|marathon|kidsrun|run|ijsbaan|"
    r"fietsen|fietstocht|\w*toernooi\w*)\b"
)
SPORT_WITH_SOURCE = re.compile(r"\b(?:stap mee|valbus|valpreventie\w*)\b")
KIDS = re.compile(
    r"\b(?:kinder\w*|kinderen|peuter\w*|kleuter\w*|familie\w*|"
    r"family|gezins\w*|jeugd\w*|jongeren|kidsrun|sinterklaas\w*|"
    r"pakjesboot\w*|kleintjes|jongerenkoor\w*|"
    r"ouder\s*(?:&|en)\s*kind)\b"
)
CHILD_AGE = re.compile(r"\b\d{1,2}\s+(?:tot|t/m|-)\s+\d{1,2}\s+jaar\b")
YOUTH_CONTEXT = re.compile(r"\b(?:buurtsport|jeugd\w*|jongeren|meiden|jongens)\b")
CULTURE = re.compile(
    r"\b(?:monument\w*|erfgoed|kunst\w*|muziek\w*|"
    r"theatervoorstelling|theaterproductie\w*|theaterstuk|"
    r"film\w*|cultuur\w*|culture|kinderboek\w*|boek\w*|"
    r"literair\w*|historisch\w*|concert\w*|jubileumconcert|"
    r"meezingconcert|kerstconcert|adventsconcert|musical|koor\w*|"
    r"orgel\w*|piano\w*|karaoke|tribute\w*|rock\w*|band|bands|"
    r"songbook|candlelight|disco|dans\w*|ballet|opera\w*|"
    r"cabaret|comedy|fotografi\w*|schrijver\w*|stadsdichter|bibliotheek|"
    r"stadsbibliotheek|djembé|djembe|dinnershow)\b"
)
EXPLICIT_PERFORMANCE = re.compile(
    r"\b(?:voorstelling\w*|peutervoorstelling\w*|undercoversessie\w*|"
    r"introdans|videoclip\w*|music|sing-along|zangavond|oudejaarsconference|"
    r"gospel|jongerenkoor\w*|mannenkoor\w*|mannenkoren|choir|orkest\w*|"
    r"drummer\w*|"
    r"superdrum\w*|museum|musea)\b"
)
MUSIC_GENRE = re.compile(r"\b(?:metalcore|thrash metal|alternative metal)\b")
KNOWN_CULTURAL_ACTIVITY = re.compile(
    r"\b(?:festival (?:de )?verwondering|verweven verhalen|gouda bij kaarslicht)\b"
)
WORKSHOP = re.compile(
    r"\b(?:workshop|fotografieworkshop|cursus fotografie|praktijkles|masterclass)\b"
)
PRACTICAL_LESSON = re.compile(
    r"\b(?:snijtechnieken|sieraad maken|tekenen|schilderen|borduren|"
    r"snoeien|handwerken)\b"
)
LECTURE = re.compile(r"\b(?:lezing|lecture|kennissessie|talk)\b")
PRESENTATION_TALK = re.compile(r"\bpresentatie\s+(?:over|door)\b")
MARKET = re.compile(
    r"\b(?:markt|market|braderie|kerstmarkt|rommelmarkt|boerenmarkt|"
    r"kaasmarkt|boekenmarkt|kunstmarkt|wintermarkt)\b"
)
EXHIBITION = re.compile(r"\b(?:expositie\w*|tentoonstelling\w*|exhibition\w*)\b")
TEXTILE_EXHIBITION = re.compile(r"\btextielfestijn\b")
DESCRIPTION_EXHIBITION_OPENING = re.compile(
    r"\b(?:de|een) expositie\b.{0,100}\bgeopend\b"
)
VOLKSUNIVERSITEIT_CULTURE_URL = re.compile(
    r"\Ahttps?://(?:www\.)?volksuniversiteitgouda\.nl/kunst-cultuur(?:[/?#]|\Z)"
)
VOLKSUNIVERSITEIT_CULINARY_URL = re.compile(
    r"\Ahttps?://(?:www\.)?volksuniversiteitgouda\.nl/culinair(?:[/?#]|\Z)"
)


def classify(event) -> set[str]:
    """Classificeer de opgeslagen evenementvelden zonder ze te wijzigen."""
    title = _text(event.get("title"))
    source = _text(event.get("source"))
    location = _text(event.get("location"))
    source_url = _text(event.get("source_url"))
    description = _text(event.get("description"))
    categories = set()

    if COMMUNITY.search(title) or KNOWN_COMMUNITY_ACTIVITY.search(title):
        categories.add("community")
    if SPORT.search(title) or (
        source == "sport•gouda" and SPORT_WITH_SOURCE.search(title)
    ):
        categories.add("sport")
    if KIDS.search(title) or CHILD_AGE.search(title) or (
        "12+" in title and YOUTH_CONTEXT.search(title)
    ):
        categories.add("kids_family")
    if (
        CULTURE.search(title)
        or EXPLICIT_PERFORMANCE.search(title)
        or MUSIC_GENRE.search(title)
        or KNOWN_CULTURAL_ACTIVITY.search(title)
        or (
            source == "volksuniversiteit gouda"
            and VOLKSUNIVERSITEIT_CULTURE_URL.search(source_url)
        )
        or (
            EXHIBITION.search(title)
            and ("cultuurhuis" in source or "museum" in location)
        )
    ):
        categories.add("culture")
    if WORKSHOP.search(title) or (
        source in {"volksuniversiteit gouda", "cultuurhuis garenspinnerij"}
        and PRACTICAL_LESSON.search(title)
    ) or (
        source == "volksuniversiteit gouda"
        and VOLKSUNIVERSITEIT_CULINARY_URL.search(source_url)
    ):
        categories.add("workshop")
    if LECTURE.search(title) or PRESENTATION_TALK.search(title):
        categories.add("lecture")
    if MARKET.search(title):
        categories.add("market")
    if (
        EXHIBITION.search(title)
        or TEXTILE_EXHIBITION.search(title)
        or DESCRIPTION_EXHIBITION_OPENING.search(description)
    ):
        categories.add("exhibition")

    return categories or {"other"}
