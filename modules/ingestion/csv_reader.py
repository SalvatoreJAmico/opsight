import io

import pandas as pd


CSV_ENCODING_FALLBACKS = ("utf-8", "cp1252", "latin-1")


class CsvDecodingError(ValueError):
    pass


def read_csv_with_fallback(source, **kwargs):
    last_error = None

    for encoding in CSV_ENCODING_FALLBACKS:
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            return pd.read_csv(source, encoding=encoding, **kwargs)
        except UnicodeDecodeError as exc:
            last_error = exc

    attempted = ", ".join(CSV_ENCODING_FALLBACKS)
    detail = f": {last_error}" if last_error else ""
    raise CsvDecodingError(
        f"CSV decoding failed after trying encodings: {attempted}{detail}"
    )
