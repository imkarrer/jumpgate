import unittest

from mock import MagicMock, patch
import SoftLayer

from jumpgate.compute.drivers.sl.servers import (
	ServerActionV2, ServersDetailV2)


TENANT_ID = 333333
INSTANCE_ID = 7890782


class TestServersServerActionV2(unittest.TestCase):

    def test_init(self):
        app = MagicMock()
        instance = ServerActionV2(app)
        self.assertEqual(app, instance.app)

    def setUp(self):
        self.req, self.resp = MagicMock(), MagicMock()
        self.vg_clientMock = MagicMock()
        self.req.env = {'sl_client': {
                        'Virtual_Guest': self.vg_clientMock,
                        'Account': MagicMock()}}

    def perform_server_action(self, tenant_id, instance_id):
        instance = ServerActionV2(app=None)
        instance.on_post(self.req, self.resp, tenant_id, instance_id)

    @patch('SoftLayer.CCIManager')
    @patch('SoftLayer.CCIManager.get_instance')
    @patch('json.loads')
    def test_on_post_create(self, bodyMock, cciGetInstanceMock,
                            cciManagerMock):
        bodyMock.return_value = {'createImage': {'name': 'foobar'}}
        cciGetInstanceMock.return_value = {'blockDevices':
                                           [{'device': 0},
                                            {'device': 1}]}
        instance = ServerActionV2(MagicMock())
        instance.on_post(self.req, self.resp, TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 202)

    @patch('SoftLayer.CCIManager')
    @patch('json.loads')
    def test_on_post_create_fail(self, bodyMock, cciManagerMock):
        e = SoftLayer.SoftLayerAPIError(123, 'abc')
        self.vg_clientMock.createArchiveTransaction.side_effect = e
        bodyMock.return_value = {'createImage': {'name': 'foobar'}}
        instance = ServerActionV2(MagicMock())
        instance.on_post(self.req, self.resp, TENANT_ID, INSTANCE_ID)
        self.assertRaises(SoftLayer.SoftLayerAPIError,
                          self.vg_clientMock.createArchiveTransaction)
        self.assertEquals(self.resp.status, 500)

    @patch('json.loads')
    def test_on_post_powerOn(self, bodyMock):
        bodyMock.return_value = {'os-start': None}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 202)
        self.vg_clientMock.powerOn.assert_called_with(id=INSTANCE_ID)

    @patch('json.loads')
    def test_on_post_powerOff(self, bodyMock):
        bodyMock.return_value = {'os-stop': None}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 202)
        self.vg_clientMock.powerOff.assert_called_with(id=INSTANCE_ID)

    @patch('json.loads')
    def test_on_post_reboot_soft(self, bodyMock):
        bodyMock.return_value = {'reboot': {'type': 'SOFT'}}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 202)
        self.vg_clientMock.rebootSoft.assert_called_with(id=INSTANCE_ID)

    @patch('json.loads')
    def test_on_post_reboot_hard(self, bodyMock):
        bodyMock.return_value = {'reboot': {'type': 'HARD'}}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 202)
        self.vg_clientMock.rebootHard.assert_called_with(id=INSTANCE_ID)

    @patch('json.loads')
    def test_on_post_reboot_default(self, bodyMock):
        bodyMock.return_value = {'reboot': {'type': 'DEFAULT'}}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 202)
        self.vg_clientMock.rebootDefault.assert_called_with(id=INSTANCE_ID)

    @patch('json.loads')
    @patch('SoftLayer.managers.vs.VSManager.upgrade')
    def test_on_post_resize(self, upgradeMock, bodyMock):
        bodyMock.return_value = {"resize": {"flavorRef": "2"}}
        upgradeMock.return_value = True
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 202)

    @patch('json.loads')
    def test_on_post_resize_invalid(self, bodyMock):
        bodyMock.return_value = {"resize": {"flavorRef": "17"}}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 400)

    @patch('json.loads')
    def test_on_post_confirm_resize(self, bodyMock):
        bodyMock.return_value = {'confirmResize': None}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 204)

    @patch('json.loads')
    def test_on_post_body_empty(self, bodyMock):
        bodyMock.return_value = {}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 400)
        self.assertEquals(self.resp.body['badRequest']
                          ['message'], 'Malformed request body')

    @patch('json.loads')
    def test_on_post_instanceid_empty(self, bodyMock):
        bodyMock.return_value = {'os-stop': None}
        self.perform_server_action(TENANT_ID, '')
        self.assertEquals(self.resp.status, 404)
        self.assertEquals(self.resp.body['notFound']
                          ['message'], 'Invalid instance ID specified.')

    @patch('json.loads')
    def test_on_post_instanceid_none(self, bodyMock):
        bodyMock.return_value = {'os-start': None}
        self.perform_server_action(TENANT_ID, None)
        self.assertEquals(self.resp.status, 404)

    @patch('json.loads')
    def test_on_post_malformed_body(self, bodyMock):
        bodyMock.return_value = {'os_start': None}
        self.perform_server_action(TENANT_ID, INSTANCE_ID)
        self.assertEquals(self.resp.status, 400)

    def tearDown(self):
        self.req, self.resp, self.vg_clientMock = None, None, None


class TestServersServersDetailV2(unittest.TestCase):

    def setUp(self):
        self.req, self.resp = MagicMock(), MagicMock()
        self.app = MagicMock()
        self.instance = ServersDetailV2(self.app)

    def test_init(self):
        self.assertEquals(self.app, self.instance.app)

    @patch('SoftLayer.CCIManager.list_instances')
    def test_on_get(self, mockListInstance):
        href = u'http://localhost:5000/compute/v2/333582/servers/4846014'
        dict = {'status': 'ACTIVE',
                'updated': '2014-05-23T10:58:29-05:00',
                'hostId': 4846014,
                'user_id': 206942,
                'addresses': {
                    'public': [{
                        'version': 4,
                        'addr': '23.246.195.197',
                        'OS-EXT-IPS:type': 'fixed'}],
                    'private': [{
                        'version': 4,
                        'addr': '10.107.38.132',
                        'OS-EXT-IPS:type': 'fixed'}]},
                'links': [{
                    'href': href,
                    'rel': 'self'}],
                'created': '2014-05-23T10:57:07-05:00',
                'tenant_id': 333582,
                'image_name': '',
                'OS-EXT-STS:power_state': 1,
                'accessIPv4': '',
                'accessIPv6': '',
                'OS-EXT-STS:vm_state': 'ACTIVE',
                'OS-EXT-STS:task_state': None,
                'flavor': {
                    'id': '1',
                    'links': [{
                        'href': 'http://localhost:5000/compute/v2/flavors/1',
                        'rel': 'bookmark'}]},
                'OS-EXT-AZ:availability_zone': 154820,
                'id': '4846014',
                'security_groups': [{
                    'name': 'default'}],
                'name': 'minwoo-metis',
                }
        status = {'keyName': 'ACTIVE', 'name': 'Active'}
        pwrState = {'keyName': 'RUNNING', 'name': 'Running'}
        sshKeys = []
        dataCenter = {'id': 154820, 'name': 'dal06', 'longName': 'Dallas 6'}
        orderItem = {'itemId': 858,
                     'setupFee': '0',
                     'promoCodeId': '',
                     'oneTimeFeeTaxRate': '.066',
                     'description': '2 x 2.0 GHz Cores',
                     'laborFee': '0',
                     'oneTimeFee': '0',
                     'itemPriceId': '1641',
                     'setupFeeTaxRate': '.066',
                     'order': {
                         'userRecordId': 206942,
                         'privateCloudOrderFlag': False},
                     'laborFeeTaxRate': '.066',
                     'categoryCode': 'guest_core',
                     'setupFeeDeferralMonths': 12,
                     'parentId': '',
                     'recurringFee': '0',
                     'id': 34750548,
                     'quantity': '',
                     }
        billingItem = {'modifyDate': '2014-06-05T08:37:01-05:00',
                       'resourceTableId': 4846014,
                       'hostName': 'minwoo-metis',
                       'recurringMonths': 1,
                       'orderItem': orderItem,
                       }

        mockListInstance.return_value = {'billingItem': billingItem,
                                         'datacenter': dataCenter,
                                         'powerState': pwrState,
                                         'sshKeys': sshKeys,
                                         'status': status,
                                         'accountId': 'foobar',
                                         'id': '1234',
                                         'createDate': 'foobar',
                                         'hostname': 'foobar',
                                         'modifyDate': 'foobar'
                                         }
        self.instance.on_get(self.req, self.resp)
        self.assertEquals(set(self.resp.body['servers'][0].keys()),
                          set(dict.keys()))
        self.assertEquals(self.resp.status, 200)
