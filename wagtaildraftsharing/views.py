import uuid
from datetime import timezone

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.timezone import is_aware, make_aware, timedelta
from django.utils.timezone import now as timezone_now
from django.views.generic import CreateView
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.views.generic.preview import PreviewRevision
from wagtail.log_actions import log
from wagtail.models import Page, Revision

from wagtaildraftsharing.actions import WAGTAILDRAFTSHARING_CREATE_SHARING_LINK
from wagtaildraftsharing.forms import CreateWagtaildraftsharingLinkForm
from wagtaildraftsharing.models import WagtaildraftsharingLink

from . import settings as draftsharing_settings

max_age = draftsharing_settings.WAGTAIL_DRAFTSHARING_MAX_AGE


def _tz_aware_utc_now():
    now = timezone_now()
    # Depending on your version of Django and/or setting.TZ_NOW, timezone_now()
    # may not actually be TZ aware, but we always want it to be for these links
    if not is_aware(now):
        now = make_aware(now, timezone.utc)
    return now


class SharingLinkView(PreviewRevision):
    def setup(self, request, *args, **kwargs):
        key = kwargs.pop("key")
        now = _tz_aware_utc_now()

        sharing_link = get_object_or_404(
            WagtaildraftsharingLink,
            key=key,
            is_active=True,
        )
        if sharing_link.active_until and sharing_link.active_until < now:
            sharing_link.is_active = False
            sharing_link.save(update_fields=["is_active"])
            raise Http404

        revision_id = sharing_link.revision_id
        page_id = get_object_or_404(Revision, id=revision_id).object_id
        return super().setup(request, *args, page_id, revision_id, **kwargs)

    def get_object(self):
        return get_object_or_404(Page, id=self.pk).specific


@method_decorator(user_passes_test(user_has_any_page_permission), name="dispatch")
class CreateSharingLinkView(CreateView):
    model = WagtaildraftsharingLink
    form_class = CreateWagtaildraftsharingLinkForm

    def form_valid(self, form):
        revision = form.cleaned_data["revision"]
        key = uuid.uuid4()
        if max_age > 0:
            active_until = _tz_aware_utc_now() + timedelta(seconds=max_age)
        else:
            active_until = None
        sharing_link, created = WagtaildraftsharingLink.objects.get_or_create(
            revision=revision,
            defaults={
                "key": key,
                "created_by": self.request.user,
                "active_until": active_until,
            },
        )
        if created:
            log(
                instance=revision.content_object,
                action=WAGTAILDRAFTSHARING_CREATE_SHARING_LINK,
                user=self.request.user,
                revision=revision,
                data={"revision": revision.id},
            )
        return JsonResponse({"url": sharing_link.url})

    def form_invalid(self, form):
        return JsonResponse({"errors": form.errors}, status=400)
