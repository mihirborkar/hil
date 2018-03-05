"""Client support for switch related api calls."""
import json
from hil.client.base import ClientBase
from hil.client.base import check_reserved_chars


BROCADE = 'http://schema.massopencloud.org/haas/v0/switches/brocade'
POWERCONNECT_55XX = 'http://schema.massopencloud.org/haas/v0/switches/powerconnect55xx'
NEXUS = 'http://schema.massopencloud.org/haas/v0/switches/nexus'
DELL_NOS9 = 'http://schema.massopencloud.org/haas/v0/switches/dellnos9'
DELL_N3000 = 'http://schema.massopencloud.org/haas/v0/switches/delln3000'
MOCK = 'http://schema.massopencloud.org/haas/v0/switches/mock'

known_types = {
    NEXUS: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'dummy_vlan': basestring,
    }),
    DELL_N3000: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'dummy_vlan': basestring,
    }),
    DELL_NOS9: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'interface_type': basestring,
    }),
    BROCADE: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'interface_type': basestring,
    }),
    POWERCONNECT_55XX: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
    }),
    MOCK: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
    }),
}

class Switch(ClientBase):
    """Consists of calls to query and manipulate node related

    objects and relations.
    """

    def list(self):
        """List all nodes that HIL manages """
        url = self.object_url('/switches')
        return self.check_response(self.httpClient.request("GET", url))

    def register(self, switch, subtype, *args):
        """Registers a switch with name <switch> and
        model <subtype> , and relevant arguments  in <*args>
        """
#       It is assumed that the HIL administrator is aware of
#       of the switches HIL will control and has read the
#       HIL documentation to use appropriate flags to register
#       it with HIL.
        switch_api = "http://schema.massopencloud.org/haas/v0/switches/" + subtype
        if switch_api in known_types:
            try:
                known_types[switch_api].validate(args)
            except:
                SchemaError("Bad Request")
        if subtype == "nexus" or subtype == "delln3000":
            if len(args) == 4:
                switchinfo = {
                    "type": switch_api + subtype,
                    "hostname": args[0],
                    "username": args[1],
                    "password": args[2],
                    "dummy_vlan": args[3]}
            else:
                raise Exception('ERROR: subtype ' + subtype +
                                ' requires exactly 4 arguments\n' +
                                '<hostname> <username> <password>' +
                                '<dummy_vlan_no>')
        elif subtype == "mock":
            if len(args) == 3:
                switchinfo = {"type": switch_api + subtype,
                              "hostname": args[0],
                              "username": args[1], "password": args[2]}
            else:
                raise Exception('ERROR: subtype ' + subtype +
                                ' requires exactly 3 arguments\n' +
                                ' <hostname> <username> <password>')
        elif subtype == "powerconnect55xx":
            if len(args) == 3:
                switchinfo = {"type": switch_api + subtype,
                              "hostname": args[0],
                              "username": args[1], "password": args[2]}
            else:
                raise Exception('ERROR: subtype ' + subtype +
                                ' requires exactly 3 arguments\n' +
                                ' <hostname> <username> <password>')
        elif subtype == "brocade" or "dellnos9":
            if len(args) == 4:
                switchinfo = {"type": switch_api + subtype,
                              "hostname": args[0],
                              "username": args[1], "password": args[2],
                              "interface_type": args[3]}
            else:
                raise Exception('ERROR: subtype ' + subtype +
                                ' requires exactly 4 arguments\n' +
                                '<hostname> <username> <password> ' +
                                '<interface_type>' +
                                'NOTE: interface_type refers ' +
                                'to the speed of the switchports ' +
                                'ex. TenGigabitEthernet, ' +
                                'etc.')
        else:
            raise Exception('ERROR: Invalid subtype supplied')
        url = self.object_url('switch', switch)
        payload = json.dumps(switchinfo)
        return self.check_response(
                self.httpClient.request("PUT", url, data=payload)
                )

    @check_reserved_chars()
    def delete(self, switch):
        """Deletes the switch named <switch>."""
        url = self.object_url('switch', switch)
        return self.check_response(self.httpClient.request("DELETE", url))

    @check_reserved_chars()
    def show(self, switch):
        """Shows attributes of <switch>. """
        url = self.object_url('switch', switch)
        return self.check_response(self.httpClient.request("GET", url))


class Port(ClientBase):
    """Port related operations. """

    @check_reserved_chars(slashes_ok=['port'])
    def register(self, switch, port):
        """Register a <port> with <switch>. """
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("PUT", url))

    @check_reserved_chars(slashes_ok=['port'])
    def delete(self, switch, port):
        """Deletes information of the <port> for <switch> """
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("DELETE", url))

    @check_reserved_chars(slashes_ok=['port'])
    def connect_nic(self, switch, port, node, nic):
        """Connects <port> of <switch> to <nic> of <node>. """
        url = self.object_url('switch', switch, 'port', port, 'connect_nic')
        payload = json.dumps({'node': node, 'nic': nic})
        return self.check_response(
                self.httpClient.request("POST", url, data=payload)
                )

    @check_reserved_chars(slashes_ok=['port'])
    def detach_nic(self, switch, port):
        """"Detaches <port> of <switch>. """
        url = self.object_url('switch', switch, 'port', port, 'detach_nic')
        return self.check_response(self.httpClient.request("POST", url))

    @check_reserved_chars(slashes_ok=['port'])
    def show(self, switch, port):
        """Show what's connected to <port>"""
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("GET", url))

    @check_reserved_chars(slashes_ok=['port'])
    def port_revert(self, switch, port):
        """removes all vlans from a switch port"""
        url = self.object_url('switch', switch, 'port', port, 'revert')
        return self.check_response(self.httpClient.request("POST", url))
