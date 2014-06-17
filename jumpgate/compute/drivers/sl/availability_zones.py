
from SoftLayer import CCIManager

from jumpgate.common.utils import lookup


class AvailabilityZonesV2(object):
    def on_get(self, req, resp, tenant_id):
        client = req.env['sl_client']
        cci = CCIManager(client)

        all_options = cci.get_create_options()

        results = []
        # Load and sort all data centers
        for option in all_options['datacenters']:
            name = lookup(option, 'template', 'datacenter', 'name')

            results.append({'zoneState': {'available': True}, 'hosts': None,
                            'zoneName': name})
        results = sorted(results, key=lambda x: x['zoneName'])

        resp.body = {'availabilityZoneInfo': results}
        resp.status = 200
