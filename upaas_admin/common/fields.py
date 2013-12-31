# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from mongoengine.base import BaseField

from IPy import IP


class IPField(BaseField):
    """An IP field.

    Code from https://github.com/MongoEngine/mongoengine/pull/164
    Credits to https://github.com/helduel
    """
    def __init__(self, v=4, **kwargs):
        if v not in (4, 6):
            raise ValueError("IP version must be 4 or 6")
        self.v = v
        super(IPField, self).__init__(**kwargs)

    def __get__(self, instance, owner):
        value = super(IPField, self).__get__(instance, owner)
        if value is not None:
            value = IP(value)
        return value

    def validate(self, value):
        if value.version() != self.v:
            self.error("IP version mismatch")

    def to_mongo(self, value):
        if self.v == 4:
            return IP(value).int()
        else:
            return IP(value).strHex()

    def to_python(self, value):
        return IP(value)

    def prepare_query_value(self, op, value):
        if self.v == 4:
            return IP(value).int()
        return IP(value).strHex()


class IPv4Field(IPField):
    """An IPv4 field.
    """
    def __init__(self, **kwargs):
        super(IPv4Field, self).__init__(v=4, **kwargs)


class IPv6Field(IPField):
    """An IPv6 field.
    """
    def __init__(self, **kwargs):
        super(IPv6Field, self).__init__(v=6, **kwargs)


class IPNetworkField(BaseField):
    """An IP network field.
    """
    def __init__(self, v=4, **kwargs):
        if v not in (4, 6):
            raise ValueError("IP version must be 4 or 6")
        self.v = v
        super(IPNetworkField, self).__init__(**kwargs)

    def __get__(self, instance, owner):
        value = super(IPNetworkField, self).__get__(instance, owner)
        if value is not None:
            value = self.to_python(value)
        return value

    def validate(self, value):
        if value.version() != self.v:
            self.error("IP version mismatch")

    def to_mongo(self, value):
        value = IP(value)
        if self.v == 4:
            return {
                "net$prefix": value.prefixlen(),
                "net$lower": value[0].int(),
                "net$upper": value[-1].int(),
            }
        return {
            "net$prefix": value.prefixlen(),
            "net$lower": value[0].strHex(),
            "net$upper": value[-1].strHex(),
        }

    def to_python(self, value):
        if isinstance(value, dict):
            value = "%s/%i" % (value["net$lower"], value["net$prefix"])
        return IP(value)

    def prepare_query_value(self, op, value):
        if self.v == 4:
            value = IP(value).int()
        else:
            value = IP(value).strHex()
        if op == "contains":
            value = {
                "net$lower": {"$lte": value},
                "net$upper": {"$gte": value},
            }
        return value


class IPv4NetworkField(IPNetworkField):
    """An IPv6 network field.
    """
    def __init__(self, **kwargs):
        super(IPv4NetworkField, self).__init__(v=4, **kwargs)


class IPv6NetworkField(IPNetworkField):
    """An IPv6 network field.
    """
    def __init__(self, **kwargs):
        super(IPv6NetworkField, self).__init__(v=6, **kwargs)
