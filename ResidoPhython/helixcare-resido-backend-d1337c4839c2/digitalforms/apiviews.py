import django_filters
from rest_framework import status, filters
from rest_framework.views import APIView
from common.mixins import (
    StandardListCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
)
from common.response import StandardAPIResponse
from django_filters.rest_framework import DjangoFilterBackend
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from digitalforms.models import (
    Form,
    Category,
    ApprovalTeam,
    FormSection,
    FormField,
    FormRow,
    Field,
    WidgetField,
    Widget,
    WidgetRow,
    FormVersion,
    FormReview,
    UserResponse,
)
from digitalforms.serializers import (
    FormCreateSerializer,
    FormListSerializer,
    CategorySerializer,
    ApprovalTeamSerializer,
    FormSectionDetailSerializer,
    FormSectionSerializer,
    FormRowSerializer,
    UserResponseSerializer,
    FormFieldSerializer,
    WidgetFieldSerializer,
    WidgetRowSerializer,
    WidgetSerializer,
    FieldSerializer,
    FormVersionSerializer,
    FormReviewSerializer,
)


class FieldListCreateView(StandardListCreateAPIMixin):
    serializer_class = FieldSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = Field.objects.all()
    entity = "Field"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ("field_type",)
    filterset_fields = (
        "field_type",
        "active",
    )
    ordering = (
        "created_on",
        "field_type",
    )


class FieldGetUpdateView(StandardRetrieveUpdateAPIMixin):
    serializer_class = FieldSerializer
    permission_classes = [HelixUserBasePermission]
    queryset = Field.objects.all()
    entity = "Field"


class CategoryListCreateView(StandardListCreateAPIMixin):
    serializer_class = CategorySerializer
    permission_classes = [HelixUserBasePermission]
    queryset = Category.objects.all()
    entity = "Category"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ("name",)
    filterset_fields = ("active",)
    ordering = (
        "created_on",
        "name",
    )


class CategoryGetUpdateView(StandardRetrieveUpdateAPIMixin):
    serializer_class = CategorySerializer
    permission_classes = [HelixUserBasePermission]
    queryset = Category.objects.all()
    entity = "Category"


class WidgetListCreateView(StandardListCreateAPIMixin):
    serializer_class = WidgetSerializer
    permission_classes = [HelixUserBasePermission]
    queryset = Widget.objects.all()
    entity = "Widget"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ("name",)
    filterset_fields = ("active",)
    ordering = (
        "created_on",
        "name",
    )


class WidgetGetUpdateView(StandardRetrieveUpdateAPIMixin):
    serializer_class = WidgetSerializer
    permission_classes = [HelixUserBasePermission]
    queryset = Widget.objects.all()
    entity = "Widget"


class WidgetRowListCreateView(StandardListCreateAPIMixin):
    serializer_class = WidgetRowSerializer
    permission_classes = [HelixUserBasePermission]
    entity = "WidgetRow"

    def get_queryset(self):
        widget = self.kwargs.get("widget_id")
        return WidgetRow.objects.filter(widget=widget).order_by("position")

    def create(self, request, *args, **kwargs):
        request.data["widget_id"] = kwargs.get("widget_id")
        return super().create(request, *args, **kwargs)


class WidgetRowGetUpdateView(StandardRetrieveUpdateAPIMixin):
    serializer_class = WidgetRowSerializer
    permission_classes = [HelixUserBasePermission]
    entity = "WidgetRow"

    def get_queryset(self):
        widget = self.kwargs.get("widget_id")
        return WidgetRow.objects.filter(widget=widget).order_by("position")


class WidgetFieldListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = WidgetFieldSerializer
    # entity = "WidgetField"

    def get_queryset(self):
        widget = self.kwargs.get("widget_id")
        widget_row = self.kwargs.get("widget_row_id")
        return WidgetField.objects.filter(row__widget=widget, row=widget_row).order_by(
            "position"
        )

    def create(self, request, *args, **kwargs):
        request.data["row_id"] = kwargs.get("widget_row_id")
        return super().create(request, *args, **kwargs)


class WidgetFieldGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = WidgetFieldSerializer
    # entity = "WidgetField"

    def get_queryset(self):
        widget = self.kwargs.get("widget_id")
        widget_row = self.kwargs.get("widget_row_id")
        return WidgetField.objects.filter(row__widget=widget, row=widget_row).order_by(
            "position"
        )


class ApprovalTeamListCreateView(StandardListCreateAPIMixin):
    serializer_class = ApprovalTeamSerializer
    permission_classes = [HelixUserBasePermission]
    queryset = ApprovalTeam.objects.all()
    # entity = "ApprovalTeam"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ("name",)
    filterset_fields = ("active",)
    ordering = (
        "created_on",
        "name",
    )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return StandardAPIResponse(
            data=serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ApprovalTeamGetUpdateView(StandardRetrieveUpdateAPIMixin):
    serializer_class = ApprovalTeamSerializer
    permission_classes = [HelixUserBasePermission]
    queryset = ApprovalTeam.objects.all()
    # entity = "ApprovalTeam"


class FormFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter(
        field_name="versions__status", lookup_expr="exact"
    )

    class Meta:
        model = Form
        fields = (
            "status",
            "active",
            "category",
        )


class FormListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    queryset = (
        Form.objects.all().prefetch_related("versions").select_related("category")
    )
    # entity = "Form"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = (
        "name",
        "category__name",
    )
    filterset_class = FormFilterSet
    ordering = (
        "created_on",
        "name",
        "status",
        "category",
    )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FormCreateSerializer
        return FormListSerializer


class FormGetUpdateView(StandardRetrieveUpdateAPIMixin):
    serializer_class = FormCreateSerializer
    permission_classes = [HelixUserBasePermission]
    queryset = (
        Form.objects.all().prefetch_related("versions").select_related("category")
    )
    # entity = "Form"


class FormVersionGetUpdateView(StandardRetrieveUpdateAPIMixin):
    serializer_class = FormVersionSerializer
    permission_classes = [HelixUserBasePermission]
    queryset = FormVersion.objects.all()
    # entity = "FormVersion"


class DigitalFormsCountView(APIView):
    permission_classes = [HelixUserBasePermission]

    def get(self, request, *args, **kwargs):
        cat_count = Category.objects.all().count()
        at_count = ApprovalTeam.objects.all().count()
        drf_count = Form.objects.filter(versions__status="draft").count()
        in_rvw_count = Form.objects.filter(versions__status="in_review").count()
        app_count = Form.objects.filter(versions__status="approved").count()
        rjc_count = Form.objects.filter(versions__status="rejected").count()
        data = {
            "categories": cat_count,
            "approval_team": at_count,
            "draft": drf_count,
            "in_review": in_rvw_count,
            "rejected": rjc_count,
            "approved": app_count,
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class FormSectionListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    # entity = "FormSection"

    def get_serializer_class(self):
        if self.request.query_params.get("detailed") == "true":
            return FormSectionDetailSerializer
        return FormSectionSerializer

    def create(self, request, *args, **kwargs):
        request.data["form_version_id"] = kwargs.get("form_version_id")
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        queryset = FormSection.objects.filter(form_version=form_version)
        if self.request.query_params.get("detailed") == "true":
            queryset = queryset.prefetch_related(
                "form_rows", "form_rows__form_fields", "form_rows__form_fields__field"
            )
        return queryset.order_by("position")


class FormSectionGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    # entity = "FormSection"

    def get_serializer_class(self):
        if self.request.query_params.get("detailed") == "true":
            return FormSectionDetailSerializer
        return FormSectionSerializer

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        queryset = FormSection.objects.filter(form_version=form_version)
        if self.request.query_params.get("detailed") == "true":
            queryset = queryset.prefetch_related(
                "form_rows", "form_rows__form_fields", "form_rows__form_fields__field"
            )
        return queryset.order_by("position")


class FormRowListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = FormRowSerializer
    # entity = "FormRow"

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        section = self.kwargs.get("form_section_id")
        return FormRow.objects.filter(
            section__form_version=form_version, section=section
        ).order_by("position")

    def create(self, request, *args, **kwargs):
        request.data["section_id"] = kwargs.get("form_section_id")
        return super().create(request, *args, **kwargs)


class FormRowGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = FormRowSerializer
    # entity = "FormRow"

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        section = self.kwargs.get("form_section_id")
        return FormRow.objects.filter(
            section__form_version=form_version, section=section
        ).order_by("position")


class FormFieldListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = FormFieldSerializer
    # entity = "FormField"

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        section = self.kwargs.get("form_section_id")
        row = self.kwargs.get("form_row_id")
        return FormField.objects.filter(
            row__section__form_version=form_version, row__section=section, row=row
        ).order_by("position")

    def create(self, request, *args, **kwargs):
        request.data["row_id"] = kwargs.get("form_row_id")
        return super().create(request, *args, **kwargs)


class FormFieldGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = FormFieldSerializer
    # entity = "FormField"

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        section = self.kwargs.get("form_section_id")
        row = self.kwargs.get("form_row_id")
        return FormField.objects.filter(
            row__section__form_version=form_version, row__section=section, row=row
        ).order_by("position")


class FormReviewListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = FormReviewSerializer
    # entity = "FormReview"

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        return FormReview.objects.filter(form_version=form_version).order_by(
            "sequence_number"
        )

    def create(self, request, *args, **kwargs):
        request.data["form_version_id"] = kwargs.get("form_version_id")
        return super().create(request, *args, **kwargs)


class FormReviewGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    serializer_class = FormReviewSerializer
    # entity = "FormReview"

    def get_queryset(self):
        form_version = self.kwargs.get("form_version_id")
        return FormReview.objects.filter(form_version=form_version).order_by(
            "sequence_number"
        )


class UserResponseListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = UserResponseSerializer
    # entity = "UserResponse"
    allowed_methods_to_resident = {"get": True, "post": True}
    queryset = UserResponse.objects.for_current_user()
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__date_of_birth",
    )
    filterset_fields = (
        "form_version",
        "active",
        "user",
    )
    ordering = (
        "created_on",
        "updated_on",
        "active",
    )

    def create(self, request, *args, **kwargs):
        request.data["user_id"] = request.user.id
        return super().create(request, *args, **kwargs)


class UserResponseGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = UserResponseSerializer
    # entity = "UserResponse"
    allowed_methods_to_resident = {"get": True, "put": True}
    queryset = UserResponse.objects.for_current_user()

    def patch(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request=request)
