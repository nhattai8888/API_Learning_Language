from datetime import datetime, timedelta, timezone
from app.core.enums import WordMastery

def sm2_update(state, rating: int):
    """
    rating 0..5
    Update fields:
      ease_factor, repetition, interval_days, mastery, familiarity, last_reviewed_at, next_review_at
    """
    now = datetime.now(timezone.utc)

    ef = float(state.ease_factor or 2.5)
    rep = int(state.repetition or 0)
    interval = int(state.interval_days or 0)
    fam = int(state.familiarity or 0)

    if rating < 3:
        rep = 0
        interval = 1
        state.lapse_count = int(state.lapse_count or 0) + 1
        state.mastery = WordMastery.LEARNING
        fam = max(0, fam - 10)
    else:
        rep += 1
        if rep == 1:
            interval = 1
        elif rep == 2:
            interval = 3
        else:
            interval = max(1, int(round(interval * ef)))

        ef = ef + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        ef = min(2.8, max(1.3, ef))

        fam = min(100, fam + (6 + rating))
        if fam >= 85:
            state.mastery = WordMastery.MASTERED
        elif fam >= 60:
            state.mastery = WordMastery.KNOWN
        else:
            state.mastery = WordMastery.LEARNING

    state.ease_factor = ef
    state.repetition = rep
    state.interval_days = interval
    state.familiarity = fam
    state.last_reviewed_at = now
    state.next_review_at = now + timedelta(days=interval)
