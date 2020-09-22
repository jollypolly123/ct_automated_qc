from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name='in_group')
def in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
