class TrainingAdaptationService:
    def summarize(self, logs: list) -> dict:
        recent_logs = list(logs)[:5]
        completed = sum(1 for log in recent_logs if getattr(log, "status", None) == "completed")
        skipped = sum(1 for log in recent_logs if getattr(log, "status", None) == "skipped")
        pain_flags = sum(1 for log in recent_logs if getattr(log, "pain_flag", False))
        rpe_values = [
            int(getattr(log, "rpe"))
            for log in recent_logs
            if isinstance(getattr(log, "rpe", None), int | float)
        ]
        high_rpe_count = sum(1 for value in rpe_values if value >= 9)
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
            )

        if skipped >= 2:
            signals.append("שני אימונים או יותר פוספסו לאחרונה")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="adherence_risk",
                signals=signals,
                next_adjustment="הצע גרסה קצרה וקלה לביצוע לפני הוספת נפח, כדי להחזיר רצף ולא להעמיס על השבוע.",
            )

        if completed >= 3 and not skipped:
            signals.append("רצף אימונים יציב ללא כאב מדווח")
            return self._summary(
                completed=completed,
                skipped=skipped,
                pain_flags=pain_flags,
                load_signal="progress_candidate",
                signals=signals,
                next_adjustment="אפשר לשקול התקדמות קטנה במשתנה אחד בלבד: חזרה, סט, עומס קל או טווח תנועה טוב יותר.",
            )

        return self._summary(
            completed=completed,
            skipped=skipped,
            pain_flags=pain_flags,
            load_signal="maintain",
            signals=signals or ["אין מספיק דפוס ברור מהלוגים האחרונים"],
            next_adjustment="שמור על התוכנית הנוכחית ואסוף עוד לוגים לפני שינוי משמעותי.",
        )

    @staticmethod
    def _summary(
        *,
        completed: int,
        skipped: int,
        pain_flags: int,
        load_signal: str,
        signals: list[str],
        next_adjustment: str,
    ) -> dict:
        return {
            "completed_recent": completed,
            "skipped_recent": skipped,
            "pain_flags_recent": pain_flags,
            "load_signal": load_signal,
            "signals": signals,
            "next_adjustment": next_adjustment,
        }
