from jumpgate.common.error_handling import bad_request
from operator import itemgetter

NETWORK_MASK = 'id, name, subnets'


class NetworkV2(object):
    def on_get(self, req, resp, network_id):
        """
        Shows information for a specified network. (net-show)
        @param req: Http Request body
        @param resp: Http Response body
        @param network_id: Network Id
        @return: Http status
        """
        client = req.env['sl_client']
        tenant_id = req.env['auth']['tenant_id']
        pub_networks = client['Account'].getPublicNetworkVlans(mask='id')
        pub_network_id_list = [network['id'] for network in pub_networks]
        try:
            network_id = int(network_id)
        except Exception:
            return bad_request(resp, message="Malformed request body")
        vlan = client['Network_Vlan'].getObject(id=network_id,
                                                mask=NETWORK_MASK)
        resp.body = \
            {'network': format_network(vlan, tenant_id,
                                       is_public_network(pub_network_id_list,
                                                         vlan.get('id')))}
        resp.status = 200


class NetworksV2(object):
    def on_get(self, req, resp):
        """
        Handles net-list/net-show
        @param req: Http Request body
        @param resp: Http Response body
        """
        tenant_id = req.env['auth']['tenant_id']
        client = req.env['sl_client']
        vlans = client['Account'].getNetworkVlans(mask=NETWORK_MASK)
        pub_networks = client['Account'].getPublicNetworkVlans(mask='id')
        pub_network_id_list = [network['id'] for network in pub_networks]
        sl_name = req.get_param('name')
        if sl_name:
            # Neutron is not using the proper endpoint to do net-show.
            # It is handled here as a work around.
            vlan_matched = next(
                (vlan for vlan in vlans if str(vlan.get('id')) == sl_name),
                None)
            if vlan_matched:
                resp.body = {
                    'networks': [{'id': str(vlan_matched.get('id'))}]
                }
            else:
                resp.body = {'networks': []}
        else:
            network = \
                [format_network(vlan, tenant_id,
                                is_public_network(pub_network_id_list,
                                                  vlan.get('id'))) for vlan in
                 sorted(vlans, key=itemgetter('id'))]
            resp.body = {'networks': network}
        resp.status = 200


def format_network(sl_vlan, tenant_id, is_public):
    return {
        'admin_state_up': True,
        'id': sl_vlan.get('id'),
        'name': sl_vlan.get('name'),
        'shared': False,
        'status': 'ACTIVE',
        'subnets': [str(subnet['id']) for subnet in sl_vlan['subnets']],
        'tenant_id': tenant_id,
        'provider:network_type': "vlan",
        'provider:segmentation_id': sl_vlan.get('id'),
        'provider:physical_network': is_public
    }


def is_public_network(public_list, vlan):
    """
    Checks if the vlan is public.
    @param public_list: List of public vlan
    @param vlan: the vlan to check
    @return: True if vlan is public, False otherwise.
    """
    if vlan in public_list:
        return True
    else:
        return False
