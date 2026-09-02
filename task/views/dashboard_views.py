from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from task.services.dashboard_service import DashboardService
from task.utils.response.handlers import (
    success_response,
    bad_request_response,
    unauthorized_response,
)


def index_view(request):
    """Render main web application dashboard single page interface."""
    return render(request, "index.html")


@require_http_methods(["GET"])
def api_dashboard(request):
    """API endpoint for fetching current user's assigned tasks dashboard."""
    if not request.user.is_authenticated:
        return unauthorized_response()

    success, msg, detail_msg, dashboard_data = DashboardService.get_user_dashboard_data(request.user)
    if success:
        return success_response(data=dashboard_data, message=msg)
    return bad_request_response(message=detail_msg)
