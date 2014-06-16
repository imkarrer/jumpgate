import inspect
import importlib
import logging
import socket
import struct

from functools import wraps

LOG = logging.getLogger(__name__)

_driver_cache = {}


def lookup(dic, key, *keys):
    if keys:
        return lookup(dic.get(key, {}), *keys)
    return dic.get(key)


def propagate_argspec(wrapper, responder):
    if hasattr(responder, 'wrapped_argspec'):
        wrapper.wrapped_argspec = responder.wrapped_argspec
    else:
        wrapper.wrapped_argspec = inspect.getargspec(responder)


def wrap_handler_with_hooks(handler, after):
    @wraps(handler)
    def wrapped(ex, req, resp, params):
        handler(ex, req, resp, params)
        for hook in after:
            hook(req, resp)

    propagate_argspec(wrapped, handler)

    return wrapped


def import_class(canonical_name):
    segs = canonical_name.split('.')
    module_name, clazz = '.'.join(segs[0: len(segs) - 1]), segs[-1]
    module = importlib.import_module(module_name)
    class_ref = getattr(module, clazz, None)
    if class_ref is None:
        raise ImportError("%s is not defined in %s" % (clazz, module_name))
    return class_ref


def load_driver(canonical_name):
    global _driver_cache
    try:
        driver = _driver_cache.get(canonical_name)
        if driver is None:
            driver = import_class(canonical_name)
            LOG.debug("Loaded driver '%s'" % (canonical_name))
            _driver_cache[canonical_name] = driver
        return driver()
    except ImportError as e:
        LOG.error("Unable to load driver '%s'" % (canonical_name))
        raise e


# ipv4 only
def ipaddr_to_int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


# ipv4 only
def int_to_ipaddr(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


def allocation_pool_range(cidr):
    try:
        (network, subnet_len) = cidr.split('/')
        network = ipaddr_to_int(network)
        subnet_len = int(subnet_len)

        mask = ~(0xFFFFFFFF >> subnet_len)
        start_ip = network & mask

        end_ip = start_ip | ~mask
    except Exception as e:
        raise e

    return start_ip, end_ip


def get_usable_ip(gateway, cidr):
    try:
        ip_range = allocation_pool_range(cidr)
    except Exception as e:
        raise e

    gateway_int = ipaddr_to_int(gateway)
    ip_start = ip_range[0]
    ip_end = ip_range[1]

    if gateway_int > ip_start and gateway_int < ip_end:
        start = 0
        end = 0

        if (ip_start + 1) == gateway_int:
            start = ip_start + 2
            end = ip_end - 1
        elif (ip_end - 1) == gateway_int:
            start = ip_start + 1
            end = ip_end - 2
        return int_to_ipaddr(start), int_to_ipaddr(end)
    else:
        raise Exception
