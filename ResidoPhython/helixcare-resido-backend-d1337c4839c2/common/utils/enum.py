from enum import Enum


def convert_enum_to_choices(cls):
    return tuple((i.value, i.name) for i in cls)


def convert_array_to_choices(list):
    return tuple((i, i) for i in list)


def convert_dict_to_choices(dict):
    return tuple((y, x) for x, y in dict.items())


def convert_enum_to_values_array(cls):
    return [i.value for i in cls]


def convert_enum_to_dict(cls):
    return dict((i.name, i.value) for i in cls)


class EnumWithValueConverter(Enum):
    @property
    def raw_value(self):
        return self.value

    @classmethod
    def choices(cls):
        return convert_enum_to_choices(cls)

    @classmethod
    def values(cls):
        return convert_enum_to_values_array(cls)

    @classmethod
    def values_tuple(cls):
        return tuple(cls.values())

    @classmethod
    def dict(cls):
        return convert_enum_to_dict(cls)

    @classmethod
    def resolve(cls, val):
        for i in cls:
            if i.value == val:
                return i.name
        return val
