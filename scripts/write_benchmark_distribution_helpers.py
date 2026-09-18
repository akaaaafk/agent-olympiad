"""Pure inventory formatting helpers; importing does not rewrite reports/results."""
def years_text(years):
    if not years:
        return 'Unknown'
    groups = []
    start = last = years[0]
    for year in years[1:]:
        if year == last + 1:
            last = year
        else:
            groups.append(str(start) if start == last else f'{start}-{last}')
            start = last = year
    groups.append(str(start) if start == last else f'{start}-{last}')
    return ', '.join(groups)
