# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Red Hat, Inc.
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
#

import xml.sax as sax
import os
import io
import shutil

from firewall.config import ETC_FIREWALLD
from firewall.errors import *
from firewall.functions import checkProtocol, check_address, \
                               checkIPnMask, checkIP6nMask, u2b_if_py2
from firewall.core.io.io_object import *
from firewall.core.logger import log

class Service(IO_Object):
    IMPORT_EXPORT_STRUCTURE = (
        ( "version",  "" ),              # s
        ( "short", "" ),                 # s
        ( "description", "" ),           # s
        ( "ports", [ ( "", "" ), ], ),   # a(ss)
        ( "modules", [ "", ], ),         # as
        ( "destination", { "": "", }, ), # a{ss}
        )
    DBUS_SIGNATURE = '(sssa(ss)asa{ss})'
    ADDITIONAL_ALNUM_CHARS = [ "_", "-" ]
    PARSER_REQUIRED_ELEMENT_ATTRS = {
        "short": None,
        "description": None,
        "service": None,
        }
    PARSER_OPTIONAL_ELEMENT_ATTRS = {
        "service": [ "name", "version" ],
        "port": [ "port", "protocol" ],
        "module": [ "name" ],
        "destination": [ "ipv4", "ipv6" ],
        }

    def __init__(self):
        super(Service, self).__init__()
        self.version = ""
        self.short = ""
        self.description = ""
        self.ports = [ ]
        self.modules = [ ]
        self.destination = { }

    def cleanup(self):
        self.version = ""
        self.short = ""
        self.description = ""
        del self.ports[:]
        del self.modules[:]
        self.destination.clear()

    def encode_strings(self):
        """ HACK. I haven't been able to make sax parser return
            strings encoded (because of python 2) instead of in unicode.
            Get rid of it once we throw out python 2 support."""
        self.version = u2b_if_py2(self.version)
        self.short = u2b_if_py2(self.short)
        self.description = u2b_if_py2(self.description)
        self.ports = [(u2b_if_py2(po),u2b_if_py2(pr)) for (po,pr) in self.ports]
        self.modules = [u2b_if_py2(m) for m in self.modules]
        self.destination = {u2b_if_py2(k):u2b_if_py2(v) for k,v in self.destination.items()}

    def _check_config(self, config, item):
        if item == "ports":
            for port in config:
                if port[0] != "":
                    check_port(port[0])
                    check_protocol(port[1])
                else:
                    # only protocol
                    if not checkProtocol(port[1]):
                        raise FirewallError(INVALID_PROTOCOL, port[1])

        elif item == "destination":
            for destination in config:
                if destination not in [ "ipv4", "ipv6" ]:
                    raise FirewallError(INVALID_DESTINATION, destination)
                if not check_address(destination, config[destination]):
                    raise FirewallError(INVALID_ADDR, config[destination])

        elif item == "modules":
            for module in config:
                if not module.startswith("nf_conntrack_"):
                    raise FirewallError(INVALID_MODULE, module)
                elif len(module.replace("nf_conntrack_", "")) < 1:
                    raise FirewallError(INVALID_MODULE, module)

# PARSER

class service_ContentHandler(IO_Object_ContentHandler):
    def startElement(self, name, attrs):
        self.item.parser_check_element_attrs(name, attrs)
        if name == "service":
            if "name" in attrs:
                log.warning("Ignoring deprecated attribute name='%s'" % 
                            attrs["name"])
            if "version" in attrs:
                self.item.version = attrs["version"]
        elif name == "short":
            pass
        elif name == "description":
            pass
        elif name == "port":
            self.item.ports.append((attrs["port"], attrs["protocol"]))
        elif name == "destination":
            for x in [ "ipv4", "ipv6" ]:
                if x in attrs:
                    s = attrs[x]
                    if x == "ipv4" and not checkIPnMask(s):
                        raise FirewallError(INVALID_DESTINATION, s)
                    if x == "ipv6" and not checkIP6nMask(s):
                        raise FirewallError(INVALID_DESTINATION, s)
                    self.item.destination[x] = attrs[x]
        elif name == "module":
            self.item.modules.append(attrs["name"])

def service_reader(filename, path):
    service = Service()
    if not filename.endswith(".xml"):
        raise FirewallError(INVALID_NAME, filename)
    service.name = filename[:-4]
    service.check_name(service.name)
    service.filename = filename
    service.path = path
    service.default = False if path.startswith(ETC_FIREWALLD) else True
    handler = service_ContentHandler(service)
    parser = sax.make_parser()
    parser.setContentHandler(handler)
    name = "%s/%s" % (path, filename)
    with open(name, "r") as f:
        parser.parse(f)
    del handler
    del parser
    if PY2:
        service.encode_strings()
    return service

def service_writer(service, path=None):
    _path = path if path else service.path

    if service.filename:
        name = "%s/%s" % (_path, service.filename)
    else:
        name = "%s/%s.xml" % (_path, service.name)

    if os.path.exists(name):
        try:
            shutil.copy2(name, "%s.old" % name)
        except Exception as msg:
            raise IOError("Backup of '%s' failed: %s" % (name, msg))

    f = io.open(name, mode='wt', encoding='UTF-8')
    handler = IO_Object_XMLGenerator(f)
    handler.startDocument()

    # start service element
    attrs = {}
    if service.version and service.version != "":
        attrs["version"] = service.version
    handler.startElement("service", attrs)
    handler.ignorableWhitespace("\n")

    # short
    if service.short and service.short != "":
        handler.ignorableWhitespace("  ")
        handler.startElement("short", { })
        handler.characters(service.short)
        handler.endElement("short")
        handler.ignorableWhitespace("\n")

    # description
    if service.description and service.description != "":
        handler.ignorableWhitespace("  ")
        handler.startElement("description", { })
        handler.characters(service.description)
        handler.endElement("description")
        handler.ignorableWhitespace("\n")

    # ports
    for port in service.ports:
        handler.ignorableWhitespace("  ")
        handler.simpleElement("port", { "port": port[0], "protocol": port[1] })
        handler.ignorableWhitespace("\n")

    # modules
    for module in service.modules:
        handler.ignorableWhitespace("  ")
        handler.simpleElement("module", { "name": module })
        handler.ignorableWhitespace("\n")

    # destination
    if len(service.destination) > 0:
        handler.ignorableWhitespace("  ")
        handler.simpleElement("destination", service.destination)
        handler.ignorableWhitespace("\n")

    # end service element
    handler.endElement('service')
    handler.ignorableWhitespace("\n")
    handler.endDocument()
    f.close()
    del handler
