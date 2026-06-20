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
        exercise_adjustments = self._exercise_adjustments(latest_log)
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
            )

        if high_rpe_count:
            signals.append("RPE גבוה בלוגים האחרונים")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="recovery_needed",
                signals=signals,
                next_adjustment="שמור על התאוששות: הורד מעט נפח או עצימות באימון הבא ובדוק שינה, אנרגיה ותחושת מאמץ.",
                exercise_adjustments=exercise_adjustments,
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

        if self._latest_log_supports_progression(latest_log) or (completed >= 3 and not skipped):
            signals.append("רצף אימונים יציב ללא כאב מדווח")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="progress_candidate",
                signals=signals,
                next_adjustment="אפשר לשקול התקדמות קטנה במשתנה אחד בלבד: חזרה, סט, עומס קל או טווח תנועה טוב יותר.",
                exercise_adjustments=exercise_adjustments,
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
            elif isinstance(rpe, int | float) and int(rpe) >= 9:
                adjustment = "reduce_or_hold"
                reason = "high_rpe"
                next_action = "לשמור עומס או להוריד מעט ולא לרדוף אחרי כשל."
            elif status in {"skipped", "partial", "modified"} or getattr(log, "status", None) in {"skipped", "partial", "modified"}:
                adjustment = "minimum_version"
                reason = "missed_or_partial"
                next_action = "לבצע גרסת מינימום במקום להשלים את כל מה שפוספס."
            elif self._result_supports_progression(result, rpe):
                adjustment = "small_progression"
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

    def _latest_log_supports_progression(self, log) -> bool:
        if log is None or getattr(log, "status", None) != "completed" or getattr(log, "pain_flag", False):
            return False
        rpe = getattr(log, "rpe", None)
        if isinstance(rpe, int | float) and int(rpe) > 8:
            return False
        results = getattr(log, "exercise_results", None) or []
        return bool(results) and all(
            self._result_supports_progression(result, result.get("rpe", rpe))
            for result in results
            if isinstance(result, dict)
        )

    @staticmethod
    def _result_supports_progression(result: dict, rpe) -> bool:
        if result.get("status", "completed") != "completed":
            return False
        if not isinstance(rpe, int | float) or int(rpe) > 8:
            return False
        sets = result.get("sets") or []
        if isinstance(sets, list):
            return bool(sets) and all(item.get("completed", False) for item in sets if isinstance(item, dict))
        reps = result.get("reps") or []
        return bool(reps)

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
    ) -> dict:
        return {
            "completed_recent": completed,
            "skipped_recent": skipped,
            "pain_flags_recent": pain_flags,
            "load_signal": load_signal,
            "signals": signals,
            "next_adjustment": next_adjustment,
            "exercise_adjustments": exercise_adjustments,
        }
