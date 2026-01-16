from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Holiday


@receiver(post_save, sender=Holiday)
@receiver(post_delete, sender=Holiday)
def clear_worktime_holiday_caches(*args, **kwargs) -> None:
    """
    Invalidiert WorkingTimeCalculator-Caches bei Änderungen an Holiday.

    Hintergrund: WorkingTimeCalculator nutzt lru_cache, um wiederholte Holiday-Queries
    (z.B. in Monatsübersichten) zu vermeiden. In Tests und bei Admin-Änderungen müssen
    diese Caches sofort geleert werden, damit neue/gelöschte Feiertage berücksichtigt werden.
    """
    from .services import WorkingTimeCalculator

    WorkingTimeCalculator._holidays_set.cache_clear()
    WorkingTimeCalculator._count_workdays_for_canton.cache_clear()

