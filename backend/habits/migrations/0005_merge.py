from django.db import migrations


class Migration(migrations.Migration):
    """Merge migration to resolve conflicting leaf nodes.

    This migration depends on both 0002_add_user_to_habitentry and
    0004_habit_habits_habi_user_id_599ecd_idx_and_more which were
    created on different branches. It performs no schema operations
    (noop) but unifies the migration graph so `migrate` can run.
    """

    dependencies = [
        ("habits", "0002_add_user_to_habitentry"),
        ("habits", "0004_habit_habits_habi_user_id_599ecd_idx_and_more"),
    ]

    operations = []
