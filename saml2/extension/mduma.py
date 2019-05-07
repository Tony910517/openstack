
import saml2
from saml2 import md

__author__ = 'roland'

NAMESPACE = 'urn:mace:se:swamid:metadata:uma'


class UmaAs(md.LocalizedNameType_):
    """The urn:oasis:names:tc:SAML:metadata:ui:DisplayName element """

    c_tag = 'UmaAs'
    c_namespace = NAMESPACE
    c_children = md.LocalizedNameType_.c_children.copy()
    c_attributes = md.LocalizedNameType_.c_attributes.copy()
    c_child_order = md.LocalizedNameType_.c_child_order[:]
    c_cardinality = md.LocalizedNameType_.c_cardinality.copy()


def display_name_from_string(xml_string):
    return saml2.create_class_from_xml_string(UmaAs, xml_string)

