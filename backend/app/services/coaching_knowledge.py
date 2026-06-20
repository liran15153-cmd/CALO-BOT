from copy import deepcopy
import re


class CoachingKnowledgeService:
    """Compact, source-backed coaching guidance for provider context."""

    def for_intent(self, intent: str | None = None) -> dict:
        context = deepcopy(_BASE_CONTEXT)
        context["intent_focus"] = _INTENT_FOCUS.get(intent or "", _INTENT_FOCUS["general_chat"])
        return context

    def for_provider_context(self, intent: str | None = None, query: str | None = None) -> dict:
        context = self.for_intent(intent)
        provider_context = {
            "version": context["version"],
            "scope": context["scope"],
            "non_certification_note": context["non_certification_note"],
            "professional_scope": context["professional_scope"][:1],
            "trainer_skill_domains": context["trainer_skill_domains"][:5],
            "rules": context["rules"][:4],
            "programming_model": context["programming_model"][:3],
            "program_design_summary": [
                "Audit: מטרה/פרופיל/ציוד/זמן/מגבלות -> דפוסים, נפח ותדירות ברי ביצוע.",
                "עומס וחזרות לפי מטרה; טכניקה בלי כאב לפני התקדמות.",
                "סדר: מורכבים קודם; FITT-VP משנה משתנה אחד ושומר התאוששות/עקביות.",
            ],
            "progression_regression": context["progression_regression"],
            "deload_rules": context["deload_rules"][:2],
            "load_monitoring_summary": [
                "שלב עומס חיצוני עם RPE, עייפות, שינה ומוטיבציה.",
                "אם RPE גבוה או ביצועים יורדים, התאם נפח/עצימות לפני התקדמות.",
            ],
            "recovery_rules": context["recovery_rules"][:2],
            "preparticipation_screening": [
                "לפני עומס שאל על מצב רפואי, תרופות, פציעה ותסמינים חריגים.",
                "כאב בחזה, עילפון, קוצר נשימה חריג או כאב חד דורשים עצירה והפניה מקצועית.",
            ],
            "referral_rules": context["referral_rules"][:2],
            "safety_boundaries": context["safety_boundaries"][:3],
            "coaching_behavior": [
                "עברית טבעית: RPE/RIR/DOMS/HIIT/Zone 2 נשארים כמונחי אימון עם הסבר קצר.",
                "תן סיבה קצרה, פעולה אחת, ושאלת המשך אחת רק כשחסר מידע.",
                "בלי אשמה או שפת חובה; אחרי פספוס מציעים גרסת מינימום ובחירה.",
            ],
            "goal_playbook_summary": [
                "שריר/כוח: נפח או עומס לפי מטרה, התאוששות לפני כשל.",
                "שומן/עקביות: כוח, צעדים/הליכה, תיעוד וגרסת מינימום.",
            ],
            "technique_cues_summary": [
                "סקוואט: ברכיים עם כף הרגל, בלי כאב חד.",
                "הינג׳: ירך מובילה וגב ניטרלי.",
                "דחיפה/משיכה: כתפיים נוחות ושכמות בשליטה.",
                "ליבה: צלעות/אגן ונשימה.",
            ],
            "population_adjustment_summary": [
                "מבוגרים: כוח, אירובי ושיווי משקל לפי יכולת.",
                "כרוני/הפסקה/ציוד מוגבל: הדרגה לפי תסמינים, לוגים ואמצעים זמינים.",
            ],
            "adherence_coaching_summary": [
                "ABC/פתוחה: חסם/חסמים -> צעד מדיד.",
                "מעקב לוגים ותוכנית אם-אז אחרי פספוס.",
            ],
            "intent_focus": context["intent_focus"],
            "sources": _provider_source_organizations(context["sources"]),
        }
        if intent not in {"workout_plan", "workout_log"}:
            provider_context["nutrition_coaching_rules"] = context["nutrition_coaching_rules"][:2]
        if intent in {"meal_log", "meal_image"}:
            provider_context["sports_nutrition_summary"] = [
                "חלבון למתאמנים: לרוב 1.4-2.0 גרם לק״ג ליום, עם 20-40 גרם או כ-0.25 גרם לק״ג בארוחה כשזה מתאים.",
                "פיזור חלבון כל 3-4 שעות יכול לתמוך בבנייה ובהתאוששות; תזמון לפני/אחרי אימון גמיש יותר מסך הצריכה היומית.",
                "פחמימות תומכות באימונים בינוניים-עצימים ובהתאוששות; ארוחה או נשנוש 1-4 שעות לפני אימון יכולים לעזור לפי סבילות.",
                "מים והידרציה חשובים לביצוע ולהתאוששות; התאם לפי חום, הזעה, משך אימון ותחושת הגוף.",
            ]
            provider_context["body_composition_summary"] = [
                "משקל לבדו לא מתאר הרכב גוף; שלב מדדי עקביות, כוח, היקפים, ביצועים ותחושה.",
                "בניית שריר דורשת אימוני התנגדות, אנרגיה מספקת, חלבון, שינה והתקדמות הדרגתית.",
                "ירידה בשומן צריכה לשמור על כוח ומסת שריר ככל האפשר, לא לרדוף אחרי ירידה מהירה בכל מחיר.",
            ]
            provider_context["practical_nutrition_summary"] = [
                "צלחת פשוטה: חלבון + ירק/פרי + פחמימה; לא חייבים גרמים.",
                "שובע: הוסף סיבים/ירק/פרי או קטניות לפני שינוי גדול.",
                "מים: עם ארוחות וסביב אימון; יותר בחום/הזעה.",
                "תמונה: טווח קלוריות, רמת ביטחון ושאלת דיוק אחת.",
            ]
        if intent in {"general_chat", "meal_log", "meal_image"}:
            provider_context["body_recomposition_summary"] = [
                "מאזן קלורי קובע כיוון; גירעון מתון, ותדלוק מספיק סביב עומס אימון.",
                "ריקומפ: כוח+חלבון+עקביות; שינוי הרכב גוף לא תמיד נראה מיד במשקל.",
                "מדוד מגמת משקל/ממוצע שבועי עם היקפים, ביצועים ואנרגיה.",
            ]
            provider_context["supplement_education_summary"] = [
                "תוספים הם optional: אוכל, תוכנית, שינה ועקביות קודם.",
                "קריאטין monohydrate: לרוב 3-5g/יום; קפאין: 3-6mg/kg לפני אימון לא לכל אחד.",
                "אבקת חלבון = נוחות; אלקטרוליטים בחום/הזעה/ארוך.",
                "fat burners/testosterone boosters: ראיות חלשות/סיכון; העדף third-party tested.",
            ]
        if intent == "general_chat":
            provider_context["daily_activity_summary"] = [
                "בסיס צעדים אישי לפני יעד; הוסף 500-1,000 צעדים כשזה קל להתמיד.",
                "שבור ישיבה עם הפסקות תנועה קצרות, מדרגות או הליכה רגועה.",
                "קלוריות מתנועה הן טווח לא מדויק; זה כלי עקביות, לא עונש.",
            ]
            provider_context["adherence_micro_summary"] = [
                "OARS: שאלה פתוחה, שיקוף קצר, ואז צעד אחד.",
                "מצא חסם אחד: זמן/אנרגיה/כאב/ציוד/מוטיבציה.",
                "אם-אז או מינימום 2-10 דק׳ אחרי פספוס.",
                "תן שתי אפשרויות בחירה; בלי שפת חובה.",
            ]
            provider_context["menstrual_cycle_summary"] = [
                "מחזור/וסת: התאם לפי סימפטומים, אנרגיה ו-RPE; לא לפי phase קשיח.",
                "אין מספיק ראיות ל-cycle syncing כוח קבוע; לוג אישי עדיף על כלל גורף.",
                "וסת שנעלמת/כאב חריג/דימום כבד -> לא אבחון; להפנות לגורם רפואי.",
            ]
            provider_context["environment_training_summary"] = [
                "חום: קצר/האט, יותר מים/צל/מנוחות; חולשה או עילפון -> לעצור ולהתקרר.",
                "AQI גבוה: פחות עצימות וזמן בחוץ; באוויר לא בריא העדף אימון בפנים.",
                "קור/wind chill: שכבות, יובש וכיסוי; נימול/בלבול/רעד חריג -> לעצור.",
            ]
            provider_context["fueling_risk_summary"] = [
                "REDs/תדלוק חסר: לא לאבחן; מעט אוכל+עומס גבוה+עייפות/ירידת ביצועים -> תדלוק/התאוששות והפניה אם חוזר.",
                "וסת שנעלמת, פציעות מאמץ או ירידה חדה במשקל אינם יעד כושר; לא חיטוב אגרסיבי.",
            ]
            provider_context["fitness_myths_summary"] = [
                "שומן נקודתי/spot reduction: מחזקים אזור, אבל ירידת שומן נקבעת בעיקר ממאזן והרגלים.",
                "DOMS/זיעה אינם מדד איכות; התקדמות נמדדת בביצוע, עקביות, התאוששות ולוגים.",
                "fasted cardio לא עדיף לירידת שומן אם סך האימון/האוכל דומה; כוח לא הופך נשים ל׳מנופחות׳ לבד.",
            ]
        if intent in {"workout_plan", "workout_log"}:
            provider_context["instruction_coaching_summary"] = [
                "הוראה: show-tell-do; cue קצר, brace ונשיפה.",
                "feedback: פחות עם עצמאות; setup/safety pins; חימום/cool 5-10 דק׳.",
            ]
            provider_context["weekly_structure_summary"] = [
                "2-3: גוף מלא/full-body; כל שריר פעמיים בשבוע.",
                "4: upper/lower או עליון/תחתון עם התאוששות.",
                "5-6: push/pull/legs רק אם לוגים והתאוששות מחזיקים.",
            ]
            provider_context["volume_progression_summary"] = [
                "נפח: 4->10+ סטים/שריר כשמתאוששים; specialization רק זמני.",
                "Progression: סוף טווח/2-for-2 -> 2-10%; plateau -> שנה משתנה.",
                "RIR/RPE: לרוב 1-3 RIR; failure מעט ובתרגיל בטוח.",
            ]
            provider_context["equipment_substitution_summary"] = [
                "החלף לפי דפוס וציוד: סקוואט/hinge/דחיפה/משיכה/ליבה.",
                "משקל גוף/גומיות/משקולות יד: row, לחיצת רצפה, סקוואט גביע, RDL.",
                "התקדם בלי עומס: קצב, טווח, עצירה, חד-צדדי, חזרות.",
            ]
            provider_context["session_structure_summary"] = [
                "סדר: Power/מורכבים לפני עזר/חד-מפרקי; טכני לפני עייפות.",
                "מנוחה: כוח 2-4 דק׳; היפרטרופיה/סבולת 0-90 שנ׳.",
                "tempo/circuit: 4/2/1; superset בזמן קצר בלי לפגוע בטכניקה.",
            ]
            provider_context["readiness_recovery_summary"] = [
                "ירוק: ביצועים/RPE ושינה יציבים -> התקדמות קטנה אחת.",
                "צהוב: שינה/סטרס/DOMS/RPE גבוה או מעט אכילה -> הורד 20-40%, תדלוק.",
                "מחלה/נסיעה: maintenance/גרסת מינימום; כאב חד/חזה/סחרחורת -> safety.",
            ]
            provider_context["load_prescription_summary"] = [
                "בחר עומס לפי RIR יעד; מתחילים שומרים מרווח.",
                "RPE גבוה/טכניקה יורדת -> שמור/הורד; קל מדי -> חזרות נקיות.",
                "יעד חזרות נקי -> 2-10% או קפיצה קטנה באימון הבא.",
                "e1RM הוא טווח מלוג נקי; בלי 1RM למתחיל/כאב.",
            ]
            provider_context["field_assessment_summary"] = [
                "בחר 1-3 baseline; לא אבחון.",
                "אירובי: 6MWT/2MST + RPE; השווה לעצמך.",
                "תפקוד/שיווי: chair stand/TUG עם תמיכה.",
                "RPE שיפור -> התקדמות; ירידה/כאב -> הורד.",
            ]
            provider_context["concurrent_training_summary"] = [
                "כוח+אירובי יחד; עדיפות מטרה קובעת סדר.",
                "מטרה עיקרית קודם: כוח לפני אירובי עצים.",
                "ריצה/impact מפריעים יותר; אופניים/הליכה עדיף.",
            ]
            provider_context["goal_programming_summary"] = [
                "כוח: 1-5 חזרות, מנוחה וטכניקה לפני עומס.",
                "היפרטרופיה: 6-12 חזרות ונפח בר התאוששות.",
                "סבולת: 12-20 חזרות, עומס קל-בינוני.",
                "Power: מעט חזרות איכותיות או 8-10 קלות.",
            ]
            provider_context["profile_programming_summary"] = [
                "מתחיל: יציבה/טכניקה ו-12-20 חזרות לפני עומס.",
                "מבוגר: 150 דק׳, 2 ימי כוח ושיווי; זמן/ציוד: מינימום מורכב.",
                "מטרה: כוח כבד; היפרטרופיה נפח; שומן כוח+אירובי; סבולת בסיס.",
            ]
            provider_context["limitation_adaptation_summary"] = [
                "ברך: הקטן טווח/עומס; סקוואט לקופסה או step-up נמוך.",
                "גב: low-impact, glute bridge/dead bug; בלי עומס מכאיב.",
                "כתף/שורש יד: שיפוע/אחיזה ניטרלית ושכמות/rotator cuff.",
            ]
            provider_context["special_population_summary"] = [
                "נוער: 60 דק׳ תנועה יומית; טכניקה ושליטה לפני עומס.",
                "הריון/אחרי לידה: 150 דק׳ מתון, כוח קל, התאמה מול ספק רפואי.",
                "כרוני/מוגבלות/מבוגר: פעל לפי יכולת; אירובי, כוח ושיווי משקל.",
            ]
            provider_context["cardio_programming_summary"] = [
                "בסיס 150-300 דק׳; מתחיל: ריצה-הליכה לפני רצוף.",
                "עצימות: talk test/RPE; ריצה קלה/Zone 1 לדיבור נוח.",
                "Zone 2 ונפח ריצה: הוסף זמן/קילומטרים לפני קצב.",
                "Zone 3/HIIT/עליות: מעט; חום/AQI/קור -> קצר/פנים.",
            ]
            provider_context["exercise_prescription_summary"] = [
                "FITT-VP: תדירות, עצימות, זמן, סוג, נפח והתקדמות.",
                "ספציפיות ועומס יתר הדרגתי, אך לא לפני טכניקה והתאוששות.",
                "ATP-PC: קפיצה/ספרינט לפני עייפות; נחיתה/וקטור לפי מטרה.",
            ]
            provider_context["periodization_summary"] = [
                "normal week: בצע ועקוב RPE; מיקרו/מזו לפי לוגים.",
                "deload/maintenance: פחות volume כשצריך.",
                "test week/taper/plateau רק עם מטרה ודפוס.",
            ]
            provider_context["cardiorespiratory_summary"] = [
                "אירובי לבריאות: 150-300 דקות מתון או 75-150 עצים בשבוע.",
                "עקוב עם talk test, RPE או דופק; רוב העבודה קלה-בינונית.",
                "אינטרוולים רק עם בסיס, התאוששות ומטרה ברורה.",
            ]
            provider_context["warmup_mobility_summary"] = [
                "חימום/dynamic warmup: 5-10 דק ואז specific/ramp.",
                "גמישות/static: 10-30 שנ חם; לא מבטיח מניעת DOMS.",
            ]
            provider_context["mobility_balance_summary"] = [
                "חימום דינמי: 5-10 דק׳ ואז הכנה לתנועות האימון.",
                "גמישות סטטית: 2-3 ימים/שבוע, 10-30 שנ׳ למתיחה, בלי כאב חד.",
                "שיווי משקל/neuromotor: 2-3 ימים/שבוע, 20-30 דק׳ או קצר עם תמיכה.",
            ]
            provider_context["assessment_tracking_summary"] = [
                "baseline: מטרה + כוח/אירובי/תנועה/היקפים רק אם משנים החלטה.",
                "2-4 שבועות: לוגים/RPE/כאב/פספוסים; משקל=מגמה, בחר פעולה אחת.",
            ]
            provider_context["program_adaptation_summary"] = [
                "התקדם רק כשהלוגים יציבים: טכניקה טובה, RPE סביר, בלי כאב; שנה משתנה אחד.",
                "RPE/עייפות גבוהים או ביצועים יורדים: שמור או הורד נפח/עצימות.",
                "plateau: בדוק עקביות ועומס, ואז שנה נפח/תרגיל/בלוק; פספוס: חזור קצר.",
            ]
            provider_context["exercise_library_summary"] = [
                "סקוואט/step-up: quads/ארבע ראשי+גלוטס, ברכיים; hinge/hip thrust/גשר: המסטרינג+גלוטס.",
                "דחיפה אופקית/אנכית: חזה/כתפיים/טרייספס; משיכה אופקית/אנכית: גב/שכמות/בייספס.",
                "ליבה/calf/זרועות: יציבה ושליטה לפני עומס.",
            ]
        if query and query.strip():
            retrieved = _retrieve_relevant_knowledge(context, query=query, intent=intent)
            if retrieved:
                provider_context["retrieved_knowledge"] = retrieved
                _fit_provider_context_budget(provider_context, intent)
        return provider_context


def _retrieve_relevant_knowledge(context: dict, *, query: str, intent: str | None = None) -> list[dict]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    candidates = []
    for table_key in _RETRIEVAL_PROTOCOL_KEYS:
        table = context.get(table_key)
        if not isinstance(table, dict):
            continue
        for entry_key, entry in table.items():
            if not isinstance(entry, dict):
                continue
            topic = f"{table_key}.{entry_key}"
            score = _score_knowledge_entry(
                topic=topic,
                table_key=table_key,
                entry_key=entry_key,
                entry=entry,
                query=query,
                query_tokens=query_tokens,
                intent=intent,
            )
            if score >= _MIN_RETRIEVAL_SCORE:
                candidates.append((score, topic, entry))

    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
    hits = []
    seen_tables = set()
    for _score, topic, entry in candidates:
        table_key = topic.split(".", 1)[0]
        if table_key in seen_tables and len(hits) >= 2:
            continue
        hit = _compact_knowledge_hit(topic, entry)
        if hit:
            hits.append(hit)
            seen_tables.add(table_key)
        if len(hits) >= _MAX_RETRIEVED_KNOWLEDGE:
            break
    return hits


def _score_knowledge_entry(
    *,
    topic: str,
    table_key: str,
    entry_key: str,
    entry: dict,
    query: str,
    query_tokens: set[str],
    intent: str | None,
) -> int:
    normalized_query = _normalize_text(query)
    entry_text = _flatten_text(entry)
    entry_tokens = _tokenize(f"{entry_key} {entry_text}")

    overlap = query_tokens & entry_tokens
    match_score = len(overlap)
    alias_matched = False

    for alias_topic, aliases in _TOPIC_ALIASES.items():
        if alias_topic != topic:
            continue
        for alias in aliases:
            if _normalize_text(alias) in normalized_query:
                match_score += _ALIAS_MATCH_BOOST
                alias_matched = True

    if not alias_matched and len(overlap) < 2:
        return 0

    score = match_score
    score += _INTENT_TABLE_BOOSTS.get(intent or "", {}).get(table_key, 0)
    if topic in _INTENT_TOPIC_BOOSTS.get(intent or "", set()):
        score += _INTENT_TOPIC_BOOST
    return score


def _compact_knowledge_hit(topic: str, entry: dict) -> dict:
    hit = {
        "topic": topic,
        "guidance": _pick_entry_items(
            entry,
            [
                "coach_position",
                "coaching_position",
                "rules",
                "substitution_rules",
                "planning_rules",
                "adjustment_rules",
                "signals",
                "coaching_goal",
                "evidence_notes",
            ],
            limit=2,
        ),
        "action": _pick_entry_items(
            entry,
            [
                "what_to_do_instead",
                "progression_options",
                "practical_notes",
                "adjustment_rules",
                "substitution_rules",
                "planning_rules",
                "decision_gate",
            ],
            limit=2,
        ),
        "avoid": _pick_entry_items(entry, ["avoid", "caution_notes"], limit=1),
        "sources": _pick_entry_items(entry, ["source_refs"], limit=2, max_chars=90),
    }
    return {key: value for key, value in hit.items() if value}


def _pick_entry_items(entry: dict, field_names: list[str], *, limit: int, max_chars: int = 220) -> list[str]:
    items = []
    seen = set()
    for field_name in field_names:
        for value in _flatten_values(entry.get(field_name)):
            text = _trim_text(value, max_chars=max_chars)
            if not text or text in seen:
                continue
            items.append(text)
            seen.add(text)
            if len(items) >= limit:
                return items
    return items


def _fit_provider_context_budget(provider_context: dict, intent: str | None) -> None:
    budget = _PROVIDER_CONTEXT_BUDGETS.get(intent or "", _PROVIDER_CONTEXT_BUDGETS["general_chat"])
    if len(str(provider_context)) <= budget:
        return

    for key in _OPTIONAL_PROVIDER_KEYS_BY_INTENT.get(intent or "", _OPTIONAL_PROVIDER_KEYS_BY_INTENT["general_chat"]):
        provider_context.pop(key, None)
        if len(str(provider_context)) <= budget:
            return

    retrieved = provider_context.get("retrieved_knowledge")
    while isinstance(retrieved, list) and len(retrieved) > 1 and len(str(provider_context)) > budget:
        retrieved.pop()


def _flatten_text(value) -> str:
    return " ".join(_flatten_values(value))


def _flatten_values(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        items = []
        for nested in value.values():
            items.extend(_flatten_values(nested))
        return items
    if isinstance(value, (list, tuple, set)):
        items = []
        for nested in value:
            items.extend(_flatten_values(nested))
        return items
    return [str(value)]


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(_normalize_text(text))
        if len(token) >= 2 and token not in _STOPWORDS
    }


def _normalize_text(text: str) -> str:
    return " ".join(str(text).casefold().split())


def _trim_text(text: str, *, max_chars: int) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "..."


def _source_organizations(sources: list[dict]) -> list[str]:
    organizations = []
    for source in sources:
        organization = source.get("organization")
        if organization and organization not in organizations:
            organizations.append(organization)
    return organizations


def _provider_source_organizations(sources: list[dict]) -> list[str]:
    organizations = _source_organizations(sources)
    preferred = [
        "ODPHP/HHS",
        "WHO",
        "ACSM",
        "CDC",
        "CDC Physical Activity Behavior Supports",
        "Community Guide Behavior Change Programs",
        "ACE",
        "ACE IFT / Mover Method",
        "NASM",
        "ISSN",
        "Academy of Nutrition and Dietetics",
        "NCI Implementation Intentions",
    ]
    compact = []
    for organization in preferred:
        if len(compact) >= 10:
            break
        if organization in organizations:
            compact.append(organization)
    for organization in organizations:
        if len(compact) >= 10:
            break
        if organization not in compact:
            compact.append(organization)
    return compact


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9\u0590-\u05FF]+")
_MIN_RETRIEVAL_SCORE = 4
_ALIAS_MATCH_BOOST = 8
_INTENT_TOPIC_BOOST = 2
_MAX_RETRIEVED_KNOWLEDGE = 3

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "how",
    "i",
    "is",
    "it",
    "me",
    "my",
    "or",
    "the",
    "to",
    "with",
    "בלי",
    "גם",
    "זה",
    "יש",
    "לא",
    "לי",
    "מה",
    "עם",
    "על",
    "או",
    "את",
    "איך",
    "אם",
    "אני",
    "של",
    "רק",
}

_RETRIEVAL_PROTOCOL_KEYS = [
    "common_fitness_myth_protocols",
    "equipment_substitution_protocols",
    "readiness_recovery_protocols",
    "advanced_recovery_readiness_protocols",
    "concurrent_training_protocols",
    "environment_training_risk_protocols",
    "supplement_education_protocols",
    "program_adaptation_protocols",
    "volume_progression_protocols",
    "load_prescription_protocols",
    "practical_nutrition_protocols",
    "body_composition_strategy_protocols",
    "daily_activity_neat_protocols",
    "warmup_cooldown_protocols",
    "exercise_setup_safety_protocols",
]

_TOPIC_ALIASES = {
    "common_fitness_myth_protocols.spot_reduction": [
        "בטן",
        "כרס",
        "שומן בבטן",
        "שומן נקודתי",
        "כפיפות בטן",
        "spot reduction",
        "belly fat",
        "stomach fat",
    ],
    "common_fitness_myth_protocols.soreness_and_quality": [
        "doms",
        "שרירים תפוסים",
        "כאב שרירים",
        "כאבי שרירים",
        "no pain no gain",
    ],
    "equipment_substitution_protocols.no_equipment": [
        "ללא ציוד",
        "בלי ציוד",
        "אין לי ציוד",
        "משקל גוף",
        "bodyweight",
        "no equipment",
    ],
    "equipment_substitution_protocols.bands": [
        "גומייה",
        "גומיות",
        "band",
        "bands",
        "resistance band",
        "חתירה",
        "row",
    ],
    "concurrent_training_protocols.general_health_blend": [
        "כוח ואירובי",
        "אירובי וכוח",
        "cardio and strength",
        "strength and cardio",
    ],
    "concurrent_training_protocols.strength_priority": [
        "cardio kills gains",
        "אירובי פוגע בשריר",
        "אירובי אחרי כוח",
    ],
    "environment_training_risk_protocols.heat_training_adjustment": [
        "חום",
        "שרב",
        "heat",
        "hot weather",
    ],
    "environment_training_risk_protocols.air_quality_adjustment": [
        "aqi",
        "זיהום אוויר",
        "איכות אוויר",
        "air quality",
    ],
    "environment_training_risk_protocols.cold_weather_adjustment": [
        "קור",
        "cold",
        "wind chill",
    ],
    "supplement_education_protocols.creatine_monohydrate": [
        "קריאטין",
        "creatine",
    ],
    "supplement_education_protocols.caffeine_preworkout": [
        "קפאין",
        "קפה",
        "pre workout",
        "pre-workout",
        "caffeine",
    ],
    "supplement_education_protocols.protein_powder": [
        "אבקת חלבון",
        "protein powder",
        "whey",
    ],
    "supplement_education_protocols.fat_burners_and_boosters": [
        "שורף שומן",
        "שורפי שומן",
        "fat burner",
        "testosterone booster",
    ],
    "advanced_recovery_readiness_protocols.doms_soreness_decision": [
        "doms",
        "שרירים תפוסים",
        "כאבי שרירים",
        "כאב שרירים",
    ],
}

_INTENT_TABLE_BOOSTS = {
    "general_chat": {
        "common_fitness_myth_protocols": 2,
        "daily_activity_neat_protocols": 1,
        "supplement_education_protocols": 1,
    },
    "workout_plan": {
        "equipment_substitution_protocols": 3,
        "volume_progression_protocols": 2,
        "load_prescription_protocols": 2,
        "concurrent_training_protocols": 2,
        "exercise_setup_safety_protocols": 1,
    },
    "workout_log": {
        "readiness_recovery_protocols": 3,
        "advanced_recovery_readiness_protocols": 3,
        "program_adaptation_protocols": 2,
        "load_prescription_protocols": 1,
    },
    "meal_log": {
        "practical_nutrition_protocols": 3,
        "body_composition_strategy_protocols": 2,
        "supplement_education_protocols": 1,
    },
    "meal_image": {
        "practical_nutrition_protocols": 3,
        "body_composition_strategy_protocols": 2,
    },
}

_INTENT_TOPIC_BOOSTS = {
    "workout_plan": {
        "equipment_substitution_protocols.no_equipment",
        "equipment_substitution_protocols.bands",
    },
    "workout_log": {
        "advanced_recovery_readiness_protocols.doms_soreness_decision",
        "readiness_recovery_protocols.soreness_doms",
    },
}

_PROVIDER_CONTEXT_BUDGETS = {
    "general_chat": 7000,
    "workout_plan": 8500,
    "workout_log": 8500,
    "meal_log": 10500,
    "meal_image": 10500,
}

_OPTIONAL_PROVIDER_KEYS_BY_INTENT = {
    "general_chat": [
        "fueling_risk_summary",
        "menstrual_cycle_summary",
        "environment_training_summary",
        "daily_activity_summary",
        "adherence_micro_summary",
        "supplement_education_summary",
        "body_recomposition_summary",
        "fitness_myths_summary",
    ],
    "workout_plan": [
        "field_assessment_summary",
        "mobility_balance_summary",
        "warmup_mobility_summary",
        "cardiorespiratory_summary",
        "periodization_summary",
        "special_population_summary",
        "profile_programming_summary",
        "goal_programming_summary",
    ],
    "workout_log": [
        "field_assessment_summary",
        "mobility_balance_summary",
        "warmup_mobility_summary",
        "cardiorespiratory_summary",
        "periodization_summary",
        "special_population_summary",
        "profile_programming_summary",
        "goal_programming_summary",
    ],
    "meal_log": [
        "body_recomposition_summary",
        "supplement_education_summary",
        "body_composition_summary",
        "practical_nutrition_summary",
    ],
    "meal_image": [
        "body_recomposition_summary",
        "supplement_education_summary",
        "body_composition_summary",
        "practical_nutrition_summary",
    ],
}


_BASE_CONTEXT = {
    "version": "2026-06-19",
    "scope": "general_wellness_coaching",
    "non_certification_note": "המערכת נותנת תמיכת כושר כללית ואינה טוענת להסמכה, אבחון או טיפול.",
    "professional_scope": [
        "המערכת אינה תחליף להסמכה מקצועית, בדיקה רפואית, פיזיותרפיה או ייעוץ דיאטטי קליני.",
        "המאמן הדיגיטלי תומך בהרגלים, תכנון כללי, מעקב והתאמות שמרניות לפי נתונים שמורים.",
    ],
    "trainer_skill_domains": [
        "הערכה ותשאול",
        "תכנות אימונים",
        "טכניקה ודפוסי תנועה",
        "פרוגרסיות ורגרסיות",
        "התאוששות וניהול עומס",
        "תזונה כללית סביב אימון",
        "שינוי התנהגות והתמדה",
        "בטיחות והפניה לאיש מקצוע",
    ],
    "rules": [
        "יעד שבועי שימושי למבוגרים: 150-300 דקות אירובי מתון או 75-150 עצים.",
        "אימוני כוח: כל קבוצות השרירים המרכזיות לפחות 2 ימים בשבוע.",
        "עקביות קודמת למורכבות; התוכנית הטובה היא זו שהמשתמש יבצע.",
        "התקדמות הדרגתית: טכניקה וטווח ללא כאב לפני עומס, חזרות או סטים.",
        "התאם מטרה, ניסיון, זמינות, ציוד, העדפות, התאוששות ומגבלות.",
        "למתחילים או חוזרים: התחל קטן, בנה הרגל, ואז העלה נפח או עצימות.",
        "משקל גוף, גומיות ומשקולות ביתיות יכולים להספיק כשיש עקביות ומאמץ.",
        "תזונה סביב אימון: אנרגיה מספקת, חלבון, פחמימות, מים והתאמה אישית.",
        "תזונה כללית: דפוס מגוון ומזונות עשירים ברכיבים לפי תרבות והעדפות.",
        "הערכות תזונה הן טווחים עם אי ודאות, לא דיוק מוחלט.",
    ],
    "assessment_questions": [
        "מה המטרה, הניסיון, הזמינות, הציוד, המיקום, מגבלות הכאב והעדפות האימון?",
        "מה המשתמש כבר מצליח לבצע בעקביות ומה בדרך כלל גורם לו לפספס?",
        "איזה אימון אפשר לבצע השבוע גם ביום עמוס, בלי להחמיר כאב או עייפות?",
    ],
    "programming_model": [
        "השתמש ב-FITT: תדירות, עצימות, זמן וסוג פעילות, ואז התאם לפי התאוששות ולוגים.",
        "לבריאות כללית, שלב אירובי, כוח, ניידות בסיסית ולפי צורך גם שיווי משקל.",
        "לכוח או שריר, תן נפח שניתן להתמיד בו, שמור 1-3 חזרות ברזרבה ברוב הסטים, והתקדם בהדרגה.",
        "אל תקפוץ לטכניקות מתקדמות לפני שיש בסיס של טכניקה, עקביות ולוגים.",
    ],
    "program_design_variables": [
        "ניתוח צרכים: מטרה, רמת ניסיון, ציוד, זמן, מגבלות, היסטוריית אימון, העדפות וחסמי התמדה.",
        "FITT-VP: תדירות, עצימות, זמן, סוג פעילות, נפח ודפוס התקדמות הם ידיות התכנון המרכזיות.",
        "בחירת תרגילים: כסה דפוסי תנועה מרכזיים ובחר וריאציה שהמשתמש שולט בה בלי כאב חד.",
        "סדר תרגילים: מיומנות/כוח ותרגילים מורכבים לפני עזר, בידוד או ליבה כשעייפות נמוכה יותר.",
        "עומס וחזרות: התאם לטווח המטרה וליכולת בפועל; השתמש ב-RPE/RIR כאשר אין נתוני 1RM בטוחים.",
        "נפח: העלה סטים או תדירות רק כאשר התאוששות, טכניקה ולוגים תומכים בכך.",
        "מנוחה: קצרה יותר לסבולת/זמן מוגבל, ארוכה יותר לכוח או תרגילים מורכבים כבדים.",
        "התקדמות: שנה משתנה אחד בכל פעם, ואז בדוק ביצוע, כאב, עייפות ועקביות.",
    ],
    "program_quality_audit_protocols": {
        "goal_fit_check": {
            "use_when": ["כאשר המשתמש מבקש חוות דעת על תוכנית קיימת או כשנוצרת תוכנית חדשה."],
            "coaching_goal": ["לוודא שהתוכנית משרתת את המטרה והפרופיל במקום להיראות מקצועית אבל לא שימושית."],
            "checks": [
                "בדוק התאמה בין מטרה, פרופיל, ניסיון, זמינות, ציוד, מגבלות והעדפות.",
                "בדוק אם התוכנית נותנת stimulus מתאים למטרה: כוח, hypertrophy, סבולת, בריאות כללית או עקביות.",
                "בדוק אם השבוע הראשון בר ביצוע גם ביום עמוס, לא רק בתרחיש אידיאלי.",
            ],
            "pass_signals": [
                "המטרה ברורה וכל יום אימון תורם לה.",
                "יש גרסת בסיס שאפשר לבצע עם הציוד והזמן הקיימים.",
            ],
            "adjust_if_missing": [
                "ציין את הפער המרכזי והצע שינוי אחד: פחות נפח, תרגיל מתאים יותר, או חלוקת ימים פשוטה יותר.",
                "אם חסר מידע קריטי, שאל שאלה אחת בלבד לפני שינוי גדול.",
            ],
            "avoid": ["לא להציג תוכנית עמוסה כטובה רק כי יש בה הרבה תרגילים."],
            "source_refs": ["NSCA Guide to Program Design", "ACE IFT Program Design"],
        },
        "weekly_structure_balance": {
            "use_when": ["כאשר בודקים חלוקת ימים, full body, upper/lower או split."],
            "coaching_goal": ["לוודא שהתדירות והפיזור השבועי מאפשרים עקביות והתאוששות."],
            "checks": [
                "בדוק תדירות כוח ריאלית: לרוב 2-3 אימוני כוח בשבוע הם בסיס חזק למתחילים ולחוזרים.",
                "בדוק אם כל קבוצות השריר המרכזיות מקבלות גירוי לפחות פעמיים בשבוע כאשר זה מתאים למטרה ולזמינות.",
                "בדוק אם יש ימים קשים רצופים לאותו אזור בלי התאוששות מספקת.",
            ],
            "pass_signals": [
                "יש פיזור עומס ברור בין ימים כבדים, קלים או מנוחה.",
                "המשתמש יכול להשלים את השבוע גם אם יום אחד משתבש.",
            ],
            "adjust_if_missing": [
                "העבר לתוכנית full body קצרה יותר או upper/lower פשוט כאשר split מורכב פוגע בעקביות.",
                "הוסף יום מנוחה או הורד נפח אם יש עומס חוזר על אותו אזור.",
            ],
            "avoid": ["לא להוסיף עוד יום אימון לפני שמוודאים שהימים הקיימים מבוצעים."],
            "source_refs": ["ACSM 2026 Resistance Training Position Stand", "ACSM Progression Models in Resistance Training"],
        },
        "movement_pattern_coverage": {
            "use_when": ["כאשר בודקים אם תוכנית כוח מכסה את הגוף באופן שימושי."],
            "coaching_goal": ["לזהות פערי תנועה בלי להפוך את התוכנית לצ'קליסט ארוך."],
            "checks": [
                "בדוק כיסוי של squat, hinge, push, pull, core/carry ולפי צורך צעד או עבודה חד-צדדית.",
                "בדוק איזון דחיפה/משיכה ועבודה לרגליים בלי כפילות מיותרת.",
                "בדוק אם חסר דפוס תנועה מרכזי ביחס למטרה, ציוד או מגבלה.",
            ],
            "pass_signals": [
                "רוב הדפוסים המרכזיים מופיעים לאורך השבוע.",
                "יש וריאציות שהמשתמש יכול לבצע בטכניקה יציבה וללא כאב חד.",
            ],
            "adjust_if_missing": [
                "הוסף תרגיל אחד לדפוס החסר במקום להאריך את כל האימון.",
                "החלף כפילות בתרגיל שמכסה פער אמיתי, למשל row במקום עוד press.",
            ],
            "avoid": ["לא להכריח כל דפוס בכל אימון אם הזמן או ההתאוששות לא מאפשרים."],
            "source_refs": ["NSCA Guide to Program Design", "NASM Exercise Library"],
        },
        "volume_recovery_audit": {
            "use_when": ["כאשר יש עייפות, DOMS ממושך, ירידה בביצועים או תוכנית שנראית עמוסה מדי."],
            "coaching_goal": ["להתאים נפח לעצימות, RPE, שינה והתאוששות בפועל."],
            "checks": [
                "בדוק סטים קשים בשבוע, RPE/RIR, זמן מנוחה, שינה, DOMS, כאב, ביצועים והתאוששות בלוגים.",
                "בדוק אם יש יותר מדי עבודה קרובה לכשל או יותר מדי תרגילי עזר ביחס למטרה.",
                "בדוק אם המשתמש מחלים תוך 24-48 שעות מאימון רגיל.",
            ],
            "pass_signals": [
                "המשתמש מסיים אימונים עם תחושת מאמץ מתאימה ולא נשבר לשאר השבוע.",
                "ביצועים יציבים או משתפרים בלי כאב חריג.",
            ],
            "adjust_if_missing": [
                "הורד 1-2 סטים מתרגיל מרכזי או השאר 1-3 RIR ברוב הסטים.",
                "שמור את התרגילים המרכזיים והורד קודם אביזרים או עבודה כפולה.",
            ],
            "avoid": ["לא להניח שיותר נפח תמיד טוב יותר; לא להפוך DOMS חזק למדד הצלחה."],
            "source_refs": ["ACSM Training Load Monitoring", "NSCA Overtraining and Recovery"],
        },
        "progression_logic_check": {
            "use_when": ["כאשר בודקים אם התוכנית באמת יכולה להתקדם לאורך שבועות."],
            "coaching_goal": ["לוודא שיש progressive overload פשוט, מדיד ולא אגרסיבי."],
            "checks": [
                "בדוק האם יש כלל ברור להעלאת עומס, חזרות, סטים, טווח תנועה, tempo או מורכבות.",
                "בדוק שהכלל משנה משתנה אחד בכל פעם ולא כמה משתנים יחד.",
                "בדוק שיש שער התקדמות: טכניקה יציבה, RPE מתאים, אין כאב חד והלוגים תומכים.",
            ],
            "pass_signals": [
                "המשתמש יודע בדיוק מתי להעלות ומתי לשמור.",
                "ההתקדמות קטנה מספיק כדי להתמיד בה לאורך זמן.",
            ],
            "adjust_if_missing": [
                "קבע כלל אחד: למשל כשכל הסטים בטווח העליון עם RPE 7-8, מעלים מעט עומס.",
                "אם יש עייפות או כאב, שמור עומס או בצע regression במקום להעלות.",
            ],
            "avoid": ["לא לשנות עומס, סטים ותדירות באותו שבוע בלי סיבה חזקה."],
            "source_refs": ["ACSM Progression Models in Resistance Training", "NASM OPT Model"],
        },
        "exercise_selection_fit": {
            "use_when": ["כאשר תרגיל לא מתאים לציוד, לרמה, לכאב או להעדפות."],
            "coaching_goal": ["לבחור וריאציה שמשרתת את אותו דפוס וניתנת לביצוע עקבי."],
            "checks": [
                "בדוק ציוד זמין, ניסיון, טכניקה, טווח תנועה, כאב והאם יש וריאציה פשוטה יותר.",
                "בדוק אם התרגיל המרכזי מתאים למטרה או רק נראה מתקדם.",
                "בדוק אם אפשר לשמור דפוס תנועה דומה עם תרגיל בטוח ונגיש יותר.",
            ],
            "pass_signals": [
                "התרגיל ניתן לביצוע בטווח נשלט וללא כאב חד.",
                "יש חלופה ברורה אם הציוד חסר או הטכניקה לא יציבה.",
            ],
            "adjust_if_missing": [
                "החלף לוריאציה קרובה: box squat, goblet squat, hip hinge עם תיק, row בגומייה או push-up בשיפוע.",
                "הורד מורכבות לפני שמורידים את כל דפוס התנועה.",
            ],
            "avoid": ["לא להיצמד לתרגיל ספציפי כאשר וריאציה אחרת תיתן אימון טוב ובטוח יותר."],
            "source_refs": ["NSCA Guide to Program Design", "ACE Exercise Library"],
        },
        "adherence_feasibility_check": {
            "use_when": ["כאשר התוכנית טובה על הנייר אבל המשתמש מפספס או מרגיש מוצף."],
            "coaching_goal": ["להפוך תוכנית לאפשרית לביצוע בפועל, לא מושלמת תאורטית."],
            "checks": [
                "בדוק זמן אמיתי לאימון, מספר תרגילים, הכנה, ציוד, אנרגיה וחסמי התמדה.",
                "בדוק אם קיימת גרסת מינימום של 10-20 דקות ליום עמוס.",
                "בדוק אם יש יותר מדי החלטות למשתמש בזמן האימון.",
            ],
            "pass_signals": [
                "האימון ברור, קצר מספיק ונראה אפשרי גם בשבוע רגיל.",
                "יש fallback מוגדר: מלא, קצר או התאוששותי.",
            ],
            "adjust_if_missing": [
                "צמצם לתרגילים המרכזיים והוסף גרסת מינימום במקום לבנות תוכנית חדשה.",
                "הצע שינוי אחד לשבוע הקרוב ובדוק לוגים לפני הרחבה.",
            ],
            "avoid": ["לא להעניש פספוס בתוספת נפח; לא להעמיס שאלות או הוראות."],
            "source_refs": ["ACE IFT Program Design", "Community Guide Behavior Change Programs"],
        },
        "safety_scope_check": {
            "use_when": ["כאשר יש כאב, פציעה, dizziness, מצב רפואי או בקשה שחורגת מכושר כללי."],
            "coaching_goal": ["לתת ביקורת תוכנית שמרנית בלי לאבחן או לטפל."],
            "checks": [
                "בדוק כאב חד, כאב מחמיר, red flag, סחרחורת, קוצר נשימה חריג או מגבלה חדשה.",
                "בדוק אם התוכנית דורשת עומס, כשל או טווח תנועה שאינם מתאימים למידע הקיים.",
                "בדוק אם צריך להפנות לאיש מקצוע במקום לתת התאמה אגרסיבית.",
            ],
            "pass_signals": [
                "אין red flags והמשתמש מבצע בטווח נוח.",
                "יש התאמות שמרניות לכאב לא חד או חוסר נוחות.",
            ],
            "adjust_if_missing": [
                "עצור המלצת עומס והצע תנועה קלה/וריאציה נוחה רק אם אין סימן מסוכן.",
                "בכאב חד, מחמיר או סימפטום חריג: הפנה לאיש מקצוע מוסמך.",
            ],
            "avoid": ["לא לתת אבחון, טיפול, הבטחת ריפוי או הוראות רפואיות."],
            "source_refs": ["ACSM Guidelines for Exercise Testing and Prescription", "NSCA Professional Standards"],
        },
    },
    "movement_patterns": [
        "סקוואט/כריעה, hinge/כפיפה מהירך, דחיפה, משיכה, נשיאה/ליבה, וצעד/לאנג' לפי יכולת.",
        "בחר וריאציות לפי ציוד וכאב: משקל גוף, גומיות, משקולות, מכונות או טווח תנועה מוקטן.",
        "תרגיל טוב למשתמש הוא כזה שהוא מבצע בטווח נשלט, ללא כאב חד, ובצורה שניתן להתקדם בה.",
    ],
    "exercise_science_foundations": {
        "energy_systems": {
            "use_when": ["כאשר בוחרים מנוחה, עצימות, סוג אינטרוול, כוח מתפרץ או אירובי."],
            "coaching_goal": ["לחבר משך/עצימות למערכת האנרגיה הדומיננטית בלי להפוך את התשובה לשיעור ביוכימיה."],
            "rules": [
                "ATP-PC/phosphagen דומיננטי במאמצים קצרים ועצימים מאוד, בערך 1-30 שניות: קפיצה, ספרינט קצר או סט כוח כבד.",
                "המערכת הגליקוליטית/glycolytic דומיננטית יותר במאמץ קשה של בערך 30 שניות עד 3 דקות.",
                "המערכת האירובית/aerobic תומכת במאמץ ארוך יותר, התאוששות בין סטים ויכולת לבצע נפח לאורך אימון.",
                "כל המערכות עובדות יחד; לא מוכרים למשתמש 'אימון למערכת אחת' כאילו האחרות כבויות.",
            ],
            "examples": [
                "כוח מתפרץ: מעט חזרות, איכות גבוהה ומנוחה ארוכה יותר.",
                "אינטרוול של דקה-שתיים ירגיש גליקוליטי יותר ודורש התאוששות מתוכננת.",
            ],
            "avoid": ["לא לקשור שריפת שומן למערכת אנרגיה אחת; לא להשתמש בז'רגון לפני שהוא משנה החלטת אימון."],
            "source_refs": ["ACE Energy Pathways", "NASM Aerobic Energy Pathway"],
        },
        "planes_and_patterns": {
            "use_when": ["כאשר בוחרים תרגילים, משלימים תוכנית או מסבירים למה חסר דפוס תנועה."],
            "coaching_goal": ["להשתמש במישורי תנועה כדי לבנות תוכנית מאוזנת יותר בלי להעמיס אנטומיה."],
            "rules": [
                "sagittal/frontal/transverse הם מישורי תנועה: קדימה-אחורה, צד-לצד וסיבוב.",
                "סקוואט, hinge, לחיצה וחתירה רבים הם בעיקר sagittal; צעד צדדי עובד יותר frontal; רוטציה/anti-rotation עובדים transverse.",
                "רוב המשתמשים לא צריכים שיעור מלא במישורים; הם צריכים לדעת אם התוכנית מכסה דפוסים שימושיים.",
            ],
            "examples": [
                "התוכנית שלך חזקה ב-sagittal, אז נוסיף lateral lunge או carry צדדי במינון קטן.",
                "ליבה לא חייבת להיות כפיפות בטן; anti-rotation מכסה צורך אחר.",
            ],
            "avoid": ["לא להחליף תרגילים טובים רק כדי 'לגעת בכל מישור' אם המטרה והזמן לא דורשים זאת."],
            "source_refs": ["NASM Planes of Motion", "Movement Pattern Definitions Review"],
        },
        "joint_actions_and_levers": {
            "use_when": ["כאשר מסבירים למה שינוי טווח, זווית, אחיזה או מנח משנה קושי."],
            "coaching_goal": ["לתת הסבר פשוט על מפרקים ומנופים שמוביל לווריאציה טובה יותר."],
            "rules": [
                "joint action כמו flexion/extension, abduction/adduction או rotation עוזר לזהות מה התרגיל באמת מאמן.",
                "מנוף/lever arm ארוך יותר בדרך כלל מעלה קושי; קיצור מנוף או טווח יכול להפוך תרגיל לנגיש.",
                "שינוי זווית הגוף, גובה ידית או מיקום משקל משנה עומס בלי להחליף בהכרח את הדפוס.",
            ],
            "examples": [
                "שכיבת סמיכה בשיפוע מקצרת את המנוף ומפחיתה עומס, ועדיין שומרת דפוס דחיפה.",
                "הרחקת כתף עם יד ישרה קשה יותר מאותה תנועה עם מרפק כפוף.",
            ],
            "avoid": ["לא להשתמש במונחים אנטומיים כדי להישמע חכם; ההסבר חייב לעזור למשתמש לבצע טוב יותר."],
            "source_refs": ["ACE Essentials of Exercise Science", "NASM Squat Biomechanics"],
        },
        "force_vector_and_stability": {
            "use_when": ["כאשר מתאימים ציוד, כבל, גומייה, משקולת יד, מכונה או וריאציה יציבה יותר."],
            "coaching_goal": ["להסביר שכיוון ההתנגדות והיציבות משנים את התרגיל, לא רק המשקל הכתוב."],
            "rules": [
                "וקטור עומס/כיוון התנגדות קובע איפה התרגיל קשה: משקולת חופשית לרוב נגד כבידה, כבל/גומייה לפי כיוון המשיכה.",
                "בסיס תמיכה רחב, יד תמיכה או מכונה יציבה יכולים להוריד דרישת שיווי משקל כדי להתמקד בשריר/דפוס.",
                "יותר אי-יציבות אינה בהכרח טוב יותר; למתחיל או לעומס גבוה יציבות יכולה לשפר ביצוע ובטיחות.",
            ],
            "examples": [
                "חתירה בכבל וחתירה עם משקולת אינן זהות לגמרי כי כיוון המשיכה שונה.",
                "אם הכתף לא מרגישה יציבה, נבחר מכונה או אחיזה ניטרלית לפני עוד עומס.",
            ],
            "avoid": ["לא להציג תרגיל לא יציב כמתקדם אוטומטית; לא להוסיף balance כאשר המטרה היא כוח נקי."],
            "source_refs": ["NSCA Guide to Program Design", "NASM Exercise Library"],
        },
        "fatigue_and_skill_order": {
            "use_when": ["כאשר מסדרים אימון או מחליטים אם להמשיך סטים כשעייפות עולה."],
            "coaching_goal": ["לשמור תרגילים טכניים ועצימים לפני עייפות שמפרקת מהירות או טכניקה."],
            "rules": [
                "עייפות מורידה מהירות, שליטה וטכניקה; לכן power/skill ותרגילים מורכבים באים לפני עזר ובידוד.",
                "אם טכניקה יורדת, עדיף להוריד עומס/נפח או לעבור לווריאציה יציבה מאשר 'לסיים בכל מחיר'.",
                "אימון קשה יכול להיות מתוכנן, אבל ירידת איכות חוזרת בלוגים היא אות להתאמת עומס.",
            ],
            "examples": [
                "קפיצות או clean וריאציה קלה יבואו לפני סטים כבדים או עייפות גבוהה.",
                "אם RPE קופץ והטווח מתקצר, הסט הבא יהיה קל יותר או יוחלף בתרגיל יציב.",
            ],
            "avoid": ["לא לשים תרגיל מיומנות בסוף אימון מתיש; לא למדוד הצלחה לפי טכניקה שהתפרקה."],
            "source_refs": ["HPRC / NSCA Exercise Order", "NSCA Guide to Program Design"],
        },
        "motor_learning_basics": {
            "use_when": ["כאשר המשתמש לומד תרגיל, מתקן טכניקה או מקבל cue מרחוק."],
            "coaching_goal": ["לתת cue אחד שימושי ולהעדיף תרגול בטוח על עומס קוגניטיבי."],
            "rules": [
                "external cue לרוב עדיף ללמידה: 'דחוף את הרצפה' במקום רק 'כווץ ארבע ראשי'.",
                "תן cue אחד או שניים לכל היותר, ואז שנה וריאציה/טווח/עומס אם זה לא עובד.",
                "למידת תנועה דורשת חזרות איכותיות ומשוב קצר; לא מתקנים הכול בבת אחת.",
            ],
            "examples": [
                "בסקוואט: 'דחוף את הרצפה והרשה לברכיים לעקוב אחרי כף הרגל'.",
                "בהינג׳: 'סגור דלת עם האגן' עובד טוב יותר מהסבר ארוך על שרירים.",
            ],
            "avoid": ["לא לתת רשימת cues ארוכה; לא לנסות לאבחן טכניקה מדויקת בלי וידאו או נתונים."],
            "source_refs": ["NASM Cueing Clients", "Attentional Focus Resistance Training Review"],
        },
    },
    "speed_agility_plyometric_protocols": {
        "landing_mechanics_foundation": {
            "use_when": ["כאשר המשתמש מבקש קפיצות, כוח מתפרץ, agility או חזרה לספרינטים."],
            "coaching_goal": ["לבנות שליטה בנחיתה לפני שמעלים גובה, מהירות או שינויי כיוון."],
            "rules": [
                "נחיתה טובה היא שקטה ורכה: כף רגל מלאה, ברכיים עוקבות אחרי כף הרגל, אגן וחזה בשליטה.",
                "המשתמש צריך לעצור יציב אחרי החזרה לפני שמוסיפים רצף, גובה או תגובה מהירה.",
                "cue שימושי: 'נחות שקט, בולם נמוך, ואז דוחף שוב'.",
            ],
            "progression_gate": ["הנחיתות נראות דומות מתחילת הסט עד סופו ואין כאב חד או איבוד שליטה."],
            "regressions": ["נחיתה מסקוואט קטן", "step-down נמוך", "קפיצה קטנה במקום עם עצירה"],
            "avoid": ["לא להוסיף box jump, drop jump או קפיצה חד-צדדית לפני נחיתה יציבה בשתי רגליים."],
            "source_refs": ["NASM Plyometric Technique", "ACE Plyometric Guidelines"],
        },
        "low_level_plyometric_entry": {
            "use_when": ["כאשר מתחיל או חוזר רוצה קפיצות בלי בסיס קפיצה מסודר."],
            "coaching_goal": ["לתת חשיפה פליאומטרית קטנה שאינה הופכת לאימון עייפות."],
            "rules": [
                "התחל בקפיצות נמוכות: pogo hops, סקיפים קלים, קפיצה במקום או דילוג קצר.",
                "מעט סטים ומעט מגעים עם הרצפה מספיקים בהתחלה; כל חזרה צריכה להיות מהירה ונקייה.",
                "שתי רגליים לפני רגל אחת, גובה נמוך לפני גובה גבוה, קצב נשלט לפני רצף מהיר.",
            ],
            "progression_gate": ["המשתמש מסיים כשהקפיצות עדיין חדות והנחיתה שקטה, לא כשהוא מותש."],
            "regressions": ["calf raise מהיר", "march/skip במקום", "step-up מהיר בלי קפיצה"],
            "avoid": ["לא להפוך פליאומטריקה ל-HIIT; עייפות גבוהה מורידה איכות וקואורדינציה."],
            "source_refs": ["Current Concepts of Plyometric Exercise", "NASM Plyometric Technique"],
        },
        "jump_training_progression": {
            "use_when": ["כאשר בונים תוכנית קפיצות או מוסיפים power לתוכנית כוח."],
            "coaching_goal": ["להתקדם במשתנה אחד כדי לשמור איכות ולנהל עומס impact."],
            "rules": [
                "שנה משתנה אחד בכל פעם: נפח מגעים, גובה, מרחק, מהירות, חד-צדדי או מורכבות.",
                "התקדמות פשוטה: קפיצה במקום -> קפיצה קדימה -> קפיצה לרצף -> קפיצה חד-צדדית רק אם השליטה נשמרת.",
                "Box Jump - קפיצה לקופסה מתאים כשהגובה נוח; יורדים בהליכה ולא בקפיצה חוזרת.",
            ],
            "progression_gate": ["אין רעש נחיתה חריג, אין קריסת ברכיים ואין ירידה באיכות בין סטים."],
            "regressions": ["הורדת גובה", "עצירה בין חזרות", "מעבר לשתי רגליים", "הפחתת נפח מגעים"],
            "avoid": ["לא להעלות גובה ונפח יחד; לא להשתמש בגובה קופסה שמחייב משיכת ברכיים בלי שליטה."],
            "source_refs": ["ACE Plyometric Guidelines", "Current Concepts of Plyometric Exercise"],
        },
        "sprint_acceleration_exposure": {
            "use_when": ["כאשר המשתמש רוצה מהירות, ספרינט קצר או שיפור האצה."],
            "coaching_goal": ["לתת חשיפה קצרה ואיכותית להאצה בלי להפוך כל ריצה לספרינט."],
            "rules": [
                "ספרינט/האצה הם מאמץ ATP-PC קצר: מעט חזרות, מרחק קצר ומנוחה מלאה יחסית.",
                "התחל ביציאות קצרות של 5-10 שניות או 10-20 מטר, עם דגש על דחיפה חזקה וצעדים ראשונים נשלטים.",
                "מנוחה צריכה לשמר מהירות; אם החזרה הבאה איטית או מפוזרת, עוצרים או מורידים נפח.",
            ],
            "progression_gate": ["המהירות נשארת חדה, אין כאב חד, והמשתמש לא מאבד טכניקה בסוף החזרה."],
            "regressions": ["האצה בעלייה קלה", "march/skip טכני", "ריצה מהירה חלקית במקום ספרינט מלא"],
            "avoid": ["לא לתת ספרינטים מקסימליים למשתמש חסר בסיס ריצה או עם כאב/פציעה לא פתורים."],
            "source_refs": ["NSCA Acceleration and Deceleration Mechanics", "ACSM Distance Running Habits"],
        },
        "deceleration_change_of_direction": {
            "use_when": ["כאשר מתכנתים שינוי כיוון, משחקי ספורט, agility או ריצה עם בלימות."],
            "coaching_goal": ["ללמד בלימה לפני שינוי כיוון מהיר, כדי שהמהירות תהיה נשלטת."],
            "rules": [
                "בלימה קודמת לשינוי כיוון: כמה צעדים קצרים, מרכז כובד נמוך, ואז דחיפה לכיוון החדש.",
                "התחל בבלימה מתוכננת בקו ישר, המשך לחיתוך בזווית קטנה, ורק אז change of direction חד יותר.",
                "איכות טובה נראית כמו עצירה בשליטה, לא החלקה, קריסת ברך או איבוד שיווי משקל.",
            ],
            "progression_gate": ["המשתמש בולם ונשאר יציב בשלושה ניסיונות רצופים לפני שמעלים מהירות או זווית."],
            "regressions": ["walk-through", "shuffle איטי", "בלימה לקונוס בלי שינוי כיוון"],
            "avoid": ["לא להכניס חיתוכים חדים או בלימות מקסימליות בסוף אימון כשהרגליים עייפות."],
            "source_refs": ["NSCA Acceleration and Deceleration Mechanics", "NSCA Agility Movement Classification"],
        },
        "agility_reactive_progression": {
            "use_when": ["כאשר המשתמש מבקש זריזות, ספורט או תגובה לסימן."],
            "coaching_goal": ["להבדיל בין שינוי כיוון מתוכנן לבין זריזות עם תגובה אמיתית."],
            "rules": [
                "Agility אמיתי כולל תגובה ל-cue או stimulus: צבע, קול, כיוון יד או תנועה של בן זוג.",
                "מתחילים בדפוס מתוכנן, מוסיפים cue אחד צפוי, ואז cue פחות צפוי רק כשהשליטה נשמרת.",
                "המטרה היא תגובה חדה ושליטה; לא עוד סבב עייפות.",
            ],
            "progression_gate": ["המשתמש מגיב בלי לאבד מנח, בלי להחליק ובלי שהקצב מתפרק."],
            "regressions": ["ladder איטי כקואורדינציה", "shuffle לפי סימן אחד", "תגובה בהליכה מהירה"],
            "avoid": ["לא לקרוא לכל ladder drill 'agility' אם אין החלטה או תגובה לסימן."],
            "source_refs": ["NSCA Agility Movement Classification", "ACE Plyometric Guidelines"],
        },
        "power_session_order_and_rest": {
            "use_when": ["כאשר משלבים power, קפיצות, ספרינטים או שינויי כיוון באימון כוח."],
            "coaching_goal": ["למקם עבודה עצבית/מהירה בתחילת האימון ולשמור מנוחה שמאפשרת איכות."],
            "rules": [
                "קפיצות, ספרינטים וזריזות באים בתחילת האימון או לפני עייפות; מנוחה מספיקה חשובה יותר משריפה.",
                "בסטים קצרים של power, עצור כשהמהירות או הנחיתה יורדות, גם אם נשארו חזרות בתוכנית.",
                "אפשר לשלב 2-4 סטים קצרים אחרי חימום דינמי ולפני strength work אם זה משרת את המטרה.",
            ],
            "progression_gate": ["כל סט נראה חד כמו הראשון, והעבודה לא פוגעת בתרגילי הכוח המרכזיים."],
            "regressions": ["פחות סטים", "יותר מנוחה", "תרגיל פחות מורכב", "החלפה ל-med ball throw או קפיצה נמוכה"],
            "avoid": ["לא לשים drop jumps, ספרינטים או שינויי כיוון מהירים אחרי circuit מתיש."],
            "source_refs": ["HPRC / NSCA Exercise Order", "Current Concepts of Plyometric Exercise"],
        },
        "impact_volume_and_surface": {
            "use_when": ["כאשר מתכננים נפח קפיצות, משטח אימון או התאמה למשתמש כבד/חוזר/עייף."],
            "coaching_goal": ["לנהל עומס impact בלי להציג מספרי נחיתות כמדע מדויק מדי למשתמש כללי."],
            "rules": [
                "ספר מגעים/נחיתות בקירוב ושמור נפח נמוך בהתחלה; איכות ומנוחה קודמות לעוד חזרות.",
                "משטח יציב עם מעט ספיגה עדיף על רצפה מחליקה, דשא לא אחיד או בטון קשה לקפיצות רבות.",
                "אם מופיעים כאב חד, רעש נחיתה, כבדות או איבוד קצב, הורד נפח/גובה או עבור לתרגיל low-impact.",
            ],
            "progression_gate": ["אין עלייה בכאב או עייפות חריגה ביום שאחרי, והלוגים מראים התאוששות סבירה."],
            "regressions": ["אופניים/חתירה לאימפקט נמוך", "קפיצות נמוכות", "פחות מגעים", "יותר ימי התאוששות"],
            "avoid": ["לא להוסיף נפח קפיצות ביום עם כאב שוק/ברך/קרסול או אחרי עלייה חדה בריצה."],
            "source_refs": ["Current Concepts of Plyometric Exercise", "Running Injury Training Parameters Review"],
        },
    },
    "progression_regression": [
        "בחר פרוגרסיה או רגרסיה לפי ביצוע: הוסף חזרות/סטים/עומס רק כשהטכניקה יציבה, והקטן טווח/עומס/מורכבות כשיש כאב, עייפות או כשל עקביות.",
        "אם המשתמש פספס אימון, אל תכפיל עומס; חזור לתוכנית או תן גרסה קצרה.",
    ],
    "deload_rules": [
        "אם ביצועים יורדים במשך כמה אימונים, שינה ירודה, RPE גבוה חריג או כאבי שרירים מתמשכים: הורד נפח או עצימות זמנית.",
        "בכאב חד, סימפטום מסוכן או החמרה מתמשכת: עצור את התרגיל והפעל גבולות בטיחות במקום deload רגיל.",
        "Deload שימושי יכול להיות 20-40 אחוז פחות סטים/עומס, או שבוע טכני קל יותר עם אותם דפוסי תנועה.",
        "אל תעלה עומס, נפח, תדירות ומורכבות בבת אחת; קשה לדעת מה עבד ומה שבר התאוששות.",
    ],
    "load_monitoring_rules": [
        "עקוב אחרי עומס חיצוני: תרגילים, סטים, חזרות, משקל, מנוחות, משך ותדירות.",
        "עקוב אחרי עומס פנימי: RPE או sRPE, עייפות, שינה, מוטיבציה, כאבי שרירים ותחושת התאוששות.",
        "ירידה בביצועים יחד עם עייפות, חוסר חשק או כאבי שרירים מתמשכים מצביעה על צורך בהתאמת עומס.",
        "פער בין עומס חיצוני רגיל לבין עומס פנימי גבוה יכול לנבוע משינה, תזונה, סטרס או התאוששות חלשה.",
        "החלטות אימון צריכות להתבסס על רצף לוגים ולא על אימון בודד, אלא אם יש כאב חד או סימפטום חריג.",
    ],
    "readiness_recovery_protocols": {
        "green_day_progress": {
            "use_when": ["לפני אימון מתוכנן או אחרי לוגים שמראים התקדמות יציבה."],
            "coaching_goal": ["להתקדם מעט כאשר הגוף והלוגים תומכים בכך, בלי להעלות כמה משתנים יחד."],
            "signals": [
                "ביצועים יציבים או עולים, RPE נשלט, שינה ואנרגיה סבירות ואין כאב חד.",
                "המשתמש השלים כמה אימונים דומים בלי ירידה בהתאוששות.",
            ],
            "adjustment_rules": [
                "בחר התקדמות קטנה אחת: חזרה, סט, עומס קל, טווח או קצב איכותי יותר.",
                "השאר 1-3 RIR ברוב הסטים כדי לא להפוך יום טוב לעומס יתר.",
            ],
            "avoid": ["לא להעלות עומס, נפח, תדירות ומורכבות באותו שבוע רק כי אימון אחד הרגיש טוב."],
        },
        "yellow_day_adjustment": {
            "use_when": ["כאשר יש עייפות, RPE גבוה, שינה חלשה, סטרס גבוה או ירידה בביצועים בלי סימני חירום."],
            "coaching_goal": ["לשמור רצף אימונים תוך הורדת עומס זמנית במקום להפסיק לגמרי או לדחוף בכוח."],
            "signals": [
                "RPE גבוה מהרגיל, ביצועים יורדים, עייפות נמשכת או עומס פנימי גבוה ביחס לעומס החיצוני.",
                "שינה חלשה או סטרס גבוה ביומיים האחרונים.",
            ],
            "adjustment_rules": [
                "שמור את דפוסי התנועה אבל הורד 20-40% נפח או עומס, או קצר את האימון לגרסה טכנית.",
                "הארך מנוחות, השאר יותר RIR, ובחר וריאציות יציבות יותר.",
            ],
            "avoid": ["לא לפרש יום צהוב כחוסר משמעת; לא לפתור התאוששות חלשה בעוד HIIT או עוד סטים."],
        },
        "soreness_doms": {
            "use_when": ["כאשר המשתמש מדווח על DOMS או כאבי שרירים אחרי אימון קודם."],
            "coaching_goal": ["להבדיל בין כאבי שרירים רגילים לבין כאב שמצריך שינוי משמעותי או safety."],
            "signals": [
                "DOMS או כאבי שרירים מפושטים שמופיעים 24-48 שעות אחרי אימון ולא מחמירים בחדות.",
                "טווח תנועה מעט נוקשה אבל אין כאב חד, נפיחות חריגה או אובדן תפקוד.",
            ],
            "adjustment_rules": [
                "אם הכאב השרירי קל-בינוני: חימום ארוך יותר, עומס קל יותר או תנועה אירובית קלה יכולים להספיק.",
                "אם כאבי השרירים חזקים או משנים טכניקה: הורד נפח/עומס או החלף לאימון התאוששות.",
            ],
            "avoid": ["לא להשתמש בכאבי שרירים כמטרה; לא לדחוף דרך כאב שמשנה טכניקה או מחמיר."],
        },
        "sleep_stress_low_readiness": {
            "use_when": ["כאשר המשתמש ישן מעט, מדווח על סטרס גבוה או מרגיש לא מוכן לאימון קשה."],
            "coaching_goal": ["להתאים את האימון למוכנות היומית בלי לשבור רצף."],
            "signals": [
                "שינה מתחת ליעד אישי או פחות מ-7 שעות אצל רוב המבוגרים, אנרגיה נמוכה או סטרס גבוה.",
                "חימום מרגיש כבד מהרגיל או RPE עולה מהר כבר בסטים קלים.",
            ],
            "adjustment_rules": [
                "בחר גרסה קצרה, RPE 5-7, פחות סטים או אימון טכני במקום אימון שיא.",
                "אם העייפות חוזרת בכמה לוגים, בדוק עומס שבועי, תזונה, מנוחות ותזמון אימונים.",
            ],
            "avoid": ["לא להבטיח ששינה אחת גרועה מחייבת ביטול; לא להתעלם מדפוס חוזר של התאוששות חלשה."],
        },
        "red_flag_boundary": {
            "use_when": ["כאשר מוכנות נמוכה מלווה בסימנים שאינם עומס אימוני רגיל."],
            "coaching_goal": ["להבדיל בין התאמת עומס רגילה לבין מצב שבו שכבת safety צריכה להוביל."],
            "signals": [
                "כאב בחזה, סחרחורת חריגה, עילפון, קוצר נשימה חריג, כאב חד או החמרה מתמשכת.",
                "נפיחות משמעותית, חולשה פתאומית או שינוי תחושה שלא מתאים ל-DOMS רגיל.",
            ],
            "adjustment_rules": [
                "אל תבחר deload רגיל; עצור את ההמלצה האימונית והשתמש בגבולות הבטיחות הקיימים.",
                "אם אין סימני חירום אבל יש חשש, בחר תנועה קלה ושאל שאלת המשך אחת במקום להעמיס.",
            ],
            "avoid": ["לא למסגר סימני סיכון כעייפות רגילה; לא לאבחן את הסיבה הרפואית."],
        },
    },
    "advanced_recovery_readiness_protocols": {
        "sleep_debt_adjustment": {
            "use_when": ["כאשר המשתמש ישן מעט, מתעורר לא רענן או מדווח על כמה ימים של התאוששות חלשה."],
            "coaching_goal": ["להתאים את האימון בלי להפוך שינה חלשה לכישלון אישי או לאבחנה רפואית."],
            "rules": [
                "לרוב המבוגרים יעד בסיסי הוא 7+ שעות שינה; איכות השינה חשובה גם אם מספר השעות נראה סביר.",
                "אם שינה חלשה מגיעה עם RPE גבוה, ירידת ביצועים או עייפות בוקר: הורד 20-40% נפח/עומס או בחר אימון טכני.",
                "אם זה דפוס של כמה לילות, העדף שבוע שימור/maintenance קצר ושעת שינה עקבית על עוד נפח אימונים.",
            ],
            "decision_gate": ["יש שילוב של שינה חלשה עם עייפות, RPE גבוה, ביצועים נמוכים או מוטיבציה נמוכה."],
            "avoid": ["לא להשתמש באימון קשה כפיצוי על שינה; לא להבטיח ששינה אחת מתקנת עומס יתר מצטבר."],
            "source_refs": ["CDC Sleep Basics", "ACSM Training Load Monitoring"],
        },
        "stress_readiness_adjustment": {
            "use_when": ["כאשר המשתמש מדווח על סטרס, עומס עבודה, עומס לימודים או יום רגשי כבד."],
            "coaching_goal": ["לשמור רצף דרך החלטת יום צהוב במקום לדחוף עצימות או לוותר לגמרי."],
            "rules": [
                "סטרס גבוה יכול להפוך עומס חיצוני רגיל לעומס פנימי גבוה; לכן מסתכלים על RPE, שינה, חשק וביצועים יחד.",
                "יום צהוב: אותה מסגרת אימון, פחות סטים, פחות כשל, יותר RIR, או גרסה של 15-25 דקות.",
                "המטרה היום היא לא לפצות על מה שפספסת; המטרה היא לבחור פעולה אחת שתשמור אותך במסלול.",
            ],
            "decision_gate": ["המשתמש יכול לזוז בבטחה, אבל האנרגיה/סטרס לא תומכים באימון שיא."],
            "avoid": ["לא למסגר סטרס כחולשה; לא להוסיף HIIT או סטים קשים כדי 'לשחרר' משתמש שכבר שחוק."],
            "source_refs": ["ACSM Training Load Monitoring", "Community Guide Behavior Change Programs"],
        },
        "doms_soreness_decision": {
            "use_when": ["כאשר יש DOMS, שרירים תפוסים או נוקשות אחרי עומס חדש או גבוה."],
            "coaching_goal": ["להבדיל בין תפיסות שרירים רגילה לבין כאב שמצריך שינוי או safety, בלי להפוך soreness ליעד."],
            "rules": [
                "DOMS רגיל מופיע לרוב אחרי עומס חדש/גבוה ומרגיש מפושט; הוא אינו מדד לאימון טוב ואינו מטרה.",
                "אם DOMS קל-בינוני: חימום ארוך יותר, תנועה קלה, פחות עומס או עבודה על אזור אחר יכולים לשמור רצף.",
                "אם soreness חזק משנה טכניקה, מגביל תפקוד או נמשך בצורה חריגה: הורד עומס ואל תרדוף PR.",
            ],
            "decision_gate": ["אין כאב חד, נפיחות חריגה, חולשה פתאומית, שינוי תחושה או החמרה ברורה בזמן תנועה."],
            "avoid": ["לא להציג כאבי שרירים כהוכחה להתקדמות; לא להבטיח שמתיחות יפתרו DOMS."],
            "source_refs": ["Cochrane Stretching DOMS Review", "Post-Exercise Stretching Meta-analysis"],
        },
        "illness_return_to_training": {
            "use_when": ["כאשר המשתמש חולה, חוזר ממחלה קלה או שואל אם להתאמן עם סימפטומים."],
            "coaching_goal": ["לתת חזרה שמרנית לאימון בלי אבחון ובלי לעודד דחיפה דרך מחלה."],
            "rules": [
                "עם חום/fever, כאבי גוף, עייפות חריגה, שיעול עמוק, לחץ בחזה, קוצר נשימה או סימפטומים מתחת לצוואר: לא אימון עצים; מנוחה ופנייה לאיש מקצוע אם יש חשש.",
                "בסימפטומים קלים מעל הצוואר בלבד, כמו נזלת או גרון קל, אפשר לשקול הליכה או תנועה קלה לפי תחושה, לא אימון שיא.",
                "בחזרה אחרי מחלה: התחל ב-50-70% מהנפח הרגיל או אימון קצר RPE 5-6, ואז עלה רק אם ההתאוששות טובה.",
            ],
            "decision_gate": ["אין חום, אין סימפטומים בחזה/נשימה, והמשתמש מרגיש מספיק טוב לפעילות קלה."],
            "avoid": ["לא לאבחן מחלה; לא להגיד למשתמש 'להזיע את זה החוצה'; לא להתאמן בקבוצה בזמן מחלה מדבקת."],
            "source_refs": ["Mayo Clinic Exercise and Illness", "Cleveland Clinic Activity During Acute Illness"],
        },
        "travel_disruption_maintenance": {
            "use_when": ["כאשר יש נסיעה, שבוע עמוס, ציוד חסר, שינה לא יציבה או זמינות לא צפויה."],
            "coaching_goal": ["לשמר רצף ותנועה דרך גרסת מינימום במקום לנסות להשלים את כל התוכנית."],
            "rules": [
                "שבוע נסיעה הוא לרוב maintenance week: 1-3 אימונים קצרים, הליכות, ותנועות מוכרות בלי תרגילים חדשים קשים.",
                "בחר גרסת מינימום של 10-20 דקות: squat/hinge/push/pull/core או הליכה אם זה כל מה שמציאותי.",
                "כשחוזרים לשגרה, אל תכפיל נפח; חזור לתוכנית עם עומס מעט נמוך אם השינה או הלוגים חלשים.",
            ],
            "decision_gate": ["המשתמש לא יכול לבצע את התוכנית הרגילה, אבל יכול לבצע פעולה קצרה ובטוחה."],
            "avoid": ["לא להעניש על נסיעה או פספוס; לא להעמיס אימון פיצוי ארוך אחרי שבוע משובש."],
            "source_refs": ["CDC Adult Physical Activity", "Community Guide Behavior Change Programs"],
        },
        "overreaching_watchlist": {
            "use_when": ["כאשר יש ירידה חוזרת בביצועים, RPE גבוה מהרגיל, שינה נשחקת או מוטיבציה יורדת."],
            "coaching_goal": ["לתפוס הצטברות עומס מוקדם ולבחור הורדת עומס לפני שהמשתמש נתקע."],
            "rules": [
                "חפש דפוס של 2-4 לוגים: ביצועים יורדים, RPE עולה, שינה חלשה, soreness מתמשך או ירידה בחשק.",
                "אם הדפוס חוזר, הורד 20-40% נפח/עומס לשבוע או עבור ל-maintenance עד שהביצועים והתחושה מתייצבים.",
                "Overtraining אמיתי אינו אבחון של הצ'אט; הבוט משתמש בזה כסימן תכנון שמרני ומפנה כשיש סימני סיכון.",
            ],
            "decision_gate": ["יש דפוס חוזר ולא רק אימון יחיד חלש, ואין red flag שמצריך safety לפני תכנון."],
            "avoid": ["לא לקרוא לכל עייפות overtraining; לא להמשיך להוסיף עומס כשמדדי מוכנות יורדים יחד."],
            "source_refs": ["NSCA Overtraining and Recovery", "NASM Overtraining Signs", "ACSM Training Load Monitoring"],
        },
        "recovery_modality_priorities": {
            "use_when": ["כאשר המשתמש מבקש כלי התאוששות, שחרור, קרח, עיסוי, מתיחות או פתרון מהיר ל-DOMS."],
            "coaching_goal": ["לתעדף יסודות התאוששות לפני גאדג'טים או טכניקות שוליות."],
            "rules": [
                "סדר עדיפויות: שינה, התאמת עומס, חלבון/אוכל מספיק, הידרציה ותנועה קלה לפני גאדג'טים.",
                "מתיחות, foam rolling או עיסוי יכולים לעזור לתחושה, אבל לא מחליפים עומס מתאים ושינה.",
                "אם המשתמש מחפש התאוששות כי האימונים קשים מדי שוב ושוב, הפתרון הוא לשנות תוכנית ולא לקנות עוד כלי התאוששות.",
            ],
            "decision_gate": ["אין סימני injury/safety והמשתמש מבקש ניהול עייפות או תפיסות שרירים רגילות."],
            "avoid": ["לא להבטיח פתרון מהיר ל-DOMS; לא למכור recovery tools במקום תיקון עומס."],
            "source_refs": ["CDC Sleep Basics", "Cochrane Stretching DOMS Review", "ACSM Training Load Monitoring"],
        },
    },
    "program_adaptation_protocols": {
        "progression_candidate": {
            "trigger": ["3+ אימונים הושלמו", "RPE נשאר סביר", "טכניקה יציבה", "אין כאב חד או עייפות חריגה"],
            "coach_assessment": [
                "בדוק שהמשתמש מצליח לחזור על הביצוע, לא רק אימון אחד טוב.",
                "השווה עומס חיצוני ללוגים: חזרות, סטים, משקל, מנוחות וטווח תנועה.",
                "בדוק עומס פנימי: RPE/RIR, התאוששות, שינה ומוטיבציה.",
            ],
            "adjustment_options": [
                "העלה משתנה אחד בלבד: חזרה אחת, סט אחד, עומס קטן, טווח תנועה או קצב איכותי יותר.",
                "אם המטרה היא כוח, העדף עומס קטן או איכות חזרות לפני עוד נפח.",
                "אם המטרה היא היפרטרופיה, הוסף נפח רק אם ההתאוששות נשמרת.",
            ],
            "avoid": [
                "לא להעלות עומס, סטים ותדירות באותו שבוע.",
                "לא להתקדם כאשר הטכניקה מתפרקת או RPE קופץ חריג.",
            ],
            "next_check": "בדוק בלוג הבא אם RPE נשאר יציב והביצוע לא ירד.",
        },
        "high_effort_or_fatigue": {
            "trigger": ["RPE 9-10 חוזר", "sRPE גבוה מהרגיל", "עייפות או שינה חלשה", "עומס פנימי גבוה לעומת עומס חיצוני רגיל"],
            "coach_assessment": [
                "בדוק אם העלייה במאמץ נובעת מנפח, עצימות, שינה, תזונה, סטרס או מרווחי מנוחה.",
                "חפש ירידה בביצועים או תחושת אימון קשה מהרגיל בעומס שהיה קל בעבר.",
                "הפרד בין אימון קשה מתוכנן לבין התאוששות חלשה שחוזרת בכמה לוגים.",
            ],
            "adjustment_options": [
                "שמור על אותם תרגילים אבל הורד 20-40 אחוז נפח או עומס לשבוע קל.",
                "העבר אימון עצים לגרסה טכנית קלה עם RPE 5-7.",
                "הוסף יום מנוחה או קצר את האימון במקום להוסיף עוד עבודה.",
            ],
            "avoid": [
                "לא לפרש RPE גבוה כחוסר רצון.",
                "לא לפתור עייפות חוזרת בעוד עצימות.",
            ],
            "next_check": "בקש בלוג קצר של שינה, אנרגיה, RPE וביצוע באימון הבא.",
        },
        "performance_plateau": {
            "trigger": ["ביצועים תקועים 2-4 שבועות", "אותו עומס מרגיש קשה יותר", "אין עלייה בחזרות או איכות", "plateau למרות עקביות"],
            "coach_assessment": [
                "בדוק אם הייתה עקביות אמיתית לפני שינוי תוכנית.",
                "בדוק האם נפח שבועי מתאים למטרה או גבוה מדי להתאוששות.",
                "בדוק אם תרגיל מסוים מגביל בגלל טכניקה, טווח תנועה או ציוד.",
            ],
            "adjustment_options": [
                "שמור את הדפוס אך החלף וריאציה אם התרגיל תקוע או לא נוח.",
                "שנה בלוק: שבוע טכני קל, ואז חזרה עם טווח חזרות או נפח מעט שונה.",
                "לכוח: הורד חזרות והעלה מנוחה; להיפרטרופיה: בדוק נפח קרוב לכ-10 סטים לשריר בשבוע אם מתאים.",
            ],
            "avoid": [
                "לא להחליף את כל התוכנית בגלל שבוע אחד חלש.",
                "לא להוסיף עוד נפח אם הבעיה היא התאוששות חלשה.",
            ],
            "next_check": "בדוק אחרי 2-3 אימונים אם הביצוע או RPE השתפרו.",
        },
        "missed_sessions": {
            "trigger": ["אימון פוספס", "שני אימונים או יותר פוספסו", "שבוע עמוס", "חזרה אחרי רצף שנשבר"],
            "coach_assessment": [
                "זהה אם החסם היה זמן, אנרגיה, ציוד, תמיכה או תכנון.",
                "בדוק אם התוכנית גדולה מדי לזמינות בפועל.",
                "הפוך פספוס למידע תכנון ולא לכישלון אישי.",
            ],
            "adjustment_options": [
                "הצע גרסה קצרה של 10-20 דקות עם דפוסי תנועה מרכזיים.",
                "הזז את האימון הבא בלי להכפיל נפח.",
                "קבע פעולת מינימום כדי להחזיר רצף לפני הוספת עומס.",
            ],
            "avoid": [
                "לא לתת אימון פיצוי ארוך.",
                "לא להעניש בתוספת אירובי או דיאטה.",
            ],
            "next_check": "בדוק אם הגרסה הקצרה בוצעה ומה החסם הבא.",
        },
        "exercise_substitution": {
            "trigger": ["תרגיל לא נוח", "ציוד חסר", "טכניקה לא יציבה", "כאב לא חד אך תנועה לא מרגישה טוב"],
            "coach_assessment": [
                "שמור על אותו דפוס תנועה אם אפשר: סקוואט, hinge, דחיפה, משיכה, ליבה או נשיאה.",
                "בדוק אם הבעיה היא טווח, עומס, יציבות, ציוד או הבנת cue.",
                "העדף וריאציה שהמשתמש יכול לבצע בביטחון ובעקביות.",
            ],
            "adjustment_options": [
                "בחר וריאציה קלה יותר: box squat, hip hinge עם תיק, שכיבת סמיכה בשיפוע או חתירה עם גומייה.",
                "הקטן טווח תנועה או עומס ושמור קצב נשלט.",
                "החלף תרגיל רק אם cue או רגרסיה פשוטה לא פותרת את הבעיה.",
            ],
            "avoid": [
                "לא למחוק דפוס תנועה שלם בגלל תרגיל אחד.",
                "לא להתעקש על תרגיל שגורם כאב או חרדה מיותרת.",
            ],
            "next_check": "בדוק בלוג של נוחות, טכניקה ו-RPE בוריאציה החדשה.",
        },
        "return_after_break": {
            "trigger": ["הפסקה של שבועיים או יותר", "חזרה ממחלה קלה", "ירידה בכושר", "אימון ראשון אחרי תקופה עמוסה"],
            "coach_assessment": [
                "השווה לנקודת baseline עדכנית, לא לשיא קודם.",
                "בדוק אם המטרה הראשונה היא חזרה לרצף, טכניקה או ביצועים.",
                "בחר עומס שמרגיש קל-בינוני גם אם המשתמש היה מתקדם בעבר.",
            ],
            "adjustment_options": [
                "התחל בנפח נמוך: פחות סטים, פחות עומס או פחות תדירות לשבוע הראשון.",
                "שמור 2-4 חזרות ברזרבה ו-RPE 5-7 עד שהרצף חוזר.",
                "העלה בהדרגה רק אחרי 2-3 אימונים ללא כאב חריג או עייפות חריגה.",
            ],
            "avoid": [
                "לא לנסות לחזור מיד למספרים הישנים.",
                "לא למדוד הצלחה לפי כאבי שרירים חזקים.",
            ],
            "next_check": "בדוק אם המשתמש התאושש תוך 24-48 שעות ואם אפשר לחזור לתוכנית הרגילה בהדרגה.",
        },
    },
    "program_lifecycle_protocols": {
        "normal_week": {
            "use_when": ["כאשר אין סימני עייפות חריגה, פספוסים חוזרים, בדיקה מתוכננת או אירוע קרוב."],
            "coaching_goal": ["לשמור רצף, לאסוף לוגים ולהתקדם רק אם הביצוע תומך בזה."],
            "rules": [
                "normal week הוא שבוע ביצוע רגיל: עושים את התוכנית, עוקבים אחרי RPE, כאב, חזרות ועומס.",
                "אם הביצוע יציב, אפשר progressive overload קטן אחד; אם לא, שומרים.",
                "לא מחליפים בלוק בגלל אימון יחיד טוב או חלש.",
            ],
            "decision_gate": ["לפחות לוג אחד ברור ואין סימן safety או עייפות חריגה."],
            "avoid": ["לא להמציא complexity של periodization למתחיל שצריך רק עקביות."],
            "source_refs": ["ACSM Resistance Training Guidelines 2026", "ACSM Progression Models in Resistance Training"],
        },
        "reassessment_cadence": {
            "use_when": ["בתכנון בלוק, סוף חודש, שינוי מטרה, או חוסר נתונים על התקדמות."],
            "coaching_goal": ["לקבוע מתי בודקים התקדמות בלי להפוך כל אימון למבחן."],
            "rules": [
                "בצע check-in קצר שבועי על לוגים, RPE, פספוסים וכאב.",
                "בצע reassessment מלא יותר כל 4-6 שבועות או אחרי שינוי מטרה/ציוד/זמינות.",
                "הקדם בדיקה אם יש כמה פספוסים, RPE גבוה חוזר, ירידה בביצועים או כאב שמפריע.",
            ],
            "decision_gate": ["יש מספיק לוגים או שינוי אמיתי שמצדיק התאמת תוכנית."],
            "avoid": ["לא לשנות את כל התוכנית אחרי יום אחד; לא לדחות התאמה כאשר דפוס בעייתי חוזר."],
            "source_refs": ["ACSM Progression Models in Resistance Training", "ACE Strength Plateaus"],
        },
        "plateau_decision": {
            "use_when": ["כאשר המשתמש אומר שנתקע או שהלוגים לא מתקדמים."],
            "coaching_goal": ["להבדיל בין plateau אמיתי לבין שבוע חלש או חוסר עקביות."],
            "rules": [
                "plateau דורש דפוס חוזר בכמה אימונים, לא אימון אחד.",
                "לפני שינוי גדול בדוק רצף, שינה, RPE, טכניקה, תזונה בסיסית, עומס ותאריך שינוי אחרון.",
                "אם הכול יציב ועדיין אין התקדמות, שנה משתנה אחד: נפח, עצימות, טווח חזרות, תרגיל או בלוק.",
            ],
            "decision_gate": ["לפחות 2-4 שבועות או כמה לוגים דומים מראים תקיעה למרות ביצוע סביר."],
            "avoid": ["לא לקרוא לכל קושי plateau; לא להחליף הכול בבת אחת."],
            "source_refs": ["ACE Strength Plateaus", "Exercise Variation Review"],
        },
        "deload_week": {
            "use_when": ["כאשר עייפות מצטברת, ביצועים יורדים, RPE גבוה חוזר, מוטיבציה נמוכה או soreness מתמשך."],
            "coaching_goal": ["להוריד עומס זמנית כדי לשמור מוכנות ולאפשר חזרה טובה יותר."],
            "rules": [
                "deload הוא שבוע/כמה ימים של פחות training stress, בדרך כלל פחות volume לפני פחות טכניקה.",
                "שמור תרגילים מוכרים, הורד סטים/עומס/תדירות לפי הצורך, ובלי PR.",
                "אם מדובר במתחיל לא עקבי, עדיף maintenance פשוט מאשר deload מורכב.",
            ],
            "decision_gate": ["יש סימני fatigue בדפוס חוזר או אחרי בלוק קשה, ואין red flag רפואי."],
            "avoid": ["לא להשתמש ב-deload כקסם; לא לעשות test week בזמן deload."],
            "source_refs": ["Deloading Strength and Physique Sports Review", "NSCA Overtraining and Recovery"],
        },
        "maintenance_week": {
            "use_when": ["עומס חיים, נסיעה, חוסר זמן, סטרס, או תקופה שבה המטרה היא לא לאבד רצף."],
            "coaching_goal": ["לשמור מינימום יעיל במקום להיכשל בתוכנית גדולה מדי."],
            "rules": [
                "maintenance week שומר דפוסים מרכזיים עם מינימום נפח: 1-3 אימונים קצרים לפי יכולת.",
                "בחר תרגילים מוכרים, מעט סטים, RPE בינוני ופעולה שקל לסיים.",
                "המטרה היא רצף ושימור, לא PR או שיא נפח.",
            ],
            "decision_gate": ["התוכנית הרגילה לא מציאותית השבוע, אבל פעולה קצרה כן אפשרית."],
            "avoid": ["לא להעניש על שבוע עמוס; לא לנסות להשלים את כל הנפח החסר."],
            "source_refs": ["ACSM Resistance Training Guidelines 2026", "Community Guide Behavior Change Programs"],
        },
        "taper_week": {
            "use_when": ["לפני אירוע לא-קליני: מרוץ, טיול מאתגר, משחק, מבחן כושר או יום ביצוע אישי."],
            "coaching_goal": ["להוריד fatigue בלי לגרום למשתמש להרגיש חלוד."],
            "rules": [
                "taper קצר לאירוע כללי: 3-7 ימים עם פחות volume, בלי תרגילים חדשים, ושמירה קטנה על intensity.",
                "הורד עבודה שגורמת DOMS או עייפות רגליים לפני אירוע סבולת/ספורט.",
                "העדף שינה, תזמון, ציוד מוכר ותנועה קלה על אימון אחרון קשה.",
            ],
            "decision_gate": ["יש תאריך אירוע ברור והמשתמש כבר ביצע בסיס אימונים לפני כן."],
            "avoid": ["לא להוסיף אימון קשה חדש כדי 'להרוויח כושר' בשבוע האירוע."],
            "source_refs": ["NSCA Tapering and Peaking", "Tapering and Peaking Powerlifting Review"],
        },
        "test_week": {
            "use_when": ["כאשר רוצים לבדוק התקדמות אחרי בלוק או לפני עדכון תוכנית."],
            "coaching_goal": ["למדוד התקדמות בצורה בטוחה ושימושית במקום לדחוף מקסימום."],
            "rules": [
                "test week לא חייב להיות 1RM; העדף submax, חזרות איכותיות, RPE, benchmark או e1RM זהיר.",
                "בדוק רק מדדים שישנו החלטה: עומס, חזרות, זמן, מרחק, RPE או ביצוע טכני.",
                "אל תבדוק הכול באותו שבוע אם זה יפגע בהתאוששות או עקביות.",
            ],
            "decision_gate": ["יש baseline קודם, טכניקה יציבה ואין כאב חד או עייפות חריגה."],
            "avoid": ["לא לדחוף max testing למתחיל, כאב, קטין או משתמש בלי תנאי בטיחות."],
            "source_refs": ["ACSM Fitness Assessment Manual", "Load Prescription Systematic Review"],
        },
        "exercise_change": {
            "use_when": ["כאשר שוקלים להחליף תרגיל בתוכנית קיימת."],
            "coaching_goal": ["להחליף תרגיל מסיבה תכנונית, לא כי כל אימון צריך novelty."],
            "rules": [
                "שמור תרגיל מספיק זמן ללמידה ולוגים לפני שמחליפים.",
                "החלף תרגיל אם יש כאב/אי נוחות, ציוד לא מתאים, plateau חוזר אחרי בדיקות, חוסר התאמה או בעיית התמדה.",
                "שמור את דפוס התנועה כשאפשר: squat ל-squat, hinge ל-hinge, push ל-push.",
            ],
            "decision_gate": ["ההחלפה משרתת מטרה, בטיחות, ציוד או עקביות ולא רק 'muscle confusion'."],
            "avoid": ["לא לסובב תרגילים אקראית; לא להמשיך cueing אינסופי אם וריאציה אחרת תעבוד טוב יותר."],
            "source_refs": ["Exercise Variation Review", "NSCA Guide to Program Design"],
        },
    },
    "recovery_rules": [
        "התאוששות כוללת שינה, ניהול עומס, ימי מנוחה, תזונה מספקת והפחתת עומס כשכאב או עייפות עולים.",
        "לרוב המבוגרים, שינה של 7 שעות או יותר היא יעד בסיסי; שינה ירודה מצדיקה אימון קצר או קל יותר.",
        "כאבי שרירים רגילים אינם יעד בפני עצמם; כאב חד או מחמיר משנה את התוכנית ומפעיל גבולות בטיחות.",
    ],
    "behavior_change_rules": [
        "העדף פעולה קטנה וקבועה על פני תוכנית גדולה שנשברת אחרי שבוע.",
        "טפל בחסם ספציפי: זמן, אנרגיה, ציוד, מזג אוויר, פחד מפציעה, מיומנות או מוטיבציה.",
        "תן למשתמש בחירה מצומצמת כשאפשר: גרסה מלאה, קצרה או התאוששותית.",
    ],
    "exercise_prescription_principles": [
        "FITT-VP הוא שלד התכנון: תדירות, עצימות, זמן, סוג פעילות, נפח והתקדמות.",
        "ספציפיות ועומס יתר הדרגתי בונים התאמה; התאוששות, טכניקה ותגובה אישית קובעות כמה מהר להתקדם.",
        "התחל מהמינון המינימלי היעיל שהמשתמש יכול לבצע בעקביות, במיוחד במתחילים או חוזרים אחרי הפסקה.",
        "שנה משתנה מרכזי אחד בכל פעם: עומס, חזרות, סטים, תדירות, מנוחה, טווח תנועה או מורכבות.",
        "עקרונות שימושיים למאמן: ספציפיות, אינדיבידואליזציה, עומס יתר, הדרגתיות, התאוששות, שונות ורברסיביליות.",
    ],
    "periodization_rules": [
        "מיקרו-מחזור הוא בדרך כלל שבוע אימונים; מזו-מחזור הוא בלוק של כמה שבועות עם מיקוד ברור; מאקרו הוא תמונת יעד ארוכה יותר.",
        "למשתמש כללי או מתחיל, periodization צריך להיות פשוט: חזרות על תוכנית בסיסית, התקדמות קטנה, ואז הערכה מחדש.",
        "למשתמש מתקדם יותר, אפשר לתכנן בלוקים שמחליפים דגש בין נפח, עצימות, טכניקה, כוח, סיבולת או התאוששות.",
        "אל תחליף את כל התוכנית בכל שבוע; שינוי תכוף מדי מסתיר מה עובד ומחליש עקביות.",
        "השתמש בלוגים, ביצועים, RPE, שינה וכאב כדי להחליט אם להמשיך בלוק, להעלות עומס או להוריד עומס זמנית.",
    ],
    "cardiorespiratory_training_rules": [
        "יעד בריאות למבוגר: 150-300 דקות אירובי מתון או 75-150 דקות אירובי עצים בשבוע, או שילוב ביניהם.",
        "מדידת עצימות יכולה להיות פשוטה: talk test, RPE, קצב נשימה, דופק אם זמין, וקצב התאוששות אחרי מאמץ.",
        "בנה בסיס קל-בינוני לפני אינטרוולים עצימים; רוב המשתמשים צריכים קודם עקביות ויכולת להתאושש.",
        "שלב אירובי לפי מטרה: הליכה/אופניים לשומן ובריאות, עבודה אזורית לסיבולת, ואינטרוולים רק כשיש בסיס ומטרה.",
        "אם אימוני כוח הם העדיפות, מקם אירובי כך שלא יפגע בביצוע: ימים נפרדים, אחרי כוח, או עצימות נמוכה יותר.",
    ],
    "cardio_programming": {
        "base": {
            "goal": "בניית הרגל אירובי ובריאות כללית בלי עומס מיותר.",
            "frequency": ["3-5 ימים בשבוע לפי זמינות", "אפשר להתחיל גם מ-5-10 דקות אם המשתמש לא פעיל"],
            "duration": ["150-300 דקות מתון בשבוע או 75-150 דקות עצים כאשר יש יכולת", "20-30 דקות למפגש כיעד ביניים שימושי"],
            "intensity": ["Zone 1 או מתון נמוך", "talk test: אפשר לדבר בנוחות; אם אי אפשר לדבר, הורד עצימות"],
            "progression": ["העלה קודם משך או תדירות", "אל תעלה נפח שבועי ביותר מכ-10% כשאפשר להימנע מזה"],
            "coach_notes": [
                "הליכה מהירה, אופניים, אליפטי או שחייה קלה מספיקים לבסיס.",
                "המטרה הראשונה היא חוויה חיובית ויכולת לחזור על זה בשבוע הבא.",
            ],
        },
        "aerobic_efficiency": {
            "goal": "שיפור יעילות אירובית אחרי שהמשתמש מסוגל לבצע עבודה רציפה.",
            "frequency": ["2-4 מפגשים בשבוע", "מפגש איכות אחד או שניים מספיקים לרוב המשתמשים הכלליים"],
            "duration": ["30-45 דקות למפגש", "אפשר לשלב steady state עם אינטרוולים קצרים"],
            "intensity": ["Zone 1 לחימום, קירור והתאוששות", "Zone 2 סביב VT1 או RPE 5-6 לאינטרוולים נשלטים"],
            "progression": ["הגדל קודם זמן רציף ותדירות", "אחר כך הוסף אינטרוולים קצרים ב-Zone 2"],
            "coach_notes": [
                "השתמש ב-talk test או RPE אם אין דופק אמין.",
                "Zone 2 לא אמור להפוך למאבק; אם ההתאוששות יורדת, חזור ל-Zone 1.",
            ],
        },
        "intervals": {
            "goal": "שיפור יכולת בעצימות גבוהה כאשר יש בסיס, מטרה והתאוששות.",
            "frequency": ["1 מפגש בשבוע למתחילים באינטרוולים", "עד 2 מפגשים לרוב המשתמשים שאינם ספורטאי סבולת"],
            "duration": ["10-25 דקות עבודה עיקרית", "כולל חימום וקירור המפגש יכול להיות 25-45 דקות"],
            "intensity": ["Zone 3 או RPE 7-9 רק בקטעי עבודה קצרים", "התאוששות ב-Zone 1 בין קטעים"],
            "progression": ["הוסף חזרה אחת, הארך עבודה מעט או קצר התאוששות; לא הכל יחד", "שמור יום קל אחרי מפגש קשה"],
            "coach_notes": [
                "HIIT אינו חובה לירידה בשומן או בריאות.",
                "עצור אם איכות התנועה, נשימה או התאוששות מתפרקות מעבר למאמץ רגיל.",
            ],
        },
        "fat_loss_support": {
            "goal": "להגדיל הוצאה ואירוביות בלי לפגוע בכוח, שינה או עקביות.",
            "frequency": ["3-6 חשיפות קלות בשבוע לפי סבילות", "צעדים יומיים יכולים להיות יעילים יותר מאימון עצים נדיר"],
            "duration": ["10-45 דקות הליכה או עבודה קלה", "הצטברות לאורך היום נספרת"],
            "intensity": ["בעיקר Zone 1-2", "עצימות שאפשר להתאושש ממנה בקלות"],
            "progression": ["הוסף צעדים, דקות או יום קצר לפני עצימות", "הפחת אם אימוני הכוח או הרעב נפגעים"],
            "coach_notes": [
                "אירובי לירידה בשומן הוא תמיכה בהרגלים, לא עונש קלורי.",
                "עדיף נפח קל שניתן לשמר מאשר HIIT שמפרק התאוששות.",
            ],
        },
        "endurance_event": {
            "goal": "הכנה לאירוע סבולת או שיפור ביצוע מתמשך.",
            "frequency": ["3-6 מפגשים בשבוע לפי ניסיון ואירוע", "לפחות יום התאוששות או יום קל אחרי עבודה קשה"],
            "duration": ["מפגש ארוך אחד בשבוע נבנה בהדרגה", "שאר המפגשים קצרים או בינוניים לפי התאוששות"],
            "intensity": ["רוב הנפח ב-Zone 1", "מעט Zone 2/Zone 3 לפי רמה, מטרה וזמן התאוששות"],
            "progression": ["בנה מחזורי עומס והתאוששות", "הורד נפח אם ביצועים יורדים, כאב עולה או עייפות נמשכת"],
            "coach_notes": [
                "למתקדמים, חלוקה שימושית יכולה להיות 70-80% זמן ב-Zone 1, מעט Zone 2 ו-10-20% Zone 3.",
                "לא צריך להעתיק מודל ספורטאי עילית למשתמש כללי בלי נפח, ניסיון ומטרה מתאימים.",
            ],
        },
    },
    "walking_running_protocols": {
        "beginner_walk_run": {
            "use_when": ["כאשר משתמש רוצה להתחיל לרוץ, חוזר אחרי הפסקה, או לא מצליח לרוץ רצוף בנוחות."],
            "coaching_goal": ["לבנות סבילות לריצה דרך מקטעים קצרים בלי להפוך כל אימון למבחן אופי."],
            "rules": [
                "התחל בריצה-הליכה: למשל 1 דקה ריצה קלה + 3-5 דקות הליכה, 4-6 חזרות.",
                "שמור את מקטעי הריצה בקצב שבו אפשר לדבר במשפטים קצרים או ב-RPE 4-6.",
                "התקדם קודם ביותר זמן ריצה בתוך אותו אימון, ורק אחר כך ביותר אימונים או קצב.",
            ],
            "progression_gate": [
                "המשתמש מסיים 20-30 דקות ריצה-הליכה בלי כאב חד, בלי החמרה למחרת ועם נשימה נשלטת.",
                "לפחות יום אחד בלי ריצה בין אימוני ריצה בתחילת הדרך.",
            ],
            "adjust_if_hard": [
                "הארך את ההליכה או קצר את מקטע הריצה במקום לבטל את האימון.",
                "אם הנשימה יוצאת משליטה, עבור להליכה עד חזרה לדיבור נוח.",
            ],
            "avoid": ["לא לדחוף ריצה רצופה רק כדי להוכיח כושר; לא להפוך ריצה ראשונה לאינטרוולים עצימים."],
            "source_refs": ["Brigham and Women's Return to Running", "Ohio State Walk to Run Guideline", "CDC Measuring Physical Activity Intensity"],
        },
        "easy_run_base": {
            "use_when": ["כאשר המשתמש רץ קל, בונה בסיס אירובי, או שואל באיזה קצב לרוץ."],
            "coaching_goal": ["לשמור רוב הריצות קלות מספיק כדי לבנות עקביות ולהתאושש."],
            "rules": [
                "ריצה קלה היא קצב שבו אפשר לדבר במשפטים קצרים לפי talk test.",
                "RPE שימושי: קל-בינוני לרוב 3-6 מתוך 10, תלוי ברמה ובמטרה.",
                "אם הקצב גורם למרדף אחרי מספרים, הורד קצב והשתמש בנשימה/דיבור כמדד.",
            ],
            "progression_gate": ["ריצה קלה מסתיימת בתחושה שנשאר עוד קצת, והאימון הבא לא נפגע."],
            "adjust_if_hard": ["הפוך את הריצה לריצה-הליכה או הליכה מהירה ושמור את אותו זמן אימון."],
            "avoid": ["לא להפוך כל ריצה קלה ל-time trial; לא למדוד הצלחה רק לפי pace."],
            "source_refs": ["ACSM Aerobic Intensity Guidance", "CDC Measuring Physical Activity Intensity", "Talk Test Review"],
        },
        "weekly_volume_progression": {
            "use_when": ["כאשר מעלים נפח ריצה שבועי, קילומטרים, דקות או מספר ריצות."],
            "coaching_goal": ["להגדיל נפח ריצה בהדרגה בלי לקפוץ בעומס רק כי הכושר הנשימתי משתפר מהר."],
            "rules": [
                "נפח ריצה כולל זמן/קילומטרים, מספר ריצות, ריצה ארוכה ועצימות.",
                "העלה משתנה אחד: עוד דקות, עוד קילומטרים, עוד יום או קצת עצימות - לא הכל יחד.",
                "קפיצות גדולות בנפח או בריצה הארוכה מעלות סיכון עומס; העדף שבועות יציבים ועליות קטנות.",
            ],
            "progression_gate": ["2-3 שבועות של לוגים יציבים, RPE נשלט, התאוששות טובה וללא כאב חד."],
            "adjust_if_hard": ["שמור שבוע נוסף באותו נפח או הורד 20-30% לפני שמוסיף שוב."],
            "avoid": ["לא להשלים קילומטרים חסרים בסוף שבוע אחד; לא להעלות מרחק וקצב יחד."],
            "source_refs": ["Running Injury Training Parameters Review", "ACSM Training Load Monitoring"],
        },
        "long_run_management": {
            "use_when": ["כאשר המשתמש מתכונן ל-5K/10K/חצי מרתון/מרתון או בונה ריצה ארוכה שבועית."],
            "coaching_goal": ["להשתמש בריצה ארוכה לבניית בסיס בלי לתת לה להשתלט על כל השבוע."],
            "rules": [
                "ריצה ארוכה נשארת לרוב קלה או Zone 1-2, במיוחד למתחילים.",
                "הריצה הארוכה צריכה לגדול בהדרגה ולשבת בתוך נפח שבועי שהמשתמש מסוגל לשחזר.",
                "אם הריצה הארוכה מפרקת את האימונים הבאים, היא ארוכה או מהירה מדי עכשיו.",
            ],
            "progression_gate": ["המשתמש מתאושש תוך 24-48 שעות והריצה הבאה נשארת בשליטה."],
            "adjust_if_hard": ["קצר את הריצה הארוכה, פצל לריצה-הליכה, או שמור מרחק לשבוע נוסף."],
            "avoid": ["לא להפוך כל ריצה ארוכה למבחן קצב; לא להסתמך על ריצה ארוכה אחת במקום עקביות שבועית."],
            "source_refs": ["ACSM Distance Running Habits", "Running Injury Training Parameters Review"],
        },
        "intervals_and_hills": {
            "use_when": ["כאשר המשתמש רוצה אינטרוולים, חזרות בעלייה, שיפור קצב או HIIT."],
            "coaching_goal": ["להוסיף עצימות רק כאשר יש בסיס, התאוששות ומטרה ברורה."],
            "rules": [
                "אינטרוולים הם מקטעי מאמץ נשלטים, לא ספרינט עד קריסה.",
                "עליות חוזרות דורשות צעד קצר, גוף יציב ומאמץ נשלט במקום רדיפה אחרי pace.",
                "עצימות גבוהה צריכה להיות מינון קטן בתוך שבוע שרובו קל.",
            ],
            "progression_gate": ["המשתמש מסוגל לרוץ קל 20-30 דקות, מתאושש טוב ואין כאב חד או עייפות חריגה."],
            "adjust_if_hard": ["החלף אינטרוול בהאצות קצרות או מקטע Zone 2 קצר; שמור יותר הליכה/מנוחה בין חזרות."],
            "avoid": ["לא להוסיף HIIT למשתמש שאין לו בסיס או שכבר מדווח על עייפות/כאב."],
            "source_refs": ["ACSM Aerobic Intensity Guidance", "ACSM Distance Running Habits"],
        },
        "runner_strength_support": {
            "use_when": ["כאשר משתמש רץ הרבה, מתלונן על עומס חוזר, או רוצה לשפר ריצה בלי רק לרוץ יותר."],
            "coaching_goal": ["לתמוך בריצה דרך כוח, שליטה וניידות בלי להפוך את שבוע הריצה לעמוס מדי."],
            "rules": [
                "כוח לרצים צריך לכלול דפוסי רגליים, ירך, שוק, ליבה ושליטה חד-צדדית.",
                "שמור 1-2 אימוני כוח קצרים בשבוע כאשר נפח הריצה עולה.",
                "מקם כוח קשה רחוק מריצה עצימה או ריצה ארוכה כאשר ההתאוששות מוגבלת.",
            ],
            "progression_gate": ["אימוני הכוח לא פוגעים בריצה הקלה, בריצה הארוכה או בהתאוששות."],
            "adjust_if_hard": ["בחר 2-4 תרגילים מרכזיים בלבד, פחות סטים, או אימון כוח תחזוקתי."],
            "avoid": ["לא להוסיף אימון רגליים כבד יום לפני ריצה ארוכה או אינטרוולים למשתמש שלא מתאושש."],
            "source_refs": ["ACSM Distance Running Habits", "Running Injury Prevention Scoping Review"],
        },
        "form_cadence_surface": {
            "use_when": ["כאשר מדברים על טכניקת ריצה, cadence, משטח, נעליים או שינוי סגנון."],
            "coaching_goal": ["לתת cues קטנים ומעשיים בלי לאבחן טכניקה מרחוק."],
            "rules": [
                "cadence נקרא בעברית קצב צעדים; אפשר להשתמש בו כדי לעודד צעד מעט קצר ונשלט.",
                "שינוי משטח, נעליים, עליות או מעבר ממסילה לכביש הוא שינוי עומס לכל דבר.",
                "שינויים בטכניקת ריצה צריכים להיכנס במקטעים קטנים כדי לתת לרקמות להסתגל.",
            ],
            "progression_gate": ["השינוי מרגיש טבעי יותר אחרי כמה אימונים ולא מעלה כאב או RPE חריג."],
            "adjust_if_hard": ["חזור לקצב צעדים טבעי, משטח מוכר או נעל מוכרת, ושנה רק משתנה אחד."],
            "avoid": ["לא להבטיח שתיקון cadence או נעל מסוימת פותרים כאב; לא לעשות form diagnosis מרחוק."],
            "source_refs": ["ACSM Distance Running Habits", "Brigham and Women's Return to Running"],
        },
        "missed_run_adjustment": {
            "use_when": ["כאשר המשתמש פספס ריצה, שבוע התפקשש, או יש עייפות/כאב אחרי ריצה."],
            "coaching_goal": ["להחזיר עקביות בלי פיצוי יתר ובלי להפוך פספוס לכישלון."],
            "rules": [
                "אם פספסת ריצה, לא משלימים את כל הנפח ביום אחד.",
                "החזר את השבוע דרך ריצה קלה קצרה או ריצה-הליכה, ואז המשך לפי הלוגים.",
                "אם יש ירידה בביצועים, RPE גבוה, שינה חלשה או כאב, הורד נפח לפני עצימות.",
            ],
            "progression_gate": ["המשתמש חזר לאימון קל בלי החמרה ומסוגל להשלים עוד אימון רגיל השבוע."],
            "adjust_if_hard": ["הפוך את הריצה להליכה מהירה, קצר את הזמן או בחר אימון כוח קל/ניידות."],
            "avoid": ["לא לדחוף דרך כאב חד, סחרחורת, קוצר נשימה חריג או כאב שמחמיר תוך כדי ריצה."],
            "source_refs": ["Brigham and Women's Return to Running", "Ohio State Walk to Run Guideline", "ACSM Training Load Monitoring"],
        },
    },
    "daily_activity_neat_protocols": {
        "step_baseline": {
            "use_when": ["כאשר המשתמש שואל כמה צעדים לעשות, רוצה לזוז יותר, או רוצה תמיכה בירידה בשומן."],
            "coaching_goal": ["לקבוע יעד צעדים לפי המציאות של המשתמש במקום מספר קסם."],
            "rules": [
                "קודם מצא את בסיס הצעדים: ממוצע של 3-7 ימים רגילים אם יש שעון/טלפון, או הערכה גסה אם אין.",
                "יעד טוב הוא מעט מעל הבסיס, לא בהכרח 10,000 צעדים.",
                "אם אין מדידה, בחר זמן הליכה יומי: 10-20 דקות מצטברות הן נקודת פתיחה טובה.",
            ],
            "progression_gate": ["המשתמש עומד בבסיס החדש 4-5 ימים בשבוע בלי שזה פוגע בשינה, כאב או אימוני כוח."],
            "adjust_if_hard": ["הורד יעד, פצל להליכות קצרות, או בחר יעד זמן במקום ספירת צעדים."],
            "avoid": ["לא להציג יעד צעדים אחיד לכל המשתמשים; לא להפוך צעדים למדד ערך עצמי."],
            "source_refs": ["ODPHP Move Your Way", "ACSM Step Counts"],
        },
        "gradual_step_target": {
            "use_when": ["כאשר המשתמש כבר יודע את כמות הצעדים או עומד ביעד קל."],
            "coaching_goal": ["להעלות תנועה יומית בהדרגה כדי לשמור התמדה והתאוששות."],
            "rules": [
                "הוסף בדרך כלל 500-1,000 צעדים ביום או 5-10 דקות הליכה, ואז בדוק שבוע.",
                "שנה יעד אחד: יותר צעדים או יותר ימים פעילים, לא הכל בבת אחת.",
                "אם היום עמוס, יעד מינימום יכול להיות סיבוב קצר אחרי ארוחה או הליכה אחת בשכונה.",
            ],
            "progression_gate": ["היעד הושלם ברוב הימים והמשתמש מרגיש שזה מציאותי גם בשבוע עמוס."],
            "adjust_if_hard": ["חזור ליעד הקודם, פצל לשני סיבובים קצרים, או שמור יעד תחזוקה לשבוע."],
            "avoid": ["לא להעניש פספוס בהכפלת צעדים ביום הבא; לא להעלות יעד כשכאב רגליים או עייפות עולים."],
            "source_refs": ["CDC Adult Physical Activity", "ODPHP Move Your Way"],
        },
        "movement_breaks_sedentary_reset": {
            "use_when": ["כאשר המשתמש יושב הרבה, עובד מול מחשב או מתקשה להכניס אימון מלא."],
            "coaching_goal": ["לשבור ישיבה ממושכת בפעולה קצרה וברורה."],
            "rules": [
                "אחרי 30-90 דקות ישיבה, קום ל-2-5 דקות תנועה אם זה אפשרי.",
                "הפסקה יכולה להיות הליכה בבית, מים, מדרגות, פתיחת ירך/חזה או כמה calf raises.",
                "גם ביום אימון, פחות ישיבה רצופה יכולה לתמוך בתחושה, אנרגיה ועקביות.",
            ],
            "progression_gate": ["המשתמש מצליח לבצע 2-5 הפסקות תנועה ביום בלי שזה מרגיש כמו פרויקט."],
            "adjust_if_hard": ["חבר את ההפסקה להרגל קיים: קפה, שיחת טלפון, שירותים או מילוי מים."],
            "avoid": ["לא לדרוש עמידה כל היום; המטרה היא פחות רצף ישיבה, לא שלמות."],
            "source_refs": ["WHO Sedentary Behaviour Guidelines", "ACSM Sedentary Behaviour"],
        },
        "movement_snacks": {
            "use_when": ["כאשר אין זמן לאימון או שהמשתמש צריך דרך קלה לשמור רצף."],
            "coaching_goal": ["להפוך תנועה קטנה לפעולה מעשית שאינה דורשת החלפת בגדים או ציוד."],
            "rules": [
                "הפסקות תנועה קצרות של 2-3 דקות יכולות לכלול הליכה, מדרגות, סקוואט לכיסא או מתיחות קלות.",
                "בחר 1-3 הפסקות ביום לפני שמנסים תוכנית מלאה.",
                "movement snack טוב הוא כזה שמסתיים בתחושה של 'יכולתי לעשות את זה שוב מחר'.",
            ],
            "progression_gate": ["המשתמש מבצע את ההפסקות כמה ימים ברצף ומדווח שהן לא מפריעות ליום."],
            "adjust_if_hard": ["הקטן לדקה אחת או פעולה אחת, למשל רק קימה והליכה למטבח."],
            "avoid": ["לא לקרוא לזה אימון כושל; זה כלי עקביות בפני עצמו."],
            "source_refs": ["CDC Benefits of Physical Activity", "ODPHP Move Your Way"],
        },
        "post_meal_walk": {
            "use_when": ["כאשר המשתמש רוצה הרגל קל אחרי אוכל או תמיכה לא אגרסיבית בהרגלי תזונה."],
            "coaching_goal": ["להציע הליכה קצרה אחרי ארוחה בלי הבטחות רפואיות או קלוריות מדויקות."],
            "rules": [
                "הליכה רגועה של 5-15 דקות אחרי ארוחה יכולה להיות הרגל פשוט לתנועה יומית.",
                "הקצב צריך להיות נוח; זו לא חייבת להיות יחידת קרדיו.",
                "השתמש בזה בעיקר כדי לבנות רצף, עיכול נוח ויציאה מהישיבה, לא כדי 'לשרוף' ארוחה.",
            ],
            "progression_gate": ["המשתמש עושה את זה אחרי ארוחה אחת ביום בלי עומס או לחץ."],
            "adjust_if_hard": ["קצר ל-3-5 דקות או הפוך להליכה בתוך הבית."],
            "avoid": ["לא להבטיח שליטה בסוכר או ירידה במשקל מתוצאה אחת; לא להפוך אוכל לחוב שצריך לשלם."],
            "source_refs": ["CDC Benefits of Physical Activity", "ACSM Sedentary Behaviour"],
        },
        "active_errands_and_commute": {
            "use_when": ["כאשר המשתמש רוצה להוסיף תנועה בלי אימון נוסף."],
            "coaching_goal": ["למצוא מקורות תנועה קיימים ביום ולהפוך אותם לבחירה קלה."],
            "rules": [
                "אפשר לבחור מדרגות פעם-פעמיים, לחנות מעט רחוק יותר, לרדת תחנה אחת קודם או לעשות שיחת הליכה.",
                "בחר רק אפשרויות נוחות ובטוחות למיקום, מזג האוויר והזמן של המשתמש.",
                "התנועה היומיומית מחוץ לאימון נצברת גם אם היא לא מרגישה כמו אימון.",
            ],
            "progression_gate": ["המשתמש מוצא 1-2 הזדמנויות קבועות בשבוע ויכול לחזור עליהן."],
            "adjust_if_hard": ["בחר הזדמנות אחת בלבד או פעולה בבית במקום שינוי נסיעה."],
            "avoid": ["לא להציע הליכה באזור לא בטוח, בחום קיצוני או כשהמשתמש מוגבל בזמן באופן לא מציאותי."],
            "source_refs": ["ODPHP Move Your Way", "CDC Adult Physical Activity"],
        },
        "low_impact_recovery_day": {
            "use_when": ["כאשר המשתמש עייף, אחרי אימון קשה, או צריך לשמור רצף בלי עומס גבוה."],
            "coaching_goal": ["לתת יום בעומס נמוך ששומר תנועה בלי להעמיס עוד אימון קשה."],
            "rules": [
                "יום בעומס נמוך יכול להיות הליכה, אופניים קלים, מוביליטי או הפסקות תנועה קצרות.",
                "Low-impact אינו 'כלום'; זה כלי לשמור עקביות והתאוששות.",
                "אם יש כאב חד או סימפטום חריג, עוברים לגבולות הבטיחות הרגילים.",
            ],
            "progression_gate": ["המשתמש מסיים בהרגשה טובה יותר או לפחות לא גרועה יותר."],
            "adjust_if_hard": ["קצר ל-5-10 דקות, בחר תנועה בבית, או שמור רק על הליכה רגועה."],
            "avoid": ["לא להפוך יום התאוששות ל-HIIT מוסווה; לא להוסיף קפיצות או ספרינטים ביום עייף."],
            "source_refs": ["ACSM Physical Activity Guidelines", "CDC Benefits of Physical Activity"],
        },
        "fat_loss_activity_support": {
            "use_when": ["כאשר המשתמש רוצה ירידה בשומן או מנסה להגדיל הוצאה בלי עוד אימון קשה."],
            "coaching_goal": ["להציג תנועה יומית כתמיכה בהרגלים ולא כעונש קלורי."],
            "rules": [
                "צעדים, הליכות והפסקות תנועה תומכים בירידה בשומן בעיקר כי קל להתמיד בהם.",
                "תנועה יומית לא מחליפה כוח, חלבון, שינה ותזונה ברת קיימא.",
                "לא עונש על אוכל: זו דרך להעלות פעילות שבועית בלי לשבור התאוששות.",
            ],
            "progression_gate": ["המשתמש שומר על כוח/שינה/רעב סבירים בזמן שמעלים תנועה קלה."],
            "adjust_if_hard": ["שמור צעדים קבועים במקום להעלות, או החלף HIIT בהליכה קלה."],
            "avoid": ["לא לרדוף אחרי מספרי קלוריות משעון; לא להוסיף נפח אם זה מגביר רעב או פוגע באימון."],
            "source_refs": ["ODPHP Move Your Way", "ACSM Step Counts"],
        },
        "calorie_burn_uncertainty": {
            "use_when": ["כאשר המשתמש שואל כמה קלוריות שרפה הליכה, צעדים או פעילות יומית."],
            "coaching_goal": ["לענות בטווחים ולהסיט את המוקד להתמדה ומדידה עקבית."],
            "rules": [
                "קלוריות מתנועה הן טווח לא מדויק; שעונים ואפליקציות יכולים לטעות.",
                "אפשר להשתמש באותו מכשיר למעקב מגמה, לא כאמת מוחלטת.",
                "עדיף לשאול: האם יעד הצעדים עוזר לך להתמיד בלי לפגוע באימונים או בתיאבון?",
            ],
            "progression_gate": ["המשתמש מבין שהמספר משוער ומוכן לבחור פעולה לפי עקביות, לא לפי דיוק קלורי."],
            "adjust_if_hard": ["תן טווח רחב או הימנע ממספר, ובחר יעד התנהגותי כמו דקות הליכה."],
            "avoid": ["לא להציג קלוריות שרופות כמספר מדויק; לא לתת למספר להצדיק אכילה/ענישה."],
            "source_refs": ["CDC Benefits of Physical Activity", "ACSM Sedentary Behaviour"],
        },
    },
    "warmup_mobility_rules": [
        "חימום כללי של 5-10 דקות מעלה דופק, חום גוף ותחושת מוכנות לפני עבודה קשה יותר.",
        "חימום ספציפי מכין את דפוסי התנועה של האימון: סטים קלים, טווח הדרגתי, קצב נשלט וחזרות הכנה.",
        "ניידות צריכה לשרת תנועה שימושית; אל תכפה טווח או מתיחה שמייצרים כאב חד או תחושת סכנה.",
        "מתיחות סטטיות ארוכות מתאימות יותר אחרי אימון או ביחידה נפרדת כאשר המטרה היא גמישות, לא כתחליף לחימום ספציפי.",
        "לאנשים מבוגרים או למי שחוזר אחרי הפסקה, שלב שיווי משקל, קואורדינציה ותנועות יומיומיות פשוטות.",
    ],
    "warmup_cooldown_protocols": {
        "pulse_raiser": {
            "use_when": ["לפני אימון כוח, אירובי עצים, אינטרוולים, משחק או תנועה טכנית."],
            "coaching_goal": ["להעלות דופק, חום גוף ומוכנות בלי לעייף."],
            "rules": [
                "התחל ב-5-10 דקות פעילות קלה דומה לאימון: הליכה, אופניים, חתירה, ריצה קלה או תנועה כללית.",
                "האימון עצים יותר -> החימום יכול להיות ארוך ומדורג יותר.",
                "סיים כאשר המשתמש מרגיש חם ומוכן, לא מותש.",
            ],
            "decision_gate": ["המשתמש מרגיש מוכן להתחיל הכנה ספציפית או סטים קלים בלי קפיצה חדה בעצימות."],
            "avoid": ["לא להפוך את החימום לאימון בפני עצמו; לא להתחיל סט כבד קר."],
            "source_refs": ["AHA Warm Up Cool Down", "NASM Dynamic Stretching"],
        },
        "dynamic_specific_prep": {
            "use_when": ["אחרי pulse raiser ולפני דפוסי תנועה מרכזיים באימון."],
            "coaching_goal": ["להכין את התנועות של האימון דרך טווח נשלט וקצב עולה."],
            "rules": [
                "dynamic warmup צריך להיראות כמו גרסה קלה של מה שיגיע: סקוואט לפני סקוואט, hinge לפני deadlift, דחיפה לפני לחיצה.",
                "השתמש ב-ROM נשלט, חזרות קלות וקיו אחד; לא רשימת מוביליטי אקראית.",
                "לפני כוח/Power, העדף תנועה דינמית על החזקות סטטיות ארוכות.",
            ],
            "decision_gate": ["התנועה נראית יציבה יותר אחרי החימום ולא מופיע כאב חד או חוסר ביטחון."],
            "avoid": ["לא להכריח טווח תנועה שהמשתמש לא שולט בו; לא להעמיס dynamic drills קשים מדי."],
            "source_refs": ["NASM Dynamic Stretching", "AHA Warm Up Cool Down"],
        },
        "ramp_sets": {
            "use_when": ["לפני סטים כבדים, תרגיל טכני, או חזרה אחרי הפסקה."],
            "coaching_goal": ["להגיע לעומס העבודה דרך סטים קלים שמתרגלים טכניקה ומוכנות."],
            "rules": [
                "ramp sets: כמה סטים קלים עם עומס עולה וחזרות יורדות לפני סט העבודה.",
                "בתרגיל מורכב, הסטים הראשונים צריכים ללמד מסלול, נשימה וטווח, לא ליצור עייפות.",
                "אם סט חימום מרגיש כבד מהרגיל, התאמת עומס היום עדיפה על דחיפה בכוח.",
            ],
            "decision_gate": ["הסט האחרון לפני עבודה מרגיש יציב, בלי כאב חד ועם RPE נמוך-בינוני."],
            "avoid": ["לא לקפוץ מבר ריק/קל ישר לעומס עבודה כבד; לא לעשות יותר מדי סטי חימום עד עייפות."],
            "source_refs": ["NASM Acute Variables", "NSCA Exercise Technique Manual"],
        },
        "static_stretching": {
            "use_when": ["כאשר המטרה היא גמישות/ROM או תחושת tightness, לרוב אחרי חימום או ביחידה נפרדת."],
            "coaching_goal": ["לשפר או לשמר טווח תנועה בלי לפגוע באיכות כוח/Power מידית."],
            "rules": [
                "לרוב המבוגרים: 10-30 שניות למתיחה, 2-4 חזרות או כ-60 שניות מצטברות לקבוצת שריר.",
                "בצע static stretching כשהשריר חם, עד תחושת מתיחה נסבלת ולא כאב חד.",
                "לפני עבודה כבדה/נפיצה, הימנע מהחזקות סטטיות ארוכות מיד לפני הסטים המרכזיים.",
            ],
            "decision_gate": ["המתיחה משפרת נוחות או ROM בלי נימול, כאב חד או ירידה בביטחון תנועה."],
            "avoid": ["לא להקפיץ מתיחה; לא להציג static stretching כחובה לפני כל אימון."],
            "source_refs": ["ACSM Flexibility and Neuromotor Guidance", "NASM Static Stretching Evidence"],
        },
        "cooldown": {
            "use_when": ["בסוף אימון עצים, אחרי אינטרוולים, או כאשר המשתמש רוצה מעבר הדרגתי לשגרה."],
            "coaching_goal": ["להוריד קצב בהדרגה ולתת מעבר נוח, בלי הבטחות מוגזמות."],
            "rules": [
                "cool-down או שחרור יכול להיות 5-10 דקות קלות של אותה פעילות בעצימות נמוכה.",
                "אפשר להוסיף נשימה, הליכה קלה או מתיחות נוחות אם זה עוזר לתחושה.",
                "הצג cool-down ככלי מעבר ונוחות, לא כפתרון מובטח ל-DOMS או התאוששות מהירה.",
            ],
            "decision_gate": ["המשתמש מסיים רגוע יותר ולא מאריך את האימון עד עייפות נוספת."],
            "avoid": ["לא להבטיח שקירור ימנע כאבי שרירים; לא להכריח מתיחות אם הן לא נעימות."],
            "source_refs": ["AHA Warm Up Cool Down", "Cochrane Stretching DOMS Review"],
        },
        "doms_truthfulness": {
            "use_when": ["כאשר המשתמש שואל על כאבי שרירים, מתיחות אחרי אימון או התאוששות."],
            "coaching_goal": ["לדבר על DOMS בכנות: לא יעד, לא מדד איכות, ולא משהו שמתיחות פותרות בוודאות."],
            "rules": [
                "DOMS רגיל הוא כאב שרירי מפושט אחרי עומס חדש/גבוה, אבל הוא אינו יעד ואינו מדד לאימון טוב.",
                "מתיחות לפני/אחרי אימון אינן דרך אמינה למנוע או להפחית DOMS באופן משמעותי.",
                "לתחושה טובה אפשר לבחור תנועה קלה, חימום ארוך יותר באימון הבא והורדת נפח זמנית אם הכאב משנה טכניקה.",
            ],
            "decision_gate": ["הכאב מפושט ושרירי בלי סימני red flag כמו כאב חד, נפיחות חריגה, חולשה או החמרה."],
            "avoid": ["לא למכור soreness כהוכחת התקדמות; לא לטפל בכאב חד כ-DOMS רגיל."],
            "source_refs": ["Cochrane Stretching DOMS Review", "Post-Exercise Stretching Meta-analysis"],
        },
    },
    "mobility_balance_programming": {
        "dynamic_warmup": {
            "goal": "להכין את הגוף לאימון הספציפי בלי לעייף או להקטין איכות ביצוע.",
            "frequency": ["לפני אימוני כוח, אירובי עצים, משחק או עבודה טכנית"],
            "duration": ["5-10 דקות חימום כללי ואז 3-8 דקות הכנה ספציפית"],
            "methods": ["הליכה מהירה, אופניים קלים או ROM כללי", "סטים קלים של דפוסי האימון", "תנועות דינמיות כמו לאנג׳, סקוואט חלקי, סיבובי ירך וכתף"],
            "intensity_or_quality": ["קל עד בינוני", "המשתמש צריך להרגיש חם, נייד ומוכן, לא עייף"],
            "progression": ["הוסף מורכבות או קצב רק כשהתנועה נקייה", "לפני אימון כבד, התקדם דרך סטים ספציפיים קלים"],
            "coach_notes": [
                "דינמי לפני פעילות עדיף לרוב על מתיחה סטטית ארוכה.",
                "בחר תרגילי הכנה לפי מה שמופיע באימון, לא רשימת מוביליטי אקראית.",
            ],
        },
        "mobility_work": {
            "goal": "לשפר טווח תנועה שימושי ושליטה במפרקים הרלוונטיים לתרגילים ולחיי היומיום.",
            "frequency": ["2-6 חשיפות קצרות בשבוע לפי צורך", "אפשר לשלב 5-10 דקות בסוף אימון או ביום קל"],
            "duration": ["5-15 דקות לפי אזור ומטרה"],
            "methods": ["טווחי תנועה אקטיביים", "תרגילי שליטה בקצה טווח", "נשימה וקצב איטי", "עבודה סביב ירך, קרסול, כתף ועמוד שדרה לפי התוכנית"],
            "intensity_or_quality": ["מתח נסבל, בלי כאב חד או תחושת איום", "טווח שניתן לשלוט בו עדיף מטווח פסיבי גדול"],
            "progression": ["הגדל טווח, זמן שליטה או דרישת יציבות בהדרגה", "העבר טווח חדש לתרגיל כוח קל כדי שיהיה שימושי"],
            "coach_notes": [
                "מוביליטי טוב משרת סקוואט, הינג׳, דחיפה, משיכה, נשיאה או פעילות יומית.",
                "אם טווח חדש נעלם מיד או כואב, חזור לגרסה קצרה וקלה יותר.",
            ],
        },
        "static_flexibility": {
            "goal": "לשמר או לשפר טווח תנועה במפרקים וקבוצות שריר מרכזיות.",
            "frequency": ["לפחות 2-3 ימים בשבוע", "יומי יכול לעזור כאשר גמישות היא מטרה מרכזית"],
            "duration": ["10-30 שניות לכל החזקת מתיחה לרוב המבוגרים", "צבור בערך 60 שניות לכל מתיחה דרך 2-4 חזרות"],
            "methods": ["מתיחה סטטית", "PNF או מתיחה אקטיבית כאשר מתאים", "ביצוע כשהשריר כבר חם"],
            "intensity_or_quality": ["תחושת מתיחה או tightness קלה-בינונית", "לא כאב חד, נימול או החמרה"],
            "progression": ["הגדל קודם עקביות וזמן מצטבר", "אחר כך הוסף טווח בהדרגה בלי להילחם בגוף"],
            "coach_notes": [
                "מתיחות סטטיות ארוכות אינן תחליף לחימום ספציפי לפני סטים כבדים.",
                "למבוגרים יותר אפשר להאריך החזקות בזהירות אם זה נוח ומועיל.",
            ],
        },
        "neuromotor_balance": {
            "goal": "לשפר שיווי משקל, קואורדינציה, gait, יציבות ויכולת תגובה.",
            "frequency": ["2-3 ימים בשבוע", "אפשר לשלב מינונים קצרים בתוך חימום או אימון כוח"],
            "duration": ["20-30 דקות למפגש ייעודי", "או 5-10 דקות כאשר זה חלק מאימון כללי"],
            "methods": ["שיווי משקל סטטי", "צעדים רב-כיווניים", "step-up to balance", "נשיאות", "שינוי בסיס תמיכה", "tai chi או יוגה מותאמת"],
            "intensity_or_quality": ["קושי שמאתגר יציבות בלי סיכון נפילה", "איכות ושליטה קודמות למהירות או משטח לא יציב"],
            "progression": ["התקדם מתמיכה לתמיכה קלה ואז ללא תמיכה", "עבר מסגיטלי לפרונטלי ורק אחר כך רוטציה אם בטוח"],
            "coach_notes": [
                "תרגול שיווי משקל צריך להיות קרוב למשטח תמיכה כאשר יש חשש נפילה.",
                "לא צריך משטחים לא יציבים אם הם מפרקים טכניקה או ביטחון.",
            ],
        },
        "desk_sedentary_reset": {
            "goal": "לשבור ישיבה ממושכת ולשמר תנועה בסיסית ביום עמוס.",
            "frequency": ["כל 30-90 דקות ישיבה כאשר אפשר", "או 2-5 הפסקות קצרות ביום"],
            "duration": ["1-5 דקות להפסקה"],
            "methods": ["קימה והליכה קצרה", "פתיחת ירך וחזה", "סיבובי קרסול וכתף", "סקוואט לכיסא או calf raises"],
            "intensity_or_quality": ["קל מאוד", "המטרה היא תנועה וערנות, לא אימון קשה"],
            "progression": ["הוסף תדירות הפסקות לפני קושי", "חבר הפסקה להרגל קיים כמו קפה או שיחה"],
            "coach_notes": [
                "גם משתמש שמתאמן מרוויח מהפחתת ישיבה רצופה.",
                "ביום שאין אימון, reset קצר שומר רצף ומפחית תחושת תקיעות.",
            ],
        },
        "older_adult_fall_prevention": {
            "goal": "לתמוך בתפקוד יומי, ביטחון בהליכה והפחתת סיכון נפילה אצל מבוגרים.",
            "frequency": ["2 או יותר מפגשים בשבוע", "אפשר לשלב עם כוח והליכה בתוכנית רב-רכיבית"],
            "duration": ["10-30 דקות לפי יכולת, ביטחון ועייפות"],
            "methods": ["קימה מכיסא", "step-up נמוך", "עמידה על רגל אחת עם תמיכה", "הליכה לאחור בזהירות", "נשיאה קלה", "כיסא או קיר כתמיכה"],
            "intensity_or_quality": ["אתגר יציבות נמוך-בינוני עם תמיכה זמינה", "אין לבצע תרגיל שמעלה פחד נפילה מעבר לשליטה"],
            "progression": ["הקטן תמיכה או הגדל טווח רק אחרי שליטה", "הוסף כיוון תנועה או נשיאה קלה לפני משטח לא יציב"],
            "coach_notes": [
                "אימון ביתי יעיל יכול להשתמש בכיסא, קיר, מגבת ומשקל גוף.",
                "אם יש נפילות חוזרות, סחרחורת או ירידה פתאומית בתפקוד, הפנה לאיש מקצוע מתאים.",
            ],
        },
    },
    "assessment_reassessment_rules": [
        "הערכה ראשונית צריכה לאסוף מטרה, זמינות, ניסיון, ציוד, מגבלות, העדפות, חסמים, פעילות נוכחית ומדדי בסיס פשוטים.",
        "התבוננות בתנועה אינה אבחון; היא עוזרת לבחור וריאציה, טווח, קצב ועומס שהמשתמש מבצע היטב.",
        "הערכה מחדש נשענת על לוגים: ביצועים, כאב, RPE, פספוסים, שינה, זמן בפועל ותחושת מוכנות.",
        "בדוק התקדמות כל 2-4 שבועות או אחרי שינוי משמעותי, לא אחרי כל אימון בודד אלא אם יש כאב חד או סימפטום חריג.",
        "מדדים טובים הם כאלה שמשנים החלטה: יותר עקביות, יותר חזרות באותו RPE, פחות כאב, התאוששות טובה יותר או יותר ביטחון.",
    ],
    "assessment_tracking_protocols": {
        "client_intake": {
            "goal": "להבין את האדם לפני בחירת מבחנים או תוכנית.",
            "use_when": ["בתחילת עבודה", "אחרי הפסקה ארוכה", "כאשר מטרה או מגבלה משתנות"],
            "measures": ["מטרה מרכזית", "ניסיון אימון", "זמינות וציוד", "מגבלות או כאב", "העדפות וחסמי עקביות", "פעילות נוכחית"],
            "protocol_notes": [
                "בחר רק שאלות שמשנות החלטת תכנון.",
                "אם יש סימני סיכון, הפעל את כללי screening/referral הקיימים לפני מבחן מאמץ.",
            ],
            "interpretation": [
                "ה-intake קובע מה לבדוק, לא להפך.",
                "מתחיל שלא פעיל לא צריך סוללת מבחנים מתישה כדי לקבל תוכנית ראשונה.",
            ],
            "follow_up": ["בחר מבחן אחד עד שלושה שמתאימים למטרה", "קבע מדד baseline פשוט שאפשר לחזור עליו"],
        },
        "baseline_snapshot": {
            "goal": "לקבוע נקודת פתיחה שימושית למדידה בלי להפוך את onboarding למבחן מעבדה.",
            "use_when": ["לפני תוכנית חדשה", "כאשר אין נתונים שמורים", "כשצריך להראות התקדמות מעבר למשקל גוף"],
            "measures": [
                "cardiorespiratory או אירובי: משך הליכה, talk test, דופק אם זמין או RPE",
                "כוח: וריאציה נשלטת, חזרות, עומס ו-RPE",
                "סבולת שרירית: חזרות איכותיות בזמן או סט קבוע",
                "גמישות/מוביליטי: טווח שימושי לתרגיל הרלוונטי",
                "הרגלים: אימונים בשבוע, צעדים, שינה ותיעוד ארוחות אם רלוונטי",
            ],
            "protocol_notes": [
                "מדוד באותם תנאים ככל האפשר: אותו תרגיל, זמן, ציוד והוראות.",
                "אל תשווה baseline של משתמש אחד לנורמות כאילו זו אבחנה; השתמש בו להתקדמות אישית.",
            ],
            "interpretation": [
                "baseline טוב הוא כזה שמכוון תכנון או מוטיבציה.",
                "אם המדד לא משנה החלטה, עדיף לא לאסוף אותו.",
            ],
            "follow_up": ["קבע מועד בדיקה חוזרת", "חבר כל מדד לפעולה: עומס, נפח, תדירות או התאוששות"],
        },
        "movement_assessment": {
            "goal": "לבחור וריאציות תרגיל, טווח ועומס לפי שליטה בתנועה.",
            "use_when": ["לפני תוכנית כוח", "כאשר יש טכניקה לא יציבה", "לפני העלאת מורכבות או עומס"],
            "measures": ["סקוואט או ישיבה-קימה", "hip hinge", "דחיפה", "משיכה", "לאנג׳/step-up", "שיווי משקל בסיסי", "טווח כתף/ירך/קרסול לפי צורך"],
            "protocol_notes": [
                "התחל בתנועה פשוטה ובטוחה לפני מבחן חד-צדדי, קפיצה או עומס.",
                "אפשר cue אחד קצר כדי לבדוק אם מדובר בחוסר הבנה ולא במגבלה אמיתית.",
                "עצור מבחן אם יש כאב חד, סחרחורת או פחד נפילה.",
            ],
            "interpretation": [
                "הערכת תנועה היא תצפית תכנותית ולא אבחון.",
                "פיצוי בתנועה אומר לבחור רגרסיה, טווח או cue מתאים; הוא לא מוכיח שריר חלש או פציעה.",
            ],
            "follow_up": ["בחר תרגיל שהמשתמש מבצע בשליטה", "תעד cue או רגרסיה שעבדו", "בדוק שוב אחרי 2-4 שבועות"],
        },
        "muscular_fitness_testing": {
            "goal": "להעריך כוח, סבולת שרירית או התקדמות בלי לסכן משתמש שאינו מוכן ל-1RM.",
            "use_when": ["בתוכניות כוח/שריר", "כשהמשתמש יודע לבצע טכניקה יציבה", "בבדיקת התקדמות תקופתית"],
            "measures": ["חזרות איכותיות בעומס קבוע", "סט AMRAP שמור עם RPE/RIR", "עומס ל-5-10 חזרות", "זמן החזקת ליבה או נשיאה"],
            "protocol_notes": [
                "לרוב המשתמשים, השתמש ב-submax test עם RPE או RIR במקום 1RM אמיתי.",
                "עצור לפני כשל טכני, כאב חד או שינוי קיצוני בטכניקה.",
                "שמור אותו תרגיל, טווח, מנוחה וקצב כדי להשוות לאורך זמן.",
            ],
            "interpretation": [
                "יותר חזרות באותו עומס ו-RPE דומה מעידות על התקדמות שימושית.",
                "ירידה בביצוע עם RPE גבוה עשויה להעיד על התאוששות חלשה, לא עצלות.",
            ],
            "follow_up": ["העלה עומס או חזרות רק כשהטכניקה נשמרת", "שמור או הורד נפח אם RPE עולה וביצועים יורדים"],
        },
        "cardiorespiratory_testing": {
            "goal": "להעריך יכולת אירובית שימושית ולכוון עצימות בלי ציוד מעבדה.",
            "use_when": ["בתוכנית אירובית", "כאשר המטרה היא סבולת או בריאות", "במעקב אחרי יכולת התאוששות"],
            "measures": ["talk test", "RPE 0-10", "משך הליכה רצופה", "מרחק בזמן קבוע כמו 6 דקות", "דופק מנוחה או דופק מאמץ אם זמין"],
            "protocol_notes": [
                "בחר מבחן submax שמרגיש בטוח ולא מאיים.",
                "בצע חימום קצר ושמור תנאים דומים בבדיקה חוזרת.",
                "אל תשתמש במבחן מאמץ עצים כאשר יש סימפטומים חריגים או מידע רפואי חסר.",
            ],
            "interpretation": [
                "אם המשתמש יכול לדבר אבל לא לשיר, זו בדרך כלל עצימות מתונה לפי talk test.",
                "יותר מרחק או זמן באותו RPE הם סימן התקדמות טוב למשתמש כללי.",
            ],
            "follow_up": ["קבע Zone/RPE לאימונים לפי התוצאה", "העלה קודם משך או תדירות לפני עצימות"],
        },
        "body_composition_tracking": {
            "goal": "לעקוב אחרי שינויי גוף בלי לצמצם הצלחה למשקל בלבד.",
            "use_when": ["במטרות ירידה בשומן, בניית שריר או בריאות", "כאשר המשתמש רוצה לראות מגמות ארוכות טווח"],
            "measures": ["משקל כממוצע מגמה אם מתאים", "היקפים", "תמונות התקדמות אם המשתמש רוצה", "בגדים", "כוח, אנרגיה וביצועים"],
            "protocol_notes": [
                "השתמש באותם תנאים וזמן מדידה.",
                "אל תציג מדידות ביתיות כאחוז שומן מדויק.",
                "הימנע ממעקב שמעודד אובססיה או מצוקה.",
            ],
            "interpretation": [
                "משקל יכול לעלות עם בניית שריר או נוזלים גם כשההרגלים משתפרים.",
                "מדד גוף אחד אינו מספיק; שלב ביצועים, עקביות ותחושה.",
            ],
            "follow_up": ["בדוק מגמה שבועית או חודשית", "התאם תזונה/אימון לפי כמה מדדים, לא לפי שקילה בודדת"],
        },
        "progress_review": {
            "goal": "להפוך לוגים להחלטות תוכנית ולא רק לארכיון.",
            "use_when": ["כל 2-4 שבועות", "אחרי פספוסים חוזרים", "אחרי כאב/עייפות", "בסוף בלוק אימון"],
            "measures": ["אימונים שהושלמו", "פספוסים", "RPE", "עומסים/חזרות", "כאב", "שינה", "ארוחות מתועדות", "מדד baseline חוזר"],
            "protocol_notes": [
                "השווה מול baseline אישי ולא מול משתמש אחר.",
                "חפש דפוס של כמה לוגים במקום להגיב בהגזמה לאימון אחד.",
            ],
            "interpretation": [
                "התקדמות יכולה להיות יותר עקביות, אותו ביצוע בפחות מאמץ, או פחות כאב.",
                "אם אין נתונים, המטרה הבאה היא לוג קצר ולא תוכנית מורכבת יותר.",
            ],
            "follow_up": ["בחר החלטה אחת: להתקדם, לשמור, להוריד עומס, או לשנות חסם"],
        },
        "decision_rules": {
            "goal": "לתת למאמן כלל פעולה ברור אחרי מדידה.",
            "use_when": ["אחרי בדיקת baseline", "אחרי progress review", "כאשר המשתמש שואל מה לשנות"],
            "measures": ["ביצועים", "RPE/RIR", "כאב", "התאוששות", "עקביות", "מטרה"],
            "protocol_notes": [
                "אל תשנה כמה משתנים בבת אחת אם אפשר להימנע מזה.",
                "החלטה טובה צריכה להיות ניתנת לביצוע באימון הבא.",
            ],
            "interpretation": [
                "אם ביצועים משתפרים ו-RPE יציב: אפשר להתקדם מעט.",
                "אם עקביות נמוכה: הקטן תוכנית לפני שאתה מוסיף נפח.",
                "אם כאב או עייפות עולים: שמור או הורד עומס ובחר וריאציה קלה יותר.",
            ],
            "follow_up": ["התקדם במשתנה אחד בלבד", "שמור אם ההרגל עדיין נבנה", "הורד עומס אם התאוששות או כאב דורשים זאת"],
        },
    },
    "progress_measurement_protocols": {
        "goal_metric_selection": {
            "use_when": ["בתחילת תוכנית, אחרי שינוי מטרה, או כאשר חסר מדד התקדמות ברור."],
            "measures": [
                "baseline לפי מטרה: כוח, אירובי, תנועה, היקפים, הרגל או תזונה.",
                "בחר 1-3 מדדים בלבד כדי לא להפוך מעקב לעומס.",
                "כל מדד חייב לענות על השאלה: איזו החלטה נשנה אם הוא ישתנה?",
            ],
            "interpretation": [
                "מדד טוב משווה את המשתמש לעצמו ולא לנורמות כלליות.",
                "אם המדד לא משנה תכנון, הוא רעש ולא coaching signal.",
            ],
            "decision_rules": [
                "לכוח: עקוב עומס/חזרות/RPE.",
                "לאירובי: עקוב זמן/מרחק/RPE/talk test.",
                "להרכב גוף: עקוב מגמה, היקפים וביצועים יחד.",
            ],
            "avoid": ["לא להוסיף מדדים רק כי אפשר; לא להפוך onboarding למבחן ארוך."],
            "source_refs": ["ACSM Fitness Assessment Manual", "ACE Client-Centered Assessments"],
        },
        "strength_progress": {
            "use_when": ["בסקירת לוגי כוח, היפרטרופיה או חזרה אחרי הפסקה."],
            "measures": [
                "חזרות, עומס, סטים, RPE/RIR, טווח תנועה וקצב ביצוע.",
                "same load + more clean reps + similar RPE הוא סימן התקדמות.",
                "אותן חזרות/עומס עם RPE נמוך יותר גם נחשב שיפור.",
            ],
            "interpretation": [
                "ירידה זמנית בביצועים עם RPE גבוה יכולה להיות עייפות, שינה או התאוששות, לא כישלון.",
                "התקדמות בטכניקה ובשליטה קודמת לקפיצה בעומס.",
            ],
            "decision_rules": [
                "אם ביצועים משתפרים ו-RPE יציב: הוסף חזרה או עומס קטן.",
                "אם RPE גבוה חוזר או טכניקה יורדת: שמור או הורד נפח/עצימות.",
            ],
            "avoid": ["לא לבדוק 1RM למתחיל או למשתמש עם כאב; לא להעלות עומס על חזרות לא נקיות."],
            "source_refs": ["Resistance Training Monitoring Review", "ACSM Training Load Monitoring"],
        },
        "cardio_progress": {
            "use_when": ["במטרות אירובי, בריאות, סבולת או שיפור התאוששות."],
            "measures": [
                "משך רצוף, מרחק בזמן קבוע, RPE, talk test ודופק אם זמין.",
                "יותר זמן/מרחק באותו RPE או דופק דומה הוא שיפור שימושי.",
                "יכולת לדבר אבל לא לשיר מתאימה לרוב לעבודה מתונה.",
            ],
            "interpretation": [
                "אימון אירובי מתקדם קודם דרך תדירות ומשך לפני אינטרוולים עצימים.",
                "עייפות חריגה או קוצר נשימה לא רגיל מחזירים לכללי safety.",
            ],
            "decision_rules": [
                "אם הבסיס יציב: הוסף 5-10 דקות או חשיפה שבועית קטנה.",
                "אם RPE גבוה מדי: הורד קצב או פצל את האימון.",
            ],
            "avoid": ["לא להוסיף HIIT רק כי משתמש רוצה תוצאה מהירה; לא למדוד עצימות רק לפי קלוריות."],
            "source_refs": ["CDC Measuring Physical Activity Intensity", "Talk Test Review"],
        },
        "body_composition_trends": {
            "use_when": ["במטרות ירידה בשומן, בניית שריר או שינוי מראה/מידות."],
            "measures": [
                "משקל בתנאים דומים, היקפים, תמונות אם המשתמש רוצה, בגדים, כוח ואנרגיה.",
                "שקילה בודדת אינה החלטת תוכנית; עדיף ממוצע או מגמה.",
                "שלב מדדי ביצוע כדי לא לפרש עלייה במשקל אוטומטית ככישלון.",
            ],
            "interpretation": [
                "משקל הוא מגמה ולא פסק דין יומי.",
                "היקפים יורדים, כוח יציב ואנרגיה טובה יכולים להעיד על התקדמות גם כשהמשקל איטי.",
            ],
            "decision_rules": [
                "בדוק 2-4 שבועות לפני שינוי גדול בתזונה או נפח.",
                "אם המעקב יוצר מצוקה, העבר דגש להרגלים וביצועים.",
            ],
            "avoid": ["לא להבטיח אחוז שומן מדויק ממדידה ביתית; לא לעודד שקילה אובססיבית."],
            "source_refs": ["ACSM Body Composition Assessment", "NASM Beyond the Number on the Scale"],
        },
        "adherence_dashboard_review": {
            "use_when": ["כאשר בונים weekly summary, dashboard next action או תגובה אחרי שבוע לא עקבי."],
            "measures": [
                "אימונים שהושלמו, פספוסים, אימונים חלקיים, ארוחות מתועדות, streak וזמן בפועל.",
                "מספר next action צריך להישען על חסם אמיתי: זמן, אנרגיה, ציוד, כאב או תכנון.",
            ],
            "interpretation": [
                "עקביות היא מדד אימון מרכזי, לא רק מוטיבציה.",
                "אימון חלקי שנשמר בלוג הוא מידע חיובי לתכנון, לא כישלון.",
            ],
            "decision_rules": [
                "בחר next action/פעולה אחת: אימון קצר, הזזה בלו״ז, הורדת נפח או לוג פשוט.",
                "אם פספוסים חוזרים: הקטן תוכנית לפני שמוסיפים מורכבות.",
            ],
            "avoid": ["לא להפוך dashboard למנגנון אשמה; לא להציג רצף כאילו הוא חשוב יותר מהתאוששות."],
            "source_refs": ["CDC Physical Activity Tracking", "Community Guide Behavior Change Programs"],
        },
        "reassessment_decision": {
            "use_when": ["בסוף בלוק, אחרי 2-4 שבועות, אחרי plateau או כשמחליטים אם לשנות תוכנית."],
            "measures": ["baseline חוזר", "לוגים", "RPE/RIR", "כאב", "התאוששות", "עקביות", "מטרת המשתמש"],
            "interpretation": [
                "דפוס של כמה לוגים חשוב יותר מאימון אחד חריג.",
                "plateau דורש קודם בדיקת עקביות, עומס והתאוששות לפני החלפת כל התוכנית.",
            ],
            "decision_rules": [
                "כל 2-4 שבועות: התקדמות, שימור, הורדת עומס או שינוי תרגיל לפי נתונים.",
                "שנה משתנה אחד בכל פעם כדי לדעת מה עבד.",
            ],
            "avoid": ["לא להחליף תוכנית כי יום אחד הרגיש קשה; לא להתקדם כשכאב או התאוששות מדרדרים."],
            "source_refs": ["ACSM Fitness Assessment Manual", "NSCA Guide to Program Design"],
        },
    },
    "field_assessment_protocols": {
        "eligibility_screen": {
            "use_when": ["לפני מבחן baseline, בדיקה חוזרת או מבחן אירובי/תפקודי."],
            "required_profile_inputs": [
                "מטרה",
                "גיל/קבוצת גיל אם ידוע",
                "מגבלות או כאב",
                "מצב רפואי/תרופות אם נמסרו",
                "ציוד וסביבת ביצוע",
            ],
            "do_not_test_if": [
                "כאב בחזה",
                "סחרחורת או עילפון",
                "קוצר נשימה חריג",
                "כאב חד",
                "נפילה חוזרת או חשש נפילה בלי תמיכה",
                "מידע רפואי חסר שמעלה סיכון",
            ],
            "stop_flags": [
                "כאב בחזה",
                "סחרחורת",
                "קוצר נשימה חריג",
                "כאב חד",
                "איבוד שיווי משקל",
                "המשתמש מבקש לעצור",
            ],
            "referral_action": ["עצור את המבחן והפעל גבולות בטיחות; הפנה לאיש מקצוע מתאים לפי הסימן."],
        },
        "six_minute_walk": {
            "test_id": "6MWT",
            "goal": "baseline אירובי/תפקודי נמוך-ציוד להשוואה אישית לאורך זמן.",
            "population_fit": ["משתמשים כלליים שיכולים ללכת בבטחה", "לא מבחן מאמץ עצים"],
            "equipment": ["מסלול בטוח", "שעון 6 דקות", "אפשרות לעצור"],
            "setup": ["בחר מסלול שטוח ובטוח ככל האפשר", "הסבר שהמטרה היא קצב יציב ולא ספרינט"],
            "instructions": ["לך 6 דקות בקצב הכי טוב שניתן לשמור בבטחה; תעד מרחק, RPE, talk test וסימפטומים."],
            "record_fields": ["distance", "unit", "rpe", "talk_test", "symptoms", "pain_flag", "conditions_notes"],
            "scoring_units": ["מטרים או צעדים/הקפה אם אין מדידה מדויקת"],
            "interpretation_rules": ["השווה ל-baseline אישי באותם תנאים", "יותר מרחק באותו RPE הוא שיפור שימושי"],
            "action_rules": ["שיפור באותו RPE -> התקדמות קטנה במשך/תדירות", "ירידה עם RPE/סימפטומים -> שמור או הורד עומס"],
            "retest_window": ["כל 4-8 שבועות או אחרי בלוק אירובי"],
            "safety_limits": ["עצור בסחרחורת, כאב בחזה, קוצר נשימה חריג או כאב חד"],
            "source_refs": ["ATS Six-Minute Walk Test", "ACSM GETP", "CDC intensity/talk test"],
        },
        "two_minute_step": {
            "test_id": "2MST",
            "goal": "חלופה קצרה ל-baseline אירובי כאשר אין מסלול הליכה מתאים.",
            "population_fit": ["משתמשים עם מקום קטן ובטיחות עמידה", "לא מתאים אם שיווי משקל נמוך ללא תמיכה"],
            "equipment": ["שעון 2 דקות", "קיר/כיסא לתמיכה לפי צורך"],
            "setup": ["עמוד ליד תמיכה זמינה", "סמן גובה ברך נוח אם משתמשים בהוראה פורמלית"],
            "instructions": ["בצע דריכה במקום במשך 2 דקות; תעד מספר צעדים תקינים, RPE, talk test וסימפטומים."],
            "record_fields": ["step_count", "rpe", "talk_test", "symptoms", "balance_support", "pain_flag"],
            "scoring_units": ["מספר צעדים ב-2 דקות"],
            "interpretation_rules": ["השווה ל-baseline אישי", "שיפור בכמות צעדים עם RPE דומה תומך בהתקדמות אירובית"],
            "action_rules": ["שיפור יציב -> הוסף דקות/תדירות", "RPE גבוה או אי יציבות -> הורד עצימות ובחר הליכה קלה"],
            "retest_window": ["כל 4-8 שבועות"],
            "safety_limits": ["עצור באיבוד שיווי משקל, סחרחורת, כאב בחזה או קוצר נשימה חריג"],
            "source_refs": ["Senior Fitness Test / 2-Minute Step", "CDC STEADI", "ACSM GETP"],
        },
        "thirty_second_chair_stand": {
            "test_id": "30s_chair_stand",
            "goal": "baseline לתפקוד וכוח/סבולת רגליים ללא ציוד מורכב.",
            "population_fit": ["משתמשים שיכולים לקום מכיסא בבטחה", "מבוגרים או מתחילים"],
            "equipment": ["כיסא יציב", "שעון 30 שניות"],
            "setup": ["כיסא יציב ליד קיר אם צריך", "כפות רגליים יציבות"],
            "instructions": ["קום ושב מכיסא במשך 30 שניות בטכניקה בטוחה; תעד מספר חזרות, RPE וכאב."],
            "record_fields": ["reps_30s", "rpe", "pain_flag", "support_used", "conditions_notes"],
            "scoring_units": ["חזרות ב-30 שניות"],
            "interpretation_rules": ["השווה ל-baseline אישי ולא כאבחנה", "יותר חזרות באותו RPE/כאב נמוך הן שיפור"],
            "action_rules": ["שיפור -> אפשר להוסיף טווח/חזרות/עומס קל", "כאב/טכניקה יורדת -> וריאציה נתמכת או פחות נפח"],
            "retest_window": ["כל 4-8 שבועות או אחרי בלוק כוח"],
            "safety_limits": ["עצור בכאב חד, סחרחורת או חוסר שליטה בירידה לכיסא"],
            "source_refs": ["CDC STEADI Chair Stand", "Senior Fitness Test"],
        },
        "four_stage_balance": {
            "test_id": "4_stage_balance",
            "goal": "screen תפקודי לשיווי משקל כשזה רלוונטי לתוכנית, במיוחד למבוגרים.",
            "population_fit": ["מבוגרים", "משתמשים עם חשש שיווי משקל", "רק עם תמיכה זמינה"],
            "equipment": ["קיר/שיש/כיסא יציב", "שעון"],
            "setup": ["בצע ליד תמיכה", "אל תבצע לבד אם יש חשש נפילה"],
            "instructions": ["נסה עמידות מדורגות עד 10 שניות כל אחת רק אם בטוח; תעד השלב הגבוה שהושלם ותמיכה."],
            "record_fields": ["highest_stage_held", "seconds", "support_used", "symptoms", "fall_concern"],
            "scoring_units": ["שלב ושניות החזקה"],
            "interpretation_rules": ["תצפית לבחירת תרגילי שיווי משקל, לא אבחון נפילה", "השווה רק לתוצאה האישית הקודמת"],
            "action_rules": ["אם יציב -> תרגול שיווי קל מתקדם", "אם לא יציב -> תמיכה, תרגילי כיסא והפניה אם יש נפילות"],
            "retest_window": ["כל 4-8 שבועות או לפי צורך תפקודי"],
            "safety_limits": ["עצור באובדן שיווי, סחרחורת, פחד נפילה או צורך בתמיכה משמעותית"],
            "source_refs": ["CDC STEADI 4-Stage Balance Test"],
        },
        "timed_up_and_go": {
            "test_id": "TUG",
            "goal": "מדד תפקודי פשוט לקימה, הליכה קצרה, סיבוב וחזרה כאשר יש צורך תפקודי.",
            "population_fit": ["מבוגרים או משתמשים עם מטרת תפקוד", "רק בסביבה בטוחה"],
            "equipment": ["כיסא יציב", "סימון 3 מטר", "שעון", "תמיכה לפי צורך"],
            "setup": ["סמן מרחק 3 מטר", "וודא שאין מכשולים", "אפשר אביזר עזר אם המשתמש רגיל אליו"],
            "instructions": ["קום מהכיסא, לך 3 מטר, הסתובב, חזור ושב; תעד זמן, תמיכה, RPE וסימפטומים."],
            "record_fields": ["seconds", "assistive_device", "support_used", "symptoms", "pain_flag"],
            "scoring_units": ["שניות"],
            "interpretation_rules": ["השווה ל-baseline אישי; זמן טוב יותר באותה בטיחות הוא שיפור", "לא לאבחן סיכון נפילה מהצ׳אט"],
            "action_rules": ["שיפור -> התקדמות קטנה בתפקוד/שיווי", "קושי/חשש נפילה -> תרגול נתמך או הפניה מתאימה"],
            "retest_window": ["כל 4-8 שבועות או אחרי בלוק תפקודי"],
            "safety_limits": ["לא לבצע בלי תמיכה אם יש חשש נפילה; עצור בסחרחורת או כאב חד"],
            "source_refs": ["CDC STEADI Timed Up and Go / TUG"],
        },
        "movement_snapshot": {
            "test_id": "movement_snapshot",
            "goal": "תצפית קצרה לבחירת וריאציות תרגיל ולאבחון תוכנית, לא אבחון רפואי.",
            "population_fit": ["כל משתמש לפני תוכנית כוח או שינוי תרגיל"],
            "equipment": ["משקל גוף", "כיסא/קיר/גומייה לפי צורך"],
            "setup": ["בחר 2-4 דפוסים רלוונטיים: squat/sit-to-stand, hinge, push, pull, step-up או core"],
            "instructions": ["בצע כמה חזרות קלות; תעד שליטה, טווח, כאב, RPE ו-cue או רגרסיה שעזרו."],
            "record_fields": ["pattern", "variation", "range_quality", "pain_flag", "cue_that_helped", "regression_used"],
            "scoring_units": ["תצפית איכותית: יציב/צריך רגרסיה/לא מתאים היום"],
            "interpretation_rules": [
                "השתמש כ-baseline אישי לבחירת וריאציה",
                "תנועה לא נקייה אינה אבחון; היא סימן לבחור cue, טווח או רגרסיה",
            ],
            "action_rules": ["וריאציה יציבה -> תרגיל מתאים", "כאב/חוסר שליטה -> רגרסיה או תרגיל חלופי לאותו דפוס"],
            "retest_window": ["כל 2-4 שבועות או אחרי שינוי תרגיל"],
            "safety_limits": ["עצור בכאב חד, סחרחורת, איבוד שיווי משקל או חשש ממשי"],
            "source_refs": ["NASM Movement Assessments", "ACE Client-Centered Assessments"],
        },
    },
    "concurrent_training_protocols": {
        "general_health_blend": {
            "use_when": ["כאשר המשתמש רוצה גם כושר אירובי וגם כוח/שריר או בריאות כללית."],
            "coaching_goal": ["לשלב כוח ואירובי בצורה פשוטה שמשרתת בריאות ועקביות בלי להפוך את השבוע לעמוס מדי."],
            "planning_rules": [
                "ברוב משתמשי הבריאות, כוח ואירובי יכולים לחיות באותה תוכנית: 2+ ימי כוח ו-150-300 דקות אירובי מתון או פחות עצים לפי יעד.",
                "בחר את מינון האירובי לפי זמינות, התאוששות ומטרה; הליכה, אופניים או חתירה קלה יכולים לתמוך בכושר בלי לשבור אימוני כוח.",
                "אם הזמן קצר, פצל לשבוע פשוט: כוח בימים קבועים והליכות קצרות סביבם במקום אימונים עצימים רבים.",
            ],
            "decision_gate": ["הלוגים מראים שהמשתמש עומד בתוכנית בלי ירידה חדה בביצועים, שינה או כאב."],
            "avoid": ["לא להוסיף HIIT או ריצות קשות רק כי חסר אירובי; התוספת צריכה להתאים להתאוששות ולמטרה."],
        },
        "strength_priority": {
            "use_when": ["כאשר המטרה המרכזית היא כוח, היפרטרופיה או שימור מסת שריר."],
            "coaching_goal": ["לשמור איכות כוח לפני עייפות אירובית גדולה."],
            "planning_rules": [
                "ביום משולב, כוח קודם כאשר כוח/שריר הם המטרה העיקרית, במיוחד לפני רגליים כבדות או תרגיל טכני.",
                "אירובי אחרי כוח צריך להיות קל-בינוני או קצר אם הוא באותו יום; את האימון האירובי הקשה עדיף להפריד כשאפשר.",
                "אם רגליים כבדות נפגעות, החלף חלק מהריצה באופניים, הליכה בשיפוע מתון או אירובי low-impact.",
            ],
            "decision_gate": ["עומסים, חזרות ו-RPE בכוח נשמרים למרות האירובי השבועי."],
            "avoid": ["לא לשים ריצה עצימה לפני סקוואט/hinge כבד אם המטרה היא כוח או טכניקה."],
        },
        "endurance_priority": {
            "use_when": ["כאשר המטרה המרכזית היא סבולת, אירוע ריצה/רכיבה או שיפור יכולת אירובית."],
            "coaching_goal": ["לתת לאירובי המרכזי את האנרגיה הנדרשת בלי לוותר לגמרי על כוח תומך."],
            "planning_rules": [
                "אם סבולת היא המטרה, האימון האירובי האיכותי יכול לבוא קודם, וכוח נשאר תומך בנפח שניתן להתאושש ממנו.",
                "השתמש בכוח 2-3 פעמים בשבוע במינון שמחזק דפוסי תנועה ולא יוצר DOMS שמקלקל ריצות/רכיבות מפתח.",
                "קרוב לאירוע סבולת, שמור כוח אבל הורד נפח ועומס לפי עייפות ולוגים.",
            ],
            "decision_gate": ["אימוני הסבולת המרכזיים נשמרים באיכות טובה ואין DOMS שמפריע לכמה ימים."],
            "avoid": ["לא להוסיף נפח רגליים כבד לפני אימון סבולת מפתח או תחרות קרובה."],
        },
        "same_day_order": {
            "use_when": ["כאשר המשתמש יכול להתאמן רק פעם אחת ביום ורוצה לשלב כוח ואירובי."],
            "coaching_goal": ["לבחור סדר לפי מטרה ולצמצם עייפות מיותרת."],
            "planning_rules": [
                "הכלל הפשוט: המטרה החשובה יותר באה קודם באותו אימון.",
                "אם שתי המטרות דומות ובריאות כללית היא היעד, התחל בכוח טכני קצר ואז אירובי קל-בינוני, או הפרד לפי מה שמעלה עקביות.",
                "אם האירובי הוא חימום, שמור אותו קל וקצר; הוא לא אמור להפוך לאימון שמוריד איכות כוח.",
            ],
            "decision_gate": ["המשתמש מסיים את שני החלקים בטכניקה טובה ו-RPE שלא פוגע באימון הבא."],
            "avoid": ["לא להתעקש על סדר אחד לכולם; סדר הוא החלטת מטרה, לא חוק קבוע."],
        },
        "interference_management": {
            "use_when": ["כאשר כוח/שריר נתקעים אחרי הוספת הרבה אירובי או כאשר הסבולת נפגעת מעומס כוח."],
            "coaching_goal": ["לנהל את אפקט ה-interference בלי להפחיד משתמשים מאירובי."],
            "planning_rules": [
                "interference הוא סיכון תכנוני, לא סיבה להימנע מאירובי; הוא משמעותי יותר כשנפח/עצימות גבוהים מדי ביחס להתאוששות.",
                "ריצה עצימה ונפח impact גבוה נוטים להפריע יותר לכוח/היפרטרופיה ברגליים מאשר אופניים או אירובי low-impact.",
                "אם כוח יורד, בדוק קודם סך נפח אירובי, סוג אירובי, תזמון, שינה ותזונה לפני שמחליף את כל התוכנית.",
            ],
            "decision_gate": ["יש דפוס של ירידה בביצועי כוח/סבולת בכמה לוגים, לא רק אימון אחד חלש."],
            "avoid": ["לא להגיד למשתמש ש-cardio הורג gains; המסר צריך להיות מינון, סוג ותזמון."],
        },
        "recovery_spacing": {
            "use_when": ["כאשר אפשר להפריד בין אימוני כוח ואירובי או לתכנן שבוע עם כמה יחידות."],
            "coaching_goal": ["לשפר התאוששות ואיכות ביצוע על ידי רווחים חכמים בין עומסים דומים."],
            "planning_rules": [
                "כשאפשר, הפרד אימון כוח רגליים ואירובי עצים בכמה שעות לפחות, ולעיתים 24 שעות כאשר הביצועים חשובים.",
                "שמור יום קל או low-impact אחרי שילוב קשה של רגליים ואירובי עצים אם הלוגים מראים עייפות.",
                "באותו יום, פצל בוקר/ערב אם זה מתאים לחיים של המשתמש; אם לא, קצר והורד עצימות במקום לבנות לוח בלתי אפשרי.",
            ],
            "decision_gate": ["ההפרדה משפרת ביצוע, RPE או עקביות בלי לפגוע בשגרה."],
            "avoid": ["לא לבנות spacing מושלם שאי אפשר לבצע; עקביות טובה עדיפה מתזמון אידיאלי על הנייר."],
        },
    },
    "adherence_coaching_rules": [
        "השתמש בשיחה ממוקדת משתמש: שאל שאלה פתוחה, הקשב, שיקף בקצרה, ואז הצע צעד אחד.",
        "יעדי SMART צריכים להיות ספציפיים, מדידים, אפשריים, רלוונטיים ומוגבלים בזמן, אך עדיין פשוטים לביצוע.",
        "פרק חסמים לפי סוג: חוסר זמן, חוסר אנרגיה, חוסר תמיכה, פחד מפציעה, מזג אוויר, עלות, ציוד או מיומנות.",
        "בנה תוכנית גיבוי מראש: אימון מלא, גרסה קצרה, ופעולת מינימום של 5-10 דקות ליום עמוס.",
        "עודד self-monitoring דרך לוגים קצרים; המטרה היא למידה והתאמה, לא ביקורת או אשמה.",
    ],
    "adherence_micro_protocols": {
        "motivational_interviewing_oars": {
            "use_when": ["כאשר המשתמש מבקש מוטיבציה, מתלבט, מתנגד או מתקשה לחזור לשגרה."],
            "coaching_goal": ["לייצר שיחה קצרה ותומכת שמעלה בחירה ופעולה במקום הרצאה."],
            "rules": [
                "השתמש ב-OARS: שאלה פתוחה אחת, חיזוק קצר, שיקוף, וסיכום שמוביל לצעד הבא.",
                "שאל רשות לפני עצה כאשר המשתמש לא ביקש תוכנית: 'רוצה שאציע שתי אפשרויות קצרות?'",
                "חפש change talk: מה חשוב למשתמש, מה כבר עבד, ומה צעד קטן שהוא מוכן לעשות.",
            ],
            "decision_gate": ["המשתמש צריך תמיכה בהחלטה או חזרה לפעולה, לא מידע טכני נוסף."],
            "avoid": ["לא להרצות על משמעת; לא להתווכח עם התנגדות; לא להציף בשלוש שאלות."],
        },
        "barrier_to_plan": {
            "use_when": ["כאשר המשתמש אומר שאין זמן, אנרגיה, ציוד, מוטיבציה או שיש חשש מכאב."],
            "coaching_goal": ["להפוך חסם אחד לתוכנית קטנה ומעשית."],
            "rules": [
                "זהה חסם אחד: זמן, אנרגיה, כאב/חשש, ציוד, מיומנות, מזג אוויר, עלות או תמיכה.",
                "לזמן: גרסת 8-12 דקות; לאנרגיה: RPE נמוך; לציוד: משקל גוף; למוטיבציה: התחלה של 2 דקות.",
                "בכאב חד, סחרחורת או קוצר נשימה חריג, עבור לגבולות safety במקום פתרון התמדה.",
            ],
            "decision_gate": ["החסם ברור מספיק כדי לבחור פעולה אחת ב-24-72 שעות הקרובות."],
            "avoid": ["לא לפתור כל חסם ביותר נפח או עצימות; לא למסגר כאב חד כחסם מנטלי."],
        },
        "implementation_intention": {
            "use_when": ["כאשר המשתמש מוכן להתחייב לצעד הבא או חוזר אחרי פספוס חוזר."],
            "coaching_goal": ["להפוך כוונה כללית לתוכנית אם-אז עם cue ברור."],
            "rules": [
                "תוכנית טובה כוללת אם, אז, זמן/מקום, פעולה קצרה וגרסת obstacle.",
                "דוגמה: אם השעה 19:00 ואני בבית, אז אני נועל נעליים ועושה 10 דקות הליכה.",
                "שמור את הפעולה קטנה מספיק כדי שהמשתמש יוכל לבצע גם ביום בינוני.",
            ],
            "decision_gate": ["יש cue מציאותי ופעולה שמוגדרת בצורה מדידה."],
            "avoid": ["לא להשאיר 'אני אתאמן יותר' בלי זמן, מקום ופעולה; לא לבנות תוכנית גדולה מדי."],
        },
        "minimum_viable_workout": {
            "use_when": ["ביום עמוס, אחרי פספוס, במוטיבציה נמוכה או לפני נטישה של תוכנית."],
            "coaching_goal": ["לשמור זהות ורצף דרך פעולה קצרה במקום לגרור אשמה."],
            "rules": [
                "גרסת מינימום היא 2-10 דקות או דפוס תנועה אחד עד שניים, לא חוב נוסף.",
                "בחר פעולה שהמשתמש יכול לסיים בוודאות: הליכה קצרה, 2 סטים, מוביליטי קל או תרגיל אחד.",
                "אחרי מינימום מוצלח, אל תוסיף אוטומטית עוד; תן לסיום קטן להיחשב.",
            ],
            "decision_gate": ["המטרה של היום היא עקביות, לא שיא ביצועים."],
            "avoid": ["לא לקרוא לזה כישלון; לא להפוך גרסת מינימום לאימון מלא בתחפושת."],
        },
        "self_monitoring_feedback": {
            "use_when": ["אחרי לוג אימון, לוג ארוחה, פספוס או דיווח תחושה."],
            "coaching_goal": ["להפוך לוג להתאמה הבאה ולא לשיפוט."],
            "rules": [
                "שקף את הלוג בקצרה: מה קרה, מה עבד, ומה חסם את הביצוע.",
                "מהלוג בחר התאמה אחת לאימון/ארוחה הבאה: לשמור, להקטין, להזיז, או להחליף.",
                "אם אותו חסם חוזר, עדכן את if-then plan או fallback במקום להאשים את המשתמש.",
            ],
            "decision_gate": ["יש לוג או דיווח שמספיק לקבלת החלטה קטנה."],
            "avoid": ["לא להפוך מעקב לביקורת; לא להסיק דפוס גדול מלוג יחיד בלי זהירות."],
        },
        "relapse_recovery": {
            "use_when": ["אחרי פספוס אימונים, הפסקה, סוף שבוע לא עקבי או חזרה אחרי עומס חיים."],
            "coaching_goal": ["להחזיר את המשתמש למסלול בלי עונש או 'פיצוי' מוגזם."],
            "rules": [
                "פספוס הוא נתון תכנון: מה הפריע, מה הצעד הבא, ומה נשנה כדי שזה יהיה קל יותר.",
                "המלץ לחזור בתוך 24-72 שעות עם גרסה קצרה ולא להשלים נפח חסר בכוח.",
                "שמור על שפה ניטרלית: 'נעדכן' ולא 'נכשלת'.",
            ],
            "decision_gate": ["המשתמש רוצה לחזור למסלול ולא נמצא במצב safety."],
            "avoid": ["לא לתת עונש אימוני אחרי פספוס; לא להכפיל עומס כדי 'לכפר'."],
        },
        "autonomy_choice": {
            "use_when": ["כאשר יש כמה פעולות בטוחות או כשהמשתמש מרגיש נשלט/מותש."],
            "coaching_goal": ["להגדיל מחויבות דרך בחירה במקום פקודה."],
            "rules": [
                "הצע שתי אפשרויות בטוחות וברורות, ותן למשתמש לבחור מה מציאותי.",
                "השתמש בשפה תומכת אוטונומיה: 'אפשר', 'מה יותר מתאים', 'נבחר ביחד'.",
                "כאשר חסר מידע, שאל שאלה אחת שמאפשרת בחירה טובה יותר.",
            ],
            "decision_gate": ["יש לפחות שתי פעולות בטוחות שמתאימות למטרה ולמצב."],
            "avoid": ["לא להשתמש בשפת חובה או בושה; לא להעמיס יותר מדי אפשרויות."],
        },
    },
    "hebrew_coaching_language_protocols": {
        "terminology_register": {
            "use_when": ["בכל תשובת מאמן, במיוחד כשיש מונחי אימון באנגלית או נתוני לוג."],
            "coaching_goal": ["לשמור עברית טבעית וברורה בלי לתרגם בכוח מונחים שמאמנים ומתאמנים משתמשים בהם באנגלית."],
            "rules": [
                "RPE נשאר RPE ומוסבר בקצרה כ'דירוג מאמץ מ-1 עד 10' כאשר המשתמש לא מכיר.",
                "RIR נשאר RIR ומוסבר כ'כמה חזרות נקיות נשארו לך במיכל'.",
                "DOMS יוצג כ'כאבי שרירים מאוחרים (DOMS)' או 'שרירים תפוסים אחרי אימון', לא כ'דומס' לבד.",
                "כתוב חזרות, סטים, אימון, התאוששות וקלוריות; לא 'רפס', לא תרגום מילולי של every fitness term.",
            ],
            "examples": [
                "נשמור היום על RPE 7 בערך: קשה אבל בשליטה.",
                "אם נשארו בערך 2 חזרות במיכל, זה RIR 2 וזה מקום טוב לעצור בו.",
            ],
            "avoid": ["לא לערבב עברית שבורה עם תעתיקים מיותרים; לא להעמיס קיצורים לפני שהמשתמש צריך אותם."],
            "source_refs": ["CDC Plain Language", "ACE Mover Method Study"],
        },
        "response_shape": {
            "use_when": ["כאשר הבוט עונה לשאלה כללית, לוג, פספוס, התאמת תוכנית או בקשת מוטיבציה."],
            "coaching_goal": ["לייצר תשובה קצרה שמרגישה כמו מאמן: מסקנה, סיבה, פעולה אחת, ושאלה אחת רק אם צריך."],
            "rules": [
                "מבנה ברירת מחדל: תשובה קצרה, סיבה אחת, פעולה אחת לביצוע היום.",
                "אם חסר מידע קריטי, שאל שאלת המשך אחת ולא שאלון ארוך.",
                "כאשר יש לוגים, התחל מהמשמעות המעשית שלהם ולא מהרצאה תאורטית.",
            ],
            "examples": [
                "היום לא מעלים משקל. הסיבה: RPE גבוה ושינה חלשה. הפעולה: אותם תרגילים, 2 סטים פחות.",
                "המטרה היום פשוטה: לסיים גרסה קצרה של אימון A ולשמור רצף.",
            ],
            "avoid": ["לא לפתוח במאמר ארוך; לא לתת חמישה צעדים כאשר פעולה אחת מספיקה."],
            "source_refs": ["CDC Plain Writing", "ACE IFT / Mover Method"],
        },
        "plain_language_autonomy": {
            "use_when": ["כאשר המשתמש מתלבט, עייף, פספס, או מרגיש לחץ סביב התוכנית."],
            "coaching_goal": ["לתת שפה ברורה ותומכת בחירה שמגבירה עקביות בלי אשמה."],
            "rules": [
                "השתמש בשפה של בחירה: אפשר, נבחר, מה יותר מתאים, נשמור על רצף.",
                "הכר בפספוס כמידע תכנון ולא ככישלון אישי.",
                "במקום 'חייב' או 'אין תירוצים', הצע שתי אפשרויות בטוחות או גרסת מינימום.",
            ],
            "examples": [
                "אפשר לבחור היום בין הליכה של 20 דקות לבין אימון כוח קצר; מה יותר מציאותי?",
                "פספסת אימון, לא קרה כלום. לא מחזירים הכול ביום אחד; חוזרים בצעד קטן.",
            ],
            "avoid": ["לא להשתמש בבושה, אשמה, שפת חובה או פיצוי עונשי אחרי פספוס."],
            "source_refs": ["Motivational Interviewing Network of Trainers", "Self-Determination Theory Exercise Review"],
        },
        "jargon_policy": {
            "use_when": ["כאשר תשובה כוללת מושגים כמו Zone 2, HIIT, deload, maintenance או progressive overload."],
            "coaching_goal": ["לשמור מונחים מקצועיים שימושיים אבל להפוך אותם למעשיים למשתמש."],
            "rules": [
                "Zone 2 נשאר Zone 2 או אזור 2, עם הסבר: קצב שאפשר לדבר בו במשפטים קצרים.",
                "HIIT נשאר HIIT או 'אימון אינטרוולים עצים'; לא מציעים אותו כשאין בסיס או התאוששות.",
                "deload הוא 'שבוע הורדת עומס' למשתמש כללי; advanced user יכול לקבל גם את המונח deload.",
                "progressive overload עדיף 'העלאת עומס הדרגתית': עוד חזרה, עוד סט או קצת יותר משקל כשהשליטה טובה.",
            ],
            "examples": [
                "30 דקות Zone 2: קצב שאתה יכול לדבר בו במשפטים קצרים.",
                "השבוע נעשה שבוע הורדת עומס: פחות סטים ופחות קושי, אבל שומרים על הרגל האימון.",
            ],
            "avoid": ["לא להשתמש בז'רגון כדי להישמע מקצועי; מונח נשאר רק אם הוא עוזר לפעולה."],
            "source_refs": ["CDC Plain Language", "ACSM Monitoring Aerobic Exercise Intensity"],
        },
        "correction_patterns": {
            "use_when": ["כאשר המשתמש פספס, אכל אחרת מהתכנון, נכשל ביעד, או רוצה לפצות באימון/דיאטה קשים."],
            "coaching_goal": ["להחזיר למסלול בלי עונש, פיצוי או שפה שמובילה להתנהגות קיצונית."],
            "rules": [
                "התחל בנרמול קצר: פספוס הוא נתון תכנון, לא אופי.",
                "אל תיתן אימון פיצוי; תן חזרה קצרה לתוכנית או גרסת מינימום.",
                "אם המשתמש מבקש פיצוי תזונתי/אימוני קיצוני, החזר לפעולה בטוחה ומדידה.",
            ],
            "examples": [
                "לא קרה כלום. אל תנסה להחזיר הכול ביום אחד; היום עושים 25 דקות וממשיכים מחר.",
                "המטרה היא לא להעניש את עצמך, אלא לחזור למסלול עם פעולה אחת שאפשר לבצע.",
            ],
            "avoid": ["לא להציע עונש אירובי, צום קיצוני, או הכפלת נפח כדי 'לכפר'."],
            "source_refs": ["Motivational Interviewing Network of Trainers", "Community Guide Behavior Change Programs"],
        },
    },
    "behavior_change_protocols": {
        "abc_conversation": {
            "goal": "להפוך שיחת מוטיבציה לתהליך קצר שבו המשתמש שותף לבחירת הצעד הבא.",
            "use_when": ["בקשת מוטיבציה", "חזרה אחרי הפסקה", "משתמש לא יודע איך להתחיל"],
            "coach_moves": [
                "שאל שאלה פתוחה אחת על מה המשתמש רוצה להשיג ומה כבר אפשרי השבוע.",
                "שקף בקצרה את המטרה או הקושי במקום להרצות.",
                "שתף פעולה על פעולה אחת קטנה שהמשתמש בוחר ולא רק מקבל כהוראה.",
            ],
            "avoid": [
                "לא להפוך את השיחה להרצאה ארוכה על כוח רצון.",
                "לא לבחור למשתמש תוכנית גדולה לפני שהחסם המרכזי ברור.",
            ],
            "next_action": "סיים עם פעולה אחת ל-24-48 שעות ושאלת מעקב אחת בלבד אם חסר מידע.",
        },
        "barrier_problem_solving": {
            "goal": "לזהות חסם ספציפי ולהתאים פתרון מעשי במקום להאשים את המשתמש בחוסר משמעת.",
            "use_when": ["פספוסי אימון", "חוסר זמן", "חוסר אנרגיה", "חוסר תמיכה", "פחד מפציעה"],
            "coach_moves": [
                "סווג את החסם: זמן, אנרגיה, תמיכה, פחד מפציעה, מזג אוויר, ציוד, עלות או מיומנות.",
                "בחר פתרון אחד: זמן קבוע ביומן, גרסה קצרה, פעילות קלה, תמיכה מאדם נוסף או תרגיל פשוט יותר.",
                "הפוך את הפתרון למדיד: מתי, איפה, כמה דקות ומה נחשב הצלחה.",
            ],
            "avoid": [
                "לא להציע עוד נפח כאשר החסם הוא עקביות.",
                "לא להתעלם מפחד מפציעה; בחר וריאציה בטוחה וקלה יותר.",
            ],
            "next_action": "נסח ניסוי קטן לשבוע הקרוב ובקש מהמשתמש לתעד אם החסם הופיע שוב.",
        },
        "action_plan": {
            "goal": "לגשר בין כוונה טובה לבין פעולה בפועל בעזרת תוכנית אם-אז.",
            "use_when": ["המשתמש רוצה להתאמן אבל לא מתחיל", "שבוע עמוס", "הרגל חדש"],
            "coach_moves": [
                "בנה משפט אם-אז: אם מגיע הזמן/המצב שנבחר, אז אני מבצע פעולה מוגדרת.",
                "קבע שעה, מקום, משך וגרסת מינימום שאפשר לבצע גם ביום לא מושלם.",
                "חבר את הפעולה למטרה שהמשתמש כבר אמר שחשובה לו.",
            ],
            "avoid": [
                "לא ליצור תוכנית אם-אז בלי כוונה אמיתית או ערך ברור למשתמש.",
                "לא לקבוע פעולה כללית כמו 'להתאמן יותר' בלי זמן ומקום.",
            ],
            "next_action": "החזר למשתמש משפט אם-אז אחד קצר ומוכן לביצוע.",
        },
        "self_monitoring_feedback": {
            "goal": "להשתמש בלוגים כמשוב אימוני והתנהגותי, לא ככלי ביקורת.",
            "use_when": ["תיעוד אימון", "תיעוד ארוחה", "בדיקת התקדמות", "חוסר עקביות"],
            "coach_moves": [
                "בקש לוג קצר: מה בוצע, כמה זמן, RPE או תחושה, ומה הפריע אם לא בוצע.",
                "זהה דפוס אחד בלבד מתוך המעקב לפני שינוי התוכנית.",
                "תן משוב חיובי ממוקד על פעולה שנעשתה, ואז התאמה קטנה לאימון הבא.",
            ],
            "avoid": [
                "לא להציג פספוס ככישלון אישי.",
                "לא לבקש מעקב מפורט מדי אם זה יפגע בהתמדה.",
            ],
            "next_action": "בחר מדד מעקב אחד לשבוע הקרוב: אימונים, דקות הליכה, ארוחות חלבון או שינה.",
        },
        "social_support": {
            "goal": "להגדיל סיכוי להתמדה באמצעות תמיכה סביבתית פשוטה.",
            "use_when": ["המשתמש מתאמן לבד", "חוסר מוטיבציה", "קושי לשמור על תזמון"],
            "coach_moves": [
                "שאל מי יכול לתת תמיכה מינימלית: חבר, בן משפחה, קבוצת אימון או מאמן אנושי.",
                "הצע הזמנה פשוטה לפעילות משותפת או הודעת accountability קצרה.",
                "הפוך תמיכה לפעולה ספציפית: קביעת זמן, תזכורת או הליכה משותפת.",
            ],
            "avoid": [
                "לא להניח שיש למשתמש תמיכה זמינה.",
                "לא להפוך תמיכה חברתית לתלות או לבושה אם הוא מעדיף להתאמן לבד.",
            ],
            "next_action": "הצע אדם אחד או מנגנון אחד שיכול לעזור השבוע בלי להכביד.",
        },
        "relapse_recovery": {
            "goal": "להחזיר את המשתמש למסלול אחרי פספוס בלי להגדיל אשמה או עומס.",
            "use_when": ["פספוס אימון", "הפסקה של כמה ימים", "ירידה ברצף", "חזרה אחרי עומס חיים"],
            "coach_moves": [
                "נרמל פספוס כמידע תכנוני ולא ככישלון.",
                "בחר חזרה הדרגתית: אימון קצר, נפח נמוך או פעולה של 5-10 דקות.",
                "זהה מה הפיל את הרצף ובנה תוכנית גיבוי לפני השבוע הבא.",
            ],
            "avoid": [
                "לא להמליץ להשלים את כל מה שפוספס בבת אחת.",
                "לא להוסיף אימון ענישה או דיאטת פיצוי.",
            ],
            "next_action": "החזר פעולה אחת של חזרה למסלול היום או מחר, עם נפח נמוך וברור.",
        },
    },
    "population_adjustments": {
        "older_adults": [
            "שלב אירובי, כוח ושיווי משקל; בחר עצימות יחסית ליכולת ולא לפי אגו או מספרים כלליים.",
            "העדף תרגילים שמשרתים תפקוד יומי: קימה מכיסא, נשיאה, עלייה במדרגה, משיכה ודחיפה יציבה.",
            "שמור התקדמות איטית יותר כאשר התאוששות, שיווי משקל או ביטחון בתנועה נמוכים.",
        ],
        "chronic_conditions": [
            "פעילות מותאמת ליכולת עדיפה לרוב מחוסר פעילות; התחל ממה שהמשתמש מסוגל לבצע בעקביות.",
            "התחשב בתסמינים, אנרגיה, תרופות והנחיות קיימות שהמשתמש קיבל, בלי לאבחן או לשנות טיפול.",
            "בחר עצימות מתונה וניתנת לשיחה כאשר חסר מידע, והתקדם לפי תגובת הגוף והלוגים.",
        ],
        "returning_after_break": [
            "אחרי הפסקה, התחל בהדרגה עם פחות נפח ועצימות מהעבר, גם אם המשתמש היה מתקדם לפני כן.",
            "בשבועיים הראשונים, יעד מרכזי הוא חזרה לרצף וטכניקה ולא בדיקת גבולות.",
            "התקדם לפי תחושת מאמץ, התאוששות והיעדר כאב חד.",
        ],
        "limited_equipment": [
            "משקל גוף, גומיות, תיק, מגבת, מדרגה וקצב איטי יכולים ליצור גירוי אימוני יעיל.",
            "כאשר אין עומס כבד, השתמש בטווח תנועה, האטת קצב, עצירות, חד-צדדיות או יותר חזרות.",
            "שמור דפוסי תנועה מרכזיים במקום להתעקש על תרגיל חדר כושר מסוים.",
        ],
    },
    "client_profile_programming": {
        "beginner_foundation": {
            "entry_point": [
                "מתאמן חדש, חוזר אחרי הפסקה, או משתמש בלי לוגים שמראים סבילות לעומס.",
                "בחר שלב ייצוב/תנועה בסיסית לפני נפח גבוה או עומסים כבדים.",
            ],
            "primary_focus": [
                "יציבה, שליטה, טכניקה, הרגל שבועי ותחושת מסוגלות.",
                "כיסוי דפוסי תנועה מרכזיים בלי כאב חד ובלי מורכבות מיותרת.",
            ],
            "programming_rules": [
                "התחל ב-12-20 חזרות או עומס קל-בינוני כאשר המטרה היא ייצוב ושליטה.",
                "העדף 1-3 סטים, קצב איטי, וריאציות פשוטות ומנוחות שמאפשרות טכניקה נקייה.",
                "התקדם דרך חזרות, סטים או תדירות רק אחרי עקביות וטווח תנועה ללא כאב.",
            ],
            "progression_gate": [
                "המשתמש השלים כמה אימונים עם טכניקה יציבה, RPE סביר וללא כאב חד.",
                "הלוגים מראים שהאימון לא פוגע בהתאוששות או ברצף השבועי.",
            ],
            "avoid": [
                "לא להתחיל בטכניקות מתקדמות, כשל שרירי תדיר או בדיקות 1RM.",
                "לא להחליף תוכנית בכל שבוע לפני שיש בסיס עקבי.",
            ],
        },
        "intermediate_advanced": {
            "entry_point": [
                "יש היסטוריית אימון ולוגים שמראים שליטה, התאוששות ועקביות.",
                "המשתמש כבר מכיר תרגילים מרכזיים ויכול לדווח RPE/RIR או ביצועים.",
            ],
            "primary_focus": [
                "ספציפיות למטרה, ניהול נפח/עצימות, בלוקים פשוטים ומעקב אחר ביצועים.",
                "שימור טכניקה גם תחת עומס גבוה יותר או נפח גבוה יותר.",
            ],
            "programming_rules": [
                "חלק את התוכנית לבלוקים של 3-6 שבועות עם יעד ברור: נפח, כוח, טכניקה או התאוששות.",
                "שנה משתנה מרכזי אחד בכל פעם: עומס, סטים, חזרות, תדירות או בחירת תרגיל.",
                "השתמש ב-deload או שבוע קל כאשר ביצועים יורדים, RPE עולה או התאוששות נשחקת.",
            ],
            "progression_gate": [
                "ביצועים עולים או יציבים בלי כאב וללא ירידה בעקביות.",
                "המשתמש עומד בנפח הנוכחי לפני הוספת עומס או מורכבות.",
            ],
            "avoid": [
                "לא להוסיף עומס, נפח, תדירות ומורכבות יחד.",
                "לא להשתמש בטכניקות מתקדמות כדי לכסות על חוסר עקביות בסיסית.",
            ],
        },
        "older_adult": {
            "entry_point": [
                "משתמש מבוגר או כל מי שמדווח על חשש מנפילות, ירידה בתפקוד, שיווי משקל או ביטחון בתנועה.",
                "בחר מינון לפי יכולת ומצב, לא לפי מספרים של מתאמן צעיר.",
            ],
            "primary_focus": [
                "שילוב כוח, אירובי ושיווי משקל לשימור תפקוד יומי.",
                "תרגילים שימושיים: קימה מכיסא, עלייה במדרגה, נשיאה, משיכה ודחיפה בטוחה.",
            ],
            "programming_rules": [
                "שאף בהדרגה ל-150 דקות פעילות אירובית מתונה בשבוע כאשר היכולת מאפשרת.",
                "שלב לפחות 2 ימי כוח לכל קבוצות השרירים המרכזיות, עם התאמה ליכולת ותסמינים.",
                "הוסף תרגילי מאזן ושיווי משקל כמו קימה מכיסא, הליכת עקב-בוהן או עמידה נתמכת.",
            ],
            "progression_gate": [
                "המשתמש מבצע את התרגילים בביטחון, ללא סחרחורת, כאב חד או אובדן שיווי משקל.",
                "התאוששות ותפקוד יומי נשמרים אחרי האימונים.",
            ],
            "avoid": [
                "לא לכפות עומס גבוה, קפיצות או תרגילי שיווי משקל ללא תמיכה.",
                "לא להתעלם מתסמינים חריגים או הוראות מקצועיות קיימות.",
            ],
        },
        "limited_time": {
            "entry_point": [
                "זמינות קצרה, שבוע עמוס, או משתמש שמפספס כי האימון ארוך מדי.",
                "בחר גרסת מינימום במקום לוותר על האימון.",
            ],
            "primary_focus": [
                "שמירת רצף עם מעט תרגילים בעלי החזר גבוה.",
                "פחות מעבר בין תחנות ויותר דפוסים מרכזיים.",
            ],
            "programming_rules": [
                "בחר 3-5 תרגילים מורכבים שמכסים רגליים/hinge, דחיפה, משיכה וליבה.",
                "הגדר מינימום ביצוע: 10-25 דקות, 1-3 סטים, או סבב קצר לפי יכולת.",
                "קצר נפח לפני שאתה מבטל חימום קצר, טכניקה או בטיחות.",
            ],
            "progression_gate": [
                "המשתמש משלים את גרסת המינימום כמה פעמים בשבוע בלי דחייה או עומס יתר.",
                "יש זמן ואנרגיה להוסיף סט, תרגיל או יום נוסף.",
            ],
            "avoid": [
                "לא לדחוס אימון מלא לתוך חלון קצר באופן שמפרק טכניקה.",
                "לא להפוך כל אימון קצר לאימון עצים מאוד.",
            ],
        },
        "limited_equipment": {
            "entry_point": [
                "אימון ביתי, נסיעה, חדר כושר לא זמין או ציוד מצומצם.",
                "החלט לפי דפוסי תנועה ולא לפי שם תרגיל ספציפי.",
            ],
            "primary_focus": [
                "מינון מאמץ דרך טווח, קצב, חד-צדדיות, עצירות וחזרות.",
                "שימוש במשקל גוף, גומיות, תיק, מגבת, מדרגה או משקולות יד קלות.",
            ],
            "programming_rules": [
                "בנה סביב משקל גוף וגומיות כאשר אין עומס חיצוני כבד.",
                "העלה קושי דרך קצב איטי, טווח תנועה, עצירה, תרגיל חד-צדדי או עוד חזרות.",
                "שמור דפוסי סקוואט/hinge/דחיפה/משיכה/ליבה גם בלי מכונות או מוט.",
            ],
            "progression_gate": [
                "המשתמש מגיע קרוב למאמץ יעד בטכניקה טובה עם הציוד הזמין.",
                "לפני קניית ציוד, בדוק אם וריאציה, קצב או נפח פותרים את הבעיה.",
            ],
            "avoid": [
                "לא להציג חדר כושר כתנאי להתקדמות.",
                "לא לבחור תרגיל מאולתר שמסכן יציבות או אחיזה.",
            ],
        },
        "strength_goal": {
            "entry_point": [
                "המטרה המרכזית היא כוח והמשתמש מסוגל לבצע תרגילים מרכזיים בשליטה.",
                "התחל שמרני אם אין היסטוריית עומסים או טכניקה מתועדת.",
            ],
            "primary_focus": [
                "תרגילים מורכבים מוקדם באימון, מנוחות ארוכות וטכניקה יציבה.",
                "עומס איכותי שניתן לשחזר, לא מקסימום בכל אימון.",
            ],
            "programming_rules": [
                "לכוח מתקדם יותר, עומסים סביב 80% 1RM ומעלה יכולים להתאים רק עם בסיס וטכניקה.",
                "טווח 1-5 חזרות מתאים לכוח מרבי; לרוב המשתמשים 4-6 חזרות שמרני יותר בתחילת הדרך.",
                "נוח 2-5 דקות בתרגילים כבדים ושמור נפח מספיק אבל לא כזה ששובר התאוששות.",
            ],
            "progression_gate": [
                "כל הסטים הושלמו בטכניקה יציבה, בלי כאב, ועם RPE שאינו קיצוני.",
                "המשתמש מתאושש מספיק כדי לשמור ביצועים בין אימונים.",
            ],
            "avoid": [
                "לא לבצע בדיקת 1RM למתחיל או כשיש כאב/עייפות גבוהה.",
                "לא להוסיף משקל כשהטכניקה או טווח התנועה מתפרקים.",
            ],
        },
        "hypertrophy_goal": {
            "entry_point": [
                "המטרה היא בניית שריר והמשתמש יכול להתאמן בנפח עקבי.",
                "בחר נפח לפי התאוששות, לא לפי תוכנית של מישהו אחר.",
            ],
            "primary_focus": [
                "נפח איכותי, קרבה סבירה לכשל, טכניקה ושינה/תזונה תומכות.",
                "תדירות שמאפשרת לפגוע בקבוצת שריר יותר מפעם בשבוע כשזה מתאים.",
            ],
            "programming_rules": [
                "6-12 חזרות הוא טווח מרכזי להיפרטרופיה, עם 8-15 שימושי כשציוד קל או צריך שליטה.",
                "כ-10 סטים לקבוצת שריר בשבוע הוא עוגן פתיחה סביר, ואז מתאימים לפי התאוששות וביצועים.",
                "שמור לרוב 1-3 חזרות ברזרבה ואל תרדוף אחרי כשל בכל סט.",
            ],
            "progression_gate": [
                "הנפח הנוכחי לא גורם לירידה בביצועים, כאב או עייפות מתמשכת.",
                "המשתמש משלים את רוב האימונים ויכול להוסיף חזרות, סט או עומס קטן.",
            ],
            "avoid": [
                "לא להוסיף סטים בלי לבדוק התאוששות ולוגים.",
                "לא להציג כאב שרירי קיצוני כסימן שחייבים להתקדם.",
            ],
        },
        "fat_loss_goal": {
            "entry_point": [
                "המטרה היא ירידה בשומן, שינוי הרכב גוף או שיפור בריאות מטבולית כללית.",
                "האימון צריך לתמוך בהרגלים, לא להפוך לעונש קלורי.",
            ],
            "primary_focus": [
                "שימור כוח ושריר, הליכה/אירובי נגיש ותיעוד תזונה בטווחים.",
                "עקביות שבועית וגרעון מתון דרך הרגלים, לא דיאטת קיצון.",
            ],
            "programming_rules": [
                "שלב אימוני כוח עם אירובי קל-בינוני או צעדים כדי לשמור שריר ולשפר הוצאה אנרגטית.",
                "התחל מתדירות שאפשר לבצע גם בשבוע עמוס; כוח 2-4 ימים ואירובי נגיש לפי התאוששות.",
                "שמור חלבון, שינה ונפח אימון שאפשר להתאושש ממנו בזמן גרעון.",
            ],
            "progression_gate": [
                "המשתמש מתמיד בלי רעב קיצוני, עייפות גבוהה או ירידה חדה בביצועים.",
                "הלוגים מראים שהרגלי תזונה ואימון יציבים לפני העלאת עומס.",
            ],
            "avoid": [
                "לא לעודד דיאטת קיצון, אימוני ענישה או שריפת קלוריות כפיצוי.",
                "לא להעלות אירובי אם זה פוגע בכוח, שינה או עקביות.",
            ],
        },
        "endurance_goal": {
            "entry_point": [
                "המטרה היא סבולת, כושר אירובי או אירוע ריצה/רכיבה/הליכה.",
                "התחל מבסיס אירובי לפני אינטרוולים רבים.",
            ],
            "primary_focus": [
                "בסיס אירובי, התקדמות הדרגתית במשך/תדירות, וניהול עצימות עם talk test או RPE.",
                "שילוב כוח כדי לתמוך ברקמות ובתפקוד, בלי לפגוע באימוני הסבולת.",
            ],
            "programming_rules": [
                "בנה בסיס אירובי עם עבודה קלה-בינונית שבה אפשר לדבר במשפטים קצרים לפי talk test.",
                "העלה קודם משך או תדירות, ורק אחר כך עצימות או אינטרוולים.",
                "רוב העבודה צריכה להישאר קלה-בינונית; עצימות גבוהה מגיעה במינון קטן אחרי בסיס עקבי.",
            ],
            "progression_gate": [
                "המשתמש מסיים אימונים בלי ירידה חדה בהתאוששות או כאבים חוזרים.",
                "אפשר להוסיף 5-10 דקות או יחידת אימון קלה לפני אינטרוולים.",
            ],
            "avoid": [
                "לא להתחיל מהרבה HIIT או Zone 3 בלי בסיס.",
                "לא להגדיל נפח שבועי בחדות אחרי פספוסים.",
            ],
        },
    },
    "movement_limitation_adaptations": {
        "joint_pain_general": {
            "signal": [
                "משתמש מדווח שכאב מפרק מופיע בתרגיל מסוים, בלי סימנים מסוכנים שמחייבים עצירה מלאה.",
                "המטרה היא למצוא וריאציה נסבלת, לא לאבחן את מקור הכאב.",
            ],
            "coaching_goal": [
                "שמר דפוס תנועה ואימון ככל האפשר דרך התאמת תרגיל.",
                "העדף טווח ללא כאב, עומס מתאים ושליטה במקום ביטול אוטומטי של האימון.",
            ],
            "adjustment_rules": [
                "שנה קודם טווח תנועה, תנוחה, קצב או התנגדות לפני שאתה מחליף את כל התוכנית.",
                "אם תרגיל עדיין כואב, החלף לתרגיל אחר שמשרת אותו דפוס בלי כאב חד.",
                "בדוק אחרי ההתאמה: כאב, RPE, שליטה והאם המשתמש מסוגל לחזור על זה בשבוע הבא.",
            ],
            "exercise_options": [
                "הקטנת טווח תנועה",
                "הורדת עומס",
                "וריאציה נתמכת",
                "תרגיל חלופי לאותו דפוס תנועה",
            ],
            "progression_gate": [
                "שני אימונים או יותר בוצעו בטווח החדש בלי החמרה.",
                "המשתמש מדווח על שליטה וביטחון, לא רק על סיום האימון.",
            ],
            "avoid": [
                "לא לדחוף דרך כאב חד או מחמיר.",
                "לא להבטיח שההתאמה מטפלת בפציעה.",
            ],
        },
        "knee_sensitive_lower_body": {
            "signal": [
                "אי נוחות בברך בסקוואט, לאנג׳, step-up או ירידה במדרגות.",
                "אין דיווח על נפיחות חריגה, קריסה, נעילה או טראומה חריפה שמחייבים הפניה.",
            ],
            "coaching_goal": [
                "שמור אימון רגליים דרך עומק, זווית ועומס שמתאימים לברך.",
                "העבר עומס לירך/גלוטס כשצריך בלי לוותר על חיזוק ארבע ראשי לאורך זמן.",
            ],
            "adjustment_rules": [
                "הקטן עומק סקוואט או השתמש בסקוואט לקופסה כדי לשלוט בטווח תנועה.",
                "בחר step-up נמוך או תרגיל נתמך כאשר ירידה עמוקה מכאיבה.",
                "השתמש ב-hip hinge, גשר גלוטס או דדליפט רומני קל כאשר כפיפת ברך עמוקה לא נסבלת.",
            ],
            "exercise_options": [
                "סקוואט לקופסה",
                "step-up נמוך עם תמיכה",
                "sit-to-stand מכיסא",
                "גשר גלוטס",
                "דדליפט רומני קל",
            ],
            "progression_gate": [
                "המשתמש משלים את הטווח הנוכחי בלי כאב חד או החמרה למחרת.",
                "אפשר להגדיל עומק, חזרות או עומס אחד בכל פעם.",
            ],
            "avoid": [
                "לא לקפוץ או לבצע לאנג׳ עמוק כשזה מעורר כאב.",
                "לא להכריח ברך לעומק או זווית שהמשתמש לא שולט בהם.",
            ],
        },
        "low_back_sensitive_training": {
            "signal": [
                "רגישות בגב תחתון בזמן hinge, סקוואט, נשיאה או תרגילי ליבה.",
                "אין סימני חירום כמו חולשה פתאומית, אובדן תחושה, טראומה או תסמינים חריגים.",
            ],
            "coaching_goal": [
                "להשאיר את המשתמש פעיל עם פעילות low-impact ותנועות נשלטות.",
                "לבנות מחדש שליטה בירך, ליבה וגלוטס בלי עומס שמייצר כאב.",
            ],
            "adjustment_rules": [
                "העדף פעילות low-impact והתקדמות הדרגתית במקום מנוחה מוחלטת אם אין סימני סיכון.",
                "התחל ב-hip hinge קל, glute bridge, dead bug או bird dog לפי סבילות.",
                "הורד עומס, טווח או מהירות כאשר הגב מפצה במקום הירך והליבה.",
            ],
            "exercise_options": [
                "glute bridge",
                "dead bug",
                "bird dog",
                "hip hinge לקיר",
                "הליכה או אופניים קלים",
            ],
            "progression_gate": [
                "המשתמש מבצע תרגילי ליבה/ירך עם נשימה ושליטה וללא החמרת כאב.",
                "אפשר לחזור בהדרגה ל-hinge טעון רק אחרי שליטה בטווח קל.",
            ],
            "avoid": [
                "לא לבצע הרמות כבדות, כפיפות חוזרות או פיתולים תחת עומס כאשר הם מגבירים כאב.",
                "לא לאבחן פריצת דיסק, סיאטיקה או מקור כאב.",
            ],
        },
        "shoulder_sensitive_push_pull": {
            "signal": [
                "אי נוחות בכתף בלחיצה, הרמה מעל הראש, שכיבת סמיכה, חתירה או משיכה.",
                "המטרה היא להתאים זווית, טווח ותמיכת שכמה לפני ביטול כל אימון פלג גוף עליון.",
            ],
            "coaching_goal": [
                "שמר דחיפה/משיכה בטווח כתף נוח.",
                "חזק שליטת שכמה ו-rotator cuff לפני עומס או טווח גבוה יותר.",
            ],
            "adjustment_rules": [
                "העבר לחיצה לשיפוע, לחיצת רצפה או אחיזה ניטרלית אם טווח כתף מלא כואב.",
                "בחר חתירה נתמכת, משיכה עם גומייה או טווח קצר כאשר שכמה לא יציבה.",
                "שלב תרגילי rotator cuff ושכמה קלים כמו איזומטריה או external rotation ללא כאב.",
            ],
            "exercise_options": [
                "שכיבת סמיכה בשיפוע",
                "לחיצת רצפה",
                "חתירה נתמכת",
                "external rotation עם גומייה",
                "איזומטריה לכתף",
            ],
            "progression_gate": [
                "טווח התנועה גדל בלי כאב והכתף נשארת יציבה.",
                "המשתמש שולט בשכמות לפני הוספת עומס או לחיצה מעל הראש.",
            ],
            "avoid": [
                "לא ללחוץ מעל הראש בכאב חד.",
                "לא להשתמש במשיכה מאחורי הראש או בטווח שמייצר צביטה.",
            ],
        },
        "wrist_sensitive_push_support": {
            "signal": [
                "שורש כף היד רגיש בשכיבות סמיכה, פלאנק, burpee או תרגילי תמיכה על כפות ידיים.",
                "אין סימן לטראומה חריפה, נפיחות חריגה או אובדן תפקוד.",
            ],
            "coaching_goal": [
                "שמר תרגילי דחיפה וליבה עם מנח שורש כף יד נסבל.",
                "הפחת עומס הארכה על שורש כף היד בלי לוותר על הדפוס.",
            ],
            "adjustment_rules": [
                "בחר אחיזה ניטרלית על ידיות, משקולות או אגרופים אם זה נוח יותר.",
                "העלה שיפוע בשכיבת סמיכה כדי להקטין עומס על שורש כף היד.",
                "החלף פלאנק על כפות ידיים לפלאנק אמות כאשר תמיכה על כף היד לא נסבלת.",
            ],
            "exercise_options": [
                "שכיבת סמיכה בשיפוע",
                "שכיבת סמיכה על ידיות",
                "פלאנק אמות",
                "לחיצת חזה עם משקולות באחיזה ניטרלית",
            ],
            "progression_gate": [
                "המנח החדש מאפשר סטים ללא כאב או נימול.",
                "אפשר להוריד שיפוע או להאריך זמן תמיכה רק אם השליטה נשמרת.",
            ],
            "avoid": [
                "לא לכפות הארכה עמוקה של שורש כף היד.",
                "לא להמשיך בתרגיל אם מופיע נימול, כאב חד או ירידה באחיזה.",
            ],
        },
        "ankle_hip_mobility_limited": {
            "signal": [
                "משתמש מתקשה להגיע לעומק סקוואט, לאנג׳ או step-up בגלל קרסול/ירך/שיווי משקל.",
                "אין צורך לאבחן; משתמשים בהתאמת טווח ומנח כדי לשמור דפוס תנועה.",
            ],
            "coaching_goal": [
                "לאפשר תנועה איכותית בטווח שימושי לפני עומק מלא.",
                "לבנות ניידות ושליטה דרך וריאציה מתאימה.",
            ],
            "adjustment_rules": [
                "הקטן עומק או השתמש בסקוואט לקופסה כאשר הטווח המלא מפרק טכניקה.",
                "נסה הגבהת עקב מתונה, עמידה רחבה יותר או תמיכה לפי נוחות ושליטה.",
                "בחר step-up נמוך או split squat נתמך כאשר שיווי משקל מגביל.",
            ],
            "exercise_options": [
                "סקוואט לקופסה",
                "סקוואט עם הגבהת עקב",
                "split squat נתמך",
                "step-up נמוך",
                "ניידות קרסול דינמית",
            ],
            "progression_gate": [
                "המשתמש שומר כף רגל יציבה, ברך במסלול נוח וגו בשליטה.",
                "מגדילים עומק או מורכבות רק אחרי שהטווח הנוכחי עקבי.",
            ],
            "avoid": [
                "לא לרדוף אחרי עומק על חשבון כאב או קריסה.",
                "לא להוסיף עומס לפני שהמשתמש שולט בטווח.",
            ],
        },
    },
    "special_population_programming": {
        "youth_resistance_training": {
            "use_when": [
                "המשתמש הוא ילד/נער או מבקש תוכנית לנוער.",
                "המטרה היא כושר, ספורט, ביטחון בתנועה או חיזוק כללי, לא מקסימום עומס.",
            ],
            "coaching_goal": [
                "לבנות שליטה, טכניקה, יציבות מפרקים והרגלי אימון טובים.",
                "לחזק תנועה ומשחק פעיל בלי להפוך אימון ילדים לגרסת מבוגר מוקטנת.",
            ],
            "programming_rules": [
                "נוער צריך לשאוף ל-60 דקות פעילות מתונה-עצימה ביום כחלק ממשחק, ספורט או תנועה מגוונת.",
                "באימוני התנגדות, טכניקה ושליטה באים לפני עומס, נפח או מורכבות.",
                "התחל ממשקל גוף, גומיות, מטאטא/מקל טכני או עומסים קלים וחזרות גבוהות.",
                "התקדם לפי בגרות, הקשבה להוראות, שליטה בתנועה ויכולת לבצע סטים בטוחים.",
            ],
            "progression_gate": [
                "הנער מבצע את התרגיל בטכניקה יציבה לאורך כל הסט.",
                "יש השגחה מתאימה, סביבת אימון בטוחה והבנה של כללי בטיחות בסיסיים.",
            ],
            "avoid": [
                "לא להשתמש בבדיקות 1RM או מקסימום עומס כמדד רגיל לנוער מתחיל.",
                "לא להעתיק תוכנית כוח/בודיבילדינג של מבוגרים לילדים.",
                "לא לעודד תוספי ביצועים או עומסים מתקדמים בלי מסגרת מקצועית מתאימה.",
            ],
        },
        "pregnancy_postpartum_general": {
            "use_when": [
                "משתמשת מציינת הריון, אחרי לידה, או חזרה לפעילות בתקופה סביב לידה.",
                "המידע הוא כללי בלבד ואינו מחליף ליווי רפואי או פיזיותרפיה רצפת אגן.",
            ],
            "coaching_goal": [
                "לשמור פעילות מתונה, כוח בסיסי ותחושת מסוגלות לפי מצב ותחושה.",
                "להתאים עומס, תנוחה ונשימה במקום לרדוף אחרי ביצועי שיא.",
            ],
            "programming_rules": [
                "במצב לא מסובך, יעד כללי הוא 150 דקות פעילות אירובית מתונה בשבוע בזמן הריון ואחרי לידה.",
                "אפשר לשלב כוח קל-בינוני, גומיות ומשקל גוף אם זה מרגיש טוב ואין הנחיה רפואית אחרת.",
                "התחל לאט אם לא הייתה פעילות לפני כן, והשתמש במקטעים קצרים במקום אימון ארוך.",
                "אחרי לידה, התקדמות צריכה להתחשב בשינה, התאוששות, רצפת אגן, ניתוח קיסרי או דימום/כאב.",
            ],
            "progression_gate": [
                "המשתמשת נמצאת במעקב ספק רפואי ומותר לה להיות פעילה לפי מצבה.",
                "אין החמרת כאב, דימום חריג, סחרחורת, קוצר נשימה חריג או לחץ רצפת אגן.",
            ],
            "avoid": [
                "לא לתת אישור רפואי, אבחון או טיפול בהריון/אחרי לידה.",
                "להימנע משכיבה על הגב אחרי השליש הראשון כאשר זה לא מתאים או גורם אי נוחות.",
                "לא לבחור פעילות עם סיכון נפילה גבוה, מכה לבטן או מאמץ קיצוני.",
            ],
        },
        "chronic_conditions_disabilities": {
            "use_when": [
                "המשתמש מדווח על מצב כרוני, מוגבלות, כאב מתמשך, סוכרת, יתר לחץ דם, ארתריטיס או מגבלה תפקודית.",
                "המטרה היא התאמת פעילות כללית לפי יכולת, לא טיפול במחלה.",
            ],
            "coaching_goal": [
                "להעדיף פעילות אפשרית ועקבית על פני חוסר פעילות.",
                "לשלב אירובי, כוח וניידות לפי יכולת ותסמינים.",
            ],
            "programming_rules": [
                "כאשר מסוגלים, יעד שימושי הוא 150 דקות פעילות אירובית מתונה בשבוע.",
                "שלב 2 ימים בשבוע של חיזוק שרירים מרכזיים לפי יכולת, ציוד ותסמינים.",
                "אם אי אפשר להגיע להמלצות, להיות פעיל ככל האפשר ולהקטין ישיבה עדיין מועיל.",
                "בחר דוגמאות נגישות כמו הליכה, גלגול כיסא גלגלים, אופניים, מים, גומיות או משקולות יד.",
            ],
            "progression_gate": [
                "המשתמש יודע אילו הנחיות קיבל מגורם רפואי ופועל בתוכן.",
                "הלוגים מראים שהפעילות לא מחמירה תסמינים, כאב או עייפות באופן עקבי.",
            ],
            "avoid": [
                "לא לשנות טיפול, תרופות או הנחיות רפואיות.",
                "לא להתעלם מתסמינים חריגים או מחמרה מתמשכת.",
                "לא להציג המלצה כללית כמתאימה לכל מצב כרוני.",
            ],
        },
        "older_adult_multicomponent": {
            "use_when": [
                "משתמש מבוגר, ירידה בשיווי משקל, חשש מנפילה, או מטרה של תפקוד יומי.",
                "מתאים גם למשתמשים צעירים יותר עם צורך בתנועה תפקודית ושיווי משקל.",
            ],
            "coaching_goal": [
                "לשמור עצמאות, כוח, סבולת, שיווי משקל וביטחון בתנועה.",
                "לחבר אימון לתפקוד יומי: קימה, נשיאה, מדרגות, דחיפה ומשיכה.",
            ],
            "programming_rules": [
                "שלב אירובי, כוח ושיווי משקל במקום להתמקד רק בקלוריות או משקל.",
                "כוח לפחות 2 ימים בשבוע לפי יכולת, עם תרגילים מרכזיים וגרסאות נתמכות.",
                "שיווי משקל יכול להיות קצר ותכוף: קימה מכיסא, הליכת עקב-בוהן, עמידה נתמכת או step-up נמוך.",
                "כאשר 150 דקות אירובי לא אפשריות, פעל לפי היכולת והמצב במקום לוותר.",
            ],
            "progression_gate": [
                "המשתמש שומר ביטחון, נשימה, יציבה וללא נפילות או סחרחורת.",
                "ניתן להגדיל משך, עומס או מורכבות רק אחרי שליטה בתמיכה הנוכחית.",
            ],
            "avoid": [
                "לא להסיר תמיכה מוקדם מדי בתרגילי שיווי משקל.",
                "לא לכפות קפיצות, עומסים כבדים או שינויי כיוון מהירים בלי בסיס.",
                "לא להתעלם מתרופות, הוראות רפואיות או היסטוריית נפילות.",
            ],
        },
    },
    "menstrual_cycle_training_protocols": {
        "symptom_based_autoregulation": {
            "use_when": [
                "משתמשת שואלת איך להתאמן בזמן וסת, PMS, עייפות מחזורית או שינוי תחושה לאורך החודש.",
                "הבקשה היא התאמת אימון כללית, לא אבחון כאב, פוריות או בעיה גינקולוגית.",
            ],
            "coaching_goal": [
                "להפוך את המחזור לנתון התאמה אישי ולא לסיבה לבטל אימון אוטומטית.",
                "להשתמש בסימפטומים, אנרגיה, RPE ולוגים כדי לבחור עומס יומי.",
            ],
            "rules": [
                "התאמה טובה מתחילה מסימפטומים בפועל: כאב, דימום, אנרגיה, שינה, חשק, RPE וביצועים.",
                "ביום טוב אפשר לשמור אימון רגיל; ביום קשה אפשר להוריד נפח, עצימות, טווח או לבחור גרסה טכנית.",
                "אל תתייחס לכל המשתמשות אותו דבר; יש שונות גדולה בין אנשים וגם בין מחזורים אצל אותה משתמשת.",
            ],
            "avoid": [
                "לא לקבוע שהמשתמשת חלשה או חזקה לפי יום במחזור בלבד.",
                "לא להציג מחזור כסיבה קבועה לא להרים כבד או לא להתאמן.",
            ],
            "source_refs": ["Frontiers Menstrual Cycle Resistance Training Review", "UKSI Supporting Developing Female Athlete"],
        },
        "cycle_phase_evidence_limits": {
            "use_when": [
                "בקשה ל-cycle syncing, phase-based training, או תכנון כוח לפי follicular/luteal phase.",
                "משתמשת שואלת אם חייבים לשנות תוכנית לפי הורמונים.",
            ],
            "coaching_goal": [
                "לתת תשובה מדויקת: המחקר לא תומך בכלל גורף, אבל חוויית המשתמשת חשובה.",
                "להעדיף לוג אישי על טבלת phases אוניברסלית.",
            ],
            "rules": [
                "אין מספיק ראיות איכותיות לבנות תוכנית כוח קשיחה לפי phase של המחזור.",
                "המחזור אינו תמיד 28 יום והביוץ משתנה; לכן phase calendar לבדו אינו בסיס תכנות אמין.",
                "אפשר להשתמש במעקב אישי כדי לזהות דפוסי אנרגיה, כאב או ביצועים ולשנות עומס בהתאם.",
            ],
            "avoid": [
                "לא לבנות תוכנית שמעלה נפח אוטומטית בשלב אחד ומורידה בשלב אחר בלי לוג אישי.",
                "לא להבטיח ש-cycle syncing ישפר כוח, חיטוב או הורמונים.",
            ],
            "source_refs": ["Frontiers Menstrual Cycle Resistance Training Review"],
        },
        "cycle_tracking_for_coaching": {
            "use_when": [
                "משתמשת רוצה להבין דפוסים חוזרים או לשפר תכנון סביב המחזור.",
                "יש תנודתיות באנרגיה, כאב, רעב, משקל מים או ביצועים לאורך חודש.",
            ],
            "coaching_goal": [
                "לבנות מודעות בלי להפוך מעקב למחייב או מלחיץ.",
                "לאסוף מעט נתונים שממש משנים החלטות אימון.",
            ],
            "rules": [
                "לוג מחזור שימושי יכול לכלול יום במחזור, סימפטומים, אנרגיה, RPE, ביצועים וכאב.",
                "בדוק דפוס על פני 2-3 מחזורים לפני שינוי תוכנית גדול.",
                "אם יש דפוס ברור, תכנן גרסת A/B: אימון רגיל ביום טוב וגרסה קצרה/טכנית ביום סימפטומטי.",
            ],
            "avoid": [
                "לא לחייב מעקב אם זה מגביר חרדה או חוסר נוחות.",
                "לא להשתמש בלוג כדי לתת אבחון הורמונלי.",
            ],
            "source_refs": ["Frontiers Menstrual Cycle Resistance Training Review", "UKSI Supporting Developing Female Athlete"],
        },
        "cramps_fatigue_adjustment": {
            "use_when": [
                "משתמשת מדווחת על כאבי מחזור, נפיחות, עייפות או ירידה באנרגיה אבל אין סימני סיכון.",
                "היא רוצה לדעת מה לעשות היום במקום לוותר על כל השבוע.",
            ],
            "coaching_goal": [
                "להציע תנועה נסבלת וגרסת אימון גמישה.",
                "לשמור עקביות בלי לדחוף דרך כאב חריג.",
            ],
            "rules": [
                "אפשר לבחור הליכה, ניידות, כוח קל-בינוני או אימון קצר אם זה מקל ונעים.",
                "כאבי מחזור ועייפות יכולים להצדיק פחות סטים, פחות עצימות, מנוחות ארוכות יותר או החלפת HIIT בתנועה קלה.",
                "אם תנועה מחמירה כאב או גורמת סחרחורת/חולשה חריגה, עוצרים ועוברים להכוונה מקצועית.",
            ],
            "avoid": [
                "לא להגיד שתמיד צריך להתאמן דרך כאבי מחזור.",
                "לא להבטיח שאימון יפתור כאב מחזור.",
            ],
            "source_refs": ["UKSI Supporting Developing Female Athlete", "Exercise and Dysmenorrhea Review"],
        },
        "low_energy_availability_flags": {
            "use_when": [
                "משתמשת מדווחת על וסת שנעלמה, מחזורים מאוד לא סדירים, עייפות גבוהה או ירידה חדה במשקל.",
                "יש שילוב של נפח אימון גבוה, אכילה מוגבלת, פציעות חוזרות או חשש ל-RED-S/triad.",
            ],
            "coaching_goal": [
                "לזהות סימן שמצריך עזרה מקצועית בלי לאבחן.",
                "להחזיר את השיחה לאנרגיה מספקת, התאוששות ובטיחות.",
            ],
            "rules": [
                "וסת שנעלמת או מחזורים חריגים אצל מתאמנת אינם יעד אימון ואינם סימן לכושר טוב.",
                "low energy availability יכולה להיות קשורה למחזור לא סדיר, עייפות, ירידת ביצועים ובריאות עצם.",
                "במצב כזה המאמן הדיגיטלי צריך להמליץ לפנות לרופא/דיאטן קליני או גורם מקצועי מתאים.",
            ],
            "avoid": [
                "לא להסביר היעדר וסת כסתם תוצאה רגילה של אימון קשה.",
                "לא לתת דיאטה, הוראות ירידה במשקל או אבחון RED-S/triad.",
            ],
            "source_refs": ["Female and Male Athlete Triad Coalition", "AMSSM Female Athlete Triad", "UKSI Supporting Developing Female Athlete"],
        },
    },
    "environment_training_risk_protocols": {
        "heat_load_adjustment": {
            "use_when": [
                "כאשר המשתמש מתכנן אימון בחוץ בחום, לחות, שמש חזקה או תחושת עומס חום.",
                "כאשר המשתמש מדווח על אימון קשה מהרגיל במזג אוויר חם.",
            ],
            "coaching_goal": [
                "לשמור פעילות אפשרית תוך הורדת עומס תרמי ועצימות, בלי להבטיח חסינות מחום.",
                "להפוך את האימון לגרסה קצרה, מוצלת ומדורגת יותר כאשר הסביבה מכבידה.",
            ],
            "rules": [
                "בעומס חום: העדף שעה מוקדמת/מאוחרת, צל, ביגוד קל ובהיר, שתייה ומנוחות תכופות.",
                "הורד עצימות, זמן או נפח לפני שאתה מנסה לשמור pace או משקלים רגילים.",
                "התכווצויות שריר, חולשה, סחרחורת או כאב ראש בחום הם סימן להאט, לעצור, להתקרר ולשתות לפי צורך.",
            ],
            "avoid": [
                "לא לדחוף אימון עצים בצהריים רק כדי לשמור תוכנית.",
                "לא להציג הזעה מרובה כסימן שהאימון טוב יותר.",
            ],
            "source_refs": ["CDC Heat and Athletes", "CDC Heat-related Illnesses"],
        },
        "heat_acclimatization": {
            "use_when": [
                "כאשר המשתמש חוזר לאימוני חוץ בתחילת קיץ, אחרי נסיעה או אחרי תקופה במזגן/מזג אוויר קר.",
                "כאשר יש יעד ריצה/ספורט בחום אבל אין עדיין הסתגלות הדרגתית.",
            ],
            "coaching_goal": [
                "לבנות חשיפה הדרגתית לחום במקום קפיצה פתאומית לנפח או עצימות רגילים.",
                "להשאיר את המאמץ נשלט בזמן שהגוף מסתגל.",
            ],
            "rules": [
                "heat acclimatization נבנית דרך חשיפות אימון-חום חוזרות במשך בערך 1-2 שבועות.",
                "בהתחלה קצר יותר ופחות עצים; הוסף זמן/עצימות בהדרגה רק אם אין סימפטומים חריגים.",
                "שמור מצב שתייה טוב לפני האימון ומזער התייבשות תוך כדי, במיוחד באימון ארוך.",
            ],
            "avoid": [
                "לא להניח שאפשר להתרגל לחום ביום אחד.",
                "לא להוסיף חום, עצימות ומשך יחד באותו שבוע ראשון.",
            ],
            "source_refs": ["Heat Training and Competing Consensus", "CDC Heat and Athletes"],
        },
        "heat_illness_red_flags": {
            "use_when": [
                "כאשר המשתמש מתאר חולשה, עילפון, בלבול, סחרחורת קשה, דיבור לא ברור או עור חם מאוד אחרי מאמץ בחום.",
                "כאשר יש חשד ל-heat exhaustion, heat stroke או סימני מצוקה בחום.",
            ],
            "coaching_goal": [
                "לעצור אימון ולהעביר את המשתמש לפעולה שמרנית ומיידית בלי לאבחן.",
                "להבדיל בין התאמת עומס רגילה לבין מצב שמצריך עזרה רפואית.",
            ],
            "rules": [
                "בלבול, שינוי מצב הכרה, עילפון, פרכוס, דיבור לא ברור או חום גוף גבוה מאוד הם סימני סכנה.",
                "במצב כזה מפסיקים פעילות, עוברים לצל/מקום קריר, מקררים במהירות ומבקשים עזרה רפואית דחופה.",
                "שתן כהה מאוד, כאבי שריר חריגים וחולשה אחרי מאמץ בחום מצדיקים עצירה ופנייה רפואית.",
            ],
            "avoid": [
                "לא לתת אבחון heat stroke בצ'אט.",
                "לא להציע להמשיך לאט כאשר יש בלבול, עילפון או סימני מצוקה חמורים.",
            ],
            "source_refs": ["CDC Heat-related Illnesses", "CDC Heat and Athletes"],
        },
        "air_quality_aqi_adjustment": {
            "use_when": [
                "כאשר המשתמש שואל על ריצה/הליכה/אימון בחוץ ביום עם זיהום אוויר, עשן, אובך או AQI גבוה.",
                "כאשר למשתמש יש שיעול, צפצופים, קושי נשימה או רגישות נשימתית בזמן פעילות בחוץ.",
            ],
            "coaching_goal": [
                "להתאים זמן ועצימות לפי איכות האוויר במקום להתייחס לכל יום חוץ כאותו דבר.",
                "להעדיף פעילות בפנים או שעה אחרת כאשר האוויר לא בריא.",
            ],
            "rules": [
                "בדוק AQI לפני אימון חוץ; ככל שה-AQI גרוע יותר, קח יותר הפסקות והורד עצימות.",
                "ב-AQI לא בריא או עשן משמעותי: העדף אימון בפנים או דחה אימון ארוך/עצים.",
                "שיעול, צפצופים, קושי נשימה או לחץ בחזה בזמן אוויר מזוהם מצדיקים עצירה, מעבר פנימה ופנייה לעזרה אם לא משתפר.",
            ],
            "avoid": [
                "לא להמליץ על אינטרוולים או ריצה ארוכה ביום AQI גבוה רק כי התוכנית אומרת.",
                "לא להבטיח שמסכה או קיצור אימון מבטלים סיכון לכל אדם.",
            ],
            "source_refs": ["AirNow AQI Outdoor Activity Guidance"],
        },
        "cold_wind_chill_adjustment": {
            "use_when": [
                "כאשר המשתמש מתכנן אימון בקור, רוח, גשם, שלג או wind chill נמוך.",
                "כאשר יש נימול, רעד חריג, בלבול, עור לבן/חיוור או תחושת קור שאינה נשלטת.",
            ],
            "coaching_goal": [
                "לאפשר תנועה בחוץ רק כאשר הלבוש, המשטח והסימנים מתאימים.",
                "להעביר לפנים כאשר קור, רוח או רטיבות מעלים סיכון.",
            ],
            "rules": [
                "בקור: בדוק טמפרטורה, wind chill, רטיבות ומשטח; לבש שכבות, כיסוי ידיים/אוזניים ושמור יבש.",
                "רוח ורטיבות מעלות איבוד חום; אימון קל בפנים עדיף על חשיפה לא נשלטת.",
                "רעד בלתי נשלט, בלבול, דיבור לא ברור, נימול או עור לבן/חיוור הם סימני עצירה וחימום הדרגתי.",
            ],
            "avoid": [
                "לא להציע אימון חוץ ארוך כאשר המשתמש לא יכול להישאר יבש ומכוסה.",
                "לא להתייחס ל-wind chill כפרט שולי באימון חורף.",
            ],
            "source_refs": ["ACSM Cold Weather Exercise", "National Weather Service Wind Chill"],
        },
        "outdoor_session_decision": {
            "use_when": [
                "כאשר צריך לבחור אם לבצע אימון חוץ מתוכנן או להזיז אותו בגלל מזג אוויר/איכות אוויר.",
                "כאשר המשתמש מבקש גרסת אימון בטוחה יותר בלי לוותר על עקביות.",
            ],
            "coaching_goal": [
                "לתת החלטת אימון מעשית: לבצע, לקצר, להוריד עצימות, להזיז שעה או לעבור פנימה.",
                "לשמור רצף אימון בלי פיצוי יתר ובלי דרמה.",
            ],
            "rules": [
                "בחר אחת מארבע התאמות: להקדים/לאחר, לקצר, להוריד עצימות או לבצע בפנים.",
                "אם תנאי חוץ בעייתיים, שמור את מטרת האימון דרך חלופה: הליכה בפנים, אופניים, מוביליטי או כוח קצר.",
                "כאשר סימפטומים מתחילים, אל תנסה להשלים נפח; סיים מוקדם ותעד מה קרה ללמידה עתידית.",
            ],
            "avoid": [
                "לא להפוך שינוי סביבתי לכישלון או לאימון עונש ביום הבא.",
                "לא להמציא מדד סביבה מדויק אם אין נתון; שאל על חום, לחות, AQI, רוח ותחושה.",
            ],
            "source_refs": ["CDC Heat and Athletes", "AirNow AQI Outdoor Activity Guidance", "ACSM Cold Weather Exercise"],
        },
    },
    "low_energy_availability_protocols": {
        "under_fueling_watchlist": {
            "use_when": [
                "כאשר המשתמש מתאר מעט אוכל, דילוג ארוחות או תדלוק חסר לצד עומס אימון גבוה.",
                "כאשר מופיעים עייפות חריגה, קור מתמשך, מחלה חוזרת, ירידה חדה במשקל או פציעות חוזרות.",
            ],
            "coaching_goal": [
                "לזהות דפוס סיכון בלי לאבחן REDs, הפרעת אכילה או מצב רפואי.",
                "להחזיר את השיחה לתדלוק, התאוששות ועומס אימון בר קיימא.",
            ],
            "rules": [
                "שאל שאלה אחת על אכילה סביב אימון, אנרגיה יומית והתאוששות.",
                "כאשר יש תדלוק חסר, הצע ארוחה או נשנוש סביב אימון והורדת עומס זמנית.",
                "אם הדפוס חוזר או מחמיר, המלץ לפנות לרופא, דיאטן קליני או גורם מוסמך.",
            ],
            "avoid": [
                "לא לאבחן REDs או הפרעת אכילה.",
                "לא לחשב זמינות אנרגטית או לתת סף רפואי בצ'אט.",
                "לא להוסיף גירעון, צום או HIIT כתגובה ראשונה לעייפות ותדלוק חסר.",
            ],
            "source_refs": ["IOC REDs Consensus 2023", "Nutrition and Athletic Performance Position Paper", "ANAD REDs Overview"],
        },
        "training_recovery_decline": {
            "use_when": [
                "כאשר ביצועים יורדים, RPE עולה, ההתאוששות חלשה או האימון מרגיש קשה מהרגיל במשך כמה אימונים.",
                "כאשר המשתמש מדווח על עומס אימון גבוה יחד עם שינה, אוכל או אנרגיה נמוכים.",
            ],
            "coaching_goal": [
                "להבדיל בין יום חלש רגיל לבין דפוס שמצריך הורדת עומס ותדלוק טוב יותר.",
                "לשמור על עקביות דרך התאמת עומס במקום דחיפה אגרסיבית.",
            ],
            "rules": [
                "בדוק RPE, שינה, כאב, תיאבון ואכילה לפני שאתה מוסיף נפח או עצימות.",
                "אם הביצועים יורדים והעייפות עולה, הורד עומס/נפח זמנית והדגש תדלוק והתאוששות.",
                "דפוס חוזר של פציעות, מחלות או ירידת ביצועים מצדיק הפניה מקצועית.",
            ],
            "avoid": [
                "לא לקרוא לירידת ביצועים עצלות או חוסר משמעת.",
                "לא להמליץ על עוד אימונים עצימים לפני בדיקת התאוששות ואכילה.",
            ],
            "source_refs": ["IOC REDs Consensus 2023", "Nutrition and Athletic Performance Position Paper"],
        },
        "menstrual_bone_stress_risk": {
            "use_when": [
                "כאשר משתמשת מזכירה וסת שנעלמה, מחזור לא סדיר, פציעות מאמץ או כאבי עצם חוזרים.",
                "כאשר יש שילוב של עומס אימון, ירידה במשקל או תדלוק חסר עם סימני מחזור/עצם.",
            ],
            "coaching_goal": [
                "להתייחס להיעדר וסת או פציעות מאמץ כסימן זהירות, לא כמדד לכושר.",
                "להפנות להערכה רפואית/תזונתית מתאימה בלי לאבחן.",
            ],
            "rules": [
                "וסת שנעלמת או מחזור לא סדיר לצד אימון ותדלוק חסר מצריכים זהירות והפניה לגורם מוסמך.",
                "פציעת מאמץ או כאב עצם חוזר אינם משהו שפותרים בהוספת עומס.",
                "בינתיים הצע הורדת עומס, תדלוק מספק והימנעות ממטרות חיטוב אגרסיביות.",
            ],
            "avoid": [
                "לא להציג היעדר וסת כתוצאה רגילה או רצויה של אימון קשה.",
                "לא לתת אבחון triad/REDs או תוכנית דיאטה במקום הפניה מקצועית.",
            ],
            "source_refs": ["IOC REDs Consensus 2023", "Female and Male Athlete Triad Coalition"],
        },
        "disordered_eating_boundary": {
            "use_when": [
                "כאשר המשתמש מתאר טיהור, הקאות, משלשלים, פחד קיצוני מאוכל או פעילות כפייתית לפיצוי.",
                "כאשר הבקשה מתמקדת בשליטה קיצונית במשקל או בחוקים נוקשים סביב אוכל.",
            ],
            "coaching_goal": [
                "לשמור את המוצר מחוץ לטיפול בהפרעות אכילה ולהציע תמיכה כללית ובטוחה.",
                "לעצור הדרכה שעלולה להחמיר דפוס מסוכן.",
            ],
            "rules": [
                "ענה בקצרה ובאמפתיה, ציין שאינך יכול לסייע בהתנהגות מזיקה והפנה לאיש מקצוע.",
                "אפשר להציע מבנה ארוחות כללי ומאוזן רק אם זה לא מחזק הגבלה או פיצוי.",
            ],
            "avoid": [
                "לא לאבחן הפרעת אכילה.",
                "לא לתת קלוריות יעד, צום, טיפים להסתרה, טיהור או פיצוי באימון.",
                "לא לאשר התנהגות כפייתית גם אם היא מנוסחת כמטרת כושר.",
            ],
            "source_refs": ["NEDA Eating Disorder Warning Signs", "ANAD REDs Overview"],
        },
        "body_composition_guardrails": {
            "use_when": [
                "כאשר המשתמש מבקש חיטוב, ירידה במשקל, מסה או ריקומפ עם עומס אימון משמעותי.",
                "כאשר קיימים סימני עייפות, ירידת ביצועים או תדלוק חסר בזמן שינוי משקל.",
            ],
            "coaching_goal": [
                "לשמור על שינוי הרכב גוף מתון, מדיד ובר קיימא.",
                "למנוע מעבר אוטומטי לגירעון נוסף כאשר ההתאוששות כבר חלשה.",
            ],
            "rules": [
                "חיטוב צריך להיות גירעון מתון, עם כוח, חלבון, שינה ותדלוק מספיק סביב אימונים.",
                "כאשר אנרגיה, מצב רוח או ביצועים נפגעים, שקול תחזוקה או diet break לפני עוד הגבלה.",
                "שינוי הרכב גוף לא שווה ירידה מהירה במשקל בכל מחיר.",
            ],
            "avoid": [
                "לא לעודד יעד משקל אגרסיבי או דיאטה קיצונית.",
                "לא להוסיף HIIT או נפח כעונש על אכילה או פלאטו.",
            ],
            "source_refs": ["Nutrition and Athletic Performance Position Paper", "ISSN Diets and Body Composition"],
        },
    },
    "coaching_instruction_protocols": {
        "session_flow": {
            "use_when": ["בכל יצירת אימון, התאמת אימון או הנחיית ביצוע."],
            "coaching_goal": ["לתת למשתמש מסגרת אימון ברורה, בטוחה וקלה לביצוע."],
            "coaching_moves": [
                "פתח עם חימום 5-10 דקות בקצב קל או גרסה איטית של התנועה המרכזית.",
                "הצג אימון מרכזי קצר עם סדר ברור: תרגילים מורכבים/טכניים לפני אביזרים.",
                "סיים עם שחרור/cool-down של 5-10 דקות והורדת קצב הדרגתית.",
            ],
            "progression_gate": ["המשתמש מסיים את האימון בלי כאב חד, סחרחורת או פירוק טכניקה."],
            "avoid": ["לא להתחיל עומס גבוה בלי חימום; לא להוסיף נפח כפיצוי על פספוס."],
        },
        "exercise_teaching": {
            "use_when": ["כאשר המשתמש מבקש איך לבצע תרגיל או מקבל תרגיל חדש בתוכנית."],
            "coaching_goal": ["להפוך הוראה טכנית לפעולה אחת שהמשתמש יכול לבצע מיד."],
            "coaching_moves": [
                "השתמש ב-show-tell-do: הדגם במילים קצרות, אמור cue אחד, ואז תן ניסיון ביצוע.",
                "שמור הסבר טכני קצר; הרחב רק אם המשתמש מבקש פירוט.",
                "בחר רגרסיה אם יש טעות גדולה לפני הוספת עומס.",
            ],
            "progression_gate": ["המשתמש מבצע חזרות יציבות בטווח נוח לפני עומס או וריאציה קשה יותר."],
            "avoid": ["לא להציף בשלושה תיקונים באותו סט; לא להשתמש בז׳רגון בלי להסביר."],
        },
        "cue_selection": {
            "use_when": ["כאשר צריך לתקן תנועה בזמן אימון או לתת דגש ביצוע."],
            "coaching_goal": ["לבחור cue שמתקן את הטעות החשובה ביותר בלי להעמיס על המשתמש."],
            "coaching_moves": [
                "שלב external cue לתוצאה או מסלול תנועה ו-internal cue רק כשצריך להרגיש שריר מסוים.",
                "התאם cue אחד לפי מה שרואים בלוג: ברך, גב, כתף, נשימה או קצב.",
                "אם cue לא עובד, שנה ניסוח או רגרסיה במקום לחזור עליו.",
            ],
            "progression_gate": ["המשתמש מצליח לשמור את הדגש לאורך כמה חזרות רצופות."],
            "avoid": ["לא לתת cue כללי מדי כמו 'תעשה נכון'; לא להתעלם מכאב כדי להשלים סט."],
        },
        "feedback_frequency": {
            "use_when": ["כאשר המאמן מגיב לביצוע, לוג אימון או קושי בטכניקה."],
            "coaching_goal": ["לתת מספיק feedback ללמידה בלי ליצור תלות במאמן."],
            "coaching_moves": [
                "בתחילת למידה תן feedback מיידי וברור על נקודה אחת.",
                "עם התקדמות תן פחות feedback ויותר שאלות שמפתחות עצמאות.",
                "התערב מיד כאשר יש סיכון בטיחות, כאב חד או אובדן שליטה.",
            ],
            "progression_gate": ["המשתמש יודע לתאר בעצמו מה השתפר ומה נשאר לתקן."],
            "avoid": ["לא לתקן כל חזרה אם אין סיכון; לא להמשיך אימון כאילו feedback בטיחותי הוא אופציונלי."],
        },
        "technique_safety_checklist": {
            "use_when": ["לפני עומס, אחרי תלונת כאב או כשנוסף תרגיל חדש."],
            "coaching_goal": ["לוודא מנח, אחיזה, נשימה וטווח תנועה לפני העלאת קושי."],
            "coaching_moves": [
                "בדוק מנח יציב, אחיזה נוחה, נשימה רציפה וטווח ללא כאב חד.",
                "שמור קצב נשלט לפני עומס, מהירות או טווח עמוק יותר.",
                "בכאב או סחרחורת עצור והעבר להנחיה שמרנית או הפניה מתאימה.",
            ],
            "progression_gate": ["אין כאב חד, אין סחרחורת והטכניקה נשמרת גם בסוף הסט."],
            "avoid": ["לא להעלות עומס בגלל שהמספרים נראים קלים אם המנח מתפרק."],
        },
        "client_feedback_loop": {
            "use_when": ["אחרי אימון שהושלם, פוספס, שונה או הרגיש קשה מדי."],
            "coaching_goal": ["להשתמש בתחושת המשתמש כדי להתאים את האימון הבא."],
            "coaching_moves": [
                "שאל על עייפות, soreness, כאב, אנרגיה וזמן פנוי לפני התאמת עומס.",
                "אם העייפות גבוהה או הביצוע יורד, שמור או הורד נפח במקום להתקדם.",
                "אם היה פספוס, הצע גרסה קצרה וברורה לאימון הבא.",
            ],
            "progression_gate": ["הלוגים מראים התאוששות סבירה, עקביות וטכניקה יציבה."],
            "avoid": ["לא להפוך פספוס לעונש; לא להתקדם כשיש סימני עומס יתר."],
        },
    },
    "exercise_setup_safety_protocols": {
        "machine_adjustment": {
            "use_when": ["לפני עבודה במכונה, כבל, leg press, chest press, lat pulldown או מכשיר לא מוכר."],
            "coaching_goal": ["להתחיל סט רק כשהמכשיר מכוון, יציב וברור למשתמש."],
            "rules": [
                "כוון מושב, פד, ידיות וטווח התחלה כך שהמפרק עובד במסלול נוח ולא קיצוני.",
                "בדוק שהפד מייצב בלי ללחוץ כאב, שהרגליים יציבות, ושהמשתמש מבין איך לעצור.",
                "אם המכשיר שבור, לא ברור או מסומן OUT OF ORDER, לא משתמשים בו ומחליפים תרגיל.",
            ],
            "decision_gate": ["המשתמש יודע איפה מתחילים/עוצרים, הטווח נוח, והמכשיר מרגיש יציב."],
            "avoid": ["לא להתחיל סט כבד במכשיר לא מוכר לפני כיוון קל וסט ניסיון."],
            "source_refs": [
                "TRUE Fitness Equipment Safety",
                "Precor Product Guides",
                "Life Fitness Technical Documents",
            ],
        },
        "rack_safety_pins": {
            "use_when": ["לפני squat, bench press, overhead press או כל תרגיל חופשי שבו כשל יכול לכלוא את המשתמש."],
            "coaching_goal": ["לצמצם סיכון מכשל טכני בעומס חופשי."],
            "rules": [
                "כוון safety pins או safeties לגובה מתאים לפני סטים כבדים, במיוחד bench/squat.",
                "ב-bench בלי spotter או safeties, העדף dumbbells, machine press או עומס שמרני.",
                "לפני הסט בדוק שהמוט, clips, rack וגובה היציאה מתאימים.",
            ],
            "decision_gate": ["יש rack/safeties/spotter מתאים או וריאציה חלופית בטוחה יותר."],
            "avoid": ["לא לבצע סט קרוב לכשל תחת מוט בלי safeties/spotter מתאים."],
            "source_refs": ["NSCA Professional Standards", "Rogue Spotter Arms Instructions"],
        },
        "spotting_free_weights": {
            "use_when": ["בעומסים חופשיים מעל head, face או trunk, או כאשר המשתמש קרוב לכשל."],
            "coaching_goal": ["להבהיר מתי דרוש spotter ומתי לבחור וריאציה יציבה יותר."],
            "rules": [
                "תרגילים עם עומס מעל head, face או trunk דורשים spotting מתאים או ציוד safety מתאים.",
                "spotter צריך להיות קשוב, יודע איך לעזור, ולא לגעת במוט אלא אם צריך.",
                "אם אין spotter מתאים, בחר עומס קל, dumbbells, מכונה או וריאציה נתמכת.",
            ],
            "decision_gate": ["המשתמש מבין את הסיכון ויש תמיכה מתאימה לפני סטים כבדים/קרובים לכשל."],
            "avoid": ["לא להמליץ על PR/כשל במוט חופשי בלי תנאי safety."],
            "source_refs": ["NSCA Professional Standards", "NSCA Exercise Technique Manual"],
        },
        "breathing_bracing": {
            "use_when": ["בתרגילי כוח, סקוואט, hinge, לחיצה, משיכה, נשיאה וליבה."],
            "coaching_goal": ["לתת cue נשימה פשוט ולא אגרסיבי שמתאים למשתמש כללי."],
            "rules": [
                "קח אוויר לפני החלק הקשה, עשה brace עדין, ושחרר/נשיפה דרך המאמץ.",
                "למשתמש כללי, cue קצר עדיף מהסבר Valsalva מורכב.",
                "אם נשימה/לחץ יוצרים סחרחורת או אי נוחות, הורד עומס והפסק את הסט.",
            ],
            "decision_gate": ["המשתמש שומר שליטה ונשימה בלי סחרחורת או לחץ חריג."],
            "avoid": ["לא ללמד Valsalva אגרסיבי מרחוק למתחיל או למי שיש מצב רפואי לא ברור."],
            "source_refs": ["ACE Bodyweight Squat", "NSCA Exercise Technique Manual"],
        },
        "stable_variation_defaults": {
            "use_when": ["כאשר המשתמש חדש, לא בטוח בטכניקה, חסר ציוד, או חווה חוסר יציבות."],
            "coaching_goal": ["לבחור וריאציה stable/supported לפני מורכבות ועומס."],
            "rules": [
                "מתחיל או לא בטוח: העדף supported/lower-complexity variation כמו goblet squat, machine press או lat pulldown.",
                "התקדם רק אחרי טווח יציב, קצב נשלט, ללא כאב חד ולוגים עקביים.",
                "וריאציה יציבה אינה פחות טובה; היא מאפשרת אימון טוב יותר עכשיו.",
            ],
            "decision_gate": ["המשתמש מבצע את הווריאציה בשליטה ומבין מה להרגיש/למדוד."],
            "avoid": ["לא לקפוץ לברבל כבד או תרגיל מיומן רק כי הוא 'מתקדם'."],
            "source_refs": [
                "NSCA Progressive Teaching Strategies",
                "ACSM Resistance Training Guidelines 2026",
            ],
        },
        "switch_instead_of_cueing": {
            "use_when": ["כאשר טכניקה מתפרקת, שני cues פשוטים לא עוזרים, או המשתמש מאבד ביטחון."],
            "coaching_goal": ["לדעת מתי להחליף תרגיל במקום להמשיך לתקן מרחוק."],
            "rules": [
                "אם אחרי שני cues פשוטים הטכניקה עדיין מתפרקת, הורד עומס או החלף לווריאציה יציבה יותר.",
                "אם כאב חד מופיע, עצור את התרגיל; זה לא cueing problem.",
                "בחר תרגיל באותו דפוס אם אפשר: squat, hinge, push, pull או core.",
            ],
            "decision_gate": ["cue קצר לא משפר ביצוע או שהמשתמש לא מרגיש בטוח להמשיך."],
            "avoid": ["לא לתת רצף cues ארוך שמעמיס קוגניטיבית; לא לפתור כאב בתיקון טכני בצ׳אט."],
            "source_refs": [
                "NSCA Progressive Teaching Strategies",
                "NASM Correctly Coaching Exercises",
            ],
        },
        "equipment_misuse_checks": {
            "use_when": ["במכשירים, כבלים, משקולות חופשיות, rack או אביזרי חדר כושר."],
            "coaching_goal": ["להפחית שימוש לא נכון בציוד לפני סט."],
            "rules": [
                "אל תשתמש בכבל בלי ידית מתאימה, pin לא תקין, משקולת שבורה או מכשיר שמסומן OUT OF ORDER.",
                "אל תאלתר עומס דרך double-pin/high-pin stacks או אחיזה בקצה כבל חשוף.",
                "אם setup לא ברור, בקש עזרה מצוות המקום או החלף לתרגיל מוכר ובטוח.",
            ],
            "decision_gate": ["הציוד תקין, ה-setup ברור והמשתמש יודע איך לצאת מהתרגיל."],
            "avoid": ["לא להמשיך סט כאשר הציוד מרגיש רופף, שבור או לא צפוי."],
            "source_refs": [
                "TRUE Fitness Equipment Safety",
                "Precor Product Guides",
                "Life Fitness Technical Documents",
            ],
        },
    },
    "weekly_structure_protocols": {
        "availability_first": {
            "use_when": ["כאשר המשתמש מבקש תוכנית שבועית או משנה זמינות אימונים."],
            "coaching_goal": ["לבחור מבנה שבועי שהמשתמש באמת יכול לבצע לפני אופטימיזציה מורכבת."],
            "structure_rules": [
                "התחל מזמינות, ניסיון, ציוד, מגבלות והתאוששות; לא מ-split אופנתי.",
                "כוון שכל קבוצת שריר מרכזית תקבל גירוי פעמיים בשבוע כאשר זה אפשרי.",
                "אם השבוע עמוס, שמור גרסת מינימום עקבית במקום להוסיף ימים לא ריאליים.",
            ],
            "progression_gate": ["המשתמש משלים את רוב האימונים במשך 2-4 שבועות בלי ירידה בביצועים או כאב."],
            "avoid": ["לא לבחור split מתקדם אם הזמינות או ההרגל השבועי עדיין לא יציבים."],
        },
        "beginner_full_body": {
            "use_when": ["למתחילים, חוזרים אחרי הפסקה, או משתמשים עם 2-3 ימי אימון בשבוע."],
            "coaching_goal": ["לבנות עקביות, טכניקה וגירוי לכל הגוף בלי עומס שבועי מיותר."],
            "structure_rules": [
                "למתחילים או חזרה אחרי הפסקה: 2-3 ימי גוף מלא/full-body בשבוע, לרוב לא רצופים.",
                "כל אימון כולל דפוסי בסיס: סקוואט/ברך, hinge/ירך, דחיפה, משיכה, ליבה ונשיאה או אירובי קל.",
                "שמור 1-3 ימים בין אימוני כוח לפי התאוששות, אבל אל תפתח פער גדול מדי שמפרק עקביות.",
            ],
            "progression_gate": ["המשתמש מסיים את רוב האימונים בטכניקה יציבה, RPE סביר וללא כאב חד."],
            "avoid": ["לא לפצל מוקדם מדי לימים רבים כאשר המשתמש עדיין צריך הרגל בסיסי ותדירות פשוטה."],
        },
        "intermediate_upper_lower": {
            "use_when": ["למשתמש ביניים עם כ-4 ימי אימון זמינים או צורך ביותר נפח בלי להעמיס אותו אזור ברצף."],
            "coaching_goal": ["לאפשר יותר נפח שבועי והתאוששות טובה יותר בין חשיפות לאותם שרירים."],
            "structure_rules": [
                "לביניים עם 4 ימים: upper/lower או עליון/תחתון מאפשר יותר נפח בלי להעמיס אותו אזור יום אחרי יום.",
                "דוגמה: עליון, תחתון, מנוחה/קל, עליון, תחתון; שמור התאוששות בין אותם שרירים.",
                "ב-3 ימים אפשר עדיין גוף מלא או full/upper/lower לפי מטרה וזמן.",
            ],
            "progression_gate": ["הלוגים מראים שהמשתמש עומד בנפח, מתאושש בין ימים דומים ושומר ביצועים."],
            "avoid": ["לא להוסיף יום רביעי אם שלושה ימים עדיין לא מבוצעים בעקביות."],
        },
        "advanced_split": {
            "use_when": ["למשתמש מתקדם עם 5-6 ימים זמינים, היסטוריית אימון ולוגים שמראים התאוששות."],
            "coaching_goal": ["להגדיל מיקוד ונפח רק כאשר זה משרת ביצועים ולא פוגע בעקביות."],
            "structure_rules": [
                "למתקדמים עם 5-6 ימים: push/pull/legs או split לפי דפוס/שריר יכול להעלות נפח ומיקוד.",
                "השתמש ב-split מתקדם רק אם הלוגים מראים התאוששות, טכניקה ויכולת להתמיד.",
                "שמור תרגילים מורכבים מוקדם באימון ואל תחליף התאוששות בעוד יום נפח.",
            ],
            "progression_gate": ["אין ירידה עקבית בביצועים, אין כאב מתגבר, והשינה/עייפות תומכות בתדירות גבוהה."],
            "avoid": ["לא להעתיק split מתקדם למשתמש עם זמינות נמוכה, כאב לא ברור או התאוששות חלשה."],
        },
        "recovery_spacing": {
            "use_when": ["כאשר מתכננים ימים רצופים, מוסיפים תדירות, או המשתמש מדווח על עייפות/כאב."],
            "coaching_goal": ["לשמור על גירוי שבועי בלי להעמיס שוב ושוב את אותם שרירים לפני התאוששות."],
            "structure_rules": [
                "תן בערך 48 שעות או יומיים לפני עומס קשה חוזר על אותם שרירים כאשר הנפח גבוה.",
                "אם מתאמנים ימים רצופים, החלף אזור/דפוס: עליון ואז תחתון, push ואז pull/legs.",
                "אחרי כאב חד, ירידת ביצועים או עייפות גבוהה, שמור או הורד נפח לפני הוספת תדירות.",
            ],
            "progression_gate": ["המשתמש מדווח על התאוששות טובה והביצועים לא יורדים בין חשיפות דומות."],
            "avoid": ["לא להוסיף עוד אימון לאותו אזור כדי לפצות על פספוס או על אימון חלש."],
        },
    },
    "volume_progression_protocols": {
        "minimum_effective_volume": {
            "use_when": ["כאשר המשתמש מתחיל, חוזר אחרי הפסקה, קצר בזמן או מתקשה להתאושש."],
            "coaching_goal": ["לבנות גירוי מספיק ועקבי בלי להפוך נפח גבוה למטרה בפני עצמה."],
            "progression_rules": [
                "התחל מנפח מינימלי יעיל: עד כ-4 סטים לכל שריר בשבוע יכולים עדיין לתמוך בהתקדמות כאשר זמן או התאוששות מוגבלים.",
                "למתחילים, עדיף 1-3 סטים לתרגיל באיכות טובה מאשר הרבה סטים עם טכניקה מתפרקת.",
                "העלה נפח רק אחרי שהמשתמש משלים את האימונים, שומר טכניקה ומדווח התאוששות סבירה.",
            ],
            "decision_gate": ["לפחות 2-4 שבועות של לוגים עקביים בלי כאב חד, RPE חריג או ירידת ביצועים."],
            "avoid": ["לא להוסיף סטים רק כי התוכנית נראית קצרה; קצר ועקבי עדיף מנפח שמוביל לפספוסים."],
        },
        "hypertrophy_weekly_sets": {
            "use_when": ["כאשר המטרה המרכזית היא היפרטרופיה או בניית שריר והמשתמש כבר עומד בבסיס."],
            "coaching_goal": ["להגדיל נפח שבועי בצורה שמקדמת שריר בלי לפגוע בהתאוששות או בעקביות."],
            "progression_rules": [
                "להיפרטרופיה, כוון בהדרגה לכ-10 סטים לכל שריר בשבוע כאשר הלוגים וההתאוששות תומכים בכך.",
                "פזר את הסטים על פני 2 חשיפות שבועיות או יותר במקום לדחוס הכול לאימון אחד קשה מדי.",
                "אם ביצועים יורדים, soreness נמשך או RPE עולה, שמור או הורד נפח לפני שמוסיף סטים.",
            ],
            "decision_gate": ["המשתמש משלים את רוב הסטים בטווח החזרות, עם RIR/RPE סביר וללא ירידה שבועית בביצוע."],
            "avoid": ["לא להתייחס ל-10 סטים כפקודה לכל משתמש; זה יעד התקדמות, לא תנאי פתיחה."],
        },
        "double_progression": {
            "use_when": ["כאשר יש טווח חזרות ברור, למשל 8-12, והמשתמש רוצה לדעת מתי להעלות משקל."],
            "coaching_goal": ["לתת כלל פשוט שמתקדם מחזרות נקיות לעומס גבוה יותר בלי לנחש."],
            "progression_rules": [
                "השתמש ב-double progression: קודם מלא את טווח החזרות בטכניקה טובה, אחר כך העלה עומס.",
                "כלל 2-for-2: אם המשתמש מבצע 2 חזרות מעבר ליעד בסט האחרון במשך 2 שבועות, אפשר להעלות משקל.",
                "אחרי עמידה בכלל, העלה 2-10% עומס או קפיצה קטנה זמינה, ואז חזור לקצה התחתון של טווח החזרות.",
            ],
            "decision_gate": ["החזרות הנוספות נקיות, בלי קיצור טווח, תנופה, כאב חד או RPE 10 חוזר."],
            "avoid": ["לא להעלות עומס אם המשתמש הגיע לחזרות דרך טכניקה גרועה או מנוחה קצרה מדי."],
        },
        "rir_rpe_autoregulation": {
            "use_when": ["כאשר אין נתוני 1RM בטוחים, יש שונות יומית באנרגיה, או המשתמש מדווח מאמץ."],
            "coaching_goal": ["לכוון מאמץ לפי ביצוע היום ולא רק לפי מספרים על הנייר."],
            "progression_rules": [
                "RIR מתאר כמה חזרות נקיות נשארו לפני כשל טכני; RPE מתאר כמה הסט הרגיש קשה.",
                "ככלל פשוט, RPE 8 דומה לכ-2 RIR, RPE 9 לכ-1 RIR ו-RPE 10 לכשל או 0 RIR.",
                "לרוב אימוני כוח/שריר שמור 1-3 RIR; בתרגילים מורכבים או נפח גבוה אפשר להשאיר יותר רזרבה.",
                "מתחילים צריכים להשתמש בטווחי מאמץ רחבים ושמרניים עד שהערכת RIR/RPE שלהם משתפרת.",
            ],
            "decision_gate": ["המשתמש מדווח RIR/RPE באופן עקבי והביצועים בפועל תואמים בערך את הדיווח."],
            "avoid": ["לא לרדוף אחרי כשל בכל סט; כשל תכוף מעלה עייפות ולא נדרש לרוב המשתמשים."],
        },
        "progression_decision_order": {
            "use_when": ["כאשר המשתמש שואל איך להתקדם או כאשר הלוגים מראים שהאימון קל מדי או קשה מדי."],
            "coaching_goal": ["לבחור משתנה התקדמות אחד במקום להעלות הכול יחד."],
            "progression_rules": [
                "סדר שמרני: קודם טכניקה וטווח, אחר כך חזרות, אחר כך עומס, אחר כך סטים או תדירות.",
                "למטרת כוח, העדף עומס קטן או איכות חזרות לפני הוספת הרבה נפח.",
                "להיפרטרופיה, הוסף סטים רק אחרי שטווח החזרות, RIR וההתאוששות יציבים.",
                "אם יש plateau, בדוק קודם שינה, תזונה, עקביות ומנוחה לפני החלפת כל התוכנית.",
            ],
            "decision_gate": ["לפחות שני לוגים דומים מראים שהמשתמש מוכן לשינוי, לא רק אימון יחיד טוב."],
            "avoid": ["לא להעלות חזרות, עומס, סטים ותדירות באותו שבוע; קשה לדעת מה עבד ומה שבר התאוששות."],
        },
    },
    "advanced_strength_hypertrophy_protocols": {
        "hypertrophy_volume_landmarks": {
            "use_when": ["כאשר המטרה היא היפרטרופיה והמשתמש כבר עומד בבסיס עקבי."],
            "coaching_goal": ["לכוון נפח שבועי לפי תגובה והתאוששות במקום להעתיק מספרים קשיחים."],
            "rules": [
                "התחלה פרקטית לרבים: 6-10 סטים קשים לשריר בשבוע, ואז התקדמות לפי לוגים.",
                "כ-10 סטים ומעלה לשריר בשבוע יכולים להיות יעד היפרטרופיה מתקדם, לא נקודת פתיחה לכל משתמש.",
                "התחל מנפח שהמשתמש משלים, ואז העלה סטים רק אם ביצועים, RIR ושינה תומכים בכך.",
                "פזר שריר מטרה בערך פעמיים בשבוע כברירת מחדל כדי לפזר נפח ועייפות.",
                "טווחים רחבים עובדים אם מתקרבים מספיק לכשל: 6-12 למורכבים, 8-20 לבידוד, 12-30 כשעומס קל.",
                "מעלים נפח בשריר אחד או שניים לפני שמעלים הכול, כדי לזהות תגובה והתאוששות.",
            ],
            "decision_gate": ["2-4 שבועות של לוגים מראים ביצוע יציב, RPE סביר וללא ירידה בתפקוד."],
            "avoid": ["לא להתייחס ליותר סטים כיותר טוב תמיד; נפח בלי התאוששות הוא רעש."],
            "source_refs": ["Hypertrophy Volume Meta-analysis", "ACSM Resistance Training Guidelines 2026"],
        },
        "proximity_to_failure": {
            "use_when": ["כאשר מכוונים מאמץ בסטים של כוח/היפרטרופיה."],
            "coaching_goal": ["לשמור מאמץ גבוה מספיק לגירוי בלי להפוך כל סט לכשל."],
            "rules": [
                "לרוב סטי עבודה, 1-3 RIR הוא יעד פרקטי למתאמן כללי עם טכניקה יציבה.",
                "מתחילים, תרגיל חדש או compound כבד יכולים להישאר עם 2-4 RIR עד שהטכניקה יציבה.",
                "RPE/RIR הם אומדן; בדוק אותם מול חזרות, מהירות, טכניקה והתאוששות.",
            ],
            "decision_gate": ["המשתמש מבין RIR ומדווח אותו בעקביות יחסית במשך כמה לוגים."],
            "avoid": ["לא לרדוף RPE 10 כדי להרגיש שהאימון עבד."],
            "source_refs": ["Helms RIR-Based RPE", "Training to Failure Meta-analysis"],
        },
        "failure_dosage": {
            "use_when": ["כאשר המשתמש שואל אם להתאמן עד כשל או כשהלוגים מלאים ב-RPE 10."],
            "coaching_goal": ["להשתמש בכשל במינון נמוך ובמקום מתאים, לא כעיקרון קבוע."],
            "rules": [
                "failure אינו חובה להיפרטרופיה או כוח כאשר נפח ומאמץ דומים.",
                "אם משתמשים ב-failure, עדיף מעט, בסוף אימון, ובתרגיל בטוח יותר או isolation ולא compound מסוכן.",
                "כשל חוזר שמעלה עייפות, מוריד ביצועים או פוגע בטכניקה אומר להפחית מאמץ/נפח.",
            ],
            "decision_gate": ["המשתמש מנוסה, אין כאב, והתרגיל בטוח גם כאשר החזרה האחרונה נכשלת."],
            "avoid": ["לא להמליץ failure ב-bench/squat כבדים בלי safeties/spotter מתאים."],
            "source_refs": ["Training to Failure Meta-analysis", "NSCA Professional Standards"],
        },
        "top_set_backoff": {
            "use_when": ["למשתמש ביניים/מתקדם שרוצה כוח או מדד ביצוע בלי max testing."],
            "coaching_goal": ["לקבל גירוי כבד ומדד התקדמות בלי לדחוף 1RM תכוף."],
            "rules": [
                "top set הוא סט עבודה עיקרי כבד יחסית עם RIR מוגדר, לא max.",
                "אחרי top set, השתמש ב-back-off/backoff sets קלים יותר כדי לצבור נפח איכותי.",
                "אם top set איטי מדי או RPE חורג, הורד back-off volume במקום להילחם בתוכנית.",
            ],
            "decision_gate": ["יש לוגים, טכניקה יציבה ויכולת לדווח RPE/RIR בלי לרדוף PR בכל שבוע."],
            "avoid": ["לא להשתמש ב-top set/back-off למתחיל שעדיין צריך ללמוד תנועה בסיסית."],
            "source_refs": ["ACSM Progression Models in Resistance Training", "NSCA Guide to Program Design"],
        },
        "specialization_phase": {
            "use_when": ["כאשר משתמש רוצה להתמקד בשריר/תרגיל מסוים אחרי בסיס עקבי."],
            "coaching_goal": ["להוסיף מיקוד זמני בלי להרוס התאוששות או להזניח דפוסי בסיס."],
            "rules": [
                "specialization הוא בלוק זמני של 4-8 שבועות, לא מצב קבוע לכל הגוף.",
                "העלה נפח/תדירות לשריר יעד והורד מעט נפח תחזוקה מאזורים פחות חשובים.",
                "מדוד תגובה דרך לוגים, היקפים/ביצועים/תחושה ולא דרך pump יומי.",
            ],
            "decision_gate": ["המשתמש כבר מבצע תוכנית בסיס עקבית ומתאושש מהנפח הנוכחי."],
            "avoid": ["לא לעשות specialization לכל שריר בו זמנית; זה פשוט עודף נפח."],
            "source_refs": ["Hypertrophy Volume Meta-analysis", "Exercise Variation Review"],
        },
        "plateau_troubleshooting_ladder": {
            "use_when": ["כאשר לוגים מראים תקיעה בכוח, חזרות או גודל במשך כמה שבועות."],
            "coaching_goal": ["לפתור plateau לפי סדר, בלי להחליף הכול בבת אחת."],
            "rules": [
                "בדוק קודם עקביות, שינה, תזונה בסיסית, מנוחות, כאב וטכניקה לפני עוד נפח.",
                "אם recovery חלש: הורד נפח/עצימות; אם הגירוי נמוך: הוסף חזרות, סטים או עומס קטן.",
                "אם אותו תרגיל תקוע אבל הדפוס חשוב, שנה וריאציה קרובה או טווח חזרות בלי לאבד specificity.",
            ],
            "decision_gate": ["יש כמה לוגים דומים, לא אימון יחיד, והמשתמש באמת ביצע את התוכנית."],
            "avoid": ["לא לקרוא לחוסר עקביות plateau; לא לשנות נפח, תרגיל ותדירות ביחד."],
            "source_refs": ["ACE Strength Plateaus", "NSCA Guide to Program Design"],
        },
        "exercise_rotation_specificity": {
            "use_when": ["כאשר שוקלים להחליף תרגילים לשם novelty, כאב קל, ציוד או תקיעה."],
            "coaching_goal": ["לשמור specificity למטרה תוך שימוש בוריאציות רק כשהן משרתות תכנון."],
            "rules": [
                "ספציפיות/specificity חשובה לכוח בתרגיל מסוים; אל תחליף את התרגיל הראשי כל שבוע.",
                "להיפרטרופיה אפשר יותר וריאציות, אבל עדיין שומרים דפוס ושריר מטרה.",
                "החלף תרגיל אם יש כאב, ציוד לא מתאים, עייפות מפרקית, plateau חוזר או צורך במוטיבציה.",
            ],
            "decision_gate": ["ההחלפה פותרת בעיה ברורה ושומרת את הדפוס/המטרה המרכזית."],
            "avoid": ["לא להשתמש ב-muscle confusion כסיבה; novelty בלי לוגים פוגע במדידה."],
            "source_refs": ["Exercise Variation Review", "ACSM Progression Models in Resistance Training"],
        },
    },
    "load_prescription_protocols": {
        "starting_load_selection": {
            "use_when": ["כאשר בונים תרגיל חדש בתוכנית או אין לוגים אמינים לעומס קודם."],
            "coaching_goal": ["לבחור עומס פתיחה שמאפשר טכניקה נקייה, טווח חזרות יעד ו-RIR מתאים."],
            "rules": [
                "בחר עומס שבו המשתמש מסיים את טווח החזרות עם RIR יעד, לא לפי אגו או 1RM משוער.",
                "למתחילים, כאב, או תרגיל חדש: שמור מרווח גדול יותר, לרוב 2-4 RIR ו-RPE בינוני.",
                "אם אין נתונים, התחל קל, העלה בהדרגה בסטי ramp, ועצור לפני כשל טכני.",
            ],
            "decision_gate": ["הסט הראשון מראה טכניקה יציבה, נשימה סבירה וללא כאב חד."],
            "avoid": ["לא להתחיל בעומס כבד בגלל שהטווח כתוב בתוכנית; הטווח משרת ביצוע, לא מחליף שיפוט."],
        },
        "rir_rpe_calibration": {
            "use_when": ["כאשר המשתמש מדווח RPE/RIR או לא יודע אם המשקל מתאים."],
            "coaching_goal": ["לכייל תחושת מאמץ לאורך כמה לוגים במקום להניח שהדיווח מדויק מיד."],
            "rules": [
                "RIR הוא מספר החזרות הנקיות שנשארו לפני כשל טכני; RPE מתאר כמה הסט הרגיש קשה.",
                "כלל שימושי: RPE 8 קרוב ל-2 RIR, RPE 9 קרוב ל-1 RIR, ו-RPE 10 הוא כשל או 0 RIR.",
                "כיול RPE/RIR טוב יותר אצל משתמשים עם ניסיון; אצל מתחילים השתמש גם בטכניקה ובמהירות חזרות.",
            ],
            "decision_gate": ["הדיווח חוזר בעקביות ומתאים לביצוע בפועל במשך כמה סטים או אימונים."],
            "avoid": ["לא לקבל RIR/RPE כמדידה מדויקת אם המשתמש חדש או אם הטכניקה משתנה מאוד."],
        },
        "set_to_set_adjustment": {
            "use_when": ["במהלך אימון, כאשר הסט הראשון קל מדי, קשה מדי או הטכניקה משתנה."],
            "coaching_goal": ["להתאים את הסט הבא בלי לשנות את כל האימון."],
            "rules": [
                "אם הסט היה קל מדי והטכניקה נקייה, הוסף חזרות בטווח או קפיצת עומס קטנה בסט הבא.",
                "אם RPE גבוה, חזרות נופלות או טכניקה יורדת, שמור עומס, הארך מנוחה או הורד עומס.",
                "אם כאב מופיע, עצור את התרגיל או החלף וריאציה במקום לרדוף אחרי הסטים הכתובים.",
            ],
            "decision_gate": ["החלטה בין סטים מבוססת על RPE, חזרות בפועל, טכניקה, מנוחה וכאב."],
            "avoid": ["לא להעלות עומס באמצע אימון אם המשתמש כבר מקצר טווח, נעזר בתנופה או מאבד שליטה."],
        },
        "next_session_load_decision": {
            "use_when": ["אחרי לוג אימון, כאשר מחליטים מה לעשות בפעם הבאה באותו תרגיל."],
            "coaching_goal": ["להפוך לוגים להחלטת עומס ברורה: להעלות, לשמור, להוריד או להחליף."],
            "rules": [
                "אם המשתמש השלים את יעד החזרות בטכניקה נקייה ו-RPE סביר, העלה 2-10% או קפיצה קטנה זמינה.",
                "אם הגיע רק לחלק מהיעד אבל הטכניקה טובה, שמור עומס ונסה להוסיף חזרות בפעם הבאה.",
                "אם RPE גבוה, טכניקה יורדת, או התאוששות חלשה, שמור או הורד עומס לפני הוספת נפח.",
            ],
            "decision_gate": ["לפחות לוג אחד ברור, ועדיף 2 לוגים, מראה דפוס ולא רק יום חריג."],
            "avoid": ["לא להעלות עומס כאשר ההתקדמות הושגה דרך מנוחה קצרה מדי, טווח מקוצר או כאב."],
        },
        "submax_strength_estimation": {
            "use_when": ["כאשר רוצים הערכת כוח בלי בדיקת 1RM אמיתית."],
            "coaching_goal": ["להשתמש ב-e1RM או טווח עומס כהערכה תכנונית בלבד, לא כיעד מקסימום."],
            "rules": [
                "e1RM צריך להגיע מלוג נקי: עומס, חזרות נקיות, RIR/RPE וטווח תנועה עקבי.",
                "הצג e1RM כטווח אמון נמוך-בינוני, במיוחד אם יש מעט לוגים או RIR לא מכויל.",
                "לתכנון כללי, submax של 5-10 חזרות בטכניקה טובה עדיף לרוב על ניסיון 1RM.",
            ],
            "decision_gate": ["אין כאב, יש טכניקה יציבה, והמשתמש מבין שזו הערכה ולא מבחן כוח רשמי."],
            "avoid": ["לא לבצע או להסיק 1RM למתחיל, קטין, כאב, עייפות גבוהה או ללא תנאי בטיחות."],
        },
        "heavy_load_safety_gate": {
            "use_when": ["לפני עומסים כבדים, סטים קרובים לכשל, ברבל, או תרגיל עם סיכון גבוה יותר מרחוק."],
            "coaching_goal": ["לשמור על אימון כוח יעיל בלי לתת הוראות מסוכנות לעומס מקסימלי מרחוק."],
            "rules": [
                "עומס כבד דורש טכניקה מוכחת, חימום/ramp sets, מנוחה מספקת וסביבת אימון בטוחה.",
                "בתרגילים כבדים כמו squat/bench press, העדף rack, safety pins או ספוטר מתאים כאשר קרובים לכשל.",
                "כאב חד, סחרחורת, כאב בחזה או אובדן שליטה מעבירים את ההחלטה לשכבת safety ולא ל-load prescription.",
            ],
            "decision_gate": ["יש ציוד בטוח, ניסיון מתאים, טכניקה עקבית ואין סימן סיכון."],
            "avoid": ["לא להמליץ על בדיקת מקסימום מרחוק או על כשל טכני בתרגיל מורכב בלי תנאי בטיחות."],
        },
    },
    "equipment_substitution_protocols": {
        "no_equipment": {
            "use_when": ["כאשר המשתמש בבית, בנסיעה, בלי חדר כושר או בלי ציוד זמין."],
            "coaching_goal": ["לשמור את מטרת האימון דרך דפוס התנועה גם כשהתרגיל המקורי לא אפשרי."],
            "substitution_rules": [
                "שמור קודם על דפוס התנועה: סקוואט, hinge, דחיפה, משיכה, לאנג׳/צעד, ליבה או נשיאה.",
                "ללא ציוד, שמור את הדפוס בעזרת משקל גוף, קיר, כיסא, מדרגה, מגבת, תיק גב או טווח תנועה מותאם.",
                "דוגמאות: סקוואט לכיסא במקום leg press, שכיבות סמיכה בשיפוע במקום bench press, גשר ישבן במקום hip thrust כבד.",
            ],
            "progression_options": [
                "הגדל טווח תנועה, האט קצב, הוסף עצירה, עבור לחד-צדדי או הוסף חזרות לפני שמחפש ציוד.",
                "כאשר קל מדי גם בטכניקה איטית, השתמש בתיק גב או בגרסה חד-צדדית שמורה.",
            ],
            "avoid": ["לא לבטל אימון בגלל שאין ציוד; לא להחליף דפוס מרכזי בתרגיל אקראי רק כי הוא קשה."],
        },
        "bands": {
            "use_when": ["כאשר יש גומיות התנגדות, עוגן דלת או צורך בפתרון נייד וזול."],
            "coaching_goal": ["לייצר התנגדות שימושית בדפוסי דחיפה, משיכה, ירך וכתף בלי ציוד כבד."],
            "substitution_rules": [
                "גומיות מתאימות במיוחד לחתירה/row, face pull, pull-apart, לחיצה בעמידה, הרחקות ותרגילי ירך.",
                "בחר עוגן יציב וזווית שמחקה את כיוון המשיכה של התרגיל המקורי.",
                "במשיכה, חתירה עם גומייה יכולה להחליף cable row; בכתף, face pull עם גומייה יכול להחליף כבל.",
            ],
            "progression_options": [
                "התרחק מהעוגן, בחר גומייה חזקה יותר, האט אקסצנטרי או עצור בקצה התנועה.",
                "שלב גומייה עם משקל גוף, למשל banded push-up או banded glute bridge, רק אם הטכניקה נשמרת.",
            ],
            "avoid": ["לא להשתמש בעוגן לא יציב; לא לבחור גומייה שמושכת את המשתמש לטכניקה לא נשלטת."],
        },
        "dumbbells": {
            "use_when": ["כאשר יש משקולות יד, קטלבל, תיק עם משקל או עומס ידני מוגבל."],
            "coaching_goal": ["לשמור עומס חיצוני פשוט וגמיש בלי תלות במוט או מכונה."],
            "substitution_rules": [
                "לחיצת רצפה/floor press או לחיצת משקולות בשיפוע יכולות להחליף bench press לפי ציוד וטווח.",
                "סקוואט גביע/goblet squat, split squat ו-step-up יכולים להחליף squat/leg press לפי יכולת.",
                "RDL עם משקולות יד, קטלבל או תיק יכול להחליף deadlift/RDL עם מוט כאשר שומרים גב ניטרלי.",
            ],
            "progression_options": [
                "הוסף חזרות, עומס קטן, סט, טווח, האטת קצב או וריאציה חד-צדדית לפי הלוגים.",
                "כאשר המשקל קל מדי, השתמש ב-tempo, עצירה בתחתית, unilateral או טווח ארוך יותר.",
            ],
            "avoid": ["לא לרדוף אחרי עומס יד כבד אם האחיזה, הגב או הכתף מגבילים את הטכניקה."],
        },
        "machines_cables": {
            "use_when": ["כאשר יש חדר כושר, מכונות, כבלים או צורך בגרסה יציבה יותר ללמידה."],
            "coaching_goal": ["להשתמש במכונה או כבל ככלי יעיל, לא כסימן שהתוכנית טובה יותר."],
            "substitution_rules": [
                "מכונה וכבל יכולים להחליף תרגיל חופשי כאשר צריך יציבות, שליטה בטווח או עקומת התנגדות נוחה.",
                "leg press יכול להחליף וריאציית סקוואט זמנית, cable row יכול להחליף חתירה חופשית, chest press יכול להחליף לחיצת חזה.",
                "שמור התאמה לדפוס ולמטרה: דחיפה נשארת דחיפה, משיכה נשארת משיכה, ירך נשארת hinge או extension.",
            ],
            "progression_options": [
                "התקדם דרך עומס קטן, טווח מלא נשלט, קצב או מעבר הדרגתי לגרסה חופשית אם זה משרת את המטרה.",
                "השתמש במכונה כדי ללמוד מאמץ וטווח לפני מעבר לתרגיל מורכב יותר.",
            ],
            "avoid": ["לא להציג מכונות כקלות מדי או חופשיים כעליונים תמיד; הבחירה תלויה במטרה ובמשתמש."],
        },
        "progression_without_load": {
            "use_when": ["כאשר אין אפשרות להעלות משקל אבל התרגיל כבר קל מדי."],
            "coaching_goal": ["להוסיף אתגר בלי לשבור טכניקה או לקנות ציוד מיותר מוקדם מדי."],
            "substitution_rules": [
                "אם אין עומס נוסף, אל תחליף מיד תרגיל; קודם שנה את המשתנים שניתן לשלוט בהם.",
                "שמור את התרגיל באותו דפוס והעלה קושי רק אם הטכניקה וההתאוששות נשמרות.",
            ],
            "progression_options": [
                "השתמש בקצב איטי, טווח תנועה גדול יותר, עצירה, חזרות נוספות, פחות מנוחה או גרסה חד-צדדית.",
                "אפשר להשתמש במנוף קשה יותר: שכיבות סמיכה נמוכות יותר, split squat עמוק יותר, RDL חד-רגלי נתמך.",
            ],
            "avoid": ["לא להפוך כל סט לסבל ארוך; אם העומס קל מדי לאורך זמן, תכנן רכישת ציוד מינימלית או גישה לעומס מתאים."],
        },
    },
    "session_structure_protocols": {
        "exercise_order": {
            "use_when": ["בכל בניית אימון כוח, התאמת אימון קיים או קיצור אימון."],
            "coaching_goal": ["למקם עבודה טכנית וחשובה לפני עייפות כדי לשמור ביצוע ובטיחות."],
            "structure_rules": [
                "אם יש Power או כוח מתפרץ, מקם אותו אחרי חימום ולפני כוח כבד או נפח.",
                "מקם תרגילים מורכבים ורב-מפרקיים לפני תרגילי עזר או חד-מפרקיים.",
                "עבודה כבדה, מיומנות גבוהה וטכניקה חדשה מגיעות לפני בידוד, ליבה או finisher.",
            ],
            "adjustment_rules": [
                "ביום קצר, שמור את התרגיל המרכזי והסר אביזרים לפני שמקצר חימום או מפרק טכניקה.",
            ],
            "avoid": ["לא להתחיל בבידוד או finisher אם זה פוגע בתרגיל המרכזי של המטרה."],
        },
        "rest_intervals": {
            "use_when": ["כאשר בוחרים מנוחה בין סטים או מסבירים למה אימון אורך זמן מסוים."],
            "coaching_goal": ["להתאים מנוחה למטרה בלי לקצר עד שהטכניקה או הביצוע נפגעים."],
            "structure_rules": [
                "לכוח כבד השתמש לרוב ב-2-4 דקות, ולעיתים 3-5 דקות בתרגילים כבדים מאוד.",
                "להיפרטרופיה או סבולת השתמש בערך 0-90 שניות לפי איכות, נשימה ומטרת הסט.",
                "ל-Power שמור מנוחה שמחזירה מהירות ואיכות, לא רק דופק גבוה.",
            ],
            "adjustment_rules": ["אם חזרות או טכניקה יורדות בגלל קוצר מנוחה, הארך מנוחה לפני שמוריד עומס."],
            "avoid": ["לא להפוך כל אימון ל-cardio circuit כאשר המטרה היא כוח או טכניקה כבדה."],
        },
        "tempo_control": {
            "use_when": ["כאשר המשתמש לומד תנועה, צריך שליטה, או אין אפשרות להעלות עומס."],
            "coaching_goal": ["להשתמש בקצב כדי ללמד שליטה ולהעלות קושי בלי לזייף טווח או כאב."],
            "structure_rules": [
                "ללמידה ויציבות, tempo כמו 4/2/1 יכול לעזור: ירידה איטית, עצירה קצרה ועלייה נשלטת.",
                "להיפרטרופיה, קצב בינוני ושליטה באקסצנטרי מספיקים לרוב; לא צריך ספירה מסובכת לכל סט.",
                "ל-Power, הכוונה היא עלייה מהירה ואיכותית עם עומס מתאים, לא זריקת משקל בלי שליטה.",
            ],
            "adjustment_rules": ["כאשר ציוד קל מדי, האט קצב או הוסף עצירה לפני שמוסיף נפח גדול."],
            "avoid": ["לא לכפות tempo איטי בתרגיל כוח מתפרץ; לא להאריך סט עד פירוק טכניקה."],
        },
        "supersets_and_circuits": {
            "use_when": ["כאשר הזמן קצר או רוצים להעלות צפיפות עבודה בלי לבטל תרגילים חשובים."],
            "coaching_goal": ["לחסוך זמן בלי לפגוע בתרגיל המרכזי, בטכניקה או בהתאוששות בין סטים כבדים."],
            "structure_rules": [
                "superset/סופרסט הוא שני תרגילים ברצף עם מעט או בלי מנוחה, ואז מנוחה לפני הסבב הבא.",
                "בחר זוגות שלא מתנגשים: דחיפה עם משיכה, עליון עם תחתון, או כוח יציב ואז יציבות קלה יותר.",
                "ב-circuit למתחילים או לזמן קצר, שמור עומס בינוני וקצב נשלט לפני עצימות גבוהה.",
            ],
            "adjustment_rules": ["אם superset מוריד ביצוע בתרגיל המרכזי, הפרד מנוחות או שים אותו בסוף."],
            "avoid": ["לא לשלב שני תרגילים טכניים כבדים ברצף כשזה פוגע בבטיחות או במטרה."],
        },
        "warmup_ramp_sets": {
            "use_when": ["לפני תרגיל מרכזי, אימון כוח כבד או משתמש שחוזר אחרי הפסקה."],
            "coaching_goal": ["להכין תנועה, טווח ועומס בלי לבזבז את רוב האימון."],
            "structure_rules": [
                "התחל בחימום כללי קצר ואז חימום ספציפי לדפוסי האימון.",
                "לפני סטים כבדים, השתמש ב-ramp sets: כמה סטים קלים שעולים בעומס ויורדים בחזרות.",
                "חימום צריך לשפר ביצוע, לא לעייף; עצור לפני שהוא הופך לאימון בפני עצמו.",
            ],
            "adjustment_rules": ["ביום קצר, קצר אביזרים ולא את סטי החימום הדרושים לתרגיל המרכזי."],
            "avoid": ["לא להיכנס לסט כבד ראשון בלי הכנה ספציפית; לא לעשות חימום ארוך שמתיש משתמש מתחיל."],
        },
    },
    "nutrition_coaching_rules": [
        "לפני אימון, פחמימות עוזרות לדלק וחלבון תומך תיקון ובנייה; התזמון תלוי סבילות ואורך האימון.",
        "אחרי אימון קשה, ארוחה או נשנוש עם פחמימות וחלבון בתוך חלון סביר יכולים לעזור התאוששות.",
        "אל תיתן תפריט רפואי, דיאטת קיצון או מספרי קלוריות מדויקים בלי נתונים ובלי מסגרת מקצועית מתאימה.",
    ],
    "practical_nutrition_protocols": {
        "non_clinical_scope": {
            "use_when": ["בכל תשובת תזונה, תיעוד ארוחה או ניתוח תמונת אוכל."],
            "coaching_goal": ["לתת תמיכת הרגלים כללית בלי להפוך את המאמן לדיאטן קליני או רופא."],
            "rules": [
                "עסוק בהרגלים, בחירות מזון כלליות, טווחים, תכנון סביב אימון ושאלות הבהרה קצרות.",
                "במצבים רפואיים, הריון, קטינים, הפרעות אכילה, ירידה קיצונית במשקל או תפריט טיפולי - הישאר כללי והפנה לאיש מקצוע מתאים.",
                "אל תציג קלוריות, מאקרו או תוצאות מתמונה כמספר מדויק או כאבחנה.",
            ],
            "decision_gate": ["הבקשה נשארת בתחום wellness והרגלי אוכל כלליים, ולא דורשת טיפול או אבחון תזונתי אישי."],
            "avoid": ["לא לבנות תפריט רפואי, לא להבטיח ירידה מהירה, לא לתת פרוטוקול תוספים או תרופות."],
        },
        "plate_builder": {
            "use_when": ["כאשר המשתמש שואל מה לאכול, איך לבנות ארוחה, או איך לשפר ארוחה שתועדה."],
            "coaching_goal": ["לתת מבנה ארוחה פשוט שאפשר לבצע בלי ספירת גרמים."],
            "rules": [
                "צלחת התחלה טובה: מקור חלבון, ירק או פרי, פחמימה שמתאימה לאימון, ושומן/טעם במידה.",
                "במקום 'אסור', הצע החלפה אחת: הוסף ירק, בחר דגן מלא/קטניות, או הוסף חלבון זמין.",
                "התאם לתרבות אוכל, אלרגיות, תקציב, זמן והעדפות; ביצוע עקבי עדיף מתפריט מושלם.",
            ],
            "decision_gate": ["המשתמש צריך פעולה בארוחה הקרובה ולא חישוב תזונתי מלא."],
            "avoid": ["לא להפוך את הצלחת לחוק קשיח; לא להציג מזונות כטובים/רעים באופן מוסרי."],
        },
        "protein_anchor": {
            "use_when": ["כאשר המטרה היא שובע, בניית שריר, התאוששות או שיפור ארוחה."],
            "coaching_goal": ["להפוך חלבון לעוגן פשוט בארוחות בלי לקפוץ מיד למקרו מדויק."],
            "rules": [
                "ברירת המחדל: מקור חלבון בכל ארוחה מרכזית, כמו ביצים, יוגורט, עוף, דג, טופו, קטניות או גבינה.",
                "טווחי גרם/ק״ג מתאימים רק כשיש הקשר בריא וספורטיבי והמשתמש מבקש דיוק; הצג אותם כטווח כללי.",
                "אם החלבון חסר בלוג, הצע תוספת אחת לארוחה הבאה במקום ביקורת על כל היום.",
            ],
            "decision_gate": ["אין מגבלה רפואית או תזונתית שמחייבת דיאטן קליני."],
            "avoid": ["לא להמליץ על עודף חלבון או אבקות כפתרון ראשון; לא להתעלם מאלרגיות/העדפות."],
        },
        "fiber_produce_habit": {
            "use_when": ["כאשר המשתמש רוצה שובע, ירידה בשומן, עיכול טוב יותר או ארוחה דלה במזון מלא."],
            "coaching_goal": ["להוסיף סיבים, ירקות ופירות בצעד קטן."],
            "rules": [
                "הצע תוספת אחת: ירק בארוחה, פרי שלם, קטניות, שיבולת שועל או דגן מלא.",
                "השתמש בשפה פרקטית: 'תוסיף' או 'תחליף חלק' במקום למחוק את כל הארוחה.",
                "העדף פרי שלם על שתייה מתוקה/מיץ כשזה מתאים, בלי להפוך את זה לאיסור מוחלט.",
            ],
            "decision_gate": ["המשתמש יכול לשנות רכיב אחד בארוחה הקרובה או בקנייה הקרובה."],
            "avoid": ["לא להעמיס סיבים בבת אחת אם המשתמש רגיש; לא לתת טיפול לבעיות עיכול רפואיות."],
        },
        "hydration_habit": {
            "use_when": ["כאשר המשתמש שואל על מים, אימון בחום, עייפות, או תיעוד ארוחות בלי שתייה."],
            "coaching_goal": ["להפוך שתייה להרגל פשוט שמותאם לאימון, חום והזעה."],
            "rules": [
                "נקודת התחלה פשוטה: מים עם ארוחות ועוד שתייה לפני/במהלך/אחרי אימון לפי צמא, חום והזעה.",
                "בחר מים או משקה דל סוכר כברירת מחדל; בקבוק זמין מקל על עקביות.",
                "בימים חמים, אימון ארוך או הזעה רבה, הצורך במים עולה; אל תיתן מספר ליטרים קשיח לכולם.",
            ],
            "decision_gate": ["אין סימני התייבשות חמורים או מצב רפואי שמצריך הנחיה מקצועית."],
            "avoid": ["לא להבטיח שמים פותרים עייפות או ירידה במשקל; לא לתת הנחיות נוזלים רפואיות."],
        },
        "meal_prep_fallback": {
            "use_when": ["כאשר המשתמש מפספס ארוחות, אוכל בחוץ הרבה, או אומר שאין זמן."],
            "coaching_goal": ["לבנות fallback שמונע קריסה של היום בלי הכנת אוכל מורכבת."],
            "rules": [
                "תבנית meal prep קצרה: חלבון זמין, ירק/פרי, פחמימה בסיסית, וטעם/רוטב שנוח לאכול.",
                "אפשר להכין רק רכיב אחד מראש: חלבון, ירקות חתוכים, אורז/תפוח אדמה, או קופסת emergency.",
                "במסעדה או קיוסק, חפש את אותה תבנית במקום לדרוש ארוחה מושלמת.",
            ],
            "decision_gate": ["החסם הוא זמן/נגישות ולא בעיה רפואית או הפרעת אכילה."],
            "avoid": ["לא לבנות תפריט שבועי גדול לפני שהמשתמש מצליח לבצע fallback קטן."],
        },
        "pre_post_workout_choices": {
            "use_when": ["כאשר הארוחה קשורה לאימון, אנרגיה באימון או התאוששות אחרי אימון."],
            "coaching_goal": ["לתת בחירות פשוטות סביב אימון בלי להפוך nutrient timing לעיקר."],
            "rules": [
                "לפני אימון בינוני-קשה: פחמימה קלה לעיכול וקצת חלבון 1-4 שעות לפני, לפי סבילות.",
                "אחרי אימון קשה: נוזלים, חלבון ופחמימה בארוחה או נשנוש; אימון קצר וקל לא דורש טקס מיוחד.",
                "סך היום, עקביות וסבילות חשובים יותר מחלון זמן מושלם.",
            ],
            "decision_gate": ["המשתמש מתאמן או מתכנן אימון, ואין בקשה לטיפול תזונתי רפואי."],
            "avoid": ["לא להציג pre-workout/post-workout כחובה יקרה; לא לדחוף תוספים."],
        },
        "food_image_uncertainty": {
            "use_when": ["כאשר מנתחים תמונת אוכל או תיאור קצר עם כמויות לא ברורות."],
            "coaching_goal": ["לשמור אמינות: טווחים, ביטחון, הנחות ושאלת המשך אחת."],
            "rules": [
                "מתמונה מחזירים טווח קלוריות/מאקרו, רמת ביטחון, מזונות שזוהו, אי ודאות והנחות.",
                "אם חסרים שמן, רוטב, גודל מנה או שיטת הכנה, שאל שאלה אחת שמדייקת הכי הרבה.",
                "שמור את התוצאה כ-estimate לעריכה, לא כערך אמת.",
            ],
            "decision_gate": ["יש מספיק מידע לתת טווח גס בלי להמציא רכיבים מרכזיים."],
            "avoid": ["לא להחזיר מספר יחיד; לא לטעון לזיהוי ודאי כאשר התמונה חלקית או מטושטשת."],
        },
    },
    "sports_nutrition_rules": [
        "תזונה סביב אימון היא תמיכה בביצוע ובהתאוששות: מספיק אנרגיה, חלבון, פחמימות, מים ושינה לפני חיפוש פרטים קטנים.",
        "הערכות קלוריות ומאקרו מוצגות כטווח או הערכה עם אי ודאות, במיוחד כאשר המידע מגיע מתיאור קצר או מתמונה.",
        "התאם המלצות להעדפות, אלרגיות, תרבות אוכל, זמינות ולוגים בפועל; הרגל שניתן לבצע עדיף מתפריט מושלם על הנייר.",
        "בבקשות רפואיות, הפרעות אכילה, מחלות רלוונטיות או ירידה קיצונית במשקל, הישאר בתמיכה כללית והפנה לאיש מקצוע מתאים.",
    ],
    "protein_guidelines": [
        "לרוב המתאמנים, טווח חלבון יומי כללי של 1.4-2.0 גרם לק״ג ליום יכול להספיק לתמיכה באימון והתאוששות.",
        "בארוחה אחת, 20-40 גרם חלבון או בערך 0.25 גרם לק״ג הם עוגן שימושי, לפי גודל גוף, מטרה וסבילות.",
        "פיזור חלבון כל 3-4 שעות יכול לתמוך בסינתזת חלבון שריר ובשובע, בלי להפוך את התזמון לכלל נוקשה.",
        "העדף מקורות מזון מלאים ונגישים; אבקת חלבון היא כלי נוחות, לא חובה ולא פתרון קסם.",
    ],
    "carbohydrate_fueling_rules": [
        "פחמימות הן מקור דלק מרכזי לאימונים בינוניים-עצימים, נפח גבוה ואימוני סיבולת.",
        "ארוחה או נשנוש 1-4 שעות לפני אימון יכולים לעזור לביצוע, במיוחד כאשר האימון ארוך, עצים או נעשה אחרי שעות בלי אוכל.",
        "אחרי אימון קשה או כפול, שילוב פחמימות וחלבון יכול לתמוך בחידוש גליקוגן ובהתאוששות.",
        "אל תציג פחמימות כאויב; התאם כמות לפי מטרה, אימונים, רעב, העדפות וסך האנרגיה.",
    ],
    "hydration_rules": [
        "מים והידרציה משפיעים על ביצוע, תחושת מאמץ, עייפות והתאוששות, במיוחד בחום או באימון ממושך.",
        "כוון לשתייה עקבית לאורך היום ולפני אימון; באימון ארוך, חם או מזיע במיוחד ייתכן צורך בנוזלים נוספים ובמלחים.",
        "סימנים כמו צמא חריג, שתן כהה מאוד, כאבי ראש או ירידה חדה בביצוע יכולים לרמוז שצריך לבדוק שתייה והתאוששות.",
        "אל תיתן נוסחת שתייה מדויקת כאילו היא מתאימה לכולם; התאם לפי משך, חום, הזעה ותחושת הגוף.",
    ],
    "body_composition_rules": [
        "משקל גוף לבדו לא מספר את כל הסיפור של הרכב גוף; עקוב גם אחרי כוח, היקפים, בגדים, ביצועים, אנרגיה ועקביות.",
        "בניית שריר דורשת אימון התנגדות מתקדם בהדרגה, מספיק אנרגיה, חלבון ושינה; לא רק יותר תרגילים.",
        "ירידה בשומן צריכה לשמור ככל האפשר על כוח ומסת שריר דרך כוח, חלבון, צעדים/אירובי נגיש וגירעון מתון.",
        "אל תעודד שקילה אובססיבית או ירידה מהירה; העדף מגמה שבועית והתנהגות שאפשר להחזיק.",
    ],
    "body_composition_strategy_protocols": {
        "energy_balance_basics": {
            "use_when": ["כאשר המשתמש שואל על ירידה במשקל, עלייה במסה, ריקומפ או למה המשקל לא משתנה."],
            "coaching_goal": ["להסביר מאזן אנרגטי בצורה פשוטה בלי להפוך את השיחה לתפריט קליני."],
            "rules": [
                "מאזן קלורי/מאזן אנרגטי קובע את כיוון המשקל לאורך זמן: אנרגיה נכנסת מול אנרגיה יוצאת.",
                "המספר המדויק של קלוריות תחזוקה הוא אומדן; משתמשים במשקל, היקפים, רעב, ביצועים ולוגים כדי לכייל.",
                "קלוריות הן כלי החלטה, לא ציון מוסרי ולא סיבה לענישה באימון.",
            ],
            "decision_gate": ["יש לפחות כמה ימי נתונים או שהמשתמש מבין שמדובר בהערכה ולא באמת מוחלטת."],
            "avoid": ["לא לתת מספר קלוריות מדויק בלי נתונים; לא להציג מאזן קלורי כאילו הוא מבטל שינה, אימון, רעב או התמדה."],
            "source_refs": ["NIDDK Body Weight Planner", "Academy Weight Management Position", "ISSN Diets and Body Composition"],
        },
        "fat_loss_phase": {
            "use_when": ["כאשר המטרה היא חיטוב, ירידה בשומן או ירידה במשקל בלי לאבד שריר."],
            "coaching_goal": ["לכוון לגירעון מתון שמאפשר כוח, חלבון, שינה והתמדה."],
            "rules": [
                "בחיטוב המטרה היא גירעון קלורי מתון, לא ריסוק אנרגיה או אימוני ענישה.",
                "שמור אימוני כוח כעוגן, יעד חלבון, צעדים/אירובי נגיש ושינה ככל האפשר.",
                "ירידה מהירה מדי, רעב חריג, עייפות קשה או ירידה בביצועים הם סימן לבדוק את המינון.",
            ],
            "decision_gate": ["מגמת משקל או היקפים יורדת לאורך כמה שבועות בלי קריסה באימונים או בתחושה."],
            "avoid": ["לא לעודד דיאטות קיצון, צום כפוי, שריפת קלוריות כעונש או יעד משקל אגרסיבי."],
            "source_refs": ["Academy Weight Management Position", "ISSN Diets and Body Composition", "ISSN Protein Position Stand"],
        },
        "muscle_gain_phase": {
            "use_when": ["כאשר המשתמש רוצה מסה, עלייה בשריר או יותר כוח וגודל."],
            "coaching_goal": ["להסביר עודף קלורי קטן ומבוקר לצד התקדמות באימוני כוח."],
            "rules": [
                "במסה, עודף קלורי קטן ומבוקר תומך בעלייה בשריר בלי עלייה מיותרת בשומן.",
                "התקדמות באימון, חלבון מספיק ושינה חשובים לא פחות מאכילה של עוד קלוריות.",
                "אם המשקל עולה מהר אבל הביצועים לא משתפרים, ייתכן שהעודף גדול מדי.",
            ],
            "decision_gate": ["יש עלייה הדרגתית במשקל או היקפים לצד שיפור בלוגי כוח/חזרות ותחושה טובה."],
            "avoid": ["לא להמליץ על אכילה ללא בקרה או גיינרים כפתרון ראשון; לא להבטיח שרוב העלייה תהיה שריר."],
            "source_refs": ["ISSN Diets and Body Composition", "ISSN Protein Position Stand", "ACSM Resistance Training Guidelines 2026"],
        },
        "recomposition_phase": {
            "use_when": ["כאשר המשתמש רוצה פחות שומן ויותר שריר, מתחיל אימוני כוח או חוזר אחרי הפסקה."],
            "coaching_goal": ["לכוון לריקומפ: שיפור הרכב גוף דרך כוח, חלבון ועקביות גם אם המשקל זז לאט."],
            "rules": [
                "ריקומפ הוא שינוי הרכב גוף: שמירה/עלייה בשריר וירידה בשומן, לא בהכרח שינוי חד במשקל.",
                "הוא ריאלי יותר במתחילים, חוזרים אחרי הפסקה, או משתמשים עם עודף שומן יחסי.",
                "המדדים החשובים: כוח עולה, היקפים/בגדים משתנים, אנרגיה סבירה ומגמת משקל שלא מטעה לבד.",
            ],
            "decision_gate": ["כמה שבועות של אימוני כוח עקביים, חלבון סביר ומדדים שאינם רק משקל יומי."],
            "avoid": ["לא להבטיח בו זמנית ירידת שומן מהירה ועליית שריר גדולה; לא לשפוט לפי שקילה אחת."],
            "source_refs": ["ISSN Diets and Body Composition", "ISSN Protein Position Stand", "Resistance Training Body Composition Review"],
        },
        "scale_trend_interpretation": {
            "use_when": ["כאשר המשתמש נלחץ משקילה יומית או שואל אם התוכנית עובדת."],
            "coaching_goal": ["להעביר את המיקוד ממספר יומי למגמת משקל ונתוני התנהגות."],
            "rules": [
                "מגמת משקל או ממוצע שבועי חשובים יותר מהמספר של היום.",
                "מים, מלח, פחמימות, מחזור, סטרס, שינה ואימון קשה יכולים להזיז משקל בלי שינוי שומן אמיתי.",
                "בדוק את הממוצע, ההיקפים, הביצועים וההתמדה לפני שינוי גדול.",
            ],
            "decision_gate": ["יש לפחות 7-14 ימים של מדידות דומות או נתונים חלופיים כמו היקפים וביצועים."],
            "avoid": ["לא לשנות תוכנית בגלל שקילה אחת; לא לעודד שקילה אם היא מגבירה חרדה או התנהגות כפייתית."],
            "source_refs": ["NIDDK Body Weight Planner", "ACSM Body Composition Assessment", "ISSN Diets and Body Composition"],
        },
        "measurements_and_non_scale_signals": {
            "use_when": ["כאשר המשקל תקוע, המשתמש בונה שריר, או רוצים dashboard התקדמות רחב יותר."],
            "coaching_goal": ["לבחור מדדים משלימים שלא מצמצמים הצלחה למשקל בלבד."],
            "rules": [
                "מדדי עזר: היקף מותניים, בגדים, תמונות התקדמות אם המשתמש רוצה, כוח, חזרות, אנרגיה ושינה.",
                "מדוד היקפים בתנאים דומים ולא כל יום; פעם בשבוע או שבועיים מספיקה לרוב.",
                "אם כוח עולה והיקפים משתפרים, המשקל יכול להיות איטי ועדיין יש התקדמות.",
            ],
            "decision_gate": ["המשתמש מסכים למדד שאינו מעורר לחץ ומוכן לעקוב בעקביות."],
            "avoid": ["לא לחייב תמונות או מדידות גוף; לא לפרש היקף אחד כאבחנה רפואית."],
            "source_refs": ["ACSM Body Composition Assessment", "ACE Client-Centered Assessments", "ISSN Diets and Body Composition"],
        },
        "plateau_review": {
            "use_when": ["כאשר המשתמש טוען שיש תקיעות/פלאטו בירידה בשומן, במשקל או בשינוי הרכב גוף."],
            "coaching_goal": ["להבדיל בין רעש מדידה, חוסר עקביות ותקיעות אמיתית לפני שינוי חד."],
            "rules": [
                "פלאטו דורש דפוס: ממוצע שבועי והיקפים לא זזים במשך כשבועיים-שלושה, לא יום אחד.",
                "בדוק קודם עקביות: לוג אוכל, חלבון, צעדים, אימוני כוח, שינה וסופי שבוע.",
                "שנה משתנה אחד: מעט פחות קלוריות, יותר צעדים, יותר דיוק בלוגים, או שלב תחזוקה אם העייפות גבוהה.",
            ],
            "decision_gate": ["יש כמה שבועות נתונים והמשתמש באמת עקבי ברוב המרכיבים המרכזיים."],
            "avoid": ["לא להוריד קלוריות אוטומטית לפני בדיקת עקביות; לא להוסיף HIIT כתגובה ראשונה לפלאטו."],
            "source_refs": ["NIDDK Body Weight Planner", "Academy Weight Management Position", "ISSN Diets and Body Composition"],
        },
        "maintenance_phase": {
            "use_when": ["כאשר המשתמש עייף מחיטוב, חוזר אחרי ירידה, או צריך להחזיק תוצאה בלי עוד לחץ."],
            "coaching_goal": ["להשתמש בתחזוקה או diet break ככלי התמדה ולא ככישלון."],
            "rules": [
                "תחזוקה היא שלב שבו המשקל נשאר יחסית יציב וההרגלים ממשיכים.",
                "diet break/הפסקת דיאטה יכולה לעזור להחזיר אנרגיה, ביצועים והתמדה לפני המשך חיטוב.",
                "אחרי ירידה, שלב תחזוקה עם אותם עוגנים - כוח, חלבון, צעדים ושינה - חשוב לשימור התוצאה.",
            ],
            "decision_gate": ["המשתמש מדווח עייפות, רעב, ירידת ביצועים או צורך בתקופה יציבה יותר."],
            "avoid": ["לא לקרוא לתחזוקה כישלון; לא להפוך הפסקה לאכילה חסרת מבנה בלי מעקב בסיסי."],
            "source_refs": ["NIDDK Body Weight Planner", "Academy Weight Management Position", "ISSN Diets and Body Composition"],
        },
    },
    "meal_timing_rules": [
        "לפני אימון קצר וקל, לא תמיד צריך ארוחה ייעודית; לפני אימון קשה, ארוחה 1-4 שעות לפני יכולה לעזור.",
        "אחרי אימון, ארוחה עם חלבון ופחמימות בתוך חלון סביר מספיקה לרוב המשתמשים; אין צורך להלחיץ סביב דקות מדויקות.",
        "כשיש אימונים צפופים באותו יום או למחרת, תזמון אוכל ונוזלים סביב האימון נעשה חשוב יותר.",
        "אם המשתמש מדווח על בחילה, כבדות או רעב באימון, התאם גודל ארוחה, שומן/סיבים ותזמון.",
    ],
    "common_fitness_myth_protocols": {
        "spot_reduction": {
            "user_claims": ["איך להוריד שומן בבטן/ידיים/ירכיים", "איזה תרגיל שורף שומן באזור מסוים", "spot reduction"],
            "coach_position": [
                "אין לבנות הבטחה של ירידת שומן נקודתית; תרגיל מקומי מחזק שריר באזור, אבל ירידת שומן נקבעת בעיקר ממאזן אנרגיה, גנטיקה ועקביות.",
                "אפשר לשפר מראה אזור מסוים דרך חיזוק השריר, ירידת שומן כללית, יציבה ותוכנית שמתאימה למשתמש.",
            ],
            "what_to_do_instead": [
                "לתת תוכנית שמחברת כוח לכל הגוף, צעדים/אירובי, חלבון, שינה ולוגים במקום מאות כפיפות בטן.",
                "אם המטרה אסתטית, להציע מדדים כמו היקף/תמונות/ביצועים ולא רק משקל יומי.",
            ],
            "avoid": ["לא להבטיח שריפת שומן נקודתית; לא למכור תרגיל בטן כתחליף לתוכנית כוללת."],
            "source_refs": ["Abdominal Exercise Spot Reduction Trial", "Localized Fat Loss Systematic Review", "University of Sydney Spot Reduction Explainer"],
        },
        "soreness_and_quality": {
            "user_claims": ["אם לא כואב לי השריר זה לא עבד", "צריך DOMS כדי לגדול", "no pain no gain"],
            "coach_position": [
                "DOMS הוא תגובה נפוצה לעומס חדש או אקסצנטרי, אבל אינו מדד אמין לאיכות אימון או לגדילת שריר.",
                "אימון טוב יכול להסתיים בלי כאבי שרירים; המדדים החשובים הם טכניקה, עומס מתאים, התקדמות, התאוששות ויכולת לחזור להתאמן.",
            ],
            "what_to_do_instead": [
                "לבדוק לוג: חזרות/משקל/RPE, שינה, כאב חריג, ויכולת לבצע את האימון הבא.",
                "אם DOMS חזק, להפחית נפח/טווח/עצימות זמנית ולעשות תנועה קלה במקום להעניש בעוד עומס.",
            ],
            "avoid": ["לא לעודד כאב כמטרה; לא לקרוא לחוסר DOMS ככישלון."],
            "source_refs": ["Cochrane Stretching DOMS Review", "Delayed Onset Muscle Soreness Review", "Cleveland Clinic DOMS"],
        },
        "sweat_and_fat_loss": {
            "user_claims": ["אם הזעתי הרבה שרפתי יותר שומן", "אימון בלי זיעה לא נחשב", "סאונה שורפת שומן"],
            "coach_position": [
                "זיעה היא בעיקר ויסות חום ואיבוד מים זמני, לא מדד ישיר לשריפת שומן או קלוריות.",
                "אפשר להתאמן טוב מאוד עם מעט זיעה, במיוחד בכוח, מזגן או עצימות מבוקרת.",
            ],
            "what_to_do_instead": [
                "למדוד איכות לפי התאמה למטרה: סטים איכותיים, RPE, דופק/דיבור באירובי, עקביות ושיפור לאורך שבועות.",
                "בחום או הזעה גבוהה, להתמקד בהידרציה, מנוחות וסימני עומס חום.",
            ],
            "avoid": ["לא להמליץ על שכבות/חום/סאונה כדי 'לשרוף שומן'; לא לבלבל ירידת מים עם ירידת שומן."],
            "source_refs": ["CDC Heat and Athletes", "CDC Heat-related Illnesses"],
        },
        "fasted_cardio": {
            "user_claims": ["חייבים אירובי על בטן ריקה", "fasted cardio שורף יותר שומן", "אסור לאכול לפני cardio"],
            "coach_position": [
                "fasted cardio לא עדיף לירידת שומן כאשר סך הקלוריות, החלבון והאימון דומים; הוא בעיקר עניין של נוחות וסבילות.",
                "אם אימון בצום פוגע בביצוע, גורם סחרחורת או מקשה להתמיד, עדיף לאכול משהו קל לפני.",
            ],
            "what_to_do_instead": [
                "לבחור תזמון שהמשתמש מסוגל לבצע בעקביות, עם עוצמה מתאימה וללא סימפטומים.",
                "לפני אימון ארוך/עצים, לשקול פחמימה קלה לעיכול ונוזלים לפי סבילות.",
            ],
            "avoid": ["לא להציג צום ככלי חובה; לא להתעלם מסחרחורת, היסטוריית אכילה רגישה או ירידת ביצועים."],
            "source_refs": ["Fasted Exercise Body Composition Review", "Body Composition Fasted vs Fed Trial", "Academy of Nutrition and Dietetics"],
        },
        "strength_training_bulky_fear": {
            "user_claims": ["אני אישה ולא רוצה להתנפח", "משקולות יהפכו אותי לגדול מדי", "רק חיטוב בלי כוח"],
            "coach_position": [
                "אימוני כוח לנשים ולגברים משפרים כוח, תפקוד, מסת שריר, צפיפות עצם והרכב גוף; הם לא הופכים משתמשת ל׳מנופחת׳ לבד.",
                "מראה שרירי מאוד דורש לרוב שנים של אימון ייעודי, נפח גבוה, תזונה מתאימה ולעיתים גורמים נוספים; תוכנית בסיסית לא עושה זאת בטעות.",
            ],
            "what_to_do_instead": [
                "להשתמש בכוח כבסיס לחיטוב: 2-3 אימוני full-body, חלבון מספק, צעדים ושינה.",
                "להתאים שפה למטרה: 'להתחזק', 'להרגיש יציבה', 'להדק הרגלים' ולא לכפות מטרת מסת שריר.",
            ],
            "avoid": ["לא לזלזל בפחד של המשתמשת; לא להבטיח צורת גוף מדויקת או תוצאה אסתטית אחת."],
            "source_refs": ["NSCA Resistance Training for Women", "Mayo Clinic Strength Training", "CDC Adult Physical Activity"],
        },
    },
    "supplement_education_protocols": {
        "creatine_monohydrate": {
            "use_when": ["שאלה על קריאטין, כוח, מסת שריר, התאוששות או pre/post workout stack."],
            "coaching_position": [
                "קריאטין monohydrate הוא אחד התוספים המבוססים יותר לביצועי כוח/עוצמה ואימונים חוזרים.",
                "זה כלי אופציונלי, לא חובה ולא תחליף לתוכנית, חלבון, שינה ועקביות.",
            ],
            "evidence_notes": [
                "הראיות חזקות בעיקר לפעילויות קצרות/עצימות, כוח, sprint חוזר והסתגלות לאימוני התנגדות.",
                "עלייה קלה במשקל יכולה להיות מים תוך-שריריים ולא בהכרח שומן.",
            ],
            "practical_notes": [
                "פרקטיקה נפוצה: 3-5 גרם ביום של creatine monohydrate.",
                "loading אינו חובה למשתמש כללי; עקביות יומית חשובה יותר מתזמון מושלם.",
            ],
            "caution_notes": [
                "במחלת כליות, תרופות רלוונטיות, הריון, קטינים או מצב רפואי לא ברור: להפנות לאיש מקצוע.",
                "ייתכנו אי נוחות בבטן או עלייה במשקל מים אצל חלק מהמשתמשים.",
            ],
            "avoid": ["לא להבטיח תוצאות שריר/כוח; לא להציג קריאטין כפתרון לפציעה או מצב רפואי."],
            "source_refs": ["ISSN Creatine Position Stand", "NIH ODS Exercise Supplements"],
        },
        "caffeine_preworkout": {
            "use_when": ["שאלה על קפה, קפאין, pre-workout, אנרגיה לפני אימון או ביצועים."],
            "coaching_position": [
                "קפאין יכול לשפר ביצועים אצל חלק מהאנשים, אבל התגובה אישית ותלויה בשינה, חרדה, סבילות ותזמון.",
                "pre-workout אינו קטגוריה אחת; צריך לבדוק רכיבים וכמות קפאין בפועל.",
            ],
            "evidence_notes": [
                "קפאין נחקר היטב בביצועי סבולת, כוח/סבולת שרירית ועירנות.",
                "מינון גבוה יותר אינו בהכרח טוב יותר ומעלה סיכון לתופעות לוואי.",
            ],
            "practical_notes": [
                "טווח מחקר נפוץ: 3-6 mg/kg כ-30-60 דקות לפני מאמץ, אך מתחילים נמוך יותר.",
                "אם זה פוגע בשינה, הביצוע לטווח ארוך עלול להיפגע למרות אימון אחד טוב.",
            ],
            "caution_notes": [
                "להיזהר עם לחץ דם, חרדה, הפרעות קצב, תרופות, הריון, קטינים או רגישות לקפאין.",
                "תופעות נפוצות: רעד, דופק, בחילה, עצבנות ושינה גרועה.",
            ],
            "avoid": [
                "לא להמליץ על scoops לא ידועים; לא לשלב כמה מקורות קפאין בלי לחשב כמות.",
                "להיזהר מ-proprietary blend/תערובת קניינית שבה אי אפשר לדעת מינון רכיבים.",
            ],
            "source_refs": ["ISSN Caffeine Position Stand", "NIH ODS Exercise Supplements"],
        },
        "protein_powder": {
            "use_when": ["שאלה על אבקת חלבון, whey, vegan protein, גיינר או השלמת חלבון."],
            "coaching_position": [
                "אבקת חלבון היא נוחות/convenience להשלים חלבון, לא מוצר חובה.",
                "קודם בודקים סך חלבון יומי, העדפות, סבילות, מחיר ואיכות תזונה כללית.",
            ],
            "evidence_notes": [
                "חלבון מספק תומך באימוני התנגדות ובהתאוששות; התוסף הוא דרך אחת להגיע ליעד.",
                "אין יתרון קסם לאבקה לעומת מזון אם סך החלבון והאיכות מתאימים.",
            ],
            "practical_notes": [
                "עוגן שימושי בארוחה: 20-40 גרם חלבון או כ-0.25 גרם לק״ג כשזה מתאים.",
                "בחר מוצר שמתאים לאלרגיות/כשרות/טבעונות/לקטוז אם המשתמש ציין זאת.",
            ],
            "caution_notes": [
                "במחלת כליות, תזונה רפואית או הפרעות אכילה: לא לתת תוכנית חלבון אישית.",
                "גיינרים יכולים להוסיף הרבה קלוריות בלי לשפר איכות תזונה.",
            ],
            "avoid": ["לא למכור אבקת חלבון כתנאי לבניית שריר; לא להחליף ארוחות שלמות בלי צורך."],
            "source_refs": ["ISSN Protein Position Stand", "Academy of Nutrition and Dietetics"],
        },
        "beta_alanine": {
            "use_when": ["שאלה על beta-alanine, עקצוץ, סבולת מאמץ או תוסף pre-workout."],
            "coaching_position": [
                "Beta-alanine עשוי לעזור בעיקר במאמצים עצימים של עשרות שניות עד כמה דקות.",
                "למשתמש כללי זה בדרך כלל פחות חשוב מקריאטין, קפאין, חלבון, שינה ותוכנית.",
            ],
            "evidence_notes": [
                "הראיות רלוונטיות יותר לביצועים עצימים חוזרים מאשר לבניית שריר כללית.",
                "עקצוץ/paresthesia הוא תופעה מוכרת ולא בהכרח מסוכנת, אבל יכול להפריע.",
            ],
            "practical_notes": [
                "אם משתמשים, מפצלים מינון לאורך היום כדי להפחית עקצוץ.",
                "טווח נפוץ במחקרים: 4-6 גרם ליום במשך 2-4 שבועות לפחות, לא כ-buzz מיידי.",
                "לא צריך להופיע בכל pre-workout כדי שהאימון יהיה טוב.",
            ],
            "caution_notes": ["רגישות אישית, אי נוחות ועקצוץ דורשים הורדת מינון או הימנעות."],
            "avoid": ["לא להציג beta-alanine כתוסף שריפת שומן או כוח מרבי."],
            "source_refs": ["ISSN Beta-Alanine Position Stand", "NIH ODS Exercise Supplements", "IOC Dietary Supplements Consensus"],
        },
        "electrolytes": {
            "use_when": ["שאלה על מלחים, איזוטוני, הזעה, אימון חם/ארוך או התכווצויות."],
            "coaching_position": [
                "אלקטרוליטים יכולים לעזור כאשר יש חום, הזעה גבוהה, אימון ארוך או כמה אימונים ביום.",
                "באימון קצר ורגיל, מים ותזונה יומית לרוב מספיקים למשתמש כללי.",
            ],
            "evidence_notes": [
                "צרכי נוזלים ומלחים משתנים לפי חום, משך, הזעה, גוף וסוג אימון.",
                "התכווצויות אינן תמיד רק מחסור במלח; עומס ועייפות גם רלוונטיים.",
            ],
            "practical_notes": [
                "בדוק צמא, משך אימון, חום, צבע שתן קיצוני, ירידה בביצוע וכמות הזעה.",
                "באימון ארוך/חם, שתייה עם נתרן ופחמימות יכולה להיות שימושית.",
            ],
            "caution_notes": ["לחץ דם, מחלות כליה/לב או הגבלת נתרן דורשים ייעוץ מקצועי."],
            "avoid": ["לא להמליץ על הרבה מלח כתיקון אוטומטי לכל עייפות או כיווץ."],
            "source_refs": ["NIH ODS Exercise Supplements", "ACSM Sports Nutrition Facts"],
        },
        "low_evidence_high_risk": {
            "use_when": ["שאלה על fat burners, testosterone boosters, detox, ממריצים, SARMs או מוצרי הבטחה מהירה."],
            "coaching_position": [
                "מוצרים עם הבטחות מהירות להרזיה, testosterone או שריפת שומן הם לרוב בעלי ראיות חלשות וסיכון גבוה יותר.",
                "המאמן צריך להחזיר את השיחה להרגלים, אימון, תזונה ושינה במקום לרדוף אחרי shortcut.",
            ],
            "evidence_notes": [
                "קטגוריות אלה נוטות לכלול תערובות לא שקופות, מינונים לא ברורים או רכיבים ממריצים.",
                "אישור שיווקי אינו הוכחה ליעילות או בטיחות.",
            ],
            "practical_notes": [
                "בדוק רשימת רכיבים, כמות קפאין/ממריצים, תרופות קיימות וסימני אזהרה.",
                "אם המוצר מבטיח ירידה מהירה או שינוי הורמונלי, התייחס אליו בחשדנות.",
            ],
            "caution_notes": [
                "מוצרים הורמונליים, SARMs, סטרואידים, ממריצים מסוכנים או שילובים לא ברורים אינם coaching רגיל.",
                "תסמינים כמו דופק חריג, כאב חזה או סחרחורת מחזירים לכללי safety.",
            ],
            "avoid": [
                "לא להמליץ על fat burners או testosterone boosters.",
                "לא לתת הוראות שימוש לחומרים הורמונליים/ממריצים מסוכנים.",
            ],
            "source_refs": ["NIH ODS Exercise Supplements", "IOC Dietary Supplements Consensus"],
        },
        "quality_and_scope": {
            "use_when": ["בכל שאלה שבה המשתמש שוקל קניית תוסף או מבקש המלצת מוצר."],
            "coaching_position": [
                "תוסף הוא כלי קטן בתוך תוכנית; לא אבחון, לא טיפול ולא הבטחת תוצאה.",
                "המלצה טובה מתחילה בשאלה: מה חסר בהרגלים או בתוכנית שהמשתמש מנסה לפתור?",
            ],
            "evidence_notes": [
                "איכות ובטיחות מוצרים משתנה; תווית לא תמיד מבטיחה תוכן מדויק.",
                "בדיקות צד שלישי מקטינות סיכון אך לא מוכיחות יעילות אישית.",
            ],
            "practical_notes": [
                "העדף מוצרים עם third-party tested/בדיקת צד שלישי כאשר תוסף באמת נדרש.",
                "שאל על תרופות, מצב רפואי, הריון/הנקה, גיל ותופעות לוואי לפני עצה פרקטית.",
            ],
            "caution_notes": [
                "קטינים, הריון, מחלות, תרופות או תופעות לוואי דורשים איש מקצוע מוסמך.",
                "בתחרות ספורטיבית יש לשקול סיכון זיהום ורכיבים אסורים.",
            ],
            "avoid": ["לא להמליץ על מותגים ספציפיים בלי יכולת בדיקה; לא להבטיח תוצאה מתוסף."],
            "source_refs": ["IOC Dietary Supplements Consensus", "NIH ODS Exercise Supplements"],
        },
    },
    "goal_playbooks": {
        "build_muscle": [
            "העדף נפח אימון עקבי וניתן להתאוששות.",
            "רוב העבודה: 1-3 חזרות ברזרבה, בלי לרדוף אחרי כשל בכל סט.",
        ],
        "improve_strength": [
            "התחל בתרגילים טכניים כשהמשתמש רענן: 4-6 חזרות ומנוחה ארוכה כשמתאים.",
            "שמור נפח מתון וטכניקה יציבה; אל תוסיף עומס בכל מחיר.",
        ],
        "lose_fat": [
            "שלב כוח לשימור שריר, הליכה/אירובי נגיש ותיעוד ארוחות בטווחים.",
            "אל תעודד דיאטת קיצון, צום כפוי או שריפת קלוריות כענישה.",
        ],
        "improve_endurance": [
            "בנה בסיס הדרגתי: רוב העבודה קלה-בינונית, מעט עצימה רק אחרי עקביות.",
            "מדוד משך, תחושת מאמץ, דופק אם זמין והתאוששות.",
        ],
        "improve_consistency": [
            "בחר מינימום ביצוע שבועי שאפשר לעמוד בו גם בשבוע עמוס.",
            "השתמש באימון קצר, הליכה או סטים ביתיים כדי לשמור רצף במקום לשבור שגרה.",
        ],
        "maintain_health": [
            "שמור שילוב של אירובי, כוח, ניידות ושיווי משקל לפי גיל ויכולת.",
            "המטרה היא תפקוד, אנרגיה, שינה ויכולת להתמיד, לא מקסימום עומס.",
        ],
    },
    "goal_specific_programming": {
        "beginner_foundation": {
            "goal": "בסיס טכניקה, שליטה ועקביות לפני העמסת נפח או משקל.",
            "set_range": ["1-3 סטים לתרגיל בתחילת הדרך", "2-4 סטים כשהטכניקה וההתאוששות יציבות"],
            "rep_range": ["12-20 חזרות לעבודת ייצוב/שליטה", "8-12 או 10-15 חזרות לתרגילי בסיס פשוטים"],
            "rest_guidance": ["60-120 שניות לפי נשימה, טכניקה ומאמץ"],
            "intensity_guidance": ["RPE 5-7", "השאר 2-4 חזרות ברזרבה ברוב הסטים"],
            "programming_notes": [
                "תעדף לימוד תנועה, טווח ללא כאב והרגל שבועי לפני וריאציות מורכבות.",
                "העלה רק משתנה אחד בכל פעם: חזרות, סטים, עומס, תדירות או מורכבות.",
            ],
        },
        "strength": {
            "goal": "שיפור כוח מרבי או כוח בתרגילים מרכזיים.",
            "set_range": ["3-6 סטים לתרגיל מרכזי כאשר המשתמש מוכן לכך"],
            "rep_range": ["1-5 חזרות לסט בתרגיל מרכזי", "4-6 חזרות כטווח שמרני יותר לרוב המשתמשים"],
            "rest_guidance": ["2-5 דקות בתרגילים כבדים", "90-180 שניות בתרגילי עזר"],
            "intensity_guidance": ["עומס גבוה רק עם טכניקה יציבה", "עצור לפני כשל טכני או כאב"],
            "programming_notes": [
                "מקם תרגילי כוח מוקדם באימון אחרי חימום ספציפי.",
                "שמור נפח מתון כדי שהמשתמש יוכל להתאושש ולהתקדם לאורך שבועות.",
            ],
        },
        "hypertrophy": {
            "goal": "בניית מסת שריר דרך נפח איכותי והתאוששות מספקת.",
            "set_range": ["3-6 סטים לתרגיל או קבוצת שריר לפי רמה והתאוששות"],
            "rep_range": ["6-12 חזרות כטווח מרכזי", "8-15 חזרות כשצריך שליטה טובה יותר או ציוד קל"],
            "rest_guidance": ["60-120 שניות ברוב תרגילי העזר", "90-180 שניות בתרגילים מורכבים"],
            "intensity_guidance": ["לרוב 1-3 חזרות ברזרבה", "לא לרדוף אחרי כשל בכל סט"],
            "programming_notes": [
                "נפח טוב הוא נפח שניתן לבצע שוב בשבוע הבא בלי ירידה חדה בביצועים.",
                "התקדמות יכולה להיות חזרות, סט נוסף, עומס קטן או טכניקה נקייה יותר.",
            ],
        },
        "muscular_endurance": {
            "goal": "סבולת שרירית, שליטה בתנועה ויכולת לבצע עבודה ממושכת יותר.",
            "set_range": ["2-4 סטים לתרגיל"],
            "rep_range": ["12-20 חזרות לסט", "20-60 שניות בתרגילי זמן כאשר זה מתאים"],
            "rest_guidance": ["30-90 שניות לפי איכות התנועה ונשימה"],
            "intensity_guidance": ["עומס קל עד בינוני", "עצימות שמאפשרת טכניקה יציבה לאורך כל הסט"],
            "programming_notes": [
                "שמור איכות תנועה; סבולת לא מצדיקה חזרות מרושלות.",
                "מתאים כבסיס, חזרה אחרי הפסקה, או תמיכה במטרות בריאות ותפקוד.",
            ],
        },
        "power": {
            "goal": "כוח מתפרץ ומהירות תנועה כאשר יש בסיס כוח וטכניקה.",
            "set_range": ["2-5 סטים איכותיים"],
            "rep_range": ["1-5 חזרות בתרגילי כוח מתפרץ", "8-10 חזרות בתרגיל נפיץ קל במסגרת contrast/OPT"],
            "rest_guidance": ["מנוחה מלאה יחסית, לרוב 2-3 דקות או עד שהאיכות חוזרת"],
            "intensity_guidance": ["תנועה מהירה ואיכותית", "עצור כשמהירות או טכניקה יורדות"],
            "programming_notes": [
                "מקם כוח מתפרץ מוקדם באימון ולא בסוף עייף.",
                "בחר וריאציות בטוחות ופשוטות; לא צריך תרגילים אולימפיים למשתמש כללי.",
            ],
        },
        "fat_loss_support": {
            "goal": "תמיכה בירידה בשומן תוך שמירה על כוח, שריר ועקביות.",
            "set_range": ["2-4 סטים לתרגיל כוח מרכזי", "נפח מינימלי יעיל בתקופות עומס או גרעון"],
            "rep_range": ["6-12 חזרות לתרגילי כוח/שריר", "10-20 חזרות לתרגילי עזר או סבולת"],
            "rest_guidance": ["60-120 שניות לפי ביצוע", "לא לקצר מנוחה אם זה מפרק טכניקה"],
            "intensity_guidance": ["שמור 1-4 חזרות ברזרבה", "אל תהפוך כל אימון לעונש קלורי"],
            "programming_notes": [
                "שמור כוח כעוגן, והוסף צעדים או אירובי נגיש בהדרגה.",
                "ירידה בשומן נשענת על הרגלים ותזונה בטוחה, לא על דיאטת קיצון.",
            ],
        },
    },
    "scenario_adjustments": {
        "missed_workout": [
            "אל תכפיל עומס באימון הבא.",
            "חזור לתוכנית המקורית או בצע גרסה קצרה של 20-30 דקות.",
        ],
        "short_time": [
            "בחר 3-4 תרגילי בסיס: סקוואט/hinge, דחיפה, משיכה וליבה.",
            "קצר מנוחות או סטים, אבל אל תדלג על חימום קצר ובטיחות.",
        ],
        "low_sleep": [
            "הורד עצימות או נפח ב-20-40 אחוז והעדף טכניקה/הליכה/ניידות.",
            "אל תנסה לשבור שיא ביום של שינה ירודה.",
        ],
        "no_equipment": [
            "השתמש במשקל גוף, תיק, מגבת, מדרגה, גומיות או וריאציות איטיות.",
            "שמור על דפוסי תנועה במקום להתעקש על תרגיל מסוים.",
        ],
        "pain_flag": [
            "עצור תנועה כואבת, עבור לטווח ללא כאב או תרגיל חלופי.",
            "כאב חד, מחמיר או עם סימנים מסוכנים דורש הפניה לאיש מקצוע מוסמך.",
        ],
    },
    "exercise_selection_rules": [
        {
            "pattern": "squat",
            "examples": ["סקוואט משקל גוף", "סקוואט גביע", "לחיצת רגליים"],
            "regressions": ["סקוואט לקופסה", "ישיבה-קימה מכיסא", "טווח תנועה חלקי"],
            "progressions": ["סקוואט גביע", "סקוואט מפוצל", "האטת שלב הירידה"],
            "safety": ["הימנע מכאב חד בברך או גב", "בחר טווח תנועה שנשלט היטב"],
        },
        {
            "pattern": "hinge",
            "examples": ["היפ הינג'", "דדליפט רומני", "גשר ישבן"],
            "regressions": ["תרגול היפ הינג' לקיר", "גשר ישבן", "טווח קצר"],
            "progressions": ["דדליפט רומני עם משקולות", "רגל אחת בתמיכה"],
            "safety": ["שמור עמוד שדרה ניטרלי", "עצור בכאב חד בגב"],
        },
        {
            "pattern": "push_pull_core",
            "examples": ["שכיבת סמיכה", "לחיצת רצפה", "חתירה", "פלאנק"],
            "regressions": ["שכיבת סמיכה בשיפוע", "חתירה קלה", "פלאנק ברכיים"],
            "progressions": ["טווח מלא", "קצב איטי", "עומס נוסף"],
            "safety": ["כתפיים נוחות", "נשימה רגועה ושליטה"],
        },
    ],
    "anatomy_muscle_map": {
        "lower_body": {
            "muscle_groups": [
                "ארבע ראשי/quadriceps: פשיטת ברך ודומיננטי בסקוואט, step-up ולחיצת רגליים.",
                "גלוטס: פשיטת ירך, ייצוב אגן וכוח ב-hip hinge, bridge, thrust ולאנג׳.",
                "המסטרינג/hamstrings: פשיטת ירך וכפיפת ברך, חשובים ב-hinge וב-RDL.",
                "שוק/calf: plantar flexion, הליכה, ריצה, קפיצה ו-calf raise.",
            ],
            "movement_patterns": ["squat", "hinge", "lunge/step-up", "carry", "calf raise"],
            "coach_uses": [
                "בחר תרגיל לפי דפוס ומטרה: quad bias, glute/hamstring bias או יציבות חד-צדדית.",
                "אם ציוד חסר, שמור את הדפוס והשריר המרכזי במקום להיצמד לתרגיל ספציפי.",
            ],
            "balance_rules": [
                "שלב knee-dominant ו-hip-dominant לאורך השבוע כדי לא לאמן רק צד אחד של הרגל.",
                "מתחילים לא צריכים לבודד כל שריר; compound movements מכסים הרבה מהבסיס.",
            ],
            "avoid": ["לא להסיק ששריר 'חלש' רק מתמונה או כאב; כאב מחזיר לכללי safety."],
            "source_refs": ["ACSM Major Muscle Groups", "NSCA Exercise Technique Manual", "ACE Exercise Library"],
        },
        "upper_push": {
            "muscle_groups": [
                "חזה/pectorals + כתף קדמית + טרייספס הם בסיס דחיפה אופקית.",
                "דלתא/כתפיים + טרייספס מובילים דחיפה אנכית, עם ליבה כמייצבת.",
            ],
            "movement_patterns": ["horizontal push", "vertical push", "push-up", "press"],
            "coach_uses": [
                "בחר זווית דחיפה לפי כתף, ציוד ומטרה: שיפוע, רצפה, מכונה או מעל הראש.",
                "כאשר הכתף רגישה, שנה זווית/טווח/אחיזה לפני הוספת עוד cues.",
            ],
            "balance_rules": [
                "איזן דחיפה עם משיכה כדי לשמור נפח כתף/שכמה סביר.",
                "טרייספס מקבל הרבה עבודה מלחיצות; בידוד נוסף צריך להתאים לנפח הכולל.",
            ],
            "avoid": ["לא להוסיף overhead pressing אם המשתמש מאבד צלעות/גב או מדווח כאב כתף חד."],
            "source_refs": ["ACE Essentials of Exercise Science", "ACE Exercise Library", "NASM Exercise Library"],
        },
        "upper_pull": {
            "muscle_groups": [
                "גב/רחב גבי, שכמות/רומבואידים/טרפז ובייספס הם בסיס משיכה.",
                "משיכה אופקית מדגישה שכמות וגב אמצעי; משיכה אנכית מדגישה רחב גבי וזרוע.",
            ],
            "movement_patterns": ["horizontal pull", "vertical pull", "row", "pulldown/pull-up"],
            "coach_uses": [
                "השתמש במשיכה כדי לאזן נפח דחיפה ולשפר שליטה בשכמות.",
                "בחר מכונה/גומייה/חתירה נתמכת כאשר גב תחתון או טכניקה מגבילים.",
            ],
            "balance_rules": [
                "push/pull מאוזן הוא כלל פשוט למשתמש כללי, במיוחד כשיש הרבה עבודה מול מחשב.",
                "בייספס מקבל עבודה במשיכות; בידוד נדרש בעיקר לפי מטרה, העדפה או פער נפח.",
            ],
            "avoid": ["לא לפתור כאב כתף או צוואר בהוספת עוד volume בלי התאמת תרגיל."],
            "source_refs": ["ACE Essentials of Exercise Science", "NASM Exercise Library", "NSCA Exercise Technique Manual"],
        },
        "core_trunk": {
            "muscle_groups": [
                "ליבה כוללת ישר בטני, אלכסונים, רחב בטני, זוקפי גב ומייצבי אגן/כתף.",
                "core training למשתמש כללי הוא שליטה בתנועה: anti-extension, anti-rotation, carry ונשימה.",
            ],
            "movement_patterns": ["brace", "anti-extension", "anti-rotation", "carry", "rotation when appropriate"],
            "coach_uses": [
                "בחר ליבה לפי תפקיד באימון: יציבה בסקוואט/hinge, נשיאה, או שליטה באגן/צלעות.",
                "קצר סט כאשר הטכניקה מתפרקת; זמן ארוך עם גב קורס אינו התקדמות.",
            ],
            "balance_rules": [
                "שלב יציבות קדמית, צדית וסיבובית במקום עוד כפיפות בטן בלבד.",
                "נשימה ו-brace פשוטים עדיפים מהסבר מורכב למתחיל.",
            ],
            "avoid": ["לא לטעון שתרגיל ליבה 'מתקן' כאב גב; כאב גב נשאר non-diagnostic."],
            "source_refs": ["NASM Exercise Library", "NSCA Exercise Technique Manual"],
        },
        "arms_shoulders_accessory": {
            "muscle_groups": [
                "בייספס מסייע במשיכות ומקבל בידוד דרך curl variations.",
                "טרייספס מסייע בדחיפות ומקבל בידוד דרך extension/pressdown variations.",
                "כתף צדית/אחורית ו-rotator cuff יכולים לתמוך בנפח כתף ושכמות כשזה רלוונטי.",
            ],
            "movement_patterns": ["curl", "triceps extension", "lateral raise", "rear-delt/rotator cuff support"],
            "coach_uses": [
                "הוסף accessories אחרי compound work או כאשר המטרה אסתטית/ספציפית.",
                "בחר מעט סטים איכותיים ולא רשימת בידודים ארוכה למתחיל.",
            ],
            "balance_rules": [
                "זרועות לא מחליפות דחיפה/משיכה בסיסית.",
                "כתף אחורית ו-rotator cuff הם תמיכה, לא רישיון להתעלם מכאב כתף.",
            ],
            "avoid": ["לא לבנות תוכנית סביב בידודים לפני שיש בסיס כוח ותנועה."],
            "source_refs": ["ACE Exercise Library - Expanded Patterns", "NASM Exercise Library - Expanded Patterns"],
        },
        "program_balance": {
            "muscle_groups": ["כל קבוצות השריר המרכזיות: רגליים, ירך, דחיפה, משיכה, ליבה, נשיאה/שיווי לפי צורך."],
            "movement_patterns": ["squat", "hinge", "push", "pull", "lunge/step", "core", "carry"],
            "coach_uses": [
                "בדוק שהשבוע מכסה דפוסים מרכזיים לפני הוספת תרגילים קטנים.",
                "למשתמש כללי, full-body או upper/lower פשוטים לרוב עדיפים מפיצול שרירים מורכב מוקדם מדי.",
            ],
            "balance_rules": [
                "איזון אנטגוניסטי פשוט: push/pull, knee/hip dominant, ימין/שמאל, ליבה קדמית/צדית.",
                "נפח שבועי צריך להתאים להתאוששות וללוגים, לא לרשימת שרירים תאורטית.",
            ],
            "avoid": ["לא לרדוף אחרי 'פגיעה בכל שריר' אם זה פוגע בעקביות או התאוששות."],
            "source_refs": ["ACSM Major Muscle Groups", "Movement Pattern Definitions Review", "NSCA Resistance Training Frequency"],
        },
    },
    "exercise_library": {
        "squat": {
            "pattern": "כריעה/סקוואט",
            "primary_muscles": ["ארבע ראשי", "גלוטס", "המסטרינג כמסייע", "ליבה מייצבת"],
            "coaching_cues": [
                "כפות רגליים מלאות על הקרקע.",
                "ברכיים עוקבות אחרי כיוון כף הרגל.",
                "חזה וגב יציבים בלי לרדוף אחרי עומק על חשבון שליטה.",
            ],
            "common_errors": [
                "ברכיים קורסות פנימה.",
                "עקבים מתנתקים בגלל עומק או טווח לא מתאים.",
                "גב מתעגל או חזה קורס תחת עומס.",
            ],
            "regressions": ["ישיבה-קימה מכיסא", "סקוואט לקופסה", "סקוואט משקל גוף לטווח חלקי"],
            "progressions": ["סקוואט גביע", "סקוואט מפוצל", "סקוואט עם עצירה", "סקוואט עם משקל חיצוני"],
            "safety_notes": [
                "בחר עומק לפי שליטה, מבנה גוף וטווח ללא כאב חד.",
                "הורד עומס או טווח אם הברך, הירך או הגב מגיבים בכאב חד.",
            ],
        },
        "hip_hinge": {
            "pattern": "הינג׳/כפיפה מהירך",
            "primary_muscles": ["גלוטס", "המסטרינג", "זוקפי גב כמייצבים", "רחב גבי כמייצב עומס"],
            "coaching_cues": [
                "דחוף ירכיים לאחור לפני שהברכיים מתכופפות הרבה.",
                "שמור עמוד שדרה ניטרלי ועומס קרוב לגוף.",
                "חזור לעמידה דרך דחיפת ירכיים קדימה ולא משיכה מהגב.",
            ],
            "common_errors": [
                "כיפוף גב או אובדן עמוד שדרה ניטרלי.",
                "כיפוף ברכיים גדול מדי שהופך את התנועה לסקוואט.",
                "עומס רחוק מהגוף או תנועה עם תנופה.",
            ],
            "regressions": ["תרגול היפ הינג׳ לקיר", "גשר ישבן", "דדליפט קטלבל מגובה"],
            "progressions": ["דדליפט רומני עם משקולות", "דדליפט קטלבל מהרצפה", "הינג׳ רגל אחת בתמיכה"],
            "safety_notes": [
                "הפסק אם יש כאב גב חד או הקרנה.",
                "עדיף טווח קצר ונקי על עומס כבד עם גב מתעגל.",
            ],
        },
        "horizontal_push": {
            "pattern": "דחיפה אופקית",
            "primary_muscles": ["חזה", "טרייספס", "כתף קדמית", "ליבה מייצבת"],
            "coaching_cues": [
                "שמור קו ישר מראש עד עקבים או ברכיים לפי הווריאציה.",
                "מרפקים במסלול נוח ולא פתוחים מדי לצדדים.",
                "כתפיים רחוקות מהאוזניים וקצב נשלט.",
            ],
            "common_errors": [
                "אגן שוקע וחוסר שליטה בליבה.",
                "מרפקים נפתחים מדי ומעמיסים על הכתף.",
                "טווח או עומס גדולים מדי לפני שליטה.",
            ],
            "regressions": ["שכיבת סמיכה על קיר", "שכיבת סמיכה בשיפוע", "שכיבת סמיכה ברכיים", "לחיצת רצפה"],
            "progressions": ["שכיבת סמיכה מלאה", "שכיבת סמיכה בירידה איטית", "שכיבת סמיכה עם רגל מוגבהת", "לחיצת חזה עם משקולות"],
            "safety_notes": [
                "הקטן טווח או שנה זווית אם יש כאב כתף חד.",
                "התקדם משיפוע נמוך יותר רק כשהקו נשמר לאורך כל הסט.",
            ],
        },
        "horizontal_pull": {
            "pattern": "משיכה אופקית",
            "primary_muscles": ["רחב גבי", "שכמות/רומבואידים", "טרפז אמצעי", "בייספס"],
            "coaching_cues": [
                "התחל משכמות ואז משוך עם מרפקים לאחור.",
                "שמור חזה פתוח וצוואר רגוע.",
                "חזור קדימה בשליטה בלי לאבד יציבה.",
            ],
            "common_errors": [
                "משיכה עם תנופה במקום גב ושכמות.",
                "כתפיים עולות לאוזניים.",
                "משיכת יתר עם גב מתעגל או טווח שלא נשלט.",
            ],
            "regressions": ["חתירה עם גומייה", "חתירה במכונה", "חתירה בשיפוע קל"],
            "progressions": ["חתירת משקולת יד", "TRX row", "חתירה כבדה יותר עם עצירה בקצה"],
            "safety_notes": [
                "בחר אחיזה וזווית שלא מייצרות כאב כתף קדמי.",
                "הורד עומס אם המשתמש לא מצליח לשמור שכמות בשליטה.",
            ],
        },
        "lunge": {
            "pattern": "צעד/לאנג׳ חד-צדדי",
            "primary_muscles": ["ארבע ראשי", "גלוטס", "המסטרינג", "מייצבי ירך וברך"],
            "coaching_cues": [
                "צעד באורך שמאפשר שליטה ושיווי משקל.",
                "ברך קדמית עוקבת אחרי כף הרגל.",
                "דחוף את הרצפה וחזור בלי לקרוס לצדדים.",
            ],
            "common_errors": [
                "ברך קורסת פנימה.",
                "צעד קצר או ארוך מדי שמפרק שליטה.",
                "דחיפה מהגב התחתון במקום מהרגליים.",
            ],
            "regressions": ["לאנג׳ אחורי קצר", "סקוואט מפוצל עם תמיכה", "step-up נמוך"],
            "progressions": ["לאנג׳ אחורי מלא", "סקוואט מפוצל", "לאנג׳ הליכה", "לאנג׳ עם משקולות"],
            "safety_notes": [
                "השתמש בתמיכה אם שיווי המשקל מגביל את הטכניקה.",
                "העדף צעד אחורי או step-up אם לאנג׳ קדמי מציק לברך.",
            ],
        },
        "core_anti_extension": {
            "pattern": "ליבה אנטי-אקסטנשן",
            "primary_muscles": ["רחב בטני", "ישר בטני", "אלכסונים", "מייצבי כתף ואגן"],
            "coaching_cues": [
                "שמור קו ישר ואל תיתן לגב התחתון לקרוס.",
                "צלעות ואגן בשליטה עם נשימה רציפה.",
                "אנטי-תנועה איכותי עדיף על החזקת זמן ארוך.",
            ],
            "common_errors": [
                "אגן שוקע או עולה גבוה מדי.",
                "עצירת נשימה.",
                "הארכת סט אחרי שהקו הישר נשבר.",
            ],
            "regressions": ["פלאנק על ברכיים", "פלאנק על שיפוע", "dead bug"],
            "progressions": ["פלאנק מלא", "פלאנק עם נגיעה בכתף", "body saw קצר", "ab rollout רק למתקדמים עם שליטה"],
            "safety_notes": [
                "עצור אם מופיע כאב גב חד או לחץ לא רגיל.",
                "קצר משך לפני שמעלה קושי אם הטכניקה מתפרקת.",
            ],
        },
        "loaded_carry": {
            "pattern": "נשיאה/יציבה תחת עומס",
            "primary_muscles": ["אמות ואחיזה", "טרפז", "ליבה", "גלוטס ומייצבי ירך"],
            "coaching_cues": [
                "עמוד גבוה עם צלעות ואגן בשליטה.",
                "כתפיים רחוקות מהאוזניים ואחיזה יציבה.",
                "צעדים קצרים ונשימה רציפה.",
            ],
            "common_errors": [
                "הטיית גוף לצד אחד תחת עומס.",
                "כתפיים מכווצות או גב מתעגל.",
                "עומס כבד מדי שמפרק הליכה ושליטה.",
            ],
            "regressions": ["נשיאה במקום", "farmer carry קל", "suitcase carry קצר עם משקל קל"],
            "progressions": ["farmer carry כבד יותר", "suitcase carry חד-צדדי", "נשיאה ארוכה יותר", "נשיאת מדרגות רק אם בטוח"],
            "safety_notes": [
                "התחל קל כאשר אחיזה או גב מגבילים.",
                "בחר מרחק קצר ובר שליטה לפני משקל כבד.",
            ],
        },
        "vertical_push": {
            "pattern": "דחיפה אנכית",
            "primary_muscles": ["כתפיים/דלתא", "טרייספס", "טרפז עליון כמסייע", "ליבה מייצבת"],
            "coaching_cues": [
                "צלעות למטה וליבה פעילה.",
                "לחץ מעל הראש בטווח כתף נוח בלי הקשתת גב.",
                "מרפקים ופרקי כף יד במסלול יציב.",
            ],
            "common_errors": [
                "הקשתת גב כדי לסיים חזרה.",
                "כתפיים עולות לאוזניים בלי שליטה.",
                "לחיצה מעבר לטווח כתף נוח.",
            ],
            "regressions": ["לחיצת כתפיים בישיבה", "לחיצה בזווית שיפוע", "landmine press או לחיצה חצי-כריעה"],
            "progressions": ["לחיצת כתפיים בעמידה", "לחיצה חד-צדדית", "לחיצת משקולות מעל הראש"],
            "safety_notes": [
                "הקטן טווח או שנה זווית בכאב כתף חד.",
                "אל תוסיף עומס אם הגב מתקשת או הצלעות בורחות.",
            ],
        },
        "vertical_pull": {
            "pattern": "משיכה אנכית",
            "primary_muscles": ["רחב גבי/לטיסימוס", "בייספס", "שכמות/טרפז תחתון", "ליבה מייצבת"],
            "coaching_cues": [
                "התחל מהורדת שכמות קלה.",
                "משוך מרפקים מטה ולצדדים בלי לזרוק צוואר קדימה.",
                "שמור צלעות ואגן בשליטה.",
            ],
            "common_errors": [
                "משיכה מאחורי הראש.",
                "תנופה או גב מתנדנד.",
                "כתפיים לאוזניים.",
            ],
            "regressions": ["פול-דאון עם גומייה", "lat pulldown קל", "תלייה אקטיבית קצרה"],
            "progressions": ["פול-דאון כבד יותר", "מתח עם עזרה", "שלילי במתח", "מתח מלא"],
            "safety_notes": [
                "בחר אחיזה שלא מכאיבה לכתף.",
                "אל תכפה מתח מלא לפני שיש שליטה בשכמות.",
            ],
        },
        "glute_bridge_hip_thrust": {
            "pattern": "פשיטת ירך/גשר גלוטס",
            "primary_muscles": ["גלוטס", "המסטרינג", "זוקפי גב כמייצבים", "ליבה"],
            "coaching_cues": [
                "דחוף דרך כפות הרגליים וסחט גלוטס למעלה.",
                "שמור צלעות ואגן בשליטה בלי הקשתת גב.",
                "קו ברכיים-ירכיים-כתפיים בסוף התנועה.",
            ],
            "common_errors": [
                "דחיפה מהגב התחתון.",
                "כפות רגליים רחוקות מדי.",
                "ברכיים קורסות פנימה.",
            ],
            "regressions": ["גשר גלוטס על הרצפה", "החזקת גשר קצרה", "גשר עם טווח חלקי"],
            "progressions": ["hip thrust על ספסל", "גשר חד-רגלי", "hip thrust עם משקל"],
            "safety_notes": [
                "עצור בכאב גב חד.",
                "הורד עומס אם המשתמש לא מרגיש שליטה בגלוטס.",
            ],
        },
        "step_up": {
            "pattern": "עלייה למדרגה/step-up",
            "primary_muscles": ["ארבע ראשי", "גלוטס", "מייצבי ירך וברך", "ליבה"],
            "coaching_cues": [
                "כל כף הרגל על המדרגה.",
                "ברך עוקבת אחרי כף הרגל.",
                "דחוף דרך הרגל שעל המדרגה בלי לקפוץ מהרגל האחורית.",
            ],
            "common_errors": [
                "מדרגה גבוהה מדי.",
                "ברך קורסת פנימה.",
                "דחיפה מהרגל התחתונה במקום מהרגל העליונה.",
            ],
            "regressions": ["מדרגה נמוכה", "step-up עם תמיכה", "ישיבה-קימה מכיסא"],
            "progressions": ["step-up גבוה יותר", "step-up עם משקולות", "step-up to balance"],
            "safety_notes": [
                "בחר גובה שמאפשר שליטה.",
                "השתמש בתמיכה אם שיווי משקל מגביל.",
            ],
        },
        "calf_raise": {
            "pattern": "כפיפה כפית/הרמת עקבים",
            "primary_muscles": ["תאומים/גסטרוקנמיוס", "סולאוס", "מייצבי קרסול ושוק"],
            "coaching_cues": [
                "עלה דרך כריות כף הרגל.",
                "עצור רגע למעלה ורד בשליטה.",
                "שמור ברכיים וכפות רגליים במסלול נוח.",
            ],
            "common_errors": [
                "קפיצה או תנופה.",
                "קריסה החוצה או פנימה בקרסול.",
                "טווח קצר מדי בלי שליטה.",
            ],
            "regressions": ["הרמת עקבים עם קיר", "שתי רגליים", "טווח חלקי"],
            "progressions": ["רגל אחת", "משקל חיצוני", "עצירה איטית בתחתית ובפסגה"],
            "safety_notes": [
                "השתמש בתמיכה לשיווי משקל.",
                "הורד עומס בכאב חד באכילס או בקרסול.",
            ],
        },
        "arm_accessory": {
            "pattern": "אביזרי זרועות",
            "primary_muscles": ["בייספס", "טרייספס", "ברכיאליס/אמה", "כתף כמייצבת"],
            "coaching_cues": [
                "מרפקים יציבים, תנועה נשלטת.",
                "שמור שורש כף יד ניטרלי ונשימה רגועה.",
                "בחר עומס שמאפשר טווח מלא בלי תנופה.",
            ],
            "common_errors": [
                "נדנוד גוף.",
                "מרפקים נודדים כדי להרים עומס.",
                "כיפוף שורש כף יד תחת עומס.",
            ],
            "regressions": ["גומייה קלה", "כבל קל", "טווח חלקי ללא כאב"],
            "progressions": ["משקולת כבדה יותר", "קצב איטי", "וריאציות curl/pushdown/extension"],
            "safety_notes": [
                "אביזרים לא מחליפים דפוסי דחיפה/משיכה מרכזיים.",
                "הפחת עומס בכאב מרפק או שורש כף יד.",
            ],
        },
    },
    "technique_cues": {
        "squat": {
            "setup": ["עמידה יציבה לפי נוחות ירך וברך", "כפות רגליים מלאות על הקרקע", "מתח קל בליבה לפני הירידה"],
            "execution": ["ברכיים עוקבות אחרי כיוון כף הרגל", "ירידה לטווח נשלט ללא כאב חד", "עלייה דרך כל כף הרגל ולא רק דרך הבהונות"],
            "common_errors": ["ברכיים קורסות פנימה", "עקב מתנתק בלי שליטה", "רדיפה אחרי עומק על חשבון כאב או גב"],
            "coach_response": ["הקטן טווח, עבור לסקוואט לקופסה, או בחר וריאציה יציבה יותר לפני עומס נוסף"],
        },
        "hinge": {
            "setup": ["רגליים יציבות", "גב ניטרלי", "עומס קרוב לגוף כאשר יש משקל חיצוני"],
            "execution": ["התנועה מתחילה מהירך/אגן לאחור", "ברכיים רכות ולא נעולות", "חזור לעמידה בלי למשוך מהגב התחתון"],
            "common_errors": ["כיפוף גב במקום תנועת ירך", "עומס רחוק מדי מהגוף", "טווח עמוק מדי לפני שליטה"],
            "coach_response": ["תרגל היפ הינג' לקיר, גשר ישבן או טווח קצר לפני דדליפט כבד יותר"],
        },
        "push": {
            "setup": ["כתפיים נוחות ולא מורמות לאוזניים", "שכמות בשליטה", "מפרקי כף יד נוחים ככל האפשר"],
            "execution": ["קצב נשלט", "מרפקים במסלול נוח", "עצור לפני כאב חד בכתף או בפרק כף היד"],
            "common_errors": ["כתפיים נמשכות קדימה בכאב", "גב קורס בשכיבת סמיכה", "טווח גדול מדי בלי שליטה"],
            "coach_response": ["בחר שיפוע גבוה יותר, לחיצת רצפה או טווח חלקי עד שהכתף רגועה"],
        },
        "pull": {
            "setup": ["עמוד שדרה יציב", "שכמות מתחילות בשליטה", "אחיזה שמאפשרת מרפקים נוחים"],
            "execution": ["משוך עם גב וזרוע יחד", "עצור רגע בקצה התנועה", "שמור צוואר רגוע"],
            "common_errors": ["משיכה עם תנופה במקום שליטה", "כתפיים עולות לאוזניים", "טווח שמייצר כאב קדמי בכתף"],
            "coach_response": ["הקטן עומס, האט קצב, או עבור לגומייה/מכונה יציבה יותר"],
        },
        "core": {
            "setup": ["צלעות ואגן בשליטה", "נשימה רציפה", "עמדה שאינה מייצרת כאב גב חד"],
            "execution": ["שמור מתח מספיק כדי לשלוט בתנועה", "הפסק לפני איבוד מנח", "העדף איכות על זמן ארוך"],
            "common_errors": ["עצירת נשימה ארוכה", "גב תחתון קורס", "החזקת פלאנק אחרי שהטכניקה התפרקה"],
            "coach_response": ["קצר זמן, עבור לברכיים/דד באג, או בחר תרגיל אנטי-תנועה קל יותר"],
        },
    },
    "preparticipation_screening": {
        "readiness_questions": [
            "האם יש מצב רפואי, אבחון קודם, הריון, פציעה משמעותית או מגבלה שלא הוזכרה?",
            "האם יש תרופות, לחץ דם, סוכרת, בעיית לב/כליות/ריאות או הוראות רופא שמשנות פעילות?",
            "מה רמת הפעילות הנוכחית ומה המשתמש כבר עושה בלי סימפטומים?",
        ],
        "red_flags": [
            "כאב בחזה, לחץ בחזה, כאב בצוואר/לסת/זרוע בזמן פעילות",
            "קוצר נשימה חריג, סחרחורת, עילפון, blackout או דפיקות לב חריגות",
            "כאב חד, נפיחות משמעותית, חולשה פתאומית או החמרה מתמשכת אחרי אימון",
        ],
        "decision": [
            "אם יש red flag: עצור המלצת אימון והפנה לאיש מקצוע רפואי מוסמך.",
            "אם יש מצב כרוני בלי red flags: תמיכה שמרנית, עצימות מתונה ושאלה על אישור/הנחיות מקצועיות.",
            "אם אין סימני סיכון: התחל בהדרגה ובנה לפי FITT, לוגים והתאוששות.",
        ],
    },
    "referral_rules": [
        "עצור והפנה לאיש מקצוע רפואי מוסמך בסימנים מסוכנים או כאב חד/מחמיר.",
        "הפנה לדיאטן קליני בבקשות לתפריט רפואי, הפרעות אכילה, ירידה קיצונית במשקל או מחלות רלוונטיות.",
        "הפנה לפיזיותרפיסט/רופא בפציעה חוזרת, כאב שמגביל תפקוד או חזרה אחרי ניתוח/טראומה.",
    ],
    "safety_boundaries": [
        "כאב בחזה, עילפון, סחרחורת חריגה, קוצר נשימה חריג או כאב חד דורשים עצירת אימון והפניה לאיש מקצוע רפואי מוסמך.",
        "אין לתת אבחון רפואי, טיפול בפציעה, הנחיות להפרעות אכילה, דיאטות קיצוניות, סטרואידים, ממריצים או חומרים מסוכנים.",
        "במחלות כרוניות, הריון, אחרי פציעה משמעותית או אצל קטינים, יש לתת תמיכה שמרנית ולהפנות להתייעצות מקצועית מתאימה.",
        "כאשר חסר מידע קריטי, שאל שאלת המשך אחת או בחר פעולה קצרה ובטוחה במקום להמציא פרטים.",
    ],
    "coaching_behavior": [
        "התחל מהדבר הבא הכי קטן ובר ביצוע.",
        "התאם אימון שהוחמץ במקום להעניש: קצר, הזז או הורד נפח.",
        "תן סיבה קצרה, פעולה אחת, ורק שאלה אחת אם חסר מידע.",
        "שמור על עברית בלבד למשתמש, למעט שמות תרגילים או מוצרים שאין להם תרגום טבעי.",
    ],
    "sources": [
        {
            "organization": "ODPHP/HHS",
        },
        {
            "organization": "WHO",
        },
        {
            "organization": "ACSM",
        },
        {
            "organization": "ACSM Physical Activity Guidelines",
        },
        {
            "organization": "ODPHP Move Your Way",
        },
        {
            "organization": "CDC Benefits of Physical Activity",
        },
        {
            "organization": "WHO Sedentary Behaviour Guidelines",
        },
        {
            "organization": "ACSM Sedentary Behaviour",
        },
        {
            "organization": "ACSM Step Counts",
        },
        {
            "organization": "ODPHP Pregnancy Activity Guidance",
        },
        {
            "organization": "ACSM Guidelines for Exercise Testing and Prescription",
        },
        {
            "organization": "ACSM Fitness Assessment Manual",
        },
        {
            "organization": "ACSM Major Muscle Groups",
        },
        {
            "organization": "ACSM Body Composition Assessment",
        },
        {
            "organization": "ACSM 2026 Resistance Training Position Stand",
        },
        {
            "organization": "ACSM Progression Models in Resistance Training",
        },
        {
            "organization": "NSCA Tapering and Peaking",
        },
        {
            "organization": "Deloading Strength and Physique Sports Review",
        },
        {
            "organization": "ACE Strength Plateaus",
        },
        {
            "organization": "Exercise Variation Review",
        },
        {
            "organization": "Tapering and Peaking Powerlifting Review",
        },
        {
            "organization": "Schoenfeld Weekly Volume Meta-analysis",
        },
        {
            "organization": "Hypertrophy Volume Meta-analysis",
        },
        {
            "organization": "Training to Failure Meta-analysis",
        },
        {
            "organization": "Loading Recommendations Review",
        },
        {
            "organization": "ACSM Resistance Training Guidelines 2026",
        },
        {
            "organization": "NSCA Resistance Training Frequency",
        },
        {
            "organization": "NSCA Guide to Program Design",
        },
        {
            "organization": "ACSM Aerobic Intensity Guidance",
        },
        {
            "organization": "ACSM Distance Running Habits",
        },
        {
            "organization": "ACSM Training Load Monitoring",
        },
        {
            "organization": "ACSM/EIM Low Back Pain Activity",
        },
        {
            "organization": "ACSM Flexibility and Neuromotor Guidance",
        },
        {
            "organization": "Academy of Nutrition and Dietetics",
        },
        {
            "organization": "Dietary Guidelines for Americans",
        },
        {
            "organization": "USDA MyPlate",
        },
        {
            "organization": "CDC Healthy Eating Tips",
        },
        {
            "organization": "CDC Water and Healthier Drinks",
        },
        {
            "organization": "NIH Hydrating for Health",
        },
        {
            "organization": "CDC",
        },
        {
            "organization": "CDC Heat and Athletes",
        },
        {
            "organization": "CDC Heat-related Illnesses",
        },
        {
            "organization": "Heat Training and Competing Consensus",
        },
        {
            "organization": "AirNow AQI Outdoor Activity Guidance",
        },
        {
            "organization": "ACSM Cold Weather Exercise",
        },
        {
            "organization": "National Weather Service Wind Chill",
        },
        {
            "organization": "CDC Adult Physical Activity",
        },
        {
            "organization": "CDC Sleep Basics",
        },
        {
            "organization": "CDC Older Adults Physical Activity",
        },
        {
            "organization": "CDC Pregnant and Postpartum Physical Activity",
        },
        {
            "organization": "CDC Chronic Conditions and Disabilities Activity",
        },
        {
            "organization": "CDC Older Adults Balance Guidance",
        },
        {
            "organization": "CDC Measuring Physical Activity Intensity",
        },
        {
            "organization": "Brigham and Women's Return to Running",
        },
        {
            "organization": "Ohio State Walk to Run Guideline",
        },
        {
            "organization": "CDC STEADI",
        },
        {
            "organization": "ATS Six-Minute Walk Test",
        },
        {
            "organization": "Senior Fitness Test",
        },
        {
            "organization": "CDC Physical Activity Behavior Supports",
        },
        {
            "organization": "CDC Physical Activity Tracking",
        },
        {
            "organization": "CDC Plain Language",
        },
        {
            "organization": "CDC Plain Writing",
        },
        {
            "organization": "Community Guide Behavior Change Programs",
        },
        {
            "organization": "Motivational Interviewing Network of Trainers",
        },
        {
            "organization": "Self-Determination Theory Exercise Review",
        },
        {
            "organization": "Community Guide Older Adult Home Exercise",
        },
        {
            "organization": "ACE",
        },
        {
            "organization": "ACE Client-Centered Assessments",
        },
        {
            "organization": "ACE Essentials of Exercise Science",
        },
        {
            "organization": "ACE Joint Pain Exercise Modifications",
        },
        {
            "organization": "ACE Exercise Library",
        },
        {
            "organization": "ACE Exercise Library - Expanded Patterns",
        },
        {
            "organization": "ACE IFT / Mover Method",
        },
        {
            "organization": "Exercise is Medicine Youth and Older Adult Activity",
        },
        {
            "organization": "ACE IFT Program Design",
        },
        {
            "organization": "ACE Energy Pathways",
        },
        {
            "organization": "ACSM CPT Behavior Change Competencies",
        },
        {
            "organization": "NCI Implementation Intentions",
        },
        {
            "organization": "ACE IFT Cardiorespiratory Training",
        },
        {
            "organization": "NASM",
        },
        {
            "organization": "NASM Resistance Training Concepts",
        },
        {
            "organization": "NASM Acute Variables",
        },
        {
            "organization": "NASM Reps in Reserve",
        },
        {
            "organization": "Helms RIR-Based RPE",
        },
        {
            "organization": "Load Prescription Systematic Review",
        },
        {
            "organization": "Resistance Training Monitoring Review",
        },
        {
            "organization": "Concurrent Training Interference Meta-analysis",
        },
        {
            "organization": "Concurrent Training Compatibility Meta-analysis",
        },
        {
            "organization": "Running Injury Training Parameters Review",
        },
        {
            "organization": "Running Injury Prevention Scoping Review",
        },
        {
            "organization": "Human Performance Resources by CHAMP",
        },
        {
            "organization": "HPRC / NSCA Exercise Order",
        },
        {
            "organization": "Superset Resistance Training Review",
        },
        {
            "organization": "NASM Superset / Vertical Loading",
        },
        {
            "organization": "Cochrane Stretching DOMS Review",
        },
        {
            "organization": "Post-Exercise Stretching Meta-analysis",
        },
        {
            "organization": "Talk Test Review",
        },
        {
            "organization": "Movement Pattern Definitions Review",
        },
        {
            "organization": "NASM Dynamic Stretching",
        },
        {
            "organization": "NASM Static Stretching Evidence",
        },
        {
            "organization": "NASM Planes of Motion",
        },
        {
            "organization": "NASM Aerobic Energy Pathway",
        },
        {
            "organization": "NASM Plyometric Technique",
        },
        {
            "organization": "ACE Plyometric Guidelines",
        },
        {
            "organization": "Current Concepts of Plyometric Exercise",
        },
        {
            "organization": "NSCA Acceleration and Deceleration Mechanics",
        },
        {
            "organization": "NSCA Agility Movement Classification",
        },
        {
            "organization": "NASM Squat Biomechanics",
        },
        {
            "organization": "ASCA Youth Resistance Training Position Stand",
        },
        {
            "organization": "NASM OPT Model",
        },
        {
            "organization": "NSCA Overtraining and Recovery",
        },
        {
            "organization": "NASM Overtraining Signs",
        },
        {
            "organization": "Mayo Clinic Exercise and Illness",
        },
        {
            "organization": "Cleveland Clinic Activity During Acute Illness",
        },
        {
            "organization": "HSS Shoulder Impingement Exercises",
        },
        {
            "organization": "NASM Rotator Cuff Corrective Exercise",
        },
        {
            "organization": "NASM Exercise Library",
        },
        {
            "organization": "NASM Exercise Library - Expanded Patterns",
        },
        {
            "organization": "NASM Beyond the Number on the Scale",
        },
        {
            "organization": "NASM Movement Assessments",
        },
        {
            "organization": "NASM Correctly Coaching Exercises",
        },
        {
            "organization": "NASM Cueing Clients",
        },
        {
            "organization": "AHA Warm Up Cool Down",
        },
        {
            "organization": "NSCA Professional Standards",
        },
        {
            "organization": "NSCA Progressive Teaching Strategies",
        },
        {
            "organization": "TRUE Fitness Equipment Safety",
        },
        {
            "organization": "Precor Product Guides",
        },
        {
            "organization": "Life Fitness Technical Documents",
        },
        {
            "organization": "Rogue Spotter Arms Instructions",
        },
        {
            "organization": "ACE Bodyweight Squat",
        },
        {
            "organization": "NSCA Exercise Technique Manual",
        },
        {
            "organization": "Attentional Focus Resistance Training Review",
        },
        {
            "organization": "ACSM",
        },
        {
            "organization": "CDC",
        },
        {
            "organization": "Academy of Nutrition and Dietetics",
        },
        {
            "organization": "ISSN",
        },
        {
            "organization": "ISSN Diets and Body Composition",
        },
        {
            "organization": "Abdominal Exercise Spot Reduction Trial",
        },
        {
            "organization": "Localized Fat Loss Systematic Review",
        },
        {
            "organization": "University of Sydney Spot Reduction Explainer",
        },
        {
            "organization": "Fasted Exercise Body Composition Review",
        },
        {
            "organization": "Body Composition Fasted vs Fed Trial",
        },
        {
            "organization": "Delayed Onset Muscle Soreness Review",
        },
        {
            "organization": "Cleveland Clinic DOMS",
        },
        {
            "organization": "NSCA Resistance Training for Women",
        },
        {
            "organization": "NIDDK Body Weight Planner",
        },
        {
            "organization": "Academy Weight Management Position",
        },
        {
            "organization": "Resistance Training Body Composition Review",
        },
        {
            "organization": "ISSN Creatine Position Stand",
        },
        {
            "organization": "ISSN Caffeine Position Stand",
        },
        {
            "organization": "ISSN Beta-Alanine Position Stand",
        },
        {
            "organization": "ISSN Protein Position Stand",
        },
        {
            "organization": "NIH ODS Exercise Supplements",
        },
        {
            "organization": "IOC Dietary Supplements Consensus",
        },
        {
            "organization": "Dietitians of Canada / Academy of Nutrition and Dietetics / ACSM",
        },
        {
            "organization": "IOC REDs Consensus 2023",
        },
        {
            "organization": "Nutrition and Athletic Performance Position Paper",
        },
        {
            "organization": "NEDA Eating Disorder Warning Signs",
        },
        {
            "organization": "ANAD REDs Overview",
        },
        {
            "organization": "Female and Male Athlete Triad Coalition",
        },
        {
            "organization": "Colorado State University Extension",
        },
        {
            "organization": "CDC",
        },
    ],
}

_INTENT_FOCUS = {
    "workout_plan": [
        "בנה תוכנית לפי זמינות, ציוד, רמת ניסיון ומגבלות.",
        "כלול חימום, תרגילי דחיפה/משיכה/רגליים/ליבה, מנוחות, חלופות וכללי עומס הדרגתי.",
        "העדף 2-4 אימוני כוח פשוטים בשבוע למשתמש כללי, ולא טכניקות מתקדמות מוקדם מדי.",
    ],
    "workout_log": [
        "חזק עקביות, זהה כאב או עומס יתר, והצע התאמה קטנה לאימון הבא.",
        "אם האימון חלקי או פוספס, הפוך אותו לנתון תכנון ולא לכישלון.",
    ],
    "meal_log": [
        "תעד אוכל כטווחים והערכות, לא כוודאות.",
        "התמקד בהרגל הבא: חלבון, ירקות/פרי, מים, או תזמון סביב אימון לפי ההקשר.",
    ],
    "meal_image": [
        "זהה מזונות רק ברמת ביטחון סבירה, החזר טווחים ושאל על כמות/רטבים/שיטת הכנה כשצריך.",
        "אל תציג קלוריות או מאקרו כמספר מדויק מתמונה.",
    ],
    "general_chat": [
        "ענה כמאמן עקביות: קצר, בטוח, מותאם לפרופיל, ומכוון לפעולה אחת.",
        "השתמש בידע הכללי רק אם הוא רלוונטי לבקשה ולא כהרצאה.",
    ],
}
