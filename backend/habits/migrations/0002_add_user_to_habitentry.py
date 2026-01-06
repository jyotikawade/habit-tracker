from django.db import migrations, models


def forwards(apps, schema_editor):
    HabitEntry = apps.get_model('habits', 'HabitEntry')
    Habit = apps.get_model('habits', 'Habit')
    # Backfill user_id from habit.user_id
    for entry in HabitEntry.objects.select_related('habit').all():
        try:
            entry.user_id = entry.habit.user_id
            entry.save(update_fields=['user'])
        except Exception:
            # skip problematic rows
            continue


def backwards(apps, schema_editor):
    # noop: leave user ids as-is
    return


class Migration(migrations.Migration):

    dependencies = [
        ('habits', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='habitentry',
            name='user',
            field=models.ForeignKey(null=True, editable=False, on_delete=models.CASCADE, to='auth.user'),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name='habitentry',
            name='user',
            field=models.ForeignKey(editable=False, on_delete=models.CASCADE, to='auth.user'),
        ),
    ]
