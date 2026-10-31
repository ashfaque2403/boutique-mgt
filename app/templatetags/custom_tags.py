# app/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def average(queryset, field):
    values = queryset.values_list(field, flat=True)
    if not values:
        return 0
    return sum(values) / len(values)
