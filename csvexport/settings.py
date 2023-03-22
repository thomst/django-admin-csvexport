from django.conf import settings



# Set the unix standard csv-format as default
CSV_EXPORT_DELIMITER = getattr(settings, 'CSV_EXPORT_DELIMITER', ',')
CSV_EXPORT_ESCAPECHAR = getattr(settings, 'CSV_EXPORT_ESCAPECHAR', '')
CSV_EXPORT_QUOTECHAR = getattr(settings, 'CSV_EXPORT_QUOTECHAR', '"')
CSV_EXPORT_DOUBLEQUOTE = getattr(settings, 'CSV_EXPORT_DOUBLEQUOTE', True)
CSV_EXPORT_LINETERMINATOR = getattr(settings, 'CSV_EXPORT_LINETERMINATOR', r'\n')
CSV_EXPORT_QUOTING = getattr(settings, 'CSV_EXPORT_QUOTING', 'QUOTE_ALL')

CSV_EXPORT_FORMAT_FORM = getattr(settings, 'CSV_EXPORT_FORMAT_FORM', True)
CSV_EXPORT_UNIQUE_FORM = getattr(settings, 'CSV_EXPORT_UNIQUE_FORM', False)
CSV_EXPORT_EMPTY_VALUE = getattr(settings, 'CSV_EXPORT_EMPTY_VALUE', '')
CSV_EXPORT_REFERENCE_DEPTH = getattr(settings, 'CSV_EXPORT_REFERENCE_DEPTH', 3)
