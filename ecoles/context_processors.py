def school(request):
    return {
        "school": getattr(request, "school", None),
        "staff": getattr(request, "staff", None),
        "current_year": getattr(request, "year", None),
    }
