from django.db.models import Manager


class PracticeLocationManager(Manager):
    @classmethod
    def get_all_trimmed_locations(cls, search=None):
        from locations.models import Location

        raw_locations = (
            Location.objects.for_current_user()
            .select_related("health_center")
            .values("id", "name", "address", "health_center__id", "health_center__name")
        )
        if search:
            raw_locations = raw_locations.filter(health_center__name__icontains=search)
        raw_locations = list(raw_locations)

        health_center_locations_map = {}
        for rl in raw_locations:
            if rl["health_center__id"] not in health_center_locations_map:
                health_center_locations_map[rl["health_center__id"]] = []
            health_center_locations_map[rl["health_center__id"]].append(rl)

        return [
            {
                "health_center_id": rls[0]["health_center__id"],
                "health_center_name": rls[0]["health_center__name"],
                "practice_locations": [
                    {
                        "practice_location_id": rl["id"],
                        "practice_location_name": rl["name"],
                        "practice_location_address": rl["address"],
                    }
                    for rl in rls
                ],
            }
            for rls in health_center_locations_map.values()
        ]
