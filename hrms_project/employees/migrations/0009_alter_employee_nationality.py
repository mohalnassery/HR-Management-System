# Generated by Django 4.2.9 on 2025-01-06 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0008_costprofitcenter_remove_employee_accom_occu_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='nationality',
            field=models.CharField(blank=True, choices=[('ALGERIAN', 'Algerian'), ('AMERICAN', 'American'), ('ARGENTINA', 'Argentina'), ('AUSTRALIAN', 'Australian'), ('BAHRAINI', 'Bahraini'), ('BANGLADESHI', 'Bangladeshi'), ('BELGIAN', 'Belgian'), ('BRAZILIAN', 'Brazilian'), ('BRITISH', 'British'), ('BULGARIAN', 'Bulgarian'), ('CAMEROONIAN', 'Cameroonian'), ('CANADIAN', 'Canadian'), ('CHILEAN', 'Chilean'), ('CHINESE', 'Chinese'), ('COLOMBIAN', 'Colombian'), ('CROATIAN', 'Croatian'), ('CUBAN', 'Cuban'), ('CYPRIOT', 'Cypriot'), ('CZECH', 'Czech'), ('DANISH', 'Danish'), ('DJIBOUTIAN', 'Djiboutian'), ('EGYPTIAN', 'Egyptian'), ('FILIPINO', 'Filipino'), ('FRENCH', 'French'), ('GERMAN', 'German'), ('GHANAIAN', 'Ghanaian'), ('GREEK', 'Greek'), ('DUTCH', 'Dutch'), ('HONG_KONGER', 'Hong Konger'), ('INDIAN', 'Indian'), ('INDONESIAN', 'Indonesian'), ('IRANIAN', 'Iranian'), ('IRAQI', 'Iraqi'), ('IRISH', 'Irish'), ('ITALIAN', 'Italian'), ('JAMAICAN', 'Jamaican'), ('JAPANESE', 'Japanese'), ('JORDANIAN', 'Jordanian'), ('KENYAN', 'Kenyan'), ('KUWAITI', 'Kuwaiti'), ('LEBANESE', 'Lebanese'), ('MALAWIAN', 'Malawian'), ('MALAYSIAN', 'Malaysian'), ('MEXICAN', 'Mexican'), ('MOROCCAN', 'Moroccan'), ('NEPALI', 'Nepali'), ('DUTCH', 'Dutch'), ('NEW_ZEALANDER', 'New Zealander'), ('NIGERIAN', 'Nigerian'), ('NORWEGIAN', 'Norwegian'), ('OMANI', 'Omani'), ('PAKISTANI', 'Pakistani'), ('POLISH', 'Polish'), ('PORTUGUESE', 'Portuguese'), ('RUSSIAN', 'Russian'), ('SAUDI', 'Saudi'), ('SCOTTISH', 'Scottish'), ('SERBIAN', 'Serbian'), ('SEYCHELLOIS', 'Seychellois'), ('SINGAPOREAN', 'Singaporean'), ('SOUTH_AFRICAN', 'South African'), ('SPANISH', 'Spanish'), ('SRI_LANKAN', 'Sri Lankan'), ('SUDANESE', 'Sudanese'), ('SWEDISH', 'Swedish'), ('SWISS', 'Swiss'), ('SYRIAN', 'Syrian'), ('TAIWANESE', 'Taiwanese'), ('TANZANIAN', 'Tanzanian'), ('THAI', 'Thai'), ('TUNISIAN', 'Tunisian'), ('TURKISH', 'Turkish'), ('EMIRATI', 'Emirati'), ('UGANDAN', 'Ugandan'), ('UKRAINIAN', 'Ukrainian'), ('VENEZUELAN', 'Venezuelan'), ('VIETNAMESE', 'Vietnamese'), ('YEMENI', 'Yemeni'), ('ZIMBABWEAN', 'Zimbabwean'), ('OTHER', 'Other')], max_length=50, null=True, verbose_name='Nationality'),
        ),
    ]
