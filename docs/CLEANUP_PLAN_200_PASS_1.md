# 200-שלבי פישוט ותיקון — מסלול עבודה (Pass 1)

> סטטוס ביצוע: שלב זה עוסק בצעד 1–20 לפי חלוקה לפי בלוקים.
> לא נעשו שינויים בתשתית, ללא Supabase, ללא מעבר ערוץ חדש, וללא feature-demo.

## 1) הגדרה חוזית להפעלה

1. Scope lock:
   - ללא Supabase בשלב זה.
   - ללא שינוי stack.
   - ללא Fake behavior.
2. Definition of Done לכל שלב:
   - שינוי קטן, בדיקה אחת לפחות רצה מחדש.
   - בדיקת מסלול רלוונטי לפחות ב־Frontend או Backend.
3. מצב סיכונים:
   - אם יש שינויי API חוסכים התנהגות קיימת — שינוי נחשב `do not proceed`.
4. עקיבות שלבים:
   - משתמשים ב־git commits לפי בלוקים קטנים (<12 קבצים רציף לכל commit).

## 2) מה כבר קיים נכון עכשיו (Baseline snapshot)

- קיימים boundaryים נכונים יחסית בין API + services + UI.
- יש `Settings` עם מצב provider, usage ו־disclaimer, ולא דולף API key.
- קיימים בדיקות חיות לכל מסלולים קריטיים (chat/workouts/dashboard/meals).
- קיימת תמיכה קיימת ב־local-only כאשר אין API key.

## 3) נקודות פישוט שבוצעו ע"י Pass 1

### 3.1 No-API-Key mode — product-level visibility
- API: `GET /api/health` מחזיר גם `no_api_key_mode`.
- Frontend: אם המצב הופעל, מוצג banner נפרד ב־sidebar עם הסבר ברור על מצב local-only.
- בדיקה: `App` טוען את banner דרך mock health נכון לאישור התצוגה.

### 3.2 איחוד חוזק חוזה תגובה
- Backend:
  - נוצר `HealthResponse` ב־`schemas.py`.
  - `main.health` מחזיר אובייקט תואם מודל.
- Frontend:
  - `HealthStatus` כולל `no_api_key_mode?` לשמירה לאחור.

### 3.3 עדכון בדיקות בסיס
- עדכנה `backend/tests/test_health.py` לכלול שדה `no_api_key_mode`.
- עדכנה `frontend/src/App.test.tsx` כדי לדמות מצב `not_configured` ולוודא הצגת banner ברור.

## 4) Risk register פנימי (Pass 1)

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| שינוי חוזר של contract בלי עדכון API tests | בינוני | גבוה | בדיקה חובה לכל שינוי חזרה ל־/api/health |
| הודעת banner אנגלית במקום עברית | נמוך | נמוך | לשלב מחרוג מהשפה בלבד כאשר זה סטטוס טכני קצר |
| fallback של `fetchHealth` בלי שדה `no_api_key_mode` בעת תקלת רשת | נמוך | נמוך | חישוב fallback לפי `ai_provider === not_configured` כבר קיים |
| שינויי תצוגה ישירים בלי lint/test | בינוני | בינוני | run `npm ... test` לפחות עבור App סביב שינויי UI |

## 5) שלבי בדיקה שבוצעו

- Backend:
  - `python -m pytest backend/tests/test_health.py`
- Frontend:
  - `npm --prefix frontend test -- --run App.test.tsx`

## 6) שאר שלבי 1–20 — מוכנים לביצוע ב־Pass הבא

1. להוסיף `docs` קצר לתכנון ו־scope קצר בכל תחילת משמרת עבודה.
2. להוסיף מסנן שפה/רמת טון אחיד יותר בפרומפטים לפי תגובת safety.
3. להוסיף מערכת סטטוס מקומית לרישום מצב של כל שלב קטן (planned/in-progress/done).

## 7) תכנית המשך (Loop Rule)

- סבב עבודה נשאר קיים: `Review → fix one concrete issue → tests → next issue`.
- אין קפיצה על שני מקטעים בו־זמנית; כל שינויים קטנים עוקבים זה אחר זה עד green.
