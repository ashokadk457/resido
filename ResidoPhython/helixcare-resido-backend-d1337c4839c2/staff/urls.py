from django.urls import re_path

import staff.apiviews

urlpatterns = (
    re_path(
        r"^api/v1/staff$",
        staff.apiviews.StaffListCreate.as_view(),
        name="staff_list_create",
    ),
    re_path(
        r"^api/v1/staff-groups$",
        staff.apiviews.StaffGroupsListCreate.as_view(),
        name="staff_groups_list_create",
    ),
    re_path(
        r"^api/v1/staff-groups/(?P<pk>[0-9a-zA-Z\-]+)$",
        staff.apiviews.StaffGroupsGetUpdate.as_view(),
        name="staff_groups_list_create",
    ),
    re_path(
        r"^api/v1/staff-count$",
        staff.apiviews.StaffCountView.as_view(),
        name="staff_count_view",
    ),
    re_path(
        r"^api/v1/staff-resend-invitations$",
        staff.apiviews.ResendInviteAPIView.as_view(),
        name="resent_invite_staff_action",
    ),
    re_path(
        r"^api/v1/staff/(?P<pk>[0-9a-zA-Z\-]+)$",
        staff.apiviews.StaffDetailAPIView.as_view(),
        name="providers_details_internal",
    ),
)
