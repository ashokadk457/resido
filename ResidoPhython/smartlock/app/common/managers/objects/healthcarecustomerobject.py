from django.db.models import Manager


class HealthCareCustomerObjectManager(Manager):
    def create_healthcare_customer(self, name, **kwargs):
        healthcare_customer = self.model(
            name=name,
            logo=kwargs.get("logo", None),
            app_conf_type=kwargs.get("app_conf_type", 1),
            allow_ext_providers=kwargs.get("allow_ext_providers", True),
            url=kwargs.get("url", ""),
            max_security_question=kwargs.get("max_security_question", 10),
            code=kwargs.get("code", None),
            website=kwargs.get("website", None),
            address=kwargs.get("address", ""),
            address_1=kwargs.get("address_1", ""),
            city=kwargs.get("city", ""),
            state=kwargs.get("state", ""),
            zipcode=kwargs.get("zipcode", ""),
            contact_prefix=kwargs.get("contact_prefix", ""),
            contact_first_name=kwargs.get("contact_first_name", ""),
            contact_mi=kwargs.get("contact_mi", ""),
            contact_last_name=kwargs.get("contact_last_name", ""),
            contact_suffix=kwargs.get("contact_suffix", ""),
            work_phone=kwargs.get("work_phone", ""),
            phone=kwargs.get("phone", ""),
            fax=kwargs.get("fax", ""),
            email=kwargs.get("email", ""),
            preferred_communication_mode=kwargs.get(
                "preferred_communication_mode", "ALL"
            ),
            country_code=kwargs.get("country_code", ""),
            status=kwargs.get("status", "YES"),
            npi=kwargs.get("npi", ""),
        )
        healthcare_customer.save()
        return healthcare_customer
