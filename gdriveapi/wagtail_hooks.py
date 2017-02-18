from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.whitelist import attribute_rule

@hooks.register('construct_whitelister_element_rules')
def whitelister_element_rules():
    return {
        'p': attribute_rule({'style': True}),
        'span': attribute_rule({'style': True}),
    }
