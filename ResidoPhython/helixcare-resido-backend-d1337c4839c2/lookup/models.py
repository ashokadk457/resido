from django.db import models

from assets.models import Asset
from audit.models import GenericModel

optional = {"null": True, "blank": True}


class Lookup(GenericModel):
    MODEL_ALL_DATA_CACHE_KEY = "LOOKUPS"

    name = models.CharField(db_index=True, max_length=500)
    code = models.CharField(max_length=500, db_index=True)
    value = models.CharField(max_length=500)
    modified_value = models.CharField(max_length=500, null=True, blank=True)
    active = models.BooleanField(default=True)
    favorite = models.BooleanField(default=False)
    description = models.TextField()
    display_name = models.CharField(max_length=1000, null=True)
    image = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, **optional)
    display_order = models.PositiveIntegerField(null=True)

    class Meta:
        unique_together = ("name", "code")
        ordering = ("-favorite", "display_order", "code")

    def __str__(self):
        return "{}: {}|{}".format(self.name, self.code, self.value)

    def save(self, *args, **kwargs):
        # print("Key is {}".format(self.pk))
        if self.pk and self.__original_code and self.__original_code != self.code:
            raise "Code cannot be changed"
        super(Lookup, self).save(*args, **kwargs)
        self.__original_code = self.code

    def __init__(self, *args, **kwargs):
        super(Lookup, self).__init__(*args, **kwargs)
        self.__original_code = self.code


class CPTCategoryValue(GenericModel):
    cpt_cat_id = models.CharField(unique=True, max_length=100)
    description = models.CharField(max_length=500)
    cpt_st_value = models.CharField(max_length=100)
    cpt_end_value = models.CharField(max_length=100)
    cpt_cat_type = models.CharField(max_length=100)


class CPTData(GenericModel):
    cpt_code = models.CharField(unique=True, max_length=100)
    description = models.CharField(max_length=500)
    mod_indicator = models.CharField(max_length=100, default="N")
    status = models.CharField(max_length=100, default="Y")
    cpt_cat_val = models.ForeignKey(
        CPTCategoryValue, on_delete=models.CASCADE, blank=True, null=True
    )


class UIMetaData(GenericModel):
    type = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    notes = models.CharField(max_length=100)
    logo = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, **optional)
    display_order = models.IntegerField(default=99)
    active = models.BooleanField(default=True)


class LoincCodes(GenericModel):
    code = models.CharField(unique=True, max_length=100)
    component = models.CharField(max_length=1000)
    long_common_name = models.TextField(**optional)
