# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Red Hat, Inc.
#
# Authors:
# Thomas Woerner <twoerner@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# force use of pygobject3 in python-slip
from gi.repository import GObject
import sys
sys.modules['gobject'] = GObject

import dbus
import dbus.service
import slip.dbus
import slip.dbus.service

from firewall.config import *
from firewall.dbus_utils import dbus_to_python
from firewall.config.dbus import *
from firewall.core.fw import Firewall
from firewall.core.io.icmptype import IcmpType
from firewall.core.logger import log
from firewall.server.decorators import *
from firewall.errors import *

############################################################################
#
# class FirewallDConfig
#
############################################################################

class FirewallDConfigIcmpType(slip.dbus.service.Object):
    """FirewallD main class"""

    persistent = True
    """ Make FirewallD persistent. """
    default_polkit_auth_required = PK_ACTION_CONFIG
    """ Use PK_ACTION_INFO as a default """

    @handle_exceptions
    def __init__(self, parent, config, icmptype, id, *args, **kwargs):
        super(FirewallDConfigIcmpType, self).__init__(*args, **kwargs)
        self.parent = parent
        self.config = config
        self.obj = icmptype
        self.id = id
        self.path = args[0]

    @dbus_handle_exceptions
    def __del__(self):
        pass

    @dbus_handle_exceptions
    def unregister(self):
        self.remove_from_connection()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # P R O P E R T I E S

    @dbus_service_method(dbus.PROPERTIES_IFACE, in_signature='ss',
                         out_signature='v')
    @dbus_handle_exceptions
    def Get(self, interface_name, property_name, sender=None):
        # get a property
        interface_name = dbus_to_python(interface_name)
        property_name = dbus_to_python(property_name)
        log.debug1("config.icmptype.%d.Get('%s', '%s')", self.id,
                   interface_name, property_name)

        if interface_name != DBUS_INTERFACE_CONFIG_ICMPTYPE:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.UnknownInterface: "
                "FirewallD does not implement %s" % interface_name)

        if property_name == "name":
            return self.obj.name
        elif property_name == "filename":
            return self.obj.filename
        elif property_name == "path":
            return self.obj.path
        elif property_name == "default":
            return self.obj.default
        elif property_name == "builtin":
            return self.config.is_builtin_icmptype(self.obj)
        else:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.AccessDenied: "
                "Property '%s' isn't exported (or may not exist)" % \
                    property_name)

    @dbus_service_method(dbus.PROPERTIES_IFACE, in_signature='s',
                         out_signature='a{sv}')
    @dbus_handle_exceptions
    def GetAll(self, interface_name, sender=None):
        interface_name = dbus_to_python(interface_name)
        log.debug1("config.icmptype.%d.GetAll('%s')", self.id, interface_name)

        if interface_name != DBUS_INTERFACE_CONFIG_ICMPTYPE:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.UnknownInterface: "
                "FirewallD does not implement %s" % interface_name)

        return {
            'name': self.obj.name,
            'filename': self.obj.filename,
            'path': self.obj.path,
            'default': self.obj.default,
        }

    @slip.dbus.polkit.require_auth(PK_ACTION_CONFIG)
    @dbus_service_method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    @dbus_handle_exceptions
    def Set(self, interface_name, property_name, new_value, sender=None):
        interface_name = dbus_to_python(interface_name)
        property_name = dbus_to_python(property_name)
        new_value = dbus_to_python(new_value)
        log.debug1("config.icmptype.%d.Set('%s', '%s', '%s')", self.id,
                   interface_name, property_name, new_value)
        self.parent.accessCheck(sender)

        if interface_name != DBUS_INTERFACE_CONFIG_ICMPTYPE:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.UnknownInterface: "
                "FirewallD does not implement %s" % interface_name)

        raise dbus.exceptions.DBusException(
            "org.freedesktop.DBus.Error.AccessDenied: "
            "Property '%s' is not settable" % property_name)

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface_name, changed_properties,
                          invalidated_properties):
        pass

    # S E T T I N G S

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, out_signature=IcmpType.DBUS_SIGNATURE)
    @dbus_handle_exceptions
    def getSettings(self, sender=None):
        """get settings for icmptype
        """
        log.debug1("config.icmptype.%d.getSettings()", self.id)
        return self.config.get_icmptype_config(self.obj)

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature=IcmpType.DBUS_SIGNATURE)
    @dbus_handle_exceptions
    def update(self, settings, sender=None):
        """update settings for icmptype
        """
        settings = dbus_to_python(settings)
        log.debug1("config.icmptype.%d.update('...')", self.id)
        self.parent.accessCheck(sender)
        self.obj = self.config.set_icmptype_config(self.obj, settings)
        self.Updated(self.obj.name)

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE)
    @dbus_handle_exceptions
    def loadDefaults(self, sender=None):
        """load default settings for builtin icmptype
        """
        log.debug1("config.icmptype.%d.loadDefaults()", self.id)
        self.parent.accessCheck(sender)
        self.obj = self.config.load_icmptype_defaults(self.obj)
        self.Updated(self.obj.name)

    @dbus.service.signal(DBUS_INTERFACE_CONFIG_ICMPTYPE, signature='s')
    @dbus_handle_exceptions
    def Updated(self, name):
        log.debug1("config.icmptype.%d.Updated('%s')" % (self.id, name))

    # R E M O V E

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE)
    @dbus_handle_exceptions
    def remove(self, sender=None):
        """remove icmptype
        """
        log.debug1("config.icmptype.%d.removeIcmpType()", self.id)
        self.parent.accessCheck(sender)
        self.config.remove_icmptype(self.obj)
        self.parent.removeIcmpType(self.obj)

    @dbus.service.signal(DBUS_INTERFACE_CONFIG_ICMPTYPE, signature='s')
    @dbus_handle_exceptions
    def Removed(self, name):
        log.debug1("config.icmptype.%d.Removed('%s')" % (self.id, name))

    # R E N A M E

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='s')
    @dbus_handle_exceptions
    def rename(self, name, sender=None):
        """rename icmptype
        """
        name = dbus_to_python(name)
        log.debug1("config.icmptype.%d.rename('%s')", self.id, name)
        self.parent.accessCheck(sender)
        new_icmptype = self.config.rename_icmptype(self.obj, name)
        self.parent._addIcmpType(new_icmptype)
        self.parent.removeIcmpType(self.obj)
        self.Renamed(name)

    @dbus.service.signal(DBUS_INTERFACE_CONFIG_ICMPTYPE, signature='s')
    @dbus_handle_exceptions
    def Renamed(self, name):
        log.debug1("config.icmptype.%d.Renamed('%s')" % (self.id, name))

    # version

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, out_signature='s')
    @dbus_handle_exceptions
    def getVersion(self, sender=None):
        log.debug1("config.icmptype.%d.getVersion()", self.id)
        return self.getSettings()[0]

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='s')
    @dbus_handle_exceptions
    def setVersion(self, version, sender=None):
        version = dbus_to_python(version, str)
        log.debug1("config.icmptype.%d.setVersion('%s')", self.id, version)
        self.parent.accessCheck(sender)
        settings = list(self.getSettings())
        settings[0] = version
        self.update(settings)

    # short

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, out_signature='s')
    @dbus_handle_exceptions
    def getShort(self, sender=None):
        log.debug1("config.icmptype.%d.getShort()", self.id)
        return self.getSettings()[1]

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='s')
    @dbus_handle_exceptions
    def setShort(self, short, sender=None):
        short = dbus_to_python(short, str)
        log.debug1("config.icmptype.%d.setShort('%s')", self.id, short)
        self.parent.accessCheck(sender)
        settings = list(self.getSettings())
        settings[1] = short
        self.update(settings)

    # description

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, out_signature='s')
    @dbus_handle_exceptions
    def getDescription(self, sender=None):
        log.debug1("config.icmptype.%d.getDescription()", self.id)
        return self.getSettings()[2]

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='s')
    @dbus_handle_exceptions
    def setDescription(self, description, sender=None):
        description = dbus_to_python(description, str)
        log.debug1("config.icmptype.%d.setDescription('%s')", self.id,
                   description)
        self.parent.accessCheck(sender)
        settings = list(self.getSettings())
        settings[2] = description
        self.update(settings)

    # destination

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, out_signature='as')
    @dbus_handle_exceptions
    def getDestinations(self, sender=None):
        log.debug1("config.icmptype.%d.getDestinations()", self.id)
        return sorted(self.getSettings()[3])

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='as')
    @dbus_handle_exceptions
    def setDestinations(self, destinations, sender=None):
        destinations = dbus_to_python(destinations, list)
        log.debug1("config.icmptype.%d.setDestinations('[%s]')", self.id,
                   ",".join(destinations))
        self.parent.accessCheck(sender)
        settings = list(self.getSettings())
        settings[3] = destinations
        self.update(settings)

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='s')
    @dbus_handle_exceptions
    def addDestination(self, destination, sender=None):
        destination = dbus_to_python(destination, str)
        log.debug1("config.icmptype.%d.addDestination('%s')", self.id,
                   destination)
        self.parent.accessCheck(sender)
        settings = list(self.getSettings())
        if destination in settings[3]:
            raise FirewallError(ALREADY_ENABLED, destination)
        settings[3].append(destination)
        self.update(settings)

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='s')
    @dbus_handle_exceptions
    def removeDestination(self, destination, sender=None):
        destination = dbus_to_python(destination, str)
        log.debug1("config.icmptype.%d.removeDestination('%s')", self.id,
                   destination)
        self.parent.accessCheck(sender)
        settings = list(self.getSettings())
        if settings[3]:
            if destination not in settings[3]:
                raise FirewallError(NOT_ENABLED, destination)
            else:
                settings[3].remove(destination)
        else:  # empty means all
            settings[3] = list(set(['ipv4', 'ipv6']) -
                               set([destination]))
        print "settings[3]:", settings[3]
        self.update(settings)

    @dbus_service_method(DBUS_INTERFACE_CONFIG_ICMPTYPE, in_signature='s',
                         out_signature='b')
    @dbus_handle_exceptions
    def queryDestination(self, destination, sender=None):
        destination = dbus_to_python(destination, str)
        log.debug1("config.icmptype.%d.queryDestination('%s')", self.id,
                   destination)
        settings = self.getSettings()
        # empty means all
        return (not settings[3] or
                destination in settings[3])
