from django.contrib.gis.db.models.functions import GeometryDistance
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import F

from common.constants import URGENT_CARE, PRIMARY_CARE


class StaffSearchEngine:
    def __init__(self, default_queryset, **kwargs):
        self.default_query_set = default_queryset
        self.search_criterion = kwargs.get("search_criterion", [])
        self.specialities_in_request = self.get_specialities_in_request()
        self.filter_criterion = kwargs.get("filter_criterion", {})
        self.latitude = kwargs.get("latitude")
        self.longitude = kwargs.get("longitude")
        self.boundary_range = int(kwargs.get("boundary_range", 0)) / 69
        self.search_point = GEOSGeometry(
            f"POINT({self.latitude} {self.longitude})", srid=4326
        )
        self.request_payload = kwargs
        self.search_results = None
        self.is_search_criteria_empty = True
        self.speciality_codes = set()
        self.primary_care_speciality_codes = set()
        self.age_choice_values = []

    def get_specialities_in_request(self):
        if not self.search_criterion:
            return []

        for search_criteria in self.search_criterion:
            if search_criteria.get("key") == "speciality":
                return search_criteria["values"]

        return []

    def _get_distinct_search_results(self):
        return self.search_results.distinct()

    def search(self):
        self.search_results = self._search()
        self.search_results = self._filter()
        self.search_results = self._apply_boundary_range()
        self.search_results = self._apply_age_filter()
        self.search_results = self._sort()
        self.search_results = self._get_distinct_search_results()
        return self.search_results

    def _sort(self):
        sort_by_distance = (
            self.request_payload.get("sort_by_distance", "").lower() == "true"
        )
        sort_by_highest_rating = (
            self.request_payload.get("sort_by_highest_rating", "").lower() == "true"
        )
        sort_by_lowest_rating = (
            self.request_payload.get("sort_by_lowest_rating", "").lower() == "true"
        )

        sort_order_found = False
        if sort_by_highest_rating:
            sort_order_found = True
            self.search_results = self.search_results.order_by(
                F("rating").desc(nulls_last=True)
            )

        if sort_by_lowest_rating:
            sort_order_found = True
            self.search_results = self.search_results.order_by("rating")

        if sort_by_distance or not sort_order_found:
            sort_order_found = True
            self.search_results = self.search_results.annotate(
                distance=GeometryDistance("locations__latlng", self.search_point)
            ).order_by("distance")

        return self.search_results

    def _apply_boundary_range(self):
        if not self.boundary_range:
            return self.search_results

        self.search_results = self.search_results.filter(
            locations__latlng__dwithin=(self.search_point, self.boundary_range)
        ).distinct()
        return self.search_results

    def _filter(self):
        qs = (
            self.search_results
            if self.search_results is not None
            else self.default_query_set
        )

        if "gender" in self.filter_criterion:
            qs = qs.filter(user__gender=self.filter_criterion["gender"])

        if "rating" in self.filter_criterion:
            rating_filter = self.filter_criterion["rating"]

            if rating_filter is not None:
                if isinstance(rating_filter, str):
                    rating_filter = [rating_filter]
                qs = qs.filter(rating__in=rating_filter)

        if "accepts_new_patient" in self.filter_criterion:
            new_patients_check = (
                True if self.filter_criterion["accepts_new_patient"] == "yes" else False
            )
            qs = qs.filter(accepts_new_patient=new_patients_check)

        if "provides_telehealth" in self.filter_criterion:
            telehealth_check = (
                True if self.filter_criterion["provides_telehealth"] == "yes" else False
            )
            qs = qs.filter(provides_telehealth=telehealth_check)

        if "languages_known" in self.filter_criterion:
            qs = qs.filter(
                user__languages_known__contains=self.filter_criterion["languages_known"]
            )

        if "qualifications" in self.filter_criterion:
            qs = qs.filter(
                qualification__contains=self.filter_criterion["qualifications"]
            )

        if "insurance_plan" in self.filter_criterion:
            insurance_plans = self.filter_criterion.get("insurance_plan", [])
            qs = qs.filter(providerinsurance__plans__id__in=insurance_plans)

        if "provider" in self.filter_criterion:
            qs = qs.filter(pk=self.filter_criterion["provider"])

        self.search_results = qs
        return self.search_results

    def _apply_age_filter(self):
        if not self.age_choice_values or self.search_results is None:
            return self.search_results

        self.speciality_codes = self.filter_in_or_out_age_based_speciality_codes(
            speciality_codes=self.speciality_codes,
            criteria_values=self.age_choice_values,
        )

        age_factored_staffs = self._get_staff_using_speciality_codes(
            speciality_codes=self.speciality_codes
        )

        return self.search_results.distinct() & age_factored_staffs

    def _search(self):
        for relevance, search_criteria in enumerate(self.search_criterion):
            criteria_key = search_criteria.get("key")
            criteria_values = search_criteria.get("values")

            if criteria_values and self.is_search_criteria_empty:
                self.is_search_criteria_empty = False

            if not criteria_values:
                continue

            if criteria_key == "age_choice":
                self.age_choice_values = criteria_values
                continue

            if (
                criteria_key == "speciality"
                and URGENT_CARE in criteria_values
                or PRIMARY_CARE in criteria_values
            ):
                current_staffs = self.get_staff_for_primary_and_urgent_care(
                    primary_care=PRIMARY_CARE in criteria_values,
                    urgent_care=URGENT_CARE in criteria_values,
                )
                if current_staffs is not None:
                    self.search_results = (
                        self.search_results | current_staffs
                        if self.search_results is not None
                        else current_staffs
                    )
            else:
                current_speciality_codes = (
                    self.get_speciality_codes_for_search_criteria(
                        criteria_key=criteria_key, criteria_values=criteria_values
                    )
                )
                self.speciality_codes = self.speciality_codes.union(
                    set(current_speciality_codes)
                )

                if self.speciality_codes:
                    current_staffs = self._get_staff_using_speciality_codes(
                        speciality_codes=self.speciality_codes
                    )
                    self.search_results = (
                        self.search_results | current_staffs
                        if self.search_results is not None
                        else current_staffs
                    )

        self.speciality_codes = self.speciality_codes.union(
            self.primary_care_speciality_codes
        )
        return self.search_results

    def get_staff_for_primary_and_urgent_care(self, primary_care, urgent_care):
        primary_care_staff, urgent_care_staff = None, None
        if urgent_care:
            # TODO Optimize here
            urgent_care_staff = self.default_query_set.filter(
                locations__is_urgent_care=True
            ).distinct()

        if primary_care_staff is not None and urgent_care_staff is not None:
            return primary_care_staff | urgent_care_staff

        if primary_care_staff is not None:
            return primary_care_staff

        if urgent_care_staff is not None:
            return urgent_care_staff

        return None

    def get_speciality_codes_for_search_criteria(self, criteria_key, criteria_values):
        speciality_codes = []
        if criteria_key == "speciality":
            return self._get_speciality_codes_using_speciality_search(
                search_strings=criteria_values
            )

        if criteria_key == "procedure":
            return self._get_speciality_codes_using_procedure_search(
                search_strings=criteria_values
            )

        if criteria_key == "condition":
            return self._get_speciality_codes_using_condition_search(
                search_strings=criteria_values
            )

        if criteria_key == "disease":
            return self._get_speciality_codes_using_diseases_search(
                search_strings=criteria_values
            )

        if criteria_key == "symptom":
            return self._get_speciality_codes_using_symptoms_search(
                search_strings=criteria_values
            )

        return speciality_codes

    def _get_staff_using_speciality_codes(self, speciality_codes):
        return self.default_query_set.filter(
            specialities__code__in=speciality_codes
        ).distinct()

    @classmethod
    def filter_in_or_out_age_based_speciality_codes(
        cls, speciality_codes, criteria_values
    ):
        if not criteria_values:
            return speciality_codes

        # age_choice_set = set(criteria_values)
        speciality_codes_set = set(speciality_codes)

        # filter out
        return speciality_codes_set
