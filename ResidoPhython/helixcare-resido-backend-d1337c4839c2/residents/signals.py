# from django.dispatch import receiver
# from django.db.models.signals import post_save, pre_save

# from notifications.managers.notificationqueue import NotificationQueueManager
# from notifications.utils import Utils
# from .models import Resident
# from .serializers import PatientSerializer
# import waffle


# @receiver(post_save, sender=Resident)
# def send_notification_for_new_registration(sender, instance, created, **kwargs):
#     if created:
#         patient = instance
#         nq_manager = NotificationQueueManager()
#         _, lang = Utils.check_notification_type(patient)
#         setting = Utils.get_tenant_notification("EMAIL", "4", lang)
#         payload = {}
#         payload["subject"] = "Welcome!!"
#         payload["message"] = (
#             "Welcome "
#             + str(instance)
#             + "! Your Patient Id is "
#             + str(instance.patient_id)
#         )
#         if instance.email:
#             nq_manager.create_object(
#                 notification_setting=setting, user=patient, payload=payload
#             )
#         patientJSON = PatientSerializer(patient).data
#         # _send_patient_to_commonwell(patientJSON)


# @receiver(pre_save, sender=Resident)
# def pre_save_patient(sender, instance, **kwargs):
#     if instance.id is None:
#         pass
#     else:
#         previous = Resident.objects.filter(id=instance.id).first()
#         if (
#             previous and previous.middle_name != instance.middle_name
#         ):  # todo add support for more fields
#             patientJSON = PatientSerializer(instance).data
#             # _send_patient_to_commonwell(patientJSON)


# def _send_patient_to_commonwell(patient):
#     if patient and waffle.switch_is_active("commonwell_sync"):
#         respCreatePatient = CommonWellAPI().create_patient(patient)
#         respDocs = CommonWellAPI().create_task(patient, "doc", 1)
#         return (respCreatePatient, respDocs)
