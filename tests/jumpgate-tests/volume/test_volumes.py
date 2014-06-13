from mock import MagicMock
from jumpgate.volume.drivers.sl.volumes import VolumesDetailV1
from jumpgate.volume.drivers.sl.volumes import VIRTUAL_DISK_IMAGE_TYPE
from SoftLayer import SoftLayerAPIError

import unittest

TENANT_ID = 333333
GOOD_VOLUME_ID = "100000"
INVALID_VOLUME_ID = "ABCDEFG"

OP_CODE = {
    'GOOD_PATH': {
        'SIMPLE': 1,
        'RET_VIRT_DISK_IMGS': 4,
        'RET_VIRT_DISK_IMG': 5,
    },
    'BAD_PATH': {
        'VIRT_DISK_IMG_OBJ_INVALID': 2,
        'GET_VIRT_DISK_IMG_API': 3,
    }
}


class TestVolumesVolumesDetailV1(unittest.TestCase):

    def setUp(self):

        self.req, self.resp = MagicMock(), MagicMock()
        self.app = VolumesDetailV1()
        self.req.env = {'sl_client': {
                        'Virtual_Disk_Image': MagicMock(),
                        'Virtual_Guest': MagicMock(),
                        'Account': MagicMock()}}

    def set_SL_client(self, operation=OP_CODE['GOOD_PATH']['SIMPLE']):
        if operation == OP_CODE['GOOD_PATH']['SIMPLE']:
            # simple good path testing, use default sl_client
            return
        elif operation == OP_CODE['BAD_PATH']['VIRT_DISK_IMG_OBJ_INVALID']:
            # Virtual_Disk_Image.getObject failure.
            self.req.env['sl_client']['Virtual_Disk_Image'].getObject = \
                MagicMock(side_effect=SoftLayerAPIError(400,
                                                        "MockFault",
                                                        None))
        elif operation == OP_CODE['BAD_PATH']['GET_VIRT_DISK_IMG_API']:
            #getVirtualDiskImages() SLAPI failure
            setattr(self.req.env['sl_client']['Account'],
                    'getVirtualDiskImages',
                    MagicMock(side_effect=SoftLayerAPIError(400,
                                                            "MockFault",
                                                            None)))
        elif operation == OP_CODE['GOOD_PATH']['RET_VIRT_DISK_IMGS']:
            def _return_disk_imgs(*args, **kwargs):
                return [{'typeId': VIRTUAL_DISK_IMAGE_TYPE['SYSTEM'],
                         'blockDevices': [MagicMock()],
                        },
                        {'typeId': VIRTUAL_DISK_IMAGE_TYPE['SWAP'],
                         'blockDevices': [MagicMock()],
                        }]
            setattr(self.req.env['sl_client']['Account'],
                    'getVirtualDiskImages',
                    MagicMock(side_effect=_return_disk_imgs))
        elif operation == OP_CODE['GOOD_PATH']['RET_VIRT_DISK_IMG']:
            def _return_disk_img(*args, **kwargs):
                return {'typeId': VIRTUAL_DISK_IMAGE_TYPE['SYSTEM'],
                         'blockDevices': [MagicMock()],
                       }
            self.req.env['sl_client']['Virtual_Disk_Image'].getObject = \
                MagicMock(side_effect=_return_disk_img)

    def test_on_get_for_volume_list_good(self):
        """ Test the good path of list volumes"""
        self.set_SL_client()
        self.app.on_get(self.req, self.resp, TENANT_ID, "detail")
        self.assertEquals(self.resp.status, 200)

    def test_on_get_for_volume_unknown_param(self):
        self.set_SL_client()
        self.app.on_get(self.req, self.resp, TENANT_ID, None)
        self.assertEquals(self.resp.status, 400)

    def test_on_get_for_volume_details_good(self):
        """ Test the good path of show volume"""
        self.set_SL_client()
        self.app.on_get(self.req, self.resp, TENANT_ID, GOOD_VOLUME_ID)
        self.assertEquals(self.resp.status, 200)

    def test_on_get_for_volume_details_invalid_volume_id(self):
        """ Test the bad path of show volume with invalid volume id"""
        self.set_SL_client()
        self.app.on_get(self.req, self.resp, TENANT_ID, INVALID_VOLUME_ID)
        self.assertEquals(self.resp.status, 400)

    def test_on_get_for_volume_details_SoftLayerAPIError(self):
        """ Test the bad path of show volume with SLAPI exception"""
        self.set_SL_client(
            operation=OP_CODE['BAD_PATH']['VIRT_DISK_IMG_OBJ_INVALID'])
        self.app.on_get(self.req, self.resp, TENANT_ID, GOOD_VOLUME_ID)
        self.assertRaises(SoftLayerAPIError)

    def test_on_get_for_volume_list_SoftLayerAPIError(self):
        """ Test the bad path of list volumes with SLAPI exception"""
        self.set_SL_client(
            operation=OP_CODE['BAD_PATH']['GET_VIRT_DISK_IMG_API'])
        self.app.on_get(self.req, self.resp, TENANT_ID, GOOD_VOLUME_ID)
        self.assertRaises(SoftLayerAPIError)

    def test_on_get_for_volume_details_good_format_volumes(self):
        """ Test the good path of format_volume func during show volume"""
        self.set_SL_client(
            operation=OP_CODE['GOOD_PATH']['RET_VIRT_DISK_IMG'])
        self.app.on_get(self.req, self.resp, TENANT_ID, GOOD_VOLUME_ID)
        self.assertEquals(list(self.resp.body.keys()), ['volume'])

    def test_on_get_for_volume_list_good_format_volumes(self):
        """ Test the good path of format_volume func during show volume"""
        self.set_SL_client(
            operation=OP_CODE['GOOD_PATH']['RET_VIRT_DISK_IMGS'])
        self.app.on_get(self.req, self.resp, TENANT_ID, "detail")
        self.assertEquals(list(self.resp.body.keys()), ['volumes'])

    def tearDown(self):
        self.req, self.resp, self.app = None, None, None
