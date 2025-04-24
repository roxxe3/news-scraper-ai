from datetime import datetime

def process_article_dates(dates_text):
    if not dates_text:
        return [None, None]

    try:
        date_parts = []
        if "Mis à jour le" in dates_text:
            split_parts = dates_text.split("Mis à jour le")
            published_text = split_parts[0].strip()
            updated_text = "Mis à jour le " + split_parts[1].strip()
            date_parts = [published_text, updated_text]
        else:
            date_parts = [dates_text.strip(), None]

        result_dates = []
        for date_text in date_parts:
            if not date_text:
                result_dates.append(None)
                continue

            if date_text.startswith("Publié le"):
                date_text = " ".join(date_text.split()[2:])
            elif date_text.startswith("Mis à jour le"):
                date_text = " ".join(date_text.split()[4:])

            parts = date_text.split()
            if len(parts) < 5:
                result_dates.append(None)
                continue

            day = int(parts[0])
            month_abbr_fr = parts[1]
            year = int(parts[2])
            time_str = parts[4]
            hour, minute = map(int, time_str.split(':'))

            month_dict_fr = {
                'janv.': 1, 'févr.': 2, 'mars': 3, 'avr.': 4, 'mai': 5, 'juin': 6,
                'juil.': 7, 'août': 8, 'sept.': 9, 'oct.': 10, 'nov.': 11, 'déc.': 12
            }

            month = month_dict_fr.get(month_abbr_fr.lower())
            if not month:
                result_dates.append(None)
                continue

            dt_object = datetime(year, month, day, hour, minute)
            result_dates.append(dt_object.isoformat())

        while len(result_dates) < 2:
            result_dates.append(None)

        return result_dates[:2]

    except Exception:
        return [None, None]