from lookup.models import Lookup


def get_all_lookup_data():
    lookup_data = {}
    for data in Lookup.objects.all():
        if not lookup_data.get(data.name):
            lookup_data[data.name] = []
        lookup_data[data.name].append((data.code, data.value))
    return lookup_data


def get_lookup_code():
    lookup_data = {}
    for data in Lookup.objects.all():
        if not lookup_data.get(data.name):
            lookup_data[data.name] = []
        lookup_data[data.name].append(data.code)
    return lookup_data
