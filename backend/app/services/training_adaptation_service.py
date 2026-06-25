from backend.app.services.pain_text import has_explicit_no_pain_statement


class TrainingAdaptationService:
    def summarize(self, logs: list) -> dict:
        recent_logs = list(logs)[:5]
        latest_log = recent_logs[0] if recent_logs else None
        completed = sum(1 for log in recent_logs if getattr(log, "status", None) == "completed")
        skipped = sum(1 for log in recent_logs if getattr(log, "status", None) == "skipped")
        partial_or_modified = sum(1 for log in recent_logs if getattr(log, "status", None) in {"partial", "modified"})
        pain_flags = sum(1 for log in recent_logs if getattr(log, "pain_flag", False))
        rpe_values = [
            int(getattr(log, "rpe"))
            for log in recent_logs
            if isinstance(getattr(log, "rpe", None), int | float)
        ]
        high_rpe_count = sum(1 for value in rpe_values if value >= 9)
        high_exercise_effort = self._latest_log_has_high_exercise_effort(latest_log)
        exercise_adjustments = self._exercise_adjustments(latest_log)
        pain_area = self._pain_area(latest_log)
        signals: list[str] = []

        if pain_flags:
            signals.append("דווח כאב בלוגים האחרונים")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="pain_caution",
                signals=signals,
                next_adjustment="התאם את האימון סביב הכאב: בחר וריאציה קלה יותר, טווח נוח יותר או עומס נמוך יותר לפני התקדמות.",
                exercise_adjustments=exercise_adjustments,
                pain_area=pain_area,
            )

        if high_rpe_count or high_exercise_effort:
            signals.append("RPE/RIR או מאמץ מילולי גבוה בלוגים האחרונים")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="recovery_needed",
                signals=signals,
                next_adjustment="שמור על התאוששות: הורד מעט נפח או עצימות באימון הבא ובדוק שינה, אנרגיה ותחושת מאמץ.",
                exercise_adjustments=exercise_adjustments,
            )

        adherence_events = skipped + partial_or_modified
        if adherence_events >= 2:
            signals.append("כמה אימונים פוספסו, קוצרו או שונו לאחרונה")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="adherence_risk",
                signals=signals,
                next_adjustment=(
                    "התוכנית כנראה גדולה מדי כרגע: בחר גרסה קצרה והורד זמנית יום אימון אחד בשבוע או הפוך יום אחד לגרסת מינימום. "
                    "שאלה אחת: מה החסם שחוזר - זמן, עייפות, כאב או ציוד?"
                ),
                exercise_adjustments=exercise_adjustments,
                plan_adjustment={
                    "type": "reduce_plan_before_rebuild",
                    "recommendation": "reduce_days_or_add_minimum_day",
                    "reduce_days_per_week_by": 1,
                    "use_minimum_version_days": True,
                    "critical_question": "מה החסם שחוזר - זמן, עייפות, כאב או ציוד?",
                },
            )

        if skipped or partial_or_modified:
            signals.append("אימון פוספס, חלקי או שונה לאחרונה")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="adherence_risk",
                signals=signals,
                next_adjustment="הצע גרסה קצרה וגרסת מינימום במקום להשלים את כל מה שפוספס: פחות סטים, פחות עומס, וביצוע נקי.",
                exercise_adjustments=exercise_adjustments,
            )

        if any(adjustment.get("reason") == "progression_gate_missing_rpe" for adjustment in exercise_adjustments):
            signals.append("שער התקדמות חסר RPE")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="maintain",
                signals=signals,
                next_adjustment="לשמור את הגרסה הנוכחית; מאמץ מילולי נשמר, אבל צריך RPE 1-10 וכאב כדי להתקדם שלב.",
                exercise_adjustments=exercise_adjustments,
            )

        if any(
            adjustment.get("reason") == "qualitative_controlled_effort"
            and adjustment.get("adjustment") == "maintain"
            for adjustment in exercise_adjustments
        ):
            signals.append("מאמץ מילולי בשליטה בלי RPE/RIR")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="maintain",
                signals=signals,
                next_adjustment="לשמור את הגרסה הנוכחית; 'בשליטה' הוא סימן טוב, אבל צריך RPE 1-10 או RIR וכאב כדי להעלות עומס.",
                exercise_adjustments=exercise_adjustments,
            )

        progress_evidence = self._latest_log_progress_evidence(latest_log)
        if progress_evidence or (completed >= 3 and not skipped):
            signals.append("רצף אימונים יציב ללא כאב מדווח")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="progress_candidate",
                signals=signals,
                next_adjustment="אפשר לשקול התקדמות קטנה במשתנה אחד בלבד: חזרה, סט, עומס קל או טווח תנועה טוב יותר.",
                exercise_adjustments=exercise_adjustments,
                progress_evidence=progress_evidence or "completed_streak",
            )

        return self._summary(
            completed=completed,
            skipped=skipped,
            pain_flags=pain_flags,
            load_signal="maintain",
            signals=signals or ["אין מספיק דפוס ברור מהלוגים האחרונים"],
            next_adjustment="שמור על התוכנית הנוכחית ואסוף עוד לוגים לפני שינוי משמעותי.",
            exercise_adjustments=exercise_adjustments,
        )

    def _exercise_adjustments(self, log) -> list[dict]:
        if log is None:
            return []
        results = getattr(log, "exercise_results", None) or []
        adjustments = []
        for result in results:
            if not isinstance(result, dict):
                continue
            exercise_name = result.get("exercise_name") or result.get("exercise")
            status = result.get("status") or getattr(log, "status", None)
            rpe = result.get("rpe") or getattr(log, "rpe", None)
            if getattr(log, "pain_flag", False):
                adjustment = "reduce_or_swap"
                reason = "pain_reported"
                next_action = "לבחור וריאציה קלה יותר או טווח ללא כאב."
            elif self._result_too_close_to_failure(result, rpe):
                adjustment = "reduce_or_hold"
                if result.get("effort_signal") == "too_hard":
                    reason = "qualitative_high_effort"
                else:
                    reason = "high_rpe" if isinstance(rpe, int | float) and int(rpe) >= 9 else "near_failure_rir"
                next_action = "לשמור עומס או להוריד מעט ולא לרדוף אחרי כשל."
            elif status in {"skipped", "partial", "modified"} or getattr(log, "status", None) in {"skipped", "partial", "modified"}:
                adjustment = "minimum_version"
                reason = "missed_or_partial"
                next_action = "לבצע גרסת מינימום במקום להשלים את כל מה שפוספס."
            elif result.get("progression_gate_missing_rpe"):
                adjustment = "maintain"
                reason = "progression_gate_missing_rpe"
                next_action = "לשמור את הגרסה הנוכחית; מאמץ מילולי נשמר, אבל צריך RPE 1-10 וכאב כדי להתקדם שלב."
            elif result.get("effort_signal") == "controlled" and rpe is None and result.get("rir") is None:
                adjustment = "maintain"
                reason = "qualitative_controlled_effort"
                next_action = "לשמור את הגרסה הנוכחית; המאמץ נשמע בשליטה, אבל לתעד RPE 1-10 או RIR וכאב לפני שמעלים עומס."
            elif self._result_underloaded(result):
                adjustment = "small_progression"
                if result.get("effort_signal") == "underloaded":
                    reason = "qualitative_underload"
                    next_action = "להעלות עומס קטן או להאט קצב כי הלוג תיאר שקל מדי, לא לקפוץ הרבה."
                else:
                    reason = "high_rir_underload"
                    next_action = "להעלות עומס קטן או להאט קצב כדי לכוון ל-RIR 1-3, לא לקפוץ הרבה."
            elif self._result_supports_progression(result, rpe):
                adjustment = "small_progression"
                if result.get("effort_signal") == "controlled" and rpe is None and result.get("rir") is None:
                    reason = "qualitative_controlled_effort"
                    next_action = "להוסיף חזרה אחת או עומס קטן אחד בלבד אם הטכניקה נשארת נקייה."
                else:
                    reason = "completed_with_manageable_effort"
                    next_action = "להוסיף חזרה אחת או עומס קטן אחד בלבד."
            else:
                adjustment = "maintain"
                reason = "insufficient_pattern"
                next_action = "לשמור את אותו עומס ולאסוף עוד לוג."
            adjustments.append(
                {
                    "exercise_id": result.get("exercise_id"),
                    "exercise_name": exercise_name,
                    "adjustment": adjustment,
                    "reason": reason,
                    "next_action": next_action,
                }
            )
        return adjustments

    def _latest_log_progress_evidence(self, log) -> str | None:
        if log is None or getattr(log, "status", None) != "completed" or getattr(log, "pain_flag", False):
            return None
        rpe = getattr(log, "rpe", None)
        if isinstance(rpe, int | float) and int(rpe) > 8:
            return None
        results = getattr(log, "exercise_results", None) or []
        if not results:
            if isinstance(rpe, int | float) and int(rpe) <= 8 and self._log_has_explicit_no_pain(log):
                return "session_rpe_no_pain"
            return None
        valid_results = [result for result in results if isinstance(result, dict)]
        if valid_results and all(
            self._result_supports_progression(result, result.get("rpe", rpe))
            for result in valid_results
        ):
            return "exercise_log"
        return None

    @staticmethod
    def _result_supports_progression(result: dict, rpe) -> bool:
        if result.get("status", "completed") != "completed":
            return False
        rpe_value = TrainingAdaptationService._numeric_effort(rpe)
        rir_value = TrainingAdaptationService._numeric_effort(result.get("rir"))
        if rpe_value is not None and rpe_value > 8:
            return False
        if rir_value is not None and rir_value <= 0:
            return False
        effort_signal = result.get("effort_signal")
        if effort_signal == "too_hard":
            return False
        if rpe_value is None and rir_value is None and effort_signal != "underloaded":
            return False
        sets = result.get("sets") or []
        if isinstance(sets, list):
            return bool(sets) and all(item.get("completed", False) for item in sets if isinstance(item, dict))
        reps = result.get("reps") or []
        return bool(reps)

    @staticmethod
    def _result_too_close_to_failure(result: dict, rpe) -> bool:
        rpe_value = TrainingAdaptationService._numeric_effort(rpe)
        if rpe_value is not None and rpe_value >= 9:
            return True
        rir_value = TrainingAdaptationService._numeric_effort(result.get("rir"))
        return (rir_value is not None and rir_value <= 0) or result.get("effort_signal") == "too_hard"

    @staticmethod
    def _result_underloaded(result: dict) -> bool:
        rir_value = TrainingAdaptationService._numeric_effort(result.get("rir"))
        return (rir_value is not None and rir_value >= 4) or result.get("effort_signal") == "underloaded"

    @staticmethod
    def _latest_log_has_high_exercise_effort(log) -> bool:
        if log is None or getattr(log, "status", None) != "completed" or getattr(log, "pain_flag", False):
            return False
        for result in getattr(log, "exercise_results", None) or []:
            if isinstance(result, dict) and TrainingAdaptationService._result_too_close_to_failure(result, result.get("rpe")):
                return True
        return False

    @staticmethod
    def _numeric_effort(value) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return int(value)
        return None

    @staticmethod
    def _log_has_explicit_no_pain(log) -> bool:
        chunks = [getattr(log, "notes", None) or ""]
        for result in getattr(log, "exercise_results", None) or []:
            if isinstance(result, dict):
                chunks.append(str(result.get("notes") or ""))
        return has_explicit_no_pain_statement(" ".join(chunks))

    @staticmethod
    def _pain_area(log) -> str | None:
        if log is None or not getattr(log, "pain_flag", False):
            return None
        chunks = [getattr(log, "notes", None) or ""]
        for result in getattr(log, "exercise_results", None) or []:
            if not isinstance(result, dict):
                continue
            chunks.extend(
                [
                    str(result.get("exercise_name") or result.get("exercise") or ""),
                    str(result.get("notes") or ""),
                ]
            )
        text = " ".join(chunks).lower()
        if "ברך" in text or "knee" in text:
            return "knee"
        if "כתף" in text or "shoulder" in text:
            return "shoulder"
        if "גב" in text or "back" in text:
            return "back"
        return None

    @staticmethod
    def _summary(
        *,
        completed: int,
        skipped: int,
        pain_flags: int,
        load_signal: str,
        signals: list[str],
        next_adjustment: str,
        exercise_adjustments: list[dict],
        pain_area: str | None = None,
        plan_adjustment: dict | None = None,
        progress_evidence: str | None = None,
    ) -> dict:
        payload = {
            "completed_recent": completed,
            "skipped_recent": skipped,
            "pain_flags_recent": pain_flags,
            "load_signal": load_signal,
            "signals": signals,
            "next_adjustment": next_adjustment,
            "exercise_adjustments": exercise_adjustments,
        }
        if pain_area:
            payload["pain_area"] = pain_area
        if plan_adjustment:
            payload["plan_adjustment"] = plan_adjustment
        if progress_evidence:
            payload["progress_evidence"] = progress_evidence
        return payload
